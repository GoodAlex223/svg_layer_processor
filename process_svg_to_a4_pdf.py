#!/usr/bin/env python3
"""
Скрипт для обработки SVG файлов со слоями из Kiri:Moto:
1. Добавляет видимые номера на каждый слой
2. Конвертирует SVG в PDF
3. Разделяет длинный PDF на стандартные страницы A4

Требования:
    pip install cairosvg PyPDF2 reportlab

Использование:
    python process_svg_to_a4_pdf.py input.svg [output_directory]
"""

import xml.etree.ElementTree as ET
import sys
import argparse
from pathlib import Path
from typing import Tuple


def parse_svg_dimensions(svg_root) -> Tuple[float, float]:
    """
    Извлекает размеры SVG документа в миллиметрах
    
    Returns:
        (width_mm, height_mm)
    """
    width_str = svg_root.get('width', '210mm')
    height_str = svg_root.get('height', '297mm')
    
    # Удаляем единицы измерения и конвертируем в float
    width_mm = float(width_str.replace('mm', '').strip())
    height_mm = float(height_str.replace('mm', '').strip())
    
    return width_mm, height_mm


def extract_path_start_position(path_d_attribute: str) -> Tuple[float, float]:
    """
    Извлекает начальные координаты из атрибута 'd' элемента path
    
    Args:
        path_d_attribute: строка атрибута 'd' элемента path
        
    Returns:
        (x, y) координаты начала пути
    """
    try:
        # SVG path начинается с команды M (move to) или m (относительный move)
        # Формат: "m x,y" или "M x,y" или "m x y"
        d_cleaned = path_d_attribute.strip()
        
        # Разделяем по пробелам
        parts = d_cleaned.replace(',', ' ').split()
        
        # Ищем первую команду m/M
        for i, part in enumerate(parts):
            if part.lower() == 'm':
                # Следующие два элемента - координаты
                if i + 2 < len(parts):
                    x = float(parts[i + 1])
                    y = float(parts[i + 2])
                    return x, y
        
        # Если не нашли команду m/M, но строка начинается с неё
        if d_cleaned.lower().startswith('m'):
            coords_part = d_cleaned[1:].strip()
            coords = coords_part.split()[0:2]
            if len(coords) >= 2:
                x = float(coords[0].replace(',', ''))
                y = float(coords[1].replace(',', ''))
                return x, y
                
    except (ValueError, IndexError) as e:
        pass
    
    # Возвращаем координаты по умолчанию, если не удалось распарсить
    return 5.0, 10.0


def add_layer_numbers_to_svg(input_svg_path: Path, output_svg_path: Path, 
                              font_size: float = 3.0, 
                              text_color: str = 'red',
                              offset_x: float = 2.0,
                              offset_y: float = -1.0) -> int:
    """
    Добавляет текстовые номера на каждый слой SVG
    
    Args:
        input_svg_path: путь к входному SVG файлу
        output_svg_path: путь к выходному SVG файлу
        font_size: размер шрифта номеров в мм
        text_color: цвет текста номеров
        offset_x: смещение текста по X от начала пути
        offset_y: смещение текста по Y от начала пути
        
    Returns:
        количество обработанных слоёв
    """
    # Регистрируем namespaces для корректной записи
    namespaces = {
        '': 'http://www.w3.org/2000/svg',
        'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        'svg': 'http://www.w3.org/2000/svg'
    }
    
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    # Парсим SVG
    tree = ET.parse(input_svg_path)
    root = tree.getroot()
    
    # Получаем размеры документа
    width_mm, height_mm = parse_svg_dimensions(root)
    print(f"Размеры SVG: {width_mm:.1f} x {height_mm:.1f} мм")
    
    # SVG namespace
    svg_ns = '{http://www.w3.org/2000/svg}'
    
    # Находим все path элементы (слои)
    paths = root.findall(f'.//{svg_ns}path')
    num_layers = len(paths)
    
    print(f"Найдено слоёв: {num_layers}")
    
    if num_layers == 0:
        print("Предупреждение: не найдено ни одного path элемента!")
        tree.write(output_svg_path, encoding='UTF-8', xml_declaration=True)
        return 0
    
    # Для каждого слоя добавляем текстовый номер
    text_elements_to_add = []
    
    for i, path in enumerate(paths):
        layer_number = i + 1
        
        # Извлекаем начальные координаты пути
        d_attr = path.get('d', '')
        x_coord, y_coord = extract_path_start_position(d_attr)
        
        # Создаём текстовый элемент с номером слоя
        text_elem = ET.Element(f'{svg_ns}text')
        text_elem.set('x', str(x_coord + offset_x))
        text_elem.set('y', str(y_coord + offset_y))
        text_elem.set('font-size', f'{font_size}mm')
        text_elem.set('font-family', 'Arial, sans-serif')
        text_elem.set('fill', text_color)
        text_elem.set('font-weight', 'bold')
        text_elem.set('stroke', 'none')
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
    tree.write(output_svg_path, encoding='UTF-8', xml_declaration=True)
    print(f"✓ SVG с номерами сохранён: {output_svg_path.name}")
    
    return num_layers


def convert_svg_to_pdf(svg_path: Path, pdf_path: Path):
    """
    Конвертирует SVG в PDF используя cairosvg
    
    Args:
        svg_path: путь к SVG файлу
        pdf_path: путь к выходному PDF файлу
    """
    try:
        import cairosvg
    except ImportError:
        print("Ошибка: библиотека cairosvg не установлена")
        print("Установите: pip install cairosvg")
        sys.exit(1)
    
    print(f"Конвертация SVG → PDF...")
    cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
    print(f"✓ PDF создан: {pdf_path.name}")


