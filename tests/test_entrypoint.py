import importlib
import sys

import matrix_rank.app


def test_importing_entrypoint_does_not_start_gui(monkeypatch):
    started = False

    def fake_main():
        nonlocal started
        started = True

    monkeypatch.setattr(matrix_rank.app, "main", fake_main)
    sys.modules.pop("matrix_rank_calculator", None)

    importlib.import_module("matrix_rank_calculator")

    assert started is False
