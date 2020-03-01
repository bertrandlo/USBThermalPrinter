# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['printing_service.py'],
             pathex=['C:\\Users\\brt\\PycharmProjects\\USBThermalPrinter'],
             binaries=[],
             datas=[('printer.ico', '.'), ('settings.ini', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
a.datas += Tree('./post_receive', prefix='post_receive')

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='printing_service',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='printer.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='printing_service')
