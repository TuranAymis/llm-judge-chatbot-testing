"""LLM değerlendirme çıktısı için tutarlılık ve rapor etiketleri."""

_VALID_STATUSES = frozenset({"PASS", "FAIL", "SISTEM_KOTA", "SISTEM_YETKI"})


def _parse_llm_score(value: object) -> int:
    """LLM score alanını 0–5 tamsayıya çevir; ayrıştırılamazsa 0."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, min(5, value))
    if isinstance(value, float):
        if value != value:  # NaN
            return 0
        return max(0, min(5, int(round(value))))
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return 0
        try:
            return max(0, min(5, int(float(s))))
        except ValueError:
            return 0
    return 0


def _ensure_status_score_consistency(out: dict) -> dict:
    st_raw = out.get("status", "FAIL")
    st = st_raw if isinstance(st_raw, str) else "FAIL"

    if st not in _VALID_STATUSES:
        out["status"] = "FAIL"
        out["score"] = 0
        prev = (out.get("reasoning") or "").strip()
        suffix = "[Tutarlılık] Geçersiz veya eksik status."
        out["reasoning"] = f"{prev} {suffix}".strip() if prev else suffix
        return out

    if st in ("SISTEM_KOTA", "SISTEM_YETKI"):
        out["score"] = _parse_llm_score(out.get("score"))
        return out

    out["score"] = _parse_llm_score(out.get("score"))

    if st == "PASS" and out["score"] < 3:
        out["status"] = "FAIL"
        prev = out.get("reasoning", "")
        out["reasoning"] = (
            f"[Tutarlılık] PASS ile uyumsuz puan (3'ten küçük). Önceki gerekçe: {prev}"
        )

    return out


def prepare_ai_evaluation(evaluation: dict | None, bot_response: str) -> dict:
    """
    Ham LLM çıktısını rapor ve assert için son şekle getirir: skor ayrıştırma,
    normalize_evaluation, tutarlılık. Bu fonksiyon dışında skor override edilmemeli
    (istisna: normalize_evaluation içindeki kaçınma kuralı).
    """
    try:
        base = dict(evaluation) if evaluation else {}
        base["score"] = _parse_llm_score(base.get("score"))
        normalized = normalize_evaluation(base, bot_response)
        normalized["score"] = _parse_llm_score(normalized.get("score"))
        return _ensure_status_score_consistency(normalized)
    except Exception as exc:
        return {
            "score": 0,
            "reasoning": f"[Değerlendirme hatası] {exc}",
            "status": "FAIL",
        }


def normalize_evaluation(evaluation: dict, bot_response: str) -> dict:
    """
    Model 'Bilmiyorum' vb. dediğinde yüksek puan verirse düzelt.
    """
    out = dict(evaluation) if evaluation else {}
    text = (bot_response or "").lower()
    evasion_markers = (
        "bilmiyorum",
        "bilemiyorum",
        "cevap veremem",
        "yardımcı olamam",
        "bu konuda bilgi",
        "elimde bilgi yok",
        "i don't know",
        "cannot answer",
    )
    if any(m in text for m in evasion_markers):
        score = out.get("score")
        if isinstance(score, (int, float)) and score >= 3:
            out["score"] = 2
            out["status"] = "FAIL"
            prev = out.get("reasoning", "")
            out["reasoning"] = (
                f"[Tutarlılık düzeltmesi] Bot kaçınmacı/cevapsız ifade kullandı; "
                f"yüksek puan kabul edilemez. Önceki gerekçe: {prev}"
            )
    return out


def classify_api_error_message(msg: str) -> str | None:
    """429/401 vb. için rapor durumu kodu; None ise genel API hatası."""
    m = msg.lower()
    if "429" in msg or "quota" in m or "rate limit" in m:
        return "SISTEM_KOTA"
    if (
        "401" in msg
        or "403" in msg
        or "api_key_invalid" in m
        or "invalid api key" in m
        or "permission denied" in m
    ):
        return "SISTEM_YETKI"
    return None


def display_status_for_report(status: str) -> str:
    if status == "SISTEM_KOTA":
        return "Sistem Hatası/Kota Sorunu"
    if status == "SISTEM_YETKI":
        return "Sistem Hatası/Yetki"
    return status
