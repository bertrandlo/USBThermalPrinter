# USBThermalPrinter  58mm 熱感式印表機列印伺服

- API
  - /priniting  接收圖檔後直接列印
  - /hello 測試回復

- 將 JPG/PNG 轉換成 ESC/POS 指令
- 透過 Flask/Waitress 接受圖檔後發送給印表機
  - http://127.0.0.1:5000/printing 透過 POST 方式接收圖檔
  - For Windows 發送給指定名稱的印表機
  - For linux 發送給 /dev/usb/lp0 (TODO)

- TODO
  - 轉移到 linux 伺服版本 透過 Rasperberry Pi Zero W 或 NanoPi 伺服
