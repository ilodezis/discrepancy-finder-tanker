# Инструкция по сборке Discrepancy Finder - Fuel (.exe)

Сборка осуществляется с помощью [PyInstaller](https://pyinstaller.org/), без сторонних зависимостей, кроме PyQt5 и pandas.

## 🔧 Требования

- Python 3.11 (устанавливается с официального сайта https://www.python.org)
- pip
- Git (по желанию)

## 📦 Установка зависимостей

```bash
pip install -r requirements.txt
pip install pyinstaller==6.13.0
