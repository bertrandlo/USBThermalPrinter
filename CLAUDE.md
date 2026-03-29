# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

USBThermalPrinter is a Chinese-language thermal receipt printing service for 58mm thermal printers (GP-58MB Series, GP-5890X, XP-58C). It converts images to ESC/POS commands and sends them to USB thermal printers on Windows.

## Running the Application

### GUI Application
```bash
python receive.py
```
Reads `settings.ini` for `guiVisibility`, `printer`, and `logging` settings. Shows PyQt5 drag-drop window if `guiVisibility=True`, otherwise starts named pipe server headless.

### HTTP Printing Service
```bash
python printing_service.py
# or with waitress directly:
waitress-serve --listen=*:5000 app:app
```
POST images to `http://host:5000/printing`. Health check at `GET /hello`.

### CLI Image Printing (Unix)
```bash
python test.py image1.jpg image2.png > /dev/usb/lp0
```

### Run Tests
```bash
python -m pytest test/ -v
```

## Architecture

### Two ThermalPrint Classes
There are **two separate implementations** of ThermalPrint:
- [thermal_printer.py](thermal_printer.py) - Standalone class using `win32print` directly
- [escconv.py](escconv.py) `ThermalPrint` class - Inherits `QObject`, adds PyQt5 named pipe server via `QLocalServer`

Both have identical `load()` and `printing()` methods but different parent classes.

### Entry Points
| File | Purpose |
|------|---------|
| [receive.py](receive.py) | GUI/pipeserver entry - reads `settings.ini`, creates `escconv.UiForm` |
| [printing_service.py](printing_service.py) | Flask HTTP service entry |
| [test.py](test.py) | CLI stdout for Unix piping |

### ESC/POS Image Processing ([thermal_printer.py:41-106](thermal_printer.py#L41-L106))
1. Image → grayscale → invert → 1-bit
2. Scale to max width (default 380px)
3. Rotate 90° + flip vertically (horizontal print)
4. Pad width to 24-pixel multiple (ESC/POS requirement)
5. Slice into 24-pixel vertical strips
6. Each strip: `ESC * 33 nl nh [data]` + `ESC J 00`
7. Footer feed + optional cut (`ESC i`)

Key ESC/POS commands: `ESC 33` (line spacing), `ESC J` (feed), `ESC * 33` (24-dot bit image), `ESC i` (cut).

### Named Pipe IPC
- Pipe name: `\\.\pipe\thermalprint`
- Client sends absolute file path as bytes
- Server reads path, loads image via QPixmap, prints

## Configuration

[settings.ini](settings.ini) uses INI format:
```ini
[General]
guiVisibility=True      # Show GUI or run headless
printer=GP-58MB Series  # Windows printer name
logging=True

[format]
maxwidthpixels=380      # Max image width in dots
header_margin=0         # Pre-print feed (dots)
footer_margin=120       # Post-print feed (dots)
line_spacing=0
cutting=True           # Auto-cut after print

[network]
listen=192.168.1.10:5000
```

Settings are read by:
- PyQt5 app: `QSettings("settings.ini", QSettings.IniFormat)`
- Flask service: `INIReader` class from [ini_reader.py](ini_reader.py)

## Building Executables

### Legacy py2exe ([build.py](build.py))
```bash
python build.py py2exe
```

### cx_Freeze ([build-new.py](build-new.py))
```bash
python build-new.py build
```

Both build to `dist/` directory. py2exe excludes `PySide` (not PyQt5), includes PyQt5 DLLs and image format plugins.

## Dependencies

Core: `Pillow`, `PyQt5`, `pywin32`, `Flask`, `Flask-Cors`, `waitress`

## Databases

- [guests.db](guests.db) - Guest records (name, phone, table_id, note, sorting_weight)
- [utf8stroke.db](utf8stroke.db) - Chinese stroke counts for sorting guests by family name

## Encoding

- Text printing: `cp950` (Traditional Chinese Windows encoding)
- Named pipe messages: UTF-8
