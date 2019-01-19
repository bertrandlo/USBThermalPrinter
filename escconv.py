# coding: utf-8
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QWidget, QGridLayout, QPushButton
from PIL import PngImagePlugin   #若要處理PNG或JPG格式 需要載入避免動態搜尋時錯誤
from PIL import JpegImagePlugin
from PIL import Image
from PIL import ImageOps
import logging, win32print, struct, os, sys
from io import StringIO, BytesIO
from time import sleep


class myGraphicsScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super(myGraphicsScene, self).__init__(*args, **kwargs)

    def dragMoveEvent(self, event):
        #預設忽略拖放 因為拖拉圖片 利用覆蓋原來的 DragMove
        return

class myGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(myGraphicsView, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.imgScene = myGraphicsScene()
        #self.imgScene.setSceneRect(0, 0, 380, 380)
        self.setScene(self.imgScene)
        self.pixmapitem = QPixmap()
        self.pixmapitem_for_printing = QPixmap()
        self.imgFileName = ''

    def dragEnterEvent(self, event):
        logging.debug('Drag - ' + event.mimeData().text())
        event.acceptProposedAction()

    def showImage(self, img: QPixmap):
        '''
        :param img: QPixmap
        '''
        if img.size().width() > 380 or img.size().height() > 380:
            self.pixmapitem = self.imgScene.addPixmap(
                img.scaled(QSize(380, 380), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.pixmapitem = self.imgScene.addPixmap(img)

        self.pixmapitem_for_printing = img

        x_offset = (380 - self.pixmapitem.pixmap().size().width()) / 2
        y_offset = (380 - self.pixmapitem.pixmap().size().height()) / 2
        self.pixmapitem.setOffset(x_offset, y_offset)
        self.imgScene.update()

    def dropEvent(self, event):
        self.imgScene.clear()
        logging.debug('Drop - ' + event.mimeData().urls()[0].toLocalFile())
        event.acceptProposedAction()
        img = QPixmap()
        img.load(event.mimeData().urls()[0].toLocalFile())
        self.imgFileName = event.mimeData().urls()[0].toLocalFile()
        self.showImage(img)

class UiForm(QWidget):
    def __init__(self, app):
        super(UiForm, self).__init__()

        settings = QSettings("settings.ini", QSettings.IniFormat)

        self.setStyleSheet("background-color: #D8D8D8;")
        self.setMinimumSize(410, 420)
        style = "font-size: 12px; padding: 1px; border-style: solid; border: 1px solid gray; border-radius: 4px;"

        iconPath = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'icon.ico')
        self.setWindowIcon(QIcon(iconPath))
        self.setWindowTitle('Thermal Printer Tool')

        self.gridLayout = QGridLayout(self)
        self.timer = QTimer(self)

        self.picviewer = myGraphicsView(self)
        self.picviewer.resize(QSize(380, 380))
        self.btnPrint = QPushButton('Print')
        self.btnTest = QPushButton('Test')
        self.btnPipe = QPushButton('Pipe')

        self.gridLayout.addWidget(self.picviewer, 1, 0, 1, 20)
        self.gridLayout.addWidget(self.btnPrint, 0, 18, 1, 2)
        self.gridLayout.addWidget(self.btnTest, 0, 15, 1, 2)
        self.gridLayout.addWidget(self.btnPipe, 0, 12, 1, 2)
        self.setLayout(self.gridLayout)
        #self.resize(self.settings.value("size", QSize(800, 400)).toSize())
        self.resize(QSize(420, 420))

        self.btnPrint.clicked.connect(self.fnPrint)
        self.btnTest.clicked.connect(self.fnTest)
        self.btnPipe.clicked.connect(self.fnPipe)

        self.printer = ThermalPrint(strPrinterName=settings.value("printer", '', type=str),
                                    img_maxWidth=settings.value("format/maxwidthpixels", 380, type=int),
                                    line_spacing=settings.value("format/line_spacing", 0, type=str),
                                    header_margin=settings.value("format/header_margin", 1, type=int),
                                    footer_margin=settings.value("format/footer_margin", 1, type=int))

    def fnPipe(self):
        self.printer.fnCreateReceivePipe()

    def fnTest(self):

        if QFileInfo(self.picviewer.imgFileName).isFile() != True:
            return False

        hPipe = QLocalSocket(self)
        hPipe.connectToServer('thermalprint', QIODevice.ReadWrite)
        if hPipe.waitForConnected(-1):
            hPipe.open(QIODevice.ReadWrite)
            hPipe.write(QByteArray().append(self.picviewer.imgFileName))
            hPipe.flush()
            logging.debug('Socket State - ' + str(hPipe.state()))

        hPipe.close()

    def fnPrint(self):

        printer = self.printer
        pixmap = self.picviewer.pixmapitem_for_printing

        tempQIODev = QBuffer()
        pixmap.save(tempQIODev, "PNG")
        printer.load(BytesIO(tempQIODev.data())) #傳入 QByteArray inst.
        printer.printing()
        return True



class ThermalPrint(QObject):

    def __init__(self, strPrinterName:str, img_maxWidth:int, header_margin:int, footer_margin:int, line_spacing:str):
        super(ThermalPrint, self).__init__()
        self.hPrinter = win32print.OpenPrinter(strPrinterName)  # GP-5890X
        self.strPrinterName = strPrinterName
        self.img_maxWidth = img_maxWidth
        self.header_margin = b'\x0a'*header_margin
        self.footer_margin = b'\x0a'*footer_margin
        self.imgFileName = ''
        self.rawPrintBuf = StringIO()
        self.line_spacing = line_spacing.encode('ascii')
        self.hPipe = None
        self.strPipeName = '\\.\pipe\thermalprint'

        Image._initialized = 2

    def fnCreateReceivePipe(self):
        self.server = QLocalServer()                    # 提供 win32 pipe
        self.server.setMaxPendingConnections(1)
        logging.debug(str(self.server.listen('thermalprint')) + ' - ' + self.server.fullServerName())
        self.server.newConnection.connect(self.servicePrint)

    def servicePrint(self):
        '''
            為了方便撕取 左右各留空 0.5cm 頁首頁尾各多送出 1cm 因此信用卡刷卡單大小 (5.8cm,10cm) 實際輸出應為 (4.8cm , 8cm)
            對應 206dpi 輸出尺寸應為 (380px , 630px)
            常見的解析度 Resolution: 203~207dpi(8dot/mm)
        '''
        logging.debug('Pending Connections: ' + str(self.server.hasPendingConnections()))
        client = self.server.nextPendingConnection()    #type: QLocalSocket
        client.setReadBufferSize(1024)
        client.waitForDisconnected(msecs=30000)

        msg = client.readAll()  # type: QByteArray
        logging.debug('DATA - ' + msg.data().decode('utf-8'))
        fn = QFileInfo(msg.data().decode('utf-8')).absoluteFilePath()

        img = QPixmap()
        img.load(fn)
        logging.debug('width: ' + str(img.width()) + ' height: ' + str(img.height()))

        if img.size().width() > self.img_maxWidth:  # 縮圖到紙捲最大列印寬度
            img = img.scaled(QSize(self.img_maxWidth, img.size().height()*(img.size().width()/self.img_maxWidth)), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        tempQIODev = QBuffer()
        img.save(tempQIODev, "PNG")

        self.load(BytesIO(tempQIODev.data()))  # 傳入 QByteArray inst.
        self.printing()

        logging.debug('ERRMSG - ' + self.server.errorString())
        logging.debug('Pending Connections: ' + str(self.server.hasPendingConnections()))

    def printing(self):
        self.hPrinter = win32print.OpenPrinter(self.strPrinterName)
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
            im2 = Image.new('1', (temp_im.size[0] + 24 - temp_im.size[0] % 24, temp_im.size[1]), 'white')
            im2.paste(temp_im, (0, 0))
            temp_im = im2

        logging.debug('temp_im.size After Fit a multiple of 24 pixels')
        logging.debug(temp_im.size)

        self.rawPrintBuf.close()
        self.rawPrintBuf = BytesIO()

        self.rawPrintBuf.write(self.header_margin)
        # Line Spacing 30h
        self.rawPrintBuf.write(ESC + b'\x33'+self.line_spacing)

        for row in range(int(temp_im.size[0] / 24)):
            strip = temp_im.crop((row * 24, 0, (row + 1) * 24, temp_im.size[1]))    # crop rectangle, as a (left, upper, right, lower)-tuple <= 380px
            # ESC * 33  ==> 24 dots double density mode
            # self.rawPrintBuf.write(b''.join((ESC+b'\x2a\x21', struct.pack('2B', temp_im.size[1] % (256), int(temp_im.size[1] / (256))), strip.tobytes())))
            # struct.pack('2B', temp_im.size[1] % (256), int(temp_im.size[1] / (256))) 指定  nl, nh
            self.rawPrintBuf.write(ESC + b'\x2a\x21' + struct.pack('2B', temp_im.size[1] % (256), int(temp_im.size[1] / (256))) + strip.tobytes())

        # 針對GP58 等加熱頭比較後縮的機種增加頁尾出紙 但會對其他機種造成定位麻煩
        # 應該把頁前頁尾放在 設定檔內方便調整

        self.rawPrintBuf.write(self.footer_margin)
