"""system_audit_v2: prepare_ai_evaluation boru hattı ve Excel kilit davranışı."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from utils.evaluation_utils import prepare_ai_evaluation


class TestPrepareAiEvaluationAudit:
    """Kaçınmacı bot + yüksek LLM puanı; string skor; tutarlılık kuralları."""

    def test_evasive_bot_high_llm_score_normalized_down(self) -> None:
        raw = {"score": 5, "status": "PASS", "reasoning": "Mükemmel"}
        out = prepare_ai_evaluation(raw, "Üzgünüm, bilmiyorum.")
        assert out["status"] == "FAIL"
        assert out["score"] == 2
        assert "Tutarlılık düzeltmesi" in out["reasoning"]

    def test_string_score_then_evasion_rule_applies(self) -> None:
        raw = {"score": "5", "status": "PASS", "reasoning": "ok"}
        out = prepare_ai_evaluation(raw, "I don't know about that")
        assert out["score"] == 2
        assert out["status"] == "FAIL"

    def test_malformed_score_defaults_zero(self) -> None:
        raw = {"score": "not-a-number", "status": "FAIL", "reasoning": "x"}
        out = prepare_ai_evaluation(raw, "normal cevap")
        assert out["score"] == 0
        assert out["status"] == "FAIL"

    def test_invalid_status_coerced(self) -> None:
        raw = {"score": 4, "status": "MAYBE", "reasoning": "?"}
        out = prepare_ai_evaluation(raw, "cevap")
        assert out["status"] == "FAIL"
        assert out["score"] == 0
        assert "Geçersiz" in out["reasoning"]

    def test_pass_with_low_score_becomes_fail(self) -> None:
        raw = {"score": 2, "status": "PASS", "reasoning": "tutarsız model"}
        out = prepare_ai_evaluation(raw, "tam ve doğru cevap")
        assert out["status"] == "FAIL"
        assert "PASS ile uyumsuz" in out["reasoning"]

    def test_system_quota_unchanged(self) -> None:
        raw = {
            "score": 0,
            "status": "SISTEM_KOTA",
            "reasoning": "429",
        }
        out = prepare_ai_evaluation(raw, "bilmiyorum")
        assert out["status"] == "SISTEM_KOTA"
        assert out["score"] == 0


class TestExcelReportingAudit:
    """Audit kapsamında: kilitli dosyada zaman damgalı yedek (mock)."""

    def test_locked_primary_yields_timestamped_workbook(self, tmp_path: Path) -> None:
        from utils import excel_writer

        rows = [
            {
                "Soru": "Q?",
                "Beklenen Cevap": "a",
                "İlk Bot Mesajı (Hoşgeldin)": "",
                "Chatbot'un Verdiği Gerçek Cevap": "b",
                "AI Puanı": 0,
                "AI Durumu": "FAIL",
                "AI Durumu (Ham)": "FAIL",
                "AI Gerekçesi (Neden?)": "",
                "Test Durumu": "FAILED",
                "Tarih": "2026-01-01 00:00:00",
            }
        ]
        dest = tmp_path / "reports"
        real = excel_writer._write_with_autowidth
        n = {"c": 0}

        def _once_pe(df, path):
            n["c"] += 1
            if n["c"] == 1:
                raise PermissionError("locked")
            return real(df, path)

        with patch.object(excel_writer, "_write_with_autowidth", _once_pe):
            excel_writer.write_excel_report(rows, dest)

        assert list(dest.glob("Chatbot_Test_Raporu_*.xlsx"))


class TestStripTrailingMetaLine:
    """Hoşgeldin / cevap metninde son satır (meta) kırpma."""

    def test_multi_line_drops_last(self) -> None:
        from utils.widget_selectors import strip_trailing_meta_line

        assert strip_trailing_meta_line("Merhaba\n14:02") == "Merhaba"

    def test_single_line_unchanged(self) -> None:
        from utils.widget_selectors import strip_trailing_meta_line

        assert strip_trailing_meta_line("Tek satır") == "Tek satır"


class TestExcelAggregateSourceFilter:
    """conftest: Excel agregatına yalnızca test_chatbot.py satırları girer (spec §5b)."""

    def test_official_module_detection(self) -> None:
        from tests.conftest import _is_official_chatbot_test

        class _Fake:
            def __init__(self, name: str) -> None:
                self.path = Path("tests") / name
                self.nodeid = f"tests/{name}::dummy"

        assert _is_official_chatbot_test(_Fake("test_chatbot.py"))
        assert not _is_official_chatbot_test(_Fake("test_infra.py"))
        assert not _is_official_chatbot_test(_Fake("test_logic_audit.py"))
        assert not _is_official_chatbot_test(_Fake("test_reporting_logic.py"))

    def test_nodeid_is_primary_contract(self) -> None:
        """nodeid içinde test_chatbot.py yeterli (path farklı olsa bile)."""
        from tests.conftest import _is_official_chatbot_test

        class _Fake:
            path = Path("tests/test_reporting_logic.py")
            nodeid = "tests/test_chatbot.py::test_monster_chatbot_per_question"

        assert _is_official_chatbot_test(_Fake())
