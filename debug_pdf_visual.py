#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Продвинутый диагностический скрипт для анализа видимых слоев на каждой странице PDF
"""

import sys
import io
from pathlib import Path
from PyPDF2 import PdfReader
import re

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_visible_layers(page, page_height):
    """
    Анализирует графическое содержимое страницы и определяет видимые слои

    Args:
        page: объект страницы PDF
        page_height: высота страницы в points

    Returns:
        список видимых номеров слоев
    """
    try:
        # Извлекаем текст с позиционной информацией
        text = page.extract_text()

        # Извлекаем все числа
        numbers = re.findall(r'\b\d+\b', text)
        numbers = [int(n) for n in numbers if n.isdigit() and int(n) > 0 and int(n) <= 1000]

        # Удаляем дубликаты и сортируем
        unique_numbers = sorted(set(numbers))

        return unique_numbers
    except Exception as e:
        print(f"Ошибка извлечения: {e}")
        return []

def debug_pdf_visual(pdf_path: Path, max_pages_to_show=5):
    """Анализирует видимое содержимое PDF страниц"""
    reader = PdfReader(pdf_path)

    print(f"Файл: {pdf_path}")
    print(f"Всего страниц: {len(reader.pages)}")
    print()

    all_visible_layers = []

    pages_to_analyze = min(max_pages_to_show, len(reader.pages))

    for page_num in range(pages_to_analyze):
        page = reader.pages[page_num]

        print(f"=== Страница {page_num + 1} ===")

        # Размеры
        mediabox = page.mediabox
        page_width = float(mediabox.width)
        page_height = float(mediabox.height)
        print(f"Размер: {page_width:.1f} x {page_height:.1f} points")

        # Извлекаем видимые слои
        visible_layers = extract_visible_layers(page, page_height)

        if visible_layers:
            all_visible_layers.extend(visible_layers)
            print(f"Найдено видимых слоев: {len(visible_layers)}")
            print(f"Диапазон: {min(visible_layers)} - {max(visible_layers)}")
            if len(visible_layers) <= 20:
                print(f"Слои: {visible_layers}")
            else:
                print(f"Первые 10: {visible_layers[:10]}")
                print(f"Последние 10: {visible_layers[-10:]}")
        else:
            print("Видимых слоев не найдено")

        print()

    # Показываем последнюю страницу если страниц больше max_pages_to_show
    if len(reader.pages) > max_pages_to_show:
        print(f"... (пропущено {len(reader.pages) - max_pages_to_show - 1} страниц) ...\n")

        page = reader.pages[-1]
        print(f"=== Страница {len(reader.pages)} (последняя) ===")

        mediabox = page.mediabox
        page_width = float(mediabox.width)
        page_height = float(mediabox.height)
        print(f"Размер: {page_width:.1f} x {page_height:.1f} points")

        visible_layers = extract_visible_layers(page, page_height)

        if visible_layers:
            all_visible_layers.extend(visible_layers)
            print(f"Найдено видимых слоев: {len(visible_layers)}")
            print(f"Диапазон: {min(visible_layers)} - {max(visible_layers)}")
            if len(visible_layers) <= 20:
                print(f"Слои: {visible_layers}")
            else:
                print(f"Первые 10: {visible_layers[:10]}")
                print(f"Последние 10: {visible_layers[-10:]}")
        else:
            print("Видимых слоев не найдено")

        print()

    # Итоговая статистика
    unique_all = sorted(set(all_visible_layers))
    if unique_all:
        print("=" * 70)
        print("ИТОГОВАЯ СТАТИСТИКА ПО ПРОВЕРЕННЫМ СТРАНИЦАМ:")
        print(f"Всего уникальных слоев найдено: {len(unique_all)}")
        print(f"Диапазон: {min(unique_all)} - {max(unique_all)}")
        print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python debug_pdf_visual.py <pdf_file> [max_pages]")
        print("  max_pages: максимальное количество страниц для детального анализа (по умолчанию: 5)")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    if not pdf_file.exists():
        print(f"Файл не найден: {pdf_file}")
        sys.exit(1)

    max_pages = 5
    if len(sys.argv) >= 3:
        try:
            max_pages = int(sys.argv[2])
        except ValueError:
            print("Неверное значение max_pages")
            sys.exit(1)

    debug_pdf_visual(pdf_file, max_pages)
