# Discrepancy Finder — Fuel Edition

**Discrepancy Finder** — утилита для сверки Excel и CSV-файлов.
Сравнивает данные акта и реестра: находит расхождения по заказам и суммам, сохраняет результат в `.txt` при необходимости.

---

## 🔧 Возможности

- 📂 Поддержка `.xlsx`, `.xls`, `.csv`
- 🆔 Поиск расхождений по ID и суммам
- 💾 Выгрузка отчёта в `.txt`
- 🌐 Интерфейс на русском языке
- 🖥️ Графическая оболочка на PyQt5
- 🔒 Работа полностью офлайн
- 🪪 Подходит для обработки ПД (см. `SECURITY_NOTES.md`)

---

## 📥 Скачать

👉 [Скачать .exe (v1.0.0-win)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.0.0-win)

👉 [Скачать .dmg (v1.0.0-mac)](https://github.com/ilodezis/discrepancy-finder/releases/tag/v1.0.0-mac)

---

## 🛠️ Как собрать вручную

См. [build_instructions.md](build_instructions.md) — подходит для Windows с Python 3.11+ и установленным `PyInstaller`.

---

## 🧾 Структура проекта

```plaintext
├── fuel_discrepancy_finder.py   # основной GUI-файл для сверки топлива
├── requirements.txt             # зависимости
├── build_instructions.md        # сборка .exe
├── SECURITY_NOTES.md            # безопасность
├── LICENSE
├── README.md
├── .gitignore
├── assets/                      # иконки, шрифты и ресурсы
```

---

## 🔐 Безопасность и аудит

Fuel Discrepancy Finder не содержит:

* сетевых вызовов (`requests`, `urllib`, сокеты)
* критичных вызовов (`os.system`, `eval`, `subprocess`)

Подробности в [SECURITY_NOTES.md](SECURITY_NOTES.md).
Программа предназначена для локального использования.

---

## 📄 Лицензия

MIT License — свободное распространение и модификация.

---

## 📬 Обратная связь

[issues](https://github.com/ilodezis/discrepancy-finder/issues) или Telegram @ilodezis
