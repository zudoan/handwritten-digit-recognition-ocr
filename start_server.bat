@echo off
chcp 65001 >nul
title NeuralVision Studio - AI Vision Server
color 0b

echo ===============================================================================
echo            🧠 NEURALVISION STUDIO - DEEP LEARNING BENCHMARK & OCR
echo ===============================================================================
echo.

set "PY311=c:\Users\AD\AppData\Local\Programs\Python\Python311\python.exe"

if exist "%PY311%" (
    echo [OK] Tìm thấy môi trường Python 3.11 Deep Learning tại:
    echo      %PY311%
    echo.
    echo Đang khởi động máy chủ tại cổng 8000...
    echo.
    "%PY311%" run_server.py
) else (
    echo [CANH BAO] Khong tim thay Python 3.11 tai duong dan co dinh, thu dung python he thong...
    python run_server.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the khoi dong may chu. Vui long kiem tra lai moi truong!
    pause
)
