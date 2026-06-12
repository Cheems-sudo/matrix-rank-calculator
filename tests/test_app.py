import builtins
import tkinter as tk

from matrix_rank import app


def test_gui_main_reports_headless_environment(monkeypatch, capsys):
    def fail_to_create_root():
        raise tk.TclError("no display name")

    monkeypatch.setattr(tk, "Tk", fail_to_create_root)

    exit_code = app.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "未检测到可用的桌面显示环境" in captured.err
    assert "matrix-rank" in captured.err


def test_gui_main_reports_missing_tkinter(monkeypatch, capsys):
    original_import = builtins.__import__

    def import_without_tkinter(name, *args, **kwargs):
        if name == "tkinter":
            raise ImportError("tkinter is unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_tkinter)

    exit_code = app.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "未安装 tkinter" in captured.err
    assert "matrix-rank" in captured.err
