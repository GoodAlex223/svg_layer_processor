#!/usr/bin/env python3
"""
Скрипт для сопоставления слоёв между упрощённым и оптимизированным SVG файлами
и восстановления правильной нумерации для порядка сборки.

Алгоритм:
1. Извлекает все пути из обоих файлов
2. Нормализует геометрию (убирает смещения)
3. Вычисляет "отпечаток" каждого пути
4. Находит соответствие между файлами
5. Добавляет правильные номера на оптимизированный файл
6. Создаёт PDF с разделением на A4

Использование:
    python match_and_number_layers.py simplified.svg optimized.svg
"""

import xml.etree.ElementTree as ET
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import re
import math


def parse_svg_path_to_points(path_d: str) -> List[Tuple[float, float]]:
    """
    Парсит SVG path в список координат (x, y).
    Упрощённая версия: обрабатывает M, L команды.
    """
    points = []
    
    # Упрощённый парсинг: заменяем команды на разделители
    path_d = path_d.replace(',', ' ')
    path_d = re.sub(r'([MLHVZmlhvz])', r' \1 ', path_d)
    tokens = path_d.split()
    
    i = 0
    current_x, current_y = 0.0, 0.0
    
    while i < len(tokens):
        cmd = tokens[i]
        
        if cmd in ['M', 'L']:  # Absolute move/line
            if i + 2 < len(tokens):
                try:
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])
                    points.append((x, y))
                    current_x, current_y = x, y
                    i += 3
                except ValueError:
                    i += 1
            else:
                i += 1
                
        elif cmd in ['m', 'l']:  # Relative move/line
            if i + 2 < len(tokens):
                try:
                    dx = float(tokens[i + 1])
                    dy = float(tokens[i + 2])
                    current_x += dx
                    current_y += dy
                    points.append((current_x, current_y))
                    i += 3
                except ValueError:
                    i += 1
            else:
                i += 1
                
        elif cmd in ['H']:  # Absolute horizontal
            if i + 1 < len(tokens):
                try:
                    current_x = float(tokens[i + 1])
                    points.append((current_x, current_y))
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1
                
        elif cmd in ['V']:  # Absolute vertical
            if i + 1 < len(tokens):
                try:
                    current_y = float(tokens[i + 1])
                    points.append((current_x, current_y))
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1
                
        else:
            i += 1
    
    return points


