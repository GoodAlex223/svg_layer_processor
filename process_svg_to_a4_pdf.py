#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обработки SVG файлов со слоями из Kiri:Moto (ИСПРАВЛЕННАЯ ВЕРСИЯ):
1. Анализирует фактические границы всех слоёв
2. Добавляет видимые номера в центре каждого слоя
3. Конвертирует SVG в PDF
4. Разделяет PDF только на область с контентом (без пустых страниц)

Требования:
    pip install svglib PyPDF2 reportlab

Использование:
    python process_svg_to_a4_pdf_fixed.py input.svg [output_directory]
"""

import xml.etree.ElementTree as ET
import sys
import io
import argparse
import re
from pathlib import Path
from typing import Tuple, List

# Fix console encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def parse_svg_dimensions(svg_root) -> Tuple[float, float]:
    """
    Извлекает размеры SVG документа в миллиметрах

    Returns:
        (width_mm, height_mm)
    """
    width_str = svg_root.get("width", "210mm")
    height_str = svg_root.get("height", "297mm")

    # Удаляем единицы измерения и конвертируем в float
    width_mm = float(width_str.replace("mm", "").strip())
    height_mm = float(height_str.replace("mm", "").strip())

    return width_mm, height_mm


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
    d = d.replace(",", " ")
    d = re.sub(r"\s+", " ", d)

    # Разбиваем на команды
    tokens = re.findall(
        r"[MLHVCSQTAZmlhvcsqtaz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", d
    )

    i = 0
    current_x, current_y = 0.0, 0.0
    current_command = None

    while i < len(tokens):
        token = tokens[i]

        # Проверяем, является ли токен командой
        if token in "MLHVCSQTAZmlhvcsqtaz":
            current_command = token
            i += 1
            continue

        # Обрабатываем координаты в зависимости от команды
        if current_command in ["M", "m"]:  # Move to
            x = float(token)
            y = float(tokens[i + 1]) if i + 1 < len(tokens) else 0

            if current_command == "M":  # Абсолютные координаты
                current_x, current_y = x, y
            else:  # Относительные координаты
                current_x += x
                current_y += y

            points.append((current_x, current_y))
            i += 2

        elif current_command in ["L", "l"]:  # Line to
            x = float(token)
            y = float(tokens[i + 1]) if i + 1 < len(tokens) else 0

            if current_command == "L":
                current_x, current_y = x, y
            else:
                current_x += x
                current_y += y

            points.append((current_x, current_y))
            i += 2

        elif current_command in ["H", "h"]:  # Horizontal line
            x = float(token)

            if current_command == "H":
                current_x = x
            else:
                current_x += x

            points.append((current_x, current_y))
            i += 1

        elif current_command in ["V", "v"]:  # Vertical line
            y = float(token)

            if current_command == "V":
                current_y = y
            else:
                current_y += y

            points.append((current_x, current_y))
            i += 1

        elif current_command in ["C", "c"]:  # Cubic Bezier
            params = [float(tokens[i + j]) for j in range(6) if i + j < len(tokens)]

            if len(params) >= 6:
                if current_command == "C":
                    current_x, current_y = params[4], params[5]
                else:
                    current_x += params[4]
                    current_y += params[5]

                points.append((current_x, current_y))
            i += 6

        elif current_command in ["S", "s"]:  # Smooth cubic Bezier
            params = [float(tokens[i + j]) for j in range(4) if i + j < len(tokens)]

            if len(params) >= 4:
                if current_command == "S":
                    current_x, current_y = params[2], params[3]
                else:
                    current_x += params[2]
                    current_y += params[3]

                points.append((current_x, current_y))
            i += 4

        elif current_command in ["Q", "q"]:  # Quadratic Bezier
            params = [float(tokens[i + j]) for j in range(4) if i + j < len(tokens)]

            if len(params) >= 4:
                if current_command == "Q":
                    current_x, current_y = params[2], params[3]
                else:
                    current_x += params[2]
                    current_y += params[3]

                points.append((current_x, current_y))
            i += 4

        elif current_command in ["T", "t"]:  # Smooth quadratic Bezier
            params = [float(tokens[i + j]) for j in range(2) if i + j < len(tokens)]

            if len(params) >= 2:
                if current_command == "T":
                    current_x, current_y = params[0], params[1]
                else:
                    current_x += params[0]
                    current_y += params[1]

                points.append((current_x, current_y))
            i += 2

        elif current_command in ["A", "a"]:  # Arc
            params = [float(tokens[i + j]) for j in range(7) if i + j < len(tokens)]

            if len(params) >= 7:
                if current_command == "A":
                    current_x, current_y = params[5], params[6]
                else:
                    current_x += params[5]
                    current_y += params[6]

                points.append((current_x, current_y))
            i += 7

        elif current_command in ["Z", "z"]:  # Close path
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


def get_path_center(d: str) -> Tuple[float, float]:
    """
    Вычисляет центр bounding box для SVG path

    Args:
        d: атрибут 'd' элемента path

    Returns:
        (center_x, center_y)
    """
    min_x, min_y, max_x, max_y = get_path_bbox(d)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    return (center_x, center_y)


# def calculate_optimal_font_size(bbox: Tuple[float, float, float, float], base_font_size: float = 3.0, max_font_size: float = 5.0, min_font_size: float = 1.0) -> float:
#     """
#     Вычисляет оптимальный размер шрифта на основе размеров слоя

