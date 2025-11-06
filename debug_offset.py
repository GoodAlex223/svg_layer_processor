#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to calculate PDF page offsets
"""

import sys
import io

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from reportlab.lib.units import mm

# Данные из анализа
content_min_y = 0.19  # мм
content_height = 7877.59  # мм
A4_HEIGHT = 297.0  # мм

# Конвертируем в points
content_min_y_points = content_min_y * mm
content_height_points = content_height * mm
content_max_y_points = content_min_y_points + content_height_points
A4_HEIGHT_points = A4_HEIGHT * mm

# Количество страниц
num_pages = int(content_height_points / A4_HEIGHT_points) + (1 if content_height_points % A4_HEIGHT_points > 0 else 0)

print(f'Контент:')
print(f'  min_y: {content_min_y} мм = {content_min_y_points:.2f} points')
print(f'  max_y: {content_min_y + content_height} мм = {content_max_y_points:.2f} points')
print(f'  height: {content_height} мм = {content_height_points:.2f} points')
print(f'  A4 height: {A4_HEIGHT} мм = {A4_HEIGHT_points:.2f} points')
print(f'  Страниц A4: {num_pages}')
print()
print(f'\n=== ВАРИАНТ 1: content_max_y - page_num*A4 (от верха вниз) ===')
for page_num in list(range(5)) + list(range(num_pages - 2, num_pages)):
    y_offset = content_max_y_points - (page_num * A4_HEIGHT_points)
    visible_min = y_offset / mm
    visible_max = (y_offset + A4_HEIGHT_points) / mm
    print(f'  Страница {page_num + 1}: y_offset = {y_offset / mm:.2f} мм, видно {visible_min:.2f} - {visible_max:.2f} мм')

print(f'\n=== ВАРИАНТ 2: content_min_y + page_num*A4 (от низа вверх) ===')
for page_num in list(range(5)) + list(range(num_pages - 2, num_pages)):
    y_offset = content_min_y_points + (page_num * A4_HEIGHT_points)
    visible_min = y_offset / mm
    visible_max = (y_offset + A4_HEIGHT_points) / mm
    print(f'  Страница {page_num + 1}: y_offset = {y_offset / mm:.2f} мм, видно {visible_min:.2f} - {visible_max:.2f} мм')

print(f'\n=== ВАРИАНТ 3: content_min_y + reverse_page_num*A4 (текущий код) ===')
for page_num in list(range(5)) + list(range(num_pages - 2, num_pages)):
    reverse_page_num = num_pages - 1 - page_num
    y_offset = content_min_y_points + (reverse_page_num * A4_HEIGHT_points)
    visible_min = y_offset / mm
    visible_max = (y_offset + A4_HEIGHT_points) / mm
    print(f'  Страница {page_num + 1}: reverse={reverse_page_num}, y_offset = {y_offset / mm:.2f} мм, видно {visible_min:.2f} - {visible_max:.2f} мм')
