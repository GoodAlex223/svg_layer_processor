#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический скрипт для проверки содержимого PDF страниц
"""

import sys
import io
from pathlib import Path
from PyPDF2 import PdfReader

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_pdf(pdf_path: Path):
    """Выводит детальную информацию о PDF"""
    reader = PdfReader(pdf_path)

    print(f"Файл: {pdf_path}")
    print(f"Всего страниц: {len(reader.pages)}")
    print()

    for page_num, page in enumerate(reader.pages, 1):
        print(f"=== Страница {page_num} ===")

        # Размеры
        mediabox = page.mediabox
        print(f"Размер: {float(mediabox.width):.1f} x {float(mediabox.height):.1f} points")

        # Извлекаем текст (номера слоев)
        try:
            text = page.extract_text()
            # Извлекаем все числа из текста
            import re
            numbers = re.findall(r'\d+', text)
            numbers = [int(n) for n in numbers if n.isdigit()]

            if numbers:
                print(f"Найдено номеров слоев: {len(numbers)}")
                print(f"Диапазон: {min(numbers)} - {max(numbers)}")
                print(f"Первые 10: {numbers[:10]}")
                print(f"Последние 10: {numbers[-10:]}")
            else:
                print("Текст не найден")
        except Exception as e:
            print(f"Ошибка извлечения текста: {e}")

        print()

        # Для A4 PDF показываем только первые 3 и последние 3 страницы
        if len(reader.pages) > 10 and page_num == 4:
            print(f"... (пропущено {len(reader.pages) - 6} страниц) ...\n")
            # Перепрыгиваем к последним страницам
            for skip_page_num in range(page_num + 1, len(reader.pages) - 2):
                pass
            continue

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python debug_pdf.py <pdf_file>")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    if not pdf_file.exists():
        print(f"Файл не найден: {pdf_file}")
        sys.exit(1)

    debug_pdf(pdf_file)
