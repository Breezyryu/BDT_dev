@echo off
echo Converting UI file...

REM 현재 배치 파일 위치로 이동
cd /d "%~dp0"

".venv\Scripts\pyuic6.exe" -x "BatteryDataTool_UI.ui" -o "BatteryDataTool_UI.py"

echo UI conversion complete.
pause

