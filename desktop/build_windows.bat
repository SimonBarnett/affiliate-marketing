@echo off
REM Build Affiliate Marketing as a Windows .exe with dial icon
REM Requires: Python 3.10+, pip install pygame pyinstaller pillow

cd /d "%~dp0"
pip install pygame pyinstaller pillow --quiet
pyinstaller --onefile --windowed --noconfirm ^
    --name "AffiliateMarketing" ^
    --icon dial_icon.ico ^
    --splash splash.png ^
    affiliate_marketing.py
echo.
echo Done: dist\AffiliateMarketing.exe
pause
