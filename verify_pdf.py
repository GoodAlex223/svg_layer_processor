#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки качества сгенерированного PDF файла
"""

import sys
import io

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from PyPDF2 import PdfReader
from pathlib import Path


def verify_pdf(pdf_path: str):
    """
    Проверяет PDF файл и выводит информацию о страницах
    """
    pdf = PdfReader(pdf_path)

    print("=" * 70)
    print(f"ПРОВЕРКА PDF ФАЙЛА")
    print("=" * 70)
    print(f"Файл: {Path(pdf_path).name}")
    print(f"Всего страниц: {len(pdf.pages)}")

    print("\nИнформация о страницах:")

    for i, page in enumerate(pdf.pages):
        mediabox = page.mediabox
        width = float(mediabox.width)
        height = float(mediabox.height)

        # Конвертируем из points в mm (1 point = 0.352778 mm)
        width_mm = width * 0.352778
        height_mm = height * 0.352778

        # Проверяем соответствие A4 (210 x 297 mm)
        is_a4 = (abs(width_mm - 210) < 1) and (abs(height_mm - 297) < 1)

        status = "✓ A4" if is_a4 else "✗ НЕ A4"

        if (i < 3) or (i >= len(pdf.pages) - 3):  # Показываем первые и последние 3
            print(f"  Страница {i + 1}: {width_mm:.1f} x {height_mm:.1f} мм {status}")
        elif i == 3:
            print(f"  ...")

    print("\n" + "=" * 70)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python verify_pdf.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    verify_pdf(pdf_file)