#     Args:
#         bbox: (min_x, min_y, max_x, max_y) bounding box слоя
#         base_font_size: базовый размер шрифта
#         max_font_size: максимальный размер шрифта
#         min_font_size: минимальный размер шрифта

#     Returns:
#         оптимальный размер шрифта в мм
#     """
#     min_x, min_y, max_x, max_y = bbox
#     width = max_x - min_x
#     height = max_y - min_y

#     # Используем меньшую из сторон для определения размера шрифта
#     min_dimension = min(width, height)

#     # Шрифт должен быть примерно 40% от меньшей стороны
#     # но не меньше min_font_size и не больше max_font_size
#     optimal_size = min_dimension * 0.4
#     optimal_size = max(min_font_size, min(optimal_size, max_font_size))


#     return optimal_size
def calculate_optimal_font_size(
    bbox: Tuple[float, float, float, float],
    base_font_size: float = 0.1,
    min_font_size: float = 0.1,
    max_font_size: float = 1.0,
) -> float:
    """
    Вычисляет оптимальный размер шрифта для номера слоя на основе размеров слоя (bbox).

    Args:
        bbox: (min_x, min_y, max_x, max_y) — границы path в мм
        base_font_size: базовый размер шрифта (в мм)
        min_font_size: минимально допустимый размер
        max_font_size: максимально допустимый размер

    Returns:
        оптимальный размер шрифта в мм
    """
    if not bbox:
        return base_font_size

    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y

    if width <= 0 or height <= 0:
        return base_font_size

    # Размер текста пропорционален минимальному размеру слоя
    # чтобы он гарантированно помещался по обеим осям
    size_by_height = height * 0.35
    size_by_width = width * 0.25  # числа подбирались эмпирически

    optimal_size = min(size_by_height, size_by_width)

    # Ограничиваем диапазон, чтобы не получались гигантские цифры
    optimal_size = max(min_font_size, min(optimal_size, max_font_size))

    # # Немного сглаживаем, чтобы не мельчали мелкие слои
    # optimal_size = (
    #     (optimal_size + base_font_size) / 2
    #     if optimal_size < base_font_size
    #     else optimal_size
    # )

    return optimal_size


def analyze_content_bounds(svg_root) -> Tuple[float, float, float, float]:
    """
    Анализирует фактические границы всех слоёв в SVG

    Args:
        svg_root: корневой элемент SVG дерева

    Returns:
        (min_y, max_y, content_height, num_layers)
    """
    svg_ns = "{http://www.w3.org/2000/svg}"
    paths = svg_root.findall(f".//{svg_ns}path")

    if len(paths) == 0:
        return (0, 0, 0, 0)

    global_min_y = float("inf")
    global_max_y = float("-inf")

    for path in paths:
        d = path.get("d", "")
        if not d:
            continue

        bbox = get_path_bbox(d)
        min_x, min_y, max_x, max_y = bbox

        global_min_y = min(global_min_y, min_y)
        global_max_y = max(global_max_y, max_y)

    content_height = global_max_y - global_min_y

    return (global_min_y, global_max_y, content_height, len(paths))


