# coding: utf-8
from PIL import PngImagePlugin   # 若要處理PNG或JPG格式 需要載入避免動態搜尋時錯誤
from PIL import JpegImagePlugin
from PIL import Image
from PIL import ImageOps
import logging
import win32print
import struct
from io import StringIO, BytesIO


class ThermalPrint:

    def __init__(self, printerName:str, img_maxWidth:int, header_margin:int, footer_margin:int, line_spacing:int, *, cutting=False):
        self.hPrinter = win32print.OpenPrinter(printerName)
        self.strPrinterName = printerName
        self.img_maxWidth = img_maxWidth
        self.header_margin = header_margin
        self.footer_margin = footer_margin
        self.imgFileName = ''
        self.rawPrintBuf = StringIO()
        self.line_spacing = line_spacing
        self.hPipe = None
        self.cutting = cutting

        Image._initialized = 2

    def printing(self, *, content: str=None):
        self.hPrinter = win32print.OpenPrinter(self.strPrinterName)

        if content is not None:
            hJob = win32print.StartDocPrinter(self.hPrinter, 1, (self.imgFileName, None, "TEXT"))
            win32print.WritePrinter(self.hPrinter, content.encode("cp950"))
        else:
            hJob = win32print.StartDocPrinter(self.hPrinter, 1, (self.imgFileName, None, "RAW"))
            win32print.StartPagePrinter(self.hPrinter)
            win32print.WritePrinter(self.hPrinter, self.rawPrintBuf.getvalue())
        win32print.EndDocPrinter(self.hPrinter)
        win32print.ClosePrinter(self.hPrinter)

    def load(self, tempBytesIO :BytesIO):
        '''
        :param im: StringIO of Image Data
        :return:
        REF: https://gist.github.com/scruss/95c61c9a1501ada2a6c5
             https://stackoverflow.com/questions/44107254/esc-pos-command-esc-for-printing-bit-image-on-printer    24pix/line
             Full ESCPOS Command Manual P.15 bit-image mode
             http://px-download.s3.amazonaws.com/SDK/ESCPOS_Command_Manual.pdf?AWSAccessKeyId=AKIAIFUMS733QL4JIF4A&Expires=1547791952&Signature=ZoNtRMrck%2FHDJHiFnWIGajM%2BuUc%3D
             Java Version - 解釋得很清楚 http://new-grumpy-mentat.blogspot.com/2014/06/java-escpos-image-printing.html
        '''

        ESC = b'\x1b'
        logging.debug('Size- ' + str(int(tempBytesIO.getbuffer().nbytes/8/1024)) + ' kBytes')
        im = Image.open(tempBytesIO)
        #logging.debug(im.format)

        # Invert image, via greyscale for compatibility
        im = ImageOps.invert(im.convert('L'))
        # ... and now convert back to single bit
        im = im.convert('1')    # type: Image
        logging.debug('im.size')
        logging.debug(im.size)

        (img_width, img_height) = im.size    # PIL image size property tuple of (width, height)
        if img_width > self.img_maxWidth:
            img_height = int(img_height*(self.img_maxWidth/img_width))
            img_width = self.img_maxWidth

        p_im = im.resize((img_width, img_height), Image.BILINEAR)
        logging.debug('p_im.size')
        logging.debug(p_im.size)
        # rotate 90 degrees for output
        temp_im = p_im.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
        # 圖形旋轉九十度後 橫向列印的部份
        logging.debug('temp_im.size')
        logging.debug(temp_im.size)

        # if origin scaled image height is not a multiple of 24 pixels, fix that
        if temp_im.size[0] % 24:
            im2 = Image.new('1', (temp_im.size[0] + 24 - temp_im.size[0] % 24, temp_im.size[1]), 'black')  # black 才是不列印
            im2.paste(temp_im, (0, 0))
            temp_im = im2

        logging.debug('temp_im.size After Fit a multiple of 24 pixels')
        logging.debug(temp_im.size)

        self.rawPrintBuf.close()
        self.rawPrintBuf = BytesIO()

        # Line Spacing 30h
        self.rawPrintBuf.write(ESC + b'\x33' + bytes([self.line_spacing]))
        self.rawPrintBuf.write(ESC + b'\x4a' + bytes([self.header_margin]))  # ESC J n

        for row in range(int(temp_im.size[0] / 24)):
            strip = temp_im.crop((row * 24, 0, (row + 1) * 24, temp_im.size[1]))    # crop rectangle, as a (left, upper, right, lower)-tuple <= 380px
            # ESC * 33  ==> 24 dots double density mode
            # self.rawPrintBuf.write(b''.join((ESC+b'\x2a\x21', struct.pack('2B', temp_im.size[1] % (256), int(temp_im.size[1] / (256))), strip.tobytes())))
            # struct.pack('2B', temp_im.size[1] % (256), int(temp_im.size[1] / (256))) 指定  nl, nh
            self.rawPrintBuf.write(ESC + b'\x2a\x21' + struct.pack('2B', temp_im.size[1] % 256, int(temp_im.size[1] / 256)) + strip.tobytes())
            self.rawPrintBuf.write(ESC + b'\x4a\x00')  # ESC J n

        # 針對GP58 等加熱頭比較後縮的機種增加頁尾出紙 但會對其他機種造成定位麻煩
        # 應該把頁前頁尾放在 設定檔內方便調整
        self.rawPrintBuf.write(ESC + b'\x4a' + bytes([self.footer_margin]))  # ESC J n
        if self.cutting:
            self.rawPrintBuf.write(ESC + b'\x69')
