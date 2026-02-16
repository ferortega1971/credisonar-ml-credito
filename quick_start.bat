@echo off
echo ========================================
echo   CREDISONAR - Quick Start
echo ========================================
echo.

echo [1/3] Instalando dependencias...
pip install -r requirements.txt
echo.

echo [2/3] Entrenando modelo...
python train_model.py
echo.

echo [3/3] Iniciando interfaz...
echo.
echo Abriendo navegador en http://localhost:8501
echo.
streamlit run src/ui/app.py

pause