def add_layer_numbers_to_svg(
    input_svg_path: Path,
    output_svg_path: Path,
    font_size: float = 3.0,
    text_color: str = "red",
) -> Tuple[int, float, float]:
    """
    Добавляет текстовые номера в центре каждого слоя SVG

    Args:
        input_svg_path: путь к входному SVG файлу
        output_svg_path: путь к выходному SVG файлу
        font_size: размер шрифта номеров в мм
        text_color: цвет текста номеров

    Returns:
        (num_layers, content_min_y, content_height)
    """
    # Регистрируем namespaces для корректной записи
    namespaces = {
        "": "http://www.w3.org/2000/svg",
        "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "svg": "http://www.w3.org/2000/svg",
    }

    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    # Парсим SVG
    tree = ET.parse(input_svg_path)
    root = tree.getroot()

    # Получаем размеры документа
    width_mm, height_mm = parse_svg_dimensions(root)
    print(f"Размеры SVG документа: {width_mm:.1f} x {height_mm:.1f} мм")

    # Анализируем фактические границы контента
    print(f"Анализ границ слоёв...")
    min_y, max_y, content_height, num_layers = analyze_content_bounds(root)

    print(f"Найдено слоёв: {num_layers}")
    print(f"Фактическая область контента:")
    print(f"  • Y координаты: {min_y:.2f} - {max_y:.2f} мм")
    print(f"  • Высота контента: {content_height:.2f} мм")
    print(f"  • Высота документа: {height_mm:.2f} мм")
    print(f"  • Пустое пространство: {height_mm - content_height:.2f} мм")

    if num_layers == 0:
        print("Предупреждение: не найдено ни одного path элемента!")
        tree.write(output_svg_path, encoding="UTF-8", xml_declaration=True)
        return (0, 0, 0)

    # SVG namespace
    svg_ns = "{http://www.w3.org/2000/svg}"

    # Находим все path элементы (слои)
    paths = root.findall(f".//{svg_ns}path")

    # Для каждого слоя добавляем текстовый номер в центре
    text_elements_to_add = []

    print(f"Добавление номеров в центре слоёв...")

    for i, path in enumerate(paths):
        layer_number = i + 1

        # Извлекаем координаты центра слоя и bbox
        d_attr = path.get("d", "")
        center_x, center_y = get_path_center(d_attr)
        bbox = get_path_bbox(d_attr)

        # Вычисляем оптимальный размер шрифта для этого слоя
        optimal_font_size = calculate_optimal_font_size(bbox, base_font_size=font_size)

        # Создаём текстовый элемент с номером слоя
        text_elem = ET.Element(f"{svg_ns}text")
        text_elem.set("x", str(center_x))
        text_elem.set("y", str(center_y))
        text_elem.set("font-size", f"{optimal_font_size}mm")
        # text_elem.set("font-size", "0.8em")
        text_elem.set("font-family", "Arial, sans-serif")
        text_elem.set("fill", text_color)
        text_elem.set("font-weight", "bold")
        text_elem.set("stroke", "none")
        text_elem.set("text-anchor", "middle")  # Центрирование по горизонтали
        text_elem.set("dominant-baseline", "middle")  # Центрирование по вертикали
        text_elem.text = str(layer_number)

        text_elements_to_add.append((path, text_elem))

        if (layer_number % 50 == 0) or (layer_number == num_layers):
            print(f"  Обработано слоёв: {layer_number}/{num_layers}")

    # Добавляем текстовые элементы в документ
    # Вставляем каждый текст сразу после соответствующего path
    for path, text_elem in text_elements_to_add:
        # Находим родительский элемент
        parent = None
        for elem in root.iter():
            if path in list(elem):
                parent = elem
                break

        if parent is not None:
            try:
                idx = list(parent).index(path)
                parent.insert(idx + 1, text_elem)
            except ValueError:
                root.append(text_elem)
        else:
            root.append(text_elem)

    # Сохраняем модифицированный SVG
    tree.write(output_svg_path, encoding="UTF-8", xml_declaration=True)
    print(f"✓ SVG с номерами сохранён: {output_svg_path.name}")

    return (int(num_layers), min_y, content_height)


