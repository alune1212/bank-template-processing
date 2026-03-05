"""模块入口覆盖测试。"""

from __future__ import annotations

import runpy


def test_module_entrypoint_invokes_main(monkeypatch):
    called = {"value": False}

    def fake_main():
        called["value"] = True

    monkeypatch.setattr("bank_template_processing.main.main", fake_main)

    runpy.run_module("bank_template_processing.__main__", run_name="__main__")

    assert called["value"] is True
