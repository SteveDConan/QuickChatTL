@echo off
"C:\Users\PS.Computer\AppData\Roaming\Python\Python310\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed ^
--add-data "sam_translate;sam_translate" ^
--add-data "assets;assets" ^
--add-data "config.json;." ^
--add-data "sam_translate_config.ini;." ^
APPXX.py
pause 