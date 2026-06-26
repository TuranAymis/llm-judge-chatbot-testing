"""Altyapı testleri: google-genai tabanlı GeminiProvider ve Excel kilit senaryosu (specs/modernization_and_reporting.md)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGeminiProviderGoogleGenAI:
    """Yeni SDK: Client + models.generate_content yolu (ağ çağrısı mock)."""

    def test_evaluate_calls_generate_content_and_parses_json(self) -> None:
        from utils.gemini_provider import GeminiProvider

        mock_response = MagicMock()
        mock_response.text = '{"score": 9, "reasoning": "uyumlu", "status": "PASS"}'

        mock_models = MagicMock()
        mock_models.generate_content.return_value = mock_response

        mock_client = MagicMock()
        mock_client.models = mock_models

        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-fake"}):
                with patch("utils.gemini_provider.genai.Client", return_value=mock_client) as client_cls:
                    provider = GeminiProvider()
                    out = provider.evaluate("Soru?", "bot cevap", "beklenen")

        client_cls.assert_called_once_with(api_key="test-key-fake")
        mock_models.generate_content.assert_called()
        kwargs = mock_models.generate_content.call_args.kwargs
        assert kwargs["model"] == "gemini-1.5-flash"
        assert "Soru?" in kwargs["contents"]
        assert out == {"score": 9, "reasoning": "uyumlu", "status": "PASS"}

    def test_falls_back_to_second_model_when_model_not_found(self) -> None:
        from utils.gemini_provider import GeminiProvider

        mock_response = MagicMock()
        mock_response.text = '{"score": 1, "reasoning": "x", "status": "FAIL"}'

        mock_models = MagicMock()

        def _gen(*, model: str, contents: str):
            if model == "gemini-1.5-flash":
                raise Exception("model not found: gemini-1.5-flash")
            return mock_response

        mock_models.generate_content.side_effect = _gen

        mock_client = MagicMock()
        mock_client.models = mock_models

        with patch("dotenv.load_dotenv"):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "k"}):
                with patch("utils.gemini_provider.genai.Client", return_value=mock_client):
                    provider = GeminiProvider()
                    out = provider.evaluate("q", "b", "e")

        assert mock_models.generate_content.call_count >= 2
        assert out["score"] == 1


class TestExcelPermissionFallbackInfra:
    """PermissionError: timestamp yedek dosya (mock ile)."""

    def test_timestamped_fallback_on_lock(self, tmp_path: Path) -> None:
        from utils import excel_writer

        rows = [
            {
                "Soru": "A?",
                "Beklenen Cevap": "b",
                "Chatbot'un Verdiği Gerçek Cevap": "c",
                "AI Puanı": 1,
                "AI Durumu": "PASS",
                "AI Durumu (Ham)": "PASS",
                "AI Gerekçesi (Neden?)": "",
                "Test Durumu": "PASSED",
                "Tarih": "2026-01-01 00:00:00",
            }
        ]
        reports_dir = tmp_path / "reports"
        real = excel_writer._write_with_autowidth
        n = {"c": 0}

        def _first_lock(df, path):
            n["c"] += 1
            if n["c"] == 1:
                raise PermissionError("locked")
            return real(df, path)

        with patch.object(excel_writer, "_write_with_autowidth", _first_lock):
            excel_writer.write_excel_report(rows, reports_dir)

        assert list(reports_dir.glob("Chatbot_Test_Raporu_*.xlsx"))

    def test_double_permission_error_prints_without_crash(self, tmp_path: Path, capsys) -> None:
        from utils import excel_writer

        rows = [
            {
                "Soru": "A?",
                "Beklenen Cevap": "b",
                "Chatbot'un Verdiği Gerçek Cevap": "c",
                "AI Puanı": 1,
                "AI Durumu": "PASS",
                "AI Durumu (Ham)": "PASS",
                "AI Gerekçesi (Neden?)": "",
                "Test Durumu": "PASSED",
                "Tarih": "2026-01-01 00:00:00",
            }
        ]

        def _always_lock(df, path):
            raise PermissionError("locked")

        with patch.object(excel_writer, "_write_with_autowidth", _always_lock):
            excel_writer.write_excel_report(rows, tmp_path)

        out = capsys.readouterr().out
        assert "kilitli" in out.lower() or "yazılamadı" in out.lower()
