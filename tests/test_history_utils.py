"""Тести legacy-модуля history_utils.py (ЛР12, INC-001, CAPA-1 і CAPA-2).

Не потребують БД: HISTORY_DIR підміняється на тимчасовий каталог. Перевіряють
режими відмови, яких раніше не перевіряв жоден тест (борг TD-8).
"""
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import history_utils as h


@pytest.fixture(autouse=True)
def isolated_history_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "HISTORY_DIR", tmp_path)
    return tmp_path


def test_save_is_atomic_and_leaves_no_temp_files(isolated_history_dir):
    h.save_history(1, [{"api": "a", "params": "p", "result": "r", "timestamp": "t"}])
    names = sorted(p.name for p in isolated_history_dir.iterdir())
    assert names == ["user_1.json"]
    assert h.load_history(1)[0]["api"] == "a"


def test_truncated_file_is_quarantined_and_history_restarts(isolated_history_dir):
    h.history_file(2).write_text('[{"api": "x", "par', encoding="utf-8")
    assert h.load_history(2) == []                      # раніше: JSONDecodeError
    names = [p.name for p in isolated_history_dir.iterdir()]
    assert "user_2.json" not in names
    assert any(n.startswith("user_2.json.corrupt-") for n in names)


def test_add_entry_recovers_after_corruption(isolated_history_dir):
    h.history_file(3).write_text("{не json", encoding="utf-8")
    assert h.add_history_entry(3, "Запит", "параметри", "результат") is True
    assert len(h.load_history(3)) == 1


def test_add_entry_never_raises_when_storage_fails(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("диск недоступний")
    monkeypatch.setattr(h, "save_history", boom)
    assert h.add_history_entry(4, "Запит", "п", "р") is False   # раніше: виняток у обробнику запиту


def test_failed_save_keeps_old_file_intact(isolated_history_dir, monkeypatch):
    h.save_history(5, [{"api": "old", "params": "", "result": "", "timestamp": ""}])

    def bad_replace(src, dst):
        raise OSError("збій заміни")
    with monkeypatch.context() as patch:
        patch.setattr(h.os, "replace", bad_replace)
        with pytest.raises(OSError):
            h.save_history(5, [{"api": "new", "params": "", "result": "", "timestamp": ""}])
    assert h.load_history(5)[0]["api"] == "old"
    assert not [p for p in isolated_history_dir.iterdir() if ".tmp-" in p.name]


def test_parallel_threads_lose_no_entries():
    def worker():
        for i in range(25):
            h.add_history_entry(6, "api", f"p{i}", "ok")
    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(h.load_history(6)) == 200


def test_delete_history_files_removes_quarantined_copies(isolated_history_dir):
    h.save_history(7, [{"api": "a", "params": "", "result": "", "timestamp": ""}])
    h.history_file(7).with_name("user_7.json.corrupt-20261117T210000Z").write_text("x")
    assert h.delete_history_files(7) is True
    assert list(isolated_history_dir.iterdir()) == []


def test_strict_load_reports_corruption_without_touching_file(isolated_history_dir):
    h.history_file(8).write_text("{не json", encoding="utf-8")
    with pytest.raises(ValueError):
        h.load_history(8, strict=True)                  # експорт персональних даних має про це знати
    assert h.history_file(8).exists()                   # файл не переносився
    assert h.quarantined_history_files(8) == []


def test_quarantined_files_are_listed_after_self_healing(isolated_history_dir):
    h.history_file(9).write_text("{не json", encoding="utf-8")
    assert h.load_history(9) == []
    assert len(h.quarantined_history_files(9)) == 1