def convert_svg_to_pdf(svg_path: Path, pdf_path: Path):
    """
    Конвертирует SVG в PDF используя svglib + reportlab

    Args:
        svg_path: путь к SVG файлу
        pdf_path: путь к выходному PDF файлу
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF
    except ImportError:
        print("Ошибка: библиотеки svglib или reportlab не установлены")
        print("Установите: pip install svglib reportlab")
        sys.exit(1)

    print(f"Конвертация SVG → PDF...")

    # Конвертируем SVG в ReportLab Drawing объект
    drawing = svg2rlg(str(svg_path))

    if drawing is None:
        print(f"Ошибка: не удалось прочитать SVG файл")
        sys.exit(1)

    # Рендерим в PDF
    renderPDF.drawToFile(drawing, str(pdf_path))

    print(f"✓ PDF создан: {pdf_path.name}")


def split_pdf_to_a4_pages(
    input_pdf_path: Path,
    output_pdf_path: Path,
    content_min_y: float,
    content_height: float,
):
    """
    Разделяет PDF на страницы A4, используя только область с контентом

    Args:
        input_pdf_path: путь к входному PDF файлу
        output_pdf_path: путь к выходному PDF файлу с страницами A4
        content_min_y: минимальная Y координата контента в мм
        content_height: высота контента в мм
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
    except ImportError:
        print("Ошибка: библиотека PyPDF2 не установлена")
        print("Установите: pip install PyPDF2")
        sys.exit(1)

    from reportlab.lib.units import mm

    # Размеры A4 в пунктах (points) - стандарт PDF
    # 1 мм = 2.834645669 points
    A4_WIDTH = 210 * mm
    A4_HEIGHT = 297 * mm

    print(f"Разделение PDF на страницы A4...")

    reader = PdfReader(input_pdf_path)

    if len(reader.pages) == 0:
        print("Ошибка: входной PDF не содержит страниц")
        sys.exit(1)

    original_page = reader.pages[0]

    # Получаем размеры оригинальной страницы
    media_box = original_page.mediabox
    original_width = float(media_box.width)
    original_height = float(media_box.height)

    print(
        f"  Размер исходного PDF: {original_width:.1f} x {original_height:.1f} points"
    )

    # Конвертируем координаты контента в points
    content_min_y_points = content_min_y * mm
    content_height_points = content_height * mm
    content_max_y_points = content_min_y_points + content_height_points

    print(f"  Область контента (в points):")
    print(f"    • Начало (Y): {content_min_y_points:.1f}")
    print(f"    • Конец (Y): {content_max_y_points:.1f}")
    print(f"    • Высота: {content_height_points:.1f}")

    # Вычисляем количество страниц A4, необходимых для размещения контента
    num_pages = int(content_height_points / A4_HEIGHT) + (
        1 if content_height_points % A4_HEIGHT > 0 else 0
    )
    print(f"  Потребуется страниц A4 для контента: {num_pages}")

    writer = PdfWriter()

    # Создаём страницы A4, извлекая соответствующие части контента
    # ВАЖНО: В PDF координата Y=0 находится ВНИЗУ страницы
    # Поэтому мы начинаем с ВЕРХА контента и идем вниз
    for page_num in range(num_pages):
        # Создаём новую пустую страницу A4
        new_page = PageObject.create_blank_page(width=A4_WIDTH, height=A4_HEIGHT)

        # Вычисляем вертикальное смещение для текущей страницы
        # Начинаем с ВЕРХА контента (максимальная Y координата) и идем вниз
        # Каждая следующая страница показывает контент ниже предыдущей
        # y_offset = content_max_y_points - ((page_num) * A4_HEIGHT)

        # Вычисляем смещение в PDF-координатах (Y=0 снизу)
        # Начинаем с самого верха оригинальной страницы
        y_offset = original_height - (page_num + 1) * A4_HEIGHT
        if y_offset < 0:
            y_offset = 0

        # # Начинаем с НИЗА контента и идем вверх
        # # Используем обратный индекс: последняя страница показывает верх контента
        # reverse_page_num = num_pages - 1 - page_num
        # y_offset = content_min_y_points + (reverse_page_num * A4_HEIGHT)

        # Создаём трансформацию: сдвигаем так, чтобы нужная часть оказалась внизу
        transformation = Transformation().translate(0, -y_offset)

        # Накладываем оригинальную страницу с трансформацией на пустую
        # ВАЖНО: используем временную страницу-обертку для правильного применения трансформации
        temp_wrapper = PageObject.create_blank_page(
            width=original_width, height=original_height
        )
        temp_wrapper.merge_page(original_page)
        temp_wrapper.add_transformation(transformation)

        # Теперь накладываем трансформированную обертку на нашу A4 страницу
        new_page.merge_page(temp_wrapper)

        # Обрезаем страницу до размеров A4
        new_page.mediabox.lower_left = [0, 0]
        new_page.mediabox.upper_right = [A4_WIDTH, A4_HEIGHT]
        new_page.cropbox.lower_left = [0, 0]
        new_page.cropbox.upper_right = [A4_WIDTH, A4_HEIGHT]

        writer.add_page(new_page)

        if (page_num + 1) % 10 == 0 or (page_num + 1) == num_pages:
            print(f"  Создано страниц: {page_num + 1}/{num_pages}")

    # Сохраняем результат
    with open(output_pdf_path, "wb") as output_file:
        writer.write(output_file)

    print(f"✓ PDF разделён на {num_pages} страниц A4: {output_pdf_path.name}")

    return num_pages


