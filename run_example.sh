#!/bin/bash
# Пример использования скрипта для обработки обоих SVG файлов

echo "=========================================="
echo "Обработка SVG файлов из Kiri:Moto"
echo "=========================================="
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python 3 не найден!"
    echo "Установите Python 3 и попробуйте снова."
    exit 1
fi

# Проверка наличия pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Ошибка: pip не найден!"
    echo "Установите pip и попробуйте снова."
    exit 1
fi

# Установка зависимостей (если требуется)
echo "Проверка зависимостей..."
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Внимание: Некоторые зависимости могут быть не установлены."
    echo "Попробуйте вручную: pip install cairosvg PyPDF2 reportlab"
fi

echo ""

# Обработка оригинального файла
if [ -f "ladyghoststl-2-014.svg" ]; then
    echo "Обработка оригинального файла: ladyghoststl-2-014.svg"
    echo "------------------------------------------"
    python3 process_svg_to_a4_pdf.py ladyghoststl-2-014.svg --output ./output_original
    echo ""
else
    echo "Файл ladyghoststl-2-014.svg не найден в текущей директории"
    echo ""
fi

# Обработка оптимизированного файла
if [ -f "nested2.svg" ]; then
    echo "Обработка оптимизированного файла: nested2.svg"
    echo "------------------------------------------"
    python3 process_svg_to_a4_pdf.py nested2.svg --output ./output_nested
    echo ""
else
    echo "Файл nested2.svg не найден в текущей директории"
    echo ""
fi

echo "=========================================="
echo "Обработка завершена!"
echo "=========================================="
echo ""
echo "Результаты находятся в директориях:"
echo "  - ./output_original/ (оригинальный файл)"
echo "  - ./output_nested/ (оптимизированный файл)"
echo ""
echo "Основные результаты:"
echo "  - *_A4.pdf - готовые PDF для печати"
echo "  - *_numbered.svg - SVG с номерами слоёв"
echo "  - *_long.pdf - полные PDF одной страницей"