def split_pdf_to_a4_pages(input_pdf_path: Path, output_pdf_path: Path):
    """
    Разделяет длинный PDF на стандартные страницы формата A4
    
    Args:
        input_pdf_path: путь к входному PDF файлу
        output_pdf_path: путь к выходному PDF файлу с страницами A4
    """
    try:
        from PyPDF2 import PdfReader, PdfWriter, Transformation
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
    
    print(f"  Размер исходного PDF: {original_width:.1f} x {original_height:.1f} points")
    print(f"  Размер A4: {A4_WIDTH:.1f} x {A4_HEIGHT:.1f} points")
    print(f"  Размер A4: 210 x 297 мм")
    
    # Вычисляем количество страниц A4, необходимых для размещения всего содержимого
    num_pages = int(original_height / A4_HEIGHT) + (1 if original_height % A4_HEIGHT > 0 else 0)
    print(f"  Потребуется страниц A4: {num_pages}")
    
    if num_pages > 50:
        print(f"  Предупреждение: будет создано {num_pages} страниц (это больше ожидаемых 31)")
    
    writer = PdfWriter()
    
    # Создаём страницы A4, извлекая соответствующие части оригинала
    for page_num in range(num_pages):
        # Клонируем оригинальную страницу
        new_page = original_page
        
        # Вычисляем вертикальное смещение для текущей страницы
        # Каждая следующая страница должна показывать следующий фрагмент
        y_offset = page_num * A4_HEIGHT
        
        # Создаём трансформацию: сдвиг вверх на y_offset
        transformation = Transformation().translate(0, -y_offset)
        
        # Применяем трансформацию к странице
        new_page.add_transformation(transformation)
        
        # Обрезаем страницу до размеров A4
        new_page.mediabox.lower_left = (0, 0)
        new_page.mediabox.upper_right = (A4_WIDTH, A4_HEIGHT)
        new_page.cropbox.lower_left = (0, 0)
        new_page.cropbox.upper_right = (A4_WIDTH, A4_HEIGHT)
        
        writer.add_page(new_page)
        
        if (page_num + 1) % 10 == 0 or (page_num + 1) == num_pages:
            print(f"  Создано страниц: {page_num + 1}/{num_pages}")
    
    # Сохраняем результат
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    print(f"✓ PDF разделён на {num_pages} страниц A4: {output_pdf_path.name}")
    
    return num_pages


def main():
    parser = argparse.ArgumentParser(
        description='Обработка SVG со слоями: нумерация, конвертация в PDF и разделение на страницы A4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python process_svg_to_a4_pdf.py input.svg
  python process_svg_to_a4_pdf.py input.svg --output ./results
  python process_svg_to_a4_pdf.py input.svg --font-size 4 --text-color blue
  
Скрипт создаст три файла:
  - input_numbered.svg (SVG с номерами слоёв)
  - input_long.pdf (полный PDF одной длинной страницей)
  - input_A4.pdf (PDF разделённый на страницы A4)
        """
    )
    
    parser.add_argument('input', type=str, help='Входной SVG файл')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Директория для выходных файлов (по умолчанию: текущая)')
    parser.add_argument('--font-size', type=float, default=3.0,
                       help='Размер шрифта номеров в мм (по умолчанию: 3.0)')
    parser.add_argument('--text-color', type=str, default='red',
                       help='Цвет текста номеров (по умолчанию: red)')
    parser.add_argument('--offset-x', type=float, default=2.0,
                       help='Смещение текста по X от начала слоя в мм (по умолчанию: 2.0)')
    parser.add_argument('--offset-y', type=float, default=-1.0,
                       help='Смещение текста по Y от начала слоя в мм (по умолчанию: -1.0)')
    
    args = parser.parse_args()
    
    # Проверяем входной файл
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Ошибка: файл '{input_path}' не найден")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.svg':
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
    print(f"ОБРАБОТКА SVG СО СЛОЯМИ")
    print("=" * 70)
    print(f"Входной файл: {input_path}")
    print(f"Директория вывода: {output_dir}")
    print("=" * 70)
    
    # Шаг 1: Добавляем номера на слои
    print("\n[ШАГ 1/3] Добавление номеров слоёв...")
    print("-" * 70)
    num_layers = add_layer_numbers_to_svg(
        input_path, 
        numbered_svg,
        font_size=args.font_size,
        text_color=args.text_color,
        offset_x=args.offset_x,
        offset_y=args.offset_y
    )
    
    # Шаг 2: Конвертируем в PDF
    print("\n[ШАГ 2/3] Конвертация в PDF...")
    print("-" * 70)
    convert_svg_to_pdf(numbered_svg, long_pdf)
    
    # Шаг 3: Разделяем на страницы A4
    print("\n[ШАГ 3/3] Разделение на страницы A4...")
    print("-" * 70)
    num_pages = split_pdf_to_a4_pages(long_pdf, final_pdf)
    
    # Итоги
    print("\n" + "=" * 70)
    print("✓ ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print(f"Статистика:")
    print(f"  • Всего слоёв: {num_layers}")
    print(f"  • Страниц A4: {num_pages}")
    print(f"\nСозданные файлы:")
    print(f"  1. {numbered_svg.name}")
    print(f"     └─ SVG с пронумерованными слоями")
    print(f"  2. {long_pdf.name}")
    print(f"     └─ Полный PDF одной длинной страницей")
    print(f"  3. {final_pdf.name}")
    print(f"     └─ Финальный PDF, разделённый на страницы A4")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
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