def main():
    parser = argparse.ArgumentParser(
        description="Обработка SVG со слоями: нумерация, конвертация в PDF и разделение на страницы A4 (ИСПРАВЛЕННАЯ ВЕРСИЯ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python process_svg_to_a4_pdf_fixed.py input.svg
  python process_svg_to_a4_pdf_fixed.py input.svg --output ./results
  python process_svg_to_a4_pdf_fixed.py input.svg --font-size 4 --text-color blue

Улучшения в этой версии:
  • Анализирует фактические границы слоёв
  • Размещает номера в центре каждого слоя
  • Разделяет только область с контентом (без пустых страниц)
  • Исправляет проблемы с обрезкой слоёв на границах страниц

Скрипт создаст три файла:
  - input_numbered.svg (SVG с номерами слоёв)
  - input_long.pdf (полный PDF одной длинной страницей)
  - input_A4.pdf (PDF разделённый на страницы A4)
        """,
    )

    parser.add_argument("input", type=str, help="Входной SVG файл")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Директория для выходных файлов (по умолчанию: текущая)",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=1.0,
        help="Размер шрифта номеров в мм (по умолчанию: 1.0)",
    )
    parser.add_argument(
        "--text-color",
        type=str,
        default="red",
        help="Цвет текста номеров (по умолчанию: red)",
    )

    args = parser.parse_args()

    # Проверяем входной файл
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Ошибка: файл '{input_path}' не найден")
        sys.exit(1)

    if not input_path.suffix.lower() == ".svg":
        print(f"Предупреждение: файл '{input_path}' не имеет расширения .svg")

    # Определяем директорию для выходных файлов
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_path.parent

    # Формируем имена выходных файлов
    base_name = input_path.stem
    numbered_svg = output_dir / f"{base_name}_numbered.svg"
    long_pdf = output_dir / f"{base_name}_long.pdf"
    final_pdf = output_dir / f"{base_name}_A4.pdf"

    # Заголовок
    print("=" * 70)
    print(f"ОБРАБОТКА SVG СО СЛОЯМИ (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("=" * 70)
    print(f"Входной файл: {input_path}")
    print(f"Директория вывода: {output_dir}")
    print("=" * 70)

    # Шаг 1: Добавляем номера на слои
    print("\n[ШАГ 1/3] Добавление номеров слоёв...")
    print("-" * 70)
    num_layers, content_min_y, content_height = add_layer_numbers_to_svg(
        input_path,
        numbered_svg,
        font_size=args.font_size,
        text_color=args.text_color,
    )

    # Шаг 2: Конвертируем в PDF
    print("\n[ШАГ 2/3] Конвертация в PDF...")
    print("-" * 70)
    convert_svg_to_pdf(numbered_svg, long_pdf)

    # Шаг 3: Разделяем на страницы A4
    print("\n[ШАГ 3/3] Разделение на страницы A4...")
    print("-" * 70)
    num_pages = split_pdf_to_a4_pages(long_pdf, final_pdf, content_min_y, content_height)

    # Итоги
    print("\n" + "=" * 70)
    print("✓ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print(f"Статистика:")
    print(f"  • Всего слоёв: {num_layers}")
    print(f"  • Страниц A4: {num_pages}")
    print(f"\nСозданные файлы:")
    print(f"  1. {numbered_svg.name}")
    print(f"     └─ SVG с пронумерованными слоями (номера в центре)")
    print(f"  2. {long_pdf.name}")
    print(f"     └─ Полный PDF одной длинной страницей")
    print(f"  3. {final_pdf.name}")
    print(f"     └─ Финальный PDF, разделённый на страницы A4 (только контент)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
