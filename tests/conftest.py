import logging
import sys
from datetime import datetime
from pathlib import Path

import allure
import pytest

logger = logging.getLogger(__name__)

results_table: list[dict] = []

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils.evaluation_utils import display_status_for_report  # noqa: E402

_OFFICIAL_REPORT_MODULE = "test_chatbot.py"


def _is_official_chatbot_test(item: pytest.Item) -> bool:
    """Yalnızca chatbot E2E modülü üretim Excel / hook Allure ekranına dahil edilir."""
    nodeid = getattr(item, "nodeid", "") or ""
    if _OFFICIAL_REPORT_MODULE in nodeid:
        return True
    path = getattr(item, "path", None)
    if path is not None:
        try:
            return path.name == _OFFICIAL_REPORT_MODULE
        except (OSError, ValueError, TypeError):
            return False
    return False


def _resolve_ai_status_raw(item, report) -> str:
    raw = getattr(item, "ai_status", None)
    if raw is not None and raw != "":
        return raw
    if report.skipped:
        return "SKIP"
    if report.passed:
        return "PASS"
    return "FAIL"


def _ai_status_display(raw: str) -> str:
    if raw in ("SISTEM_KOTA", "SISTEM_YETKI"):
        return display_status_for_report(raw)
    return raw


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        include = _is_official_chatbot_test(item)

        actual = getattr(item, "actual_answer", "Cevap Alınamadı")
        callspec_item = getattr(getattr(item, "callspec", None), "params", {}).get("item", {})
        question = getattr(item, "question", callspec_item.get("soru", "Bilinmiyor"))
        expected_answer = getattr(item, "expected_answer", callspec_item.get("cevap", ""))
        initial_welcome = getattr(item, "initial_bot_welcome", "")
        ai_score = getattr(item, "ai_score", "")
        raw_ai_status = _resolve_ai_status_raw(item, report)
        ai_status = _ai_status_display(raw_ai_status)
        ai_reasoning = getattr(item, "ai_reasoning", "")
        if not ai_reasoning and (report.failed or report.skipped) and report.longrepr is not None:
            ai_reasoning = str(report.longrepr)

        page = item.funcargs.get("page")
        if include and page:
            status_prefix = (
                "GECEN_TEST" if report.passed
                else ("ATLANAN_TEST" if report.skipped else "HATALI_TEST")
            )
            allure.attach(
                page.screenshot(full_page=True),
                name=f"{status_prefix}_Ekran_Goruntusu",
                attachment_type=allure.attachment_type.PNG,
            )

        if include:
            results_table.append({
                "Soru": question,
                "Beklenen Cevap": expected_answer,
                "İlk Bot Mesajı (Hoşgeldin)": initial_welcome,
                "Chatbot'un Verdiği Gerçek Cevap": actual,
                "AI Puanı": ai_score,
                "AI Durumu": ai_status,
                "AI Durumu (Ham)": raw_ai_status,
                "AI Gerekçesi (Neden?)": ai_reasoning,
                "Test Durumu": "PASSED" if report.passed else ("SKIPPED" if report.skipped else "FAILED"),
                "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })


@pytest.fixture(scope="session", autouse=True)
def export_to_excel():
    """Oturum boyunca `results_table` dolar; Excel yalnızca teardown'da bir kez yazılır."""
    yield

    try:
        from utils.excel_writer import _HAS_OPENPYXL, _HAS_PANDAS, write_excel_report
    except ModuleNotFoundError as exc:
        logger.error("Excel raporu atlandı: excel_writer yüklenemedi (%s)", exc)
        return

    if not _HAS_PANDAS or not _HAS_OPENPYXL:
        logger.error(
            "Excel raporu oluşturulamadı: pandas veya openpyxl eksik. "
            "Kurulum: pip install pandas openpyxl"
        )
        return

    reports_dir = _REPO_ROOT / "reports"
    snapshot = list(results_table)
    try:
        write_excel_report(snapshot, reports_dir)
    except Exception:
        logger.exception("Excel raporu oturum sonunda yazılamadı")