def normalize_points(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Нормализует точки: смещает к (0,0) и поворачивает к базовой ориентации.
    """
    if not points:
        return []
    
    # Находим центр масс
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    
    # Смещаем к (0, 0)
    translated = [(x - cx, y - cy) for x, y in points]
    
    return translated


def compute_path_signature(points: List[Tuple[float, float]], num_samples: int = 50) -> Tuple:
    """
    Вычисляет "отпечаток" пути для сравнения.
    Возвращает кортеж характеристик, инвариантных к смещению и вращению.
    """
    if not points or len(points) < 2:
        return (0, 0, 0, 0)
    
    # 1. Общая длина пути
    total_length = 0.0
    for i in range(len(points) - 1):
        dx = points[i+1][0] - points[i][0]
        dy = points[i+1][1] - points[i][1]
        total_length += math.sqrt(dx*dx + dy*dy)
    
    # 2. Количество точек
    num_points = len(points)
    
    # 3. Площадь (приближённая через shoelace formula)
    area = 0.0
    for i in range(len(points) - 1):
        area += points[i][0] * points[i+1][1]
        area -= points[i+1][0] * points[i][1]
    area = abs(area) / 2.0
    
    # 4. Bounding box соотношение сторон
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    aspect_ratio = width / height if height > 0.1 else 0
    
    # Округляем для устойчивости к мелким изменениям
    return (
        round(total_length, 1),
        num_points,
        round(area, 1),
        round(aspect_ratio, 2)
    )


def find_best_match(target_sig: Tuple, candidates: List[Tuple[int, Tuple]]) -> int:
    """
    Находит наилучшее совпадение для target_sig среди candidates.
    
    Args:
        target_sig: сигнатура искомого пути
        candidates: список (index, signature) для сравнения
        
    Returns:
        index наилучшего совпадения
    """
    best_idx = -1
    best_distance = float('inf')
    
    for idx, cand_sig in candidates:
        # Вычисляем расстояние между сигнатурами
        distance = 0.0
        
        # Длина пути (вес 1.0)
        distance += abs(target_sig[0] - cand_sig[0])
        
        # Количество точек (вес 0.1)
        distance += abs(target_sig[1] - cand_sig[1]) * 0.1
        
        # Площадь (вес 0.5)
        distance += abs(target_sig[2] - cand_sig[2]) * 0.5
        
        # Соотношение сторон (вес 10.0)
        distance += abs(target_sig[3] - cand_sig[3]) * 10.0
        
        if distance < best_distance:
            best_distance = distance
            best_idx = idx
    
    return best_idx


def match_layers(simplified_svg: Path, optimized_svg: Path) -> Dict[int, int]:
    """
    Сопоставляет слои между упрощённым и оптимизированным файлами.
    
    Returns:
        Словарь {optimized_index: simplified_index}
    """
    print("Чтение файлов...")
    
    # Читаем упрощённый файл
    tree_simp = ET.parse(simplified_svg)
    root_simp = tree_simp.getroot()
    paths_simp = root_simp.findall('.//{http://www.w3.org/2000/svg}path')
    
    # Читаем оптимизированный файл
    tree_opt = ET.parse(optimized_svg)
    root_opt = tree_opt.getroot()
    paths_opt = root_opt.findall('.//{http://www.w3.org/2000/svg}path')
    
    print(f"Упрощённый файл: {len(paths_simp)} слоёв")
    print(f"Оптимизированный файл: {len(paths_opt)} слоёв")
    
    if len(paths_simp) != len(paths_opt):
        print("⚠ ПРЕДУПРЕЖДЕНИЕ: Количество слоёв различается!")
    
    print("\nВычисление сигнатур упрощённого файла...")
    simplified_signatures = []
    for i, path in enumerate(paths_simp):
        d_attr = path.get('d', '')
        points = parse_svg_path_to_points(d_attr)
        normalized = normalize_points(points)
        signature = compute_path_signature(normalized)
        simplified_signatures.append((i, signature))
        
        if (i + 1) % 50 == 0:
            print(f"  Обработано: {i + 1}/{len(paths_simp)}")
    
    print("\nВычисление сигнатур оптимизированного файла...")
    optimized_signatures = []
    for i, path in enumerate(paths_opt):
        d_attr = path.get('d', '')
        points = parse_svg_path_to_points(d_attr)
        normalized = normalize_points(points)
        signature = compute_path_signature(normalized)
        optimized_signatures.append((i, signature))
        
        if (i + 1) % 50 == 0:
            print(f"  Обработано: {i + 1}/{len(paths_opt)}")
    
    print("\nСопоставление слоёв...")
    matches = {}  # {opt_idx: simp_idx}
    used_simplified = set()
    
    for opt_idx, opt_sig in optimized_signatures:
        # Ищем среди ещё не использованных
        available = [(idx, sig) for idx, sig in simplified_signatures 
                     if idx not in used_simplified]
        
        if available:
            best_match = find_best_match(opt_sig, available)
            matches[opt_idx] = best_match
            used_simplified.add(best_match)
        
        if (opt_idx + 1) % 50 == 0:
            print(f"  Сопоставлено: {opt_idx + 1}/{len(paths_opt)}")
    
    print(f"\n✓ Сопоставлено {len(matches)} слоёв")
    
    # Проверка качества сопоставления
    if len(matches) < len(paths_opt) * 0.95:
        print(f"⚠ ПРЕДУПРЕЖДЕНИЕ: Сопоставлено только {len(matches)}/{len(paths_opt)} слоёв")
    
    return matches


def add_numbers_to_optimized_svg(optimized_svg: Path, 
                                  output_svg: Path,
                                  matches: Dict[int, int],
                                  font_size: float = 3.0,
                                  text_color: str = 'red') -> int:
    """
    Добавляет номера на оптимизированный SVG согласно сопоставлению.
    """
    print("\nДобавление номеров на оптимизированный файл...")
    
    # Регистрируем namespaces
    namespaces = {
        '': 'http://www.w3.org/2000/svg',
        'svg': 'http://www.w3.org/2000/svg'
    }
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    
    tree = ET.parse(optimized_svg)
    root = tree.getroot()
    
    svg_ns = '{http://www.w3.org/2000/svg}'
    paths = root.findall(f'.//{svg_ns}path')
    
    text_elements = []
    
    for opt_idx, simp_idx in matches.items():
        if opt_idx >= len(paths):
            continue
            
        path = paths[opt_idx]
        layer_number = simp_idx + 1  # Нумерация с 1
        
        # Извлекаем начальные координаты
        d_attr = path.get('d', '')
        points = parse_svg_path_to_points(d_attr)
        
        if points:
            x_coord, y_coord = points[0]
        else:
            x_coord, y_coord = 5.0, 10.0 + (opt_idx * 15)
        
        # Создаём текстовый элемент
        text_elem = ET.Element(f'{svg_ns}text')
        text_elem.set('x', str(x_coord + 2))
        text_elem.set('y', str(y_coord - 1))
        text_elem.set('font-size', f'{font_size}mm')
        text_elem.set('font-family', 'Arial, sans-serif')
        text_elem.set('fill', text_color)
        text_elem.set('font-weight', 'bold')
        text_elem.set('stroke', 'none')
        text_elem.text = str(layer_number)
        
        text_elements.append((path, text_elem))
    
    # Добавляем текстовые элементы в документ
    for path, text_elem in text_elements:
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
    
    # Сохраняем
    tree.write(output_svg, encoding='UTF-8', xml_declaration=True)
    print(f"✓ Сохранён SVG с номерами: {output_svg.name}")
    
    return len(matches)


def main():
    parser = argparse.ArgumentParser(
        description='Сопоставление и нумерация слоёв SVG',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('simplified', type=str, 
                       help='Упрощённый SVG файл (simplified_1mm.svg)')
    parser.add_argument('optimized', type=str,
                       help='Оптимизированный SVG файл (nested2.svg)')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Директория для выходных файлов')
    parser.add_argument('--font-size', type=float, default=3.0,
                       help='Размер шрифта номеров в мм')
    parser.add_argument('--text-color', type=str, default='red',
                       help='Цвет номеров')
    
    args = parser.parse_args()
    
    # Проверка файлов
    simplified_path = Path(args.simplified)
    optimized_path = Path(args.optimized)
    
    if not simplified_path.exists():
        print(f"Ошибка: файл {simplified_path} не найден")
        sys.exit(1)
    
    if not optimized_path.exists():
        print(f"Ошибка: файл {optimized_path} не найден")
        sys.exit(1)
    
    # Директория вывода
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = optimized_path.parent
    
    output_svg = output_dir / f"{optimized_path.stem}_numbered.svg"
    
    print("=" * 70)
    print("СОПОСТАВЛЕНИЕ И НУМЕРАЦИЯ СЛОЁВ")
    print("=" * 70)
    print(f"Упрощённый: {simplified_path}")
    print(f"Оптимизированный: {optimized_path}")
    print(f"Вывод: {output_dir}")
    print("=" * 70)
    
    # Шаг 1: Сопоставление
    matches = match_layers(simplified_path, optimized_path)
    
    # Шаг 2: Добавление номеров
    num_numbered = add_numbers_to_optimized_svg(
        optimized_path,
        output_svg,
        matches,
        font_size=args.font_size,
        text_color=args.text_color
    )
    
    print("\n" + "=" * 70)
    print("✓ ЗАВЕРШЕНО")
    print("=" * 70)
    print(f"Сопоставлено слоёв: {num_numbered}")
    print(f"Результат: {output_svg}")
    print("=" * 70)
    
    print("\nСледующий шаг:")
    print(f"  python process_svg_to_a4_pdf.py {output_svg}")
    
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
