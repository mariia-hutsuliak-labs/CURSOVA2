#!/usr/bin/env python3
"""Інструментальна перевірка тверджень про history_utils.py (ЛР12, Завдання 3).

Кожен експеримент працює в тимчасовому каталозі на копії модуля, тому реальний
каталог history/ не чіпається. Результат використовується як доказ рівня довіри
«verified» у docs/legacy/history-utils.md.

Запуск:  python scripts/legacy_history_probe.py
"""
import multiprocessing
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# На macOS процеси стартують методом spawn і заново виконують цей модуль, тому
# робочий каталог передається дочірнім процесам через змінну середовища.
if "HISTORY_PROBE_DIR" in os.environ:
    WORK = Path(os.environ["HISTORY_PROBE_DIR"])
else:
    WORK = Path(tempfile.mkdtemp(prefix="history_probe_"))
    os.environ["HISTORY_PROBE_DIR"] = str(WORK)
    shutil.copy(ROOT / "history_utils.py", WORK / "history_utils.py")
sys.path.insert(0, str(WORK))
os.chdir(WORK)
import history_utils as h  # noqa: E402


def worker(n, errors=None):
    for i in range(n):
        try:
            h.add_history_entry(1, "api", f"p{os.getpid()}-{i}", "ok")
        except Exception:
            if errors is not None:
                with errors.get_lock():
                    errors.value += 1


def main():
    h.save_history(1, [])
    threads = [threading.Thread(target=worker, args=(100,)) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    print(f"E1 8 потоків x 100 записів в одному процесі: очікувано 800, отримано {len(h.load_history(1))}")

    h.save_history(1, [])
    errors = multiprocessing.Value("i", 0)
    procs = [multiprocessing.Process(target=worker, args=(100, errors)) for _ in range(4)]
    [p.start() for p in procs]
    [p.join() for p in procs]
    try:
        got = len(h.load_history(1))
    except Exception as exc:
        got = f"файл пошкоджено ({type(exc).__name__})"
    print(f"E2 4 процеси x 100 записів (як воркери gunicorn): очікувано 400, отримано {got}, збоїв запису {errors.value}")

    h.history_file(2).write_text('[{"api": "x", "par', encoding="utf-8")
    try:
        h.load_history(2)
        print("E3 обрізаний файл: помилки немає")
    except Exception as exc:
        print(f"E3 обрізаний файл (збій під час запису): load_history кидає {type(exc).__name__}")

    h.save_history(3, [])
    for _ in range(3000):
        h.add_history_entry(3, "api", "params" * 5, "result" * 5)
    start = time.time()
    h.add_history_entry(3, "api", "x", "y")
    ms = (time.time() - start) * 1000
    print(f"E4 додавання запису при 3000 наявних: {ms:.1f} мс, файл {h.history_file(3).stat().st_size // 1024} КБ (кожен запис перечитує і перезаписує весь файл)")

    h.history_file(4).write_text("[]", encoding="utf-8")
    h.history_file(4).unlink()                 # так робить privacy/erasure.py (без блокування)
    h.add_history_entry(4, "api", "p", "r")
    print(f"E5 після видалення файлу (erasure) наступний запис створює його знову: {h.history_file(4).exists()}")

    print(f"Тимчасовий каталог: {WORK}")
    print(f"Метод старту процесів: {multiprocessing.get_start_method()}")


if __name__ == "__main__":
    main()
