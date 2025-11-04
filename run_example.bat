@echo off
REM Пример использования скрипта для обработки обоих SVG файлов в Windows

echo ==========================================
echo Обработка SVG файлов из Kiri:Moto
echo ==========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Установка зависимостей
echo Установка зависимостей...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Внимание: Некоторые зависимости могут быть не установлены.
    echo Попробуйте вручную: pip install cairosvg PyPDF2 reportlab
    pause
)

echo.

REM Обработка оригинального файла
if exist "ladyghoststl-2-014.svg" (
    echo Обработка оригинального файла: ladyghoststl-2-014.svg
    echo ------------------------------------------
    python process_svg_to_a4_pdf.py ladyghoststl-2-014.svg --output ./output_original
    echo.
) else (
    echo Файл ladyghoststl-2-014.svg не найден в текущей директории
    echo.
)

REM Обработка оптимизированного файла
if exist "nested2.svg" (
    echo Обработка оптимизированного файла: nested2.svg
    echo ------------------------------------------
    python process_svg_to_a4_pdf.py nested2.svg --output ./output_nested
    echo.
) else (
    echo Файл nested2.svg не найден в текущей директории
    echo.
)

echo ==========================================
echo Обработка завершена!
echo ==========================================
echo.
echo Результаты находятся в директориях:
echo   - ./output_original/ (оригинальный файл)
echo   - ./output_nested/ (оптимизированный файл)
echo.
echo Основные результаты:
echo   - *_A4.pdf - готовые PDF для печати
echo   - *_numbered.svg - SVG с номерами слоёв
echo   - *_long.pdf - полные PDF одной страницей
echo.
pause
