"""Історія аналітичних запитів користувача: файл history/user_<id>.json.

Зміни за CAPA-1 і CAPA-2 (INC-001):
  * запис атомарний: дані пишуться у тимчасовий файл і підміняють основний через
    os.replace, тому читач ніколи не бачить частково записаний JSON;
  * пошкоджений файл не ламає читання: його переносять у <файл>.corrupt-<UTC-час>
    (як доказ), а історію користувача починають заново;
  * збій журналу не ламає основний сценарій: add_history_entry не кидає винятків.

Відомі обмеження (див. docs/legacy/history-utils.md): блокування діє лише в межах
одного процесу, тому при кількох процесах можливі втрати окремих записів (TD-1).
"""
import json
import logging
import os
import threading
from pathlib import Path
from datetime import datetime, timezone

HISTORY_DIR = Path("history")
HISTORY_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("history")

# Захист від race condition: без цього блокування паралельні запити одного
# користувача (наприклад, кілька вкладок або, як у нашому випадку,
# навантажувальний тест) можуть одночасно виконати read-modify-write
# по одному й тому самому history/user_<id>.json та пошкодити файл
# (JSONDecodeError: Extra data). Виявлено під час k6-навантаження.
_history_lock = threading.Lock()

def history_file(user_id):
    return HISTORY_DIR / f"user_{user_id}.json"

def _quarantine(file):
    """Переносить пошкоджений файл поруч під іншою назвою замість його видалення."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = file.with_name(f"{file.name}.corrupt-{stamp}")
    try:
        os.replace(file, target)
        logger.error("[HISTORY] Пошкоджений файл %s перенесено в %s, історію скинуто",
                     file.name, target.name)
    except OSError as exc:
        logger.error("[HISTORY] Не вдалося перенести пошкоджений файл %s: %s", file.name, exc)

def load_history(user_id, strict=False):
    """Читає історію. За замовчуванням пошкоджений файл переноситься в карантин, а історія
    починається заново. З strict=True пошкодження піднімається як ValueError і файл не
    чіпається: так читає експорт персональних даних, щоб повідомити про неповноту."""
    file = history_file(user_id)
    if not file.exists():
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except ValueError:  # JSONDecodeError і UnicodeDecodeError є підкласами ValueError
        if strict:
            raise
        _quarantine(file)
        return []

def quarantined_history_files(user_id):
    """Карантинні копії пошкодженого файлу історії користувача (докази, що мають PII)."""
    path = history_file(user_id)
    return sorted(path.parent.glob(f"{path.name}.corrupt-*"))

def save_history(user_id, history_list):
    file = history_file(user_id)
    tmp = file.with_name(f"{file.name}.tmp-{os.getpid()}-{threading.get_ident()}")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, file)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

def add_history_entry(user_id, api_name, params, result_text):
    """Додає запис в історію. Повертає True/False і НІКОЛИ не кидає винятків:
    історія є допоміжною функцією і не має ламати основний сценарій (CAPA-2)."""
    try:
        with _history_lock:
            history = load_history(user_id)

            history.append({
                "api": api_name,
                "params": params,
                "result": result_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            save_history(user_id, history)
        return True
    except Exception:  # навмисно широкий: збій журналу не повинен зупиняти звіт
        logger.exception("[HISTORY] Не вдалося записати історію користувача %s", user_id)
        return False

def delete_history_files(user_id):
    """Видаляє файл історії і його карантинні копії (право на стирання, privacy/erasure.py)."""
    path = history_file(user_id)
    existed = path.exists()
    path.unlink(missing_ok=True)
    for leftover in path.parent.glob(f"{path.name}.corrupt-*"):
        leftover.unlink(missing_ok=True)
        existed = True
    return existed
