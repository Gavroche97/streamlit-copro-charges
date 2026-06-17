@echo off
setlocal
cd /d "%~dp0"
echo Lancement de l'application Streamlit...
py -3 -m streamlit run "app.py" --server.port 8501
if %ERRORLEVEL% neq 0 (
    echo.
    echo "py -3" a echoue, tentative avec python...
    python -m streamlit run "app.py" --server.port 8501
    if %ERRORLEVEL% neq 0 (
        echo.
        echo Impossible de lancer Streamlit. Verifiez que Python est installe et que les dependances sont disponibles.
        pause
    )
)
