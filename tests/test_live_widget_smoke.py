"""Canlı widget duman testi — yalnızca RUN_LIVE_WIDGET_SMOKE=1 iken ağ gerekir (spec §6)."""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import Page, expect

from utils.widget_selectors import CHAT_INPUT, LAUNCHER_BUTTON, complete_pre_chat_registration, dismiss_kvkk_overlay_if_present

_DEFAULT_BASE = "https://monster.widget.aistudio.com.tr/"


def _base_url() -> str:
    raw = os.getenv("CHATBOT_BASE_URL", _DEFAULT_BASE).strip()
    return raw if raw.endswith("/") else raw + "/"


def _widget_timeout_ms() -> int:
    try:
        return max(5_000, int(os.getenv("CHATBOT_WIDGET_TIMEOUT_MS", "60000")))
    except ValueError:
        return 60_000


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_WIDGET_SMOKE", "").strip().lower() not in ("1", "true", "yes"),
    reason="Canlı duman için: RUN_LIVE_WIDGET_SMOKE=1",
)
def test_live_widget_opens_chat(page: Page) -> None:
    page.goto(_base_url(), wait_until="domcontentloaded")
    launcher = page.locator(LAUNCHER_BUTTON)
    expect(launcher).to_be_visible(timeout=_widget_timeout_ms())
    launcher.click()
    chat_input = page.locator(CHAT_INPUT)
    expect(chat_input).to_be_visible(timeout=30_000)
    dismiss_kvkk_overlay_if_present(page)
    complete_pre_chat_registration(page)
