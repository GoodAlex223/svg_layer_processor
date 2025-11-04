# Быстрый старт

## Что делает этот скрипт?

1. ✅ Нумерует каждый слой в вашем SVG файле из Kiri:Moto
2. ✅ Конвертирует SVG в PDF
3. ✅ Разделяет длинный PDF на стандартные страницы A4 для печати

## Установка (один раз)

### Linux/macOS

```bash
# 1. Установите системные зависимости
# Ubuntu/Debian:
sudo apt-get install libcairo2-dev libpango1.0-dev

# macOS:
brew install cairo pango

# 2. Установите Python библиотеки
pip install -r requirements.txt
```

### Windows

```bash
# 1. Скачайте и установите GTK3:
# https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

# 2. Установите Python библиотеки
pip install -r requirements.txt
```

## Использование

### Вариант 1: Автоматический (оба файла)

**Linux/macOS:**

```bash
./run_example.sh
```

**Windows:**

```cmd
run_example.bat
```

### Вариант 2: Ручной (один файл)

```bash
python process_svg_to_a4_pdf.py ваш_файл.svg
```

Или с настройками:

```bash
python process_svg_to_a4_pdf.py ваш_файл.svg --output ./results --font-size 4 --text-color blue
```

## Результаты

После выполнения вы получите:

1. **`файл_A4.pdf`** ← Это ваш основной результат! Готов для печати.
2. `файл_numbered.svg` - SVG с видимыми номерами слоёв
3. `файл_long.pdf` - полный PDF одной длинной страницей (для проверки)

## Примеры

```bash
# Для оригинального файла
python process_svg_to_a4_pdf.py ladyghoststl-2-014.svg

# Для оптимизированного файла
python process_svg_to_a4_pdf.py nested2.svg --output ./nested_output

# С крупными синими номерами
python process_svg_to_a4_pdf.py nested2.svg --font-size 5 --text-color blue
```

## Параметры

- `--output DIR` - куда сохранить результаты
- `--font-size SIZE` - размер номеров в мм (по умолчанию: 3)
- `--text-color COLOR` - цвет номеров (по умолчанию: red)
- `--offset-x X` - смещение по X в мм (по умолчанию: 2)
- `--offset-y Y` - смещение по Y в мм (по умолчанию: -1)

## Возможные проблемы

### Ошибка "cairo not found"

**Решение:** Установите системные зависимости (см. раздел "Установка" выше)

### Ошибка "No module named 'PyPDF2'"

**Решение:**

```bash
pip install PyPDF2
```

### Скрипт не запускается

**Решение:**

```bash
# Linux/macOS - сделайте файл исполняемым
chmod +x run_example.sh

# Или запустите напрямую через python
python process_svg_to_a4_pdf.py ваш_файл.svg
```

## Дополнительная справка

Полная документация: `README.md`

Справка по скрипту:

```bash
python process_svg_to_a4_pdf.py --help
```

---

**Важно:** Убедитесь, что ваши SVG файлы находятся в той же директории, где и скрипт, или укажите полный путь к файлу.
