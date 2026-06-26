"""Standalone Excel report writer -- testable without pytest fixture machinery."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
    _HAS_PANDAS = True
except ModuleNotFoundError:
    pd = None  # type: ignore[assignment]
    _HAS_PANDAS = False

try:
    import openpyxl  # noqa: F401
    _HAS_OPENPYXL = True
except ModuleNotFoundError:
    _HAS_OPENPYXL = False

REPORT_COLUMNS = [
    "Soru",
    "Beklenen Cevap",
    "İlk Bot Mesajı (Hoşgeldin)",
    "Chatbot'un Verdiği Gerçek Cevap",
    "AI Puanı",
    "AI Durumu",
    "AI Durumu (Ham)",
    "AI Gerekçesi (Neden?)",
    "Test Durumu",
    "Tarih",
]

FILENAME = "Chatbot_Test_Raporu.xlsx"
MAX_COL_WIDTH = 60


def write_excel_report(results: list[dict], dest_dir: str | Path) -> None:
    dest = Path(dest_dir)

    if not _HAS_PANDAS:
        print(
            "\nUyarı: Excel raporu oluşturulamadı. "
            "Gerekli paket eksik: pandas. "
            "Kurulum için: pip install pandas"
        )
        return

    if not _HAS_OPENPYXL:
        print(
            "\nUyarı: Excel raporu oluşturulamadı. "
            "Gerekli paket eksik: openpyxl. "
            "Kurulum için: pip install openpyxl"
        )
        return

    dest.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results, columns=REPORT_COLUMNS)
    primary = dest / FILENAME

    try:
        _write_with_autowidth(df, primary)
        print(f"\nExcel raporu kaydedildi: {primary}")
    except ModuleNotFoundError as exc:
        if "openpyxl" in str(exc):
            print(
                "\nUyarı: Excel raporu oluşturulamadı. "
                "Gerekli paket eksik: openpyxl. "
                "Kurulum için: pip install openpyxl"
            )
            return
        raise
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = dest / f"Chatbot_Test_Raporu_{stamp}.xlsx"
        try:
            _write_with_autowidth(df, fallback)
            print(
                f"\nUyarı: '{primary}' kilitli veya yazılamıyor. "
                f"Rapor yedek konuma yazıldı: {fallback}"
            )
        except PermissionError:
            print(
                f"\nUyarı: Excel raporu yazılamadı. "
                f"Hem '{primary}' hem '{fallback}' kilitli veya yazılamıyor."
            )
    except Exception as exc:
        print(f"\nUyarı: Excel raporu yazılırken beklenmeyen hata: {exc}")


def _write_with_autowidth(df: "pd.DataFrame", path: Path) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        ws = writer.sheets["Sheet1"]
        for col_cells in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(
                max_len + 2, MAX_COL_WIDTH
            )
