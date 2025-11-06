#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ распределения слоёв в SVG файле
"""

import xml.etree.ElementTree as ET
import sys
import io
import re
from typing import Tuple, List

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def parse_path_commands(d: str) -> List[Tuple[float, float]]:
    """
    Извлекает все координаты из SVG path

    Args:
        d: атрибут 'd' элемента path

    Returns:
        список координат (x, y)
    """
    points = []

    # Удаляем лишние пробелы и заменяем запятые на пробелы
    d = d.replace(',', ' ')
    d = re.sub(r'\s+', ' ', d)

    # Разбиваем на команды
    # Команды: M, L, H, V, C, S, Q, T, A, Z (и их lowercase версии)
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', d)

    i = 0
    current_x, current_y = 0.0, 0.0
    current_command = None

    while i < len(tokens):
        token = tokens[i]

        # Проверяем, является ли токен командой
        if token in 'MLHVCSQTAZmlhvcsqtaz':
            current_command = token
            i += 1
            continue

        # Обрабатываем координаты в зависимости от команды
        if current_command in ['M', 'm']:  # Move to
            x = float(token)
            y = float(tokens[i + 1]) if i + 1 < len(tokens) else 0

            if current_command == 'M':  # Абсолютные координаты
                current_x, current_y = x, y
            else:  # Относительные координаты
                current_x += x
                current_y += y

            points.append((current_x, current_y))
            i += 2

        elif current_command in ['L', 'l']:  # Line to
            x = float(token)
            y = float(tokens[i + 1]) if i + 1 < len(tokens) else 0

            if current_command == 'L':
                current_x, current_y = x, y
            else:
                current_x += x
                current_y += y

            points.append((current_x, current_y))
            i += 2

        elif current_command in ['H', 'h']:  # Horizontal line
            x = float(token)

            if current_command == 'H':
                current_x = x
            else:
                current_x += x

            points.append((current_x, current_y))
            i += 1

        elif current_command in ['V', 'v']:  # Vertical line
            y = float(token)

            if current_command == 'V':
                current_y = y
            else:
                current_y += y

            points.append((current_x, current_y))
            i += 1

        elif current_command in ['C', 'c']:  # Cubic Bezier
            # C имеет 6 параметров: x1 y1 x2 y2 x y
            params = [float(tokens[i + j]) for j in range(6) if i + j < len(tokens)]

            if len(params) >= 6:
                if current_command == 'C':
                    current_x, current_y = params[4], params[5]
                else:
                    current_x += params[4]
                    current_y += params[5]

                points.append((current_x, current_y))
            i += 6

        elif current_command in ['S', 's']:  # Smooth cubic Bezier
            # S имеет 4 параметра: x2 y2 x y
            params = [float(tokens[i + j]) for j in range(4) if i + j < len(tokens)]

            if len(params) >= 4:
                if current_command == 'S':
                    current_x, current_y = params[2], params[3]
                else:
                    current_x += params[2]
                    current_y += params[3]

                points.append((current_x, current_y))
            i += 4

        elif current_command in ['Q', 'q']:  # Quadratic Bezier
            # Q имеет 4 параметра: x1 y1 x y
            params = [float(tokens[i + j]) for j in range(4) if i + j < len(tokens)]

            if len(params) >= 4:
                if current_command == 'Q':
                    current_x, current_y = params[2], params[3]
                else:
                    current_x += params[2]
                    current_y += params[3]

                points.append((current_x, current_y))
            i += 4

        elif current_command in ['T', 't']:  # Smooth quadratic Bezier
            # T имеет 2 параметра: x y
            params = [float(tokens[i + j]) for j in range(2) if i + j < len(tokens)]

            if len(params) >= 2:
                if current_command == 'T':
                    current_x, current_y = params[0], params[1]
                else:
                    current_x += params[0]
                    current_y += params[1]

                points.append((current_x, current_y))
            i += 2

        elif current_command in ['A', 'a']:  # Arc
            # A имеет 7 параметров: rx ry x-axis-rotation large-arc-flag sweep-flag x y
            params = [float(tokens[i + j]) for j in range(7) if i + j < len(tokens)]

            if len(params) >= 7:
                if current_command == 'A':
                    current_x, current_y = params[5], params[6]
                else:
                    current_x += params[5]
                    current_y += params[6]

                points.append((current_x, current_y))
            i += 7

        elif current_command in ['Z', 'z']:  # Close path
            # Не изменяет координаты
            i += 1

        else:
            # Неизвестная команда, пропускаем
            i += 1

    return points


def get_path_bbox(d: str) -> Tuple[float, float, float, float]:
    """
    Вычисляет bounding box для SVG path

    Args:
        d: атрибут 'd' элемента path

    Returns:
        (min_x, min_y, max_x, max_y)
    """
    points = parse_path_commands(d)

    if not points:
        return (0, 0, 0, 0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return (min(xs), min(ys), max(xs), max(ys))


def analyze_svg(svg_path: str):
    """
    Анализирует распределение слоёв в SVG файле
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    svg_ns = '{http://www.w3.org/2000/svg}'

    # Получаем размеры документа
    width_str = root.get('width', '210mm')
    height_str = root.get('height', '297mm')

    width_mm = float(width_str.replace('mm', '').strip())
    height_mm = float(height_str.replace('mm', '').strip())

    print("=" * 70)
    print("АНАЛИЗ SVG ФАЙЛА")
    print("=" * 70)
    print(f"Размеры документа: {width_mm:.1f} x {height_mm:.1f} мм")
    print(f"ViewBox: {root.get('viewBox', 'не указан')}")

    # Находим все path элементы
    paths = root.findall(f'.//{svg_ns}path')
    print(f"\nВсего слоёв (paths): {len(paths)}")

    if len(paths) == 0:
        print("Слои не найдены!")
        return

    # Анализируем bounding boxes всех слоёв
    print("\nАнализ границ слоёв...")

    all_bboxes = []
    global_min_y = float('inf')
    global_max_y = float('-inf')

    for i, path in enumerate(paths):
        d = path.get('d', '')
        if not d:
            continue

        bbox = get_path_bbox(d)
        min_x, min_y, max_x, max_y = bbox

        all_bboxes.append(bbox)

        global_min_y = min(global_min_y, min_y)
        global_max_y = max(global_max_y, max_y)

        if (i + 1) % 100 == 0:
            print(f"  Обработано: {i + 1}/{len(paths)}")

    print(f"  Обработано: {len(paths)}/{len(paths)}")

    # Вычисляем фактическую область контента
    content_height = global_max_y - global_min_y

    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 70)
    print(f"Фактическая область контента:")
    print(f"  • Минимальная Y координата: {global_min_y:.2f} мм")
    print(f"  • Максимальная Y координата: {global_max_y:.2f} мм")
    print(f"  • Высота контента: {content_height:.2f} мм")
    print(f"  • Высота документа: {height_mm:.2f} мм")
    print(f"  • Пустое пространство: {height_mm - content_height:.2f} мм ({(height_mm - content_height) / height_mm * 100:.1f}%)")

    # Вычисляем сколько страниц A4 реально нужно
    A4_HEIGHT = 297.0
    pages_by_document = int(height_mm / A4_HEIGHT) + (1 if height_mm % A4_HEIGHT > 0 else 0)
    pages_by_content = int(content_height / A4_HEIGHT) + (1 if content_height % A4_HEIGHT > 0 else 0)

    print(f"\nСтраниц A4:")
    print(f"  • По размеру документа: {pages_by_document}")
    print(f"  • По размеру контента: {pages_by_content}")
    print(f"  • Разница (пустые страницы): {pages_by_document - pages_by_content}")

    # Распределение слоёв по высоте
    print(f"\nРаспределение слоёв по страницам A4 (от min_y={global_min_y:.1f}):")

    layer_distribution = {}
    for bbox in all_bboxes:
        min_x, min_y, max_x, max_y = bbox
        # Вычисляем относительно минимальной Y координаты
        relative_y = min_y - global_min_y
        page_num = int(relative_y / A4_HEIGHT)

        if page_num not in layer_distribution:
            layer_distribution[page_num] = 0
        layer_distribution[page_num] += 1

    for page in sorted(layer_distribution.keys()):
        count = layer_distribution[page]
        print(f"  • Страница {page + 1}: {count} слоёв")

    print("=" * 70)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python analyze_layers.py <svg_file>")
        sys.exit(1)

    svg_file = sys.argv[1]
    analyze_svg(svg_file)
