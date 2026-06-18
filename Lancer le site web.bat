@echo off
cd /d "%~dp0"
echo Lancement du calculateur de charges...

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3 -m streamlit run "app.py"
) else (
    python -m streamlit run "app.py"
)
pause
