"""
Monster widget (https://monster.widget.aistudio.com.tr/) — React SPA, #app kökü.
Kaynak: üretim JS bundle (tda-chat-widget); Shadow DOM / iframe yok.
"""

import os
import re

from playwright.sync_api import Page

# Sohbet kapalıyken görünen açma düğmesi
LAUNCHER_BUTTON = "button.chat-launcher-button"

# KVKK / gizlilik onayı — sohbet açıldığında giriş alanının üzerine gelir; tıklamayı engeller
KVKK_OVERLAY = ".monster-kvkk-overlay"
KVKK_OVERLAY_BUTTONS = f"{KVKK_OVERLAY} button"
KVKK_OVERLAY_ROLE_BUTTONS = f"{KVKK_OVERLAY} [role='button']"

# Metin kutusu (placeholder bundle’da UTF-8 ile “Herhangi bir şey sor”).
# Sohbet açıldıktan sonra bu alana tıklamak/odaklamak üretimde hoşgeldin balonunu tetikler.
CHAT_INPUT = "input.text-wrapper-3.input-field"

# Asistan balonları: .covo-messages içinde .background > .p (typing de aynı yapıda “Yazıyor...”)
BOT_MESSAGE_PARAGRAPHS = ".covo-messages .background .p"

TYPING_INDICATOR_SUBSTRING = "Yazıyor"

# Ön-kayıt (ad-soyad / e-posta) — CHATBOT_TEST_* ile .env’den override
# Karşılama metni üretimde değişebilir; en az birinin balonda geçmesi yeterli (büyük/küçük harf duyarsız)
_DEFAULT_GREETING_MARKERS = (
    "merhaba",
    "canavar",
    "canavar destek",
    "monster",
    "teknik destek",
    "notebook",
)


def _greeting_markers_lower() -> tuple[str, ...]:
    raw = os.getenv("CHATBOT_GREETING_MARKERS", "").strip()
    if not raw:
        return _DEFAULT_GREETING_MARKERS
    parts = tuple(p.strip().lower() for p in raw.split(",") if p.strip())
    return parts if parts else _DEFAULT_GREETING_MARKERS


def strip_trailing_meta_line(text: str) -> str:
    """Çok satırlı mesajlarda son satırı (saat/meta) düşür; tek satırda olduğu gibi döndür."""
    lines = (text or "").strip().split("\n")
    if len(lines) > 1:
        return " ".join(lines[:-1]).strip()
    return (text or "").strip()


def _pre_chat_test_name() -> str:
    raw = os.getenv("CHATBOT_TEST_NAME", "Test Otomasyon").strip()
    return raw if raw else "Test Otomasyon"


def _pre_chat_test_email() -> str:
    raw = os.getenv("CHATBOT_TEST_EMAIL", "test@otomasyon.com").strip()
    return raw if raw else "test@otomasyon.com"


def _pre_chat_step_timeout_ms() -> int:
    try:
        return max(15_000, int(os.getenv("CHATBOT_PRE_CHAT_STEP_TIMEOUT_MS", "60000")))
    except ValueError:
        return 60_000


def _count_bot_bubbles_excluding_typing(page: Page) -> int:
    return page.evaluate(
        """() => {
            const sel = '.covo-messages .background .p';
            const nodes = document.querySelectorAll(sel);
            let n = 0;
            for (const el of nodes) {
                const t = (el.textContent || '').trim();
                if (t && !t.includes('Yazıyor')) n++;
            }
            return n;
        }"""
    )


def _wait_for_bot_bubble_count_above(page: Page, prev: int, timeout_ms: int) -> None:
    page.wait_for_function(
        f"""() => {{
            const sel = '.covo-messages .background .p';
            const nodes = document.querySelectorAll(sel);
            let n = 0;
            for (const el of nodes) {{
                const t = (el.textContent || '').trim();
                if (t && !t.includes('Yazıyor')) n++;
            }}
            return n > {prev};
        }}""",
        timeout=timeout_ms,
    )


def _greeting_regex(markers_lower: tuple[str, ...]) -> re.Pattern[str]:
    parts = [re.escape(m) for m in markers_lower if m]
    if not parts:
        parts = [r"merhaba", r"canavar", r"monster"]
    return re.compile("(" + "|".join(parts) + ")", re.I)


def _wait_for_greeting_bubbles(page: Page, markers_lower: tuple[str, ...], timeout_ms: int) -> None:
    """markers listesinden en az biri bir bot balonunda geçene kadar bekler (Playwright metin eşlemesi)."""
    pat = _greeting_regex(markers_lower)
    page.locator(BOT_MESSAGE_PARAGRAPHS).filter(
        has_not_text=TYPING_INDICATOR_SUBSTRING
    ).filter(has_text=pat).first.wait_for(state="visible", timeout=timeout_ms)


def _get_last_bot_bubble_text(page: Page) -> str:
    return page.evaluate(
        """() => {
            const sel = '.covo-messages .background .p';
            const nodes = [...document.querySelectorAll(sel)].filter((el) => {
                const t = (el.textContent || '').trim();
                return t && !t.includes('Yazıyor');
            });
            if (nodes.length === 0) return '';
            return (nodes[nodes.length - 1].textContent || '').trim();
        }"""
    )


def _wait_for_email_step_ready(page: Page, timeout_ms: int) -> None:
    """
    Ad-soyad sonrası e-posta sorusu üçüncü balonda gelebilir veya metin farklı olabilir.
    En az 3 bot balonu veya posta/mail geçişi; olmazsa kısa bekleme ile devam (üretim gecikmesi).
    """
    short = min(timeout_ms, 25_000)
    try:
        page.wait_for_function(
            """() => {
                const sel = '.covo-messages .background .p';
                const nodes = [...document.querySelectorAll(sel)].filter((el) => {
                    const t = (el.textContent || '').trim();
                    return t && !t.includes('Yazıyor');
                });
                if (nodes.length >= 3) return true;
                const full = nodes.map((n) => (n.textContent || '').trim().toLowerCase()).join(' ');
                return (
                    full.includes('posta')
                    || full.includes('e-posta')
                    || full.includes('eposta')
                    || full.includes('email')
                    || (full.includes('mail') && (full.includes('adres') || full.includes('paylaş')))
                );
            }""",
            timeout=short,
        )
    except Exception:
        page.wait_for_timeout(6000)


def _needs_email_resend(last_bot_text: str) -> bool:
    """Üretimde bağlantı kurulduktan sonra e-postanın tekrar gönderilmesi istenebilir."""
    t = (last_bot_text or "").lower()
    if "bağlantı kuruluyor" in t or "baglanti kuruluyor" in t:
        return True
    if "tekrar" in t and ("gönder" in t or "gonder" in t):
        return True
    return False


def _get_greeting_bubble_text(page: Page, markers_lower: tuple[str, ...]) -> str:
    """Eşleşen karşılama balonunun metni (genelde son eşleşen)."""
    pat = _greeting_regex(markers_lower)
    loc = page.locator(BOT_MESSAGE_PARAGRAPHS).filter(
        has_not_text=TYPING_INDICATOR_SUBSTRING
    ).filter(has_text=pat)
    try:
        if loc.count() == 0:
            return ""
        return loc.last.inner_text()
    except Exception:
        return ""


def complete_pre_chat_registration(page: Page) -> str:
    """
    Sohbet açıldıktan sonra bot ad-soyad ve e-posta sorar; ardından \"Merhaba\" ile karşılama gelir.
    Bu adımlar tamamlanana kadar bekler, son karşılama metnini döndürür.
    """
    step_ms = _pre_chat_step_timeout_ms()
    chat_input = page.locator(CHAT_INPUT)
    chat_input.click()

    # İlk bot mesajı (ad-soyad isteği)
    page.wait_for_function(
        """() => {
            const sel = '.covo-messages .background .p';
            const nodes = document.querySelectorAll(sel);
            let n = 0;
            for (const el of nodes) {
                const t = (el.textContent || '').trim();
                if (t && !t.includes('Yazıyor')) n++;
            }
            return n >= 1;
        }""",
        timeout=step_ms,
    )

    prev = _count_bot_bubbles_excluding_typing(page)
    chat_input.fill(_pre_chat_test_name())
    chat_input.press("Enter")

    _wait_for_bot_bubble_count_above(page, prev, step_ms)

    _wait_for_email_step_ready(page, step_ms)

    prev = _count_bot_bubbles_excluding_typing(page)
    chat_input.fill(_pre_chat_test_email())
    chat_input.press("Enter")

    _wait_for_bot_bubble_count_above(page, prev, step_ms)

    # Bağlantı kuruluyor / "mesajı tekrar gönderin" — üretimde WebSocket gecikmesi için ara beklemeli tekrar
    for attempt in range(4):
        if not _needs_email_resend(_get_last_bot_bubble_text(page)):
            break
        page.wait_for_timeout(min(3000 + attempt * 2000, 15_000))
        prev = _count_bot_bubbles_excluding_typing(page)
        chat_input.fill(_pre_chat_test_email())
        chat_input.press("Enter")
        try:
            _wait_for_bot_bubble_count_above(page, prev, step_ms)
        except Exception:
            page.wait_for_timeout(5000)

    markers = _greeting_markers_lower()
    try:
        _wait_for_greeting_bubbles(page, markers, min(step_ms, 45_000))
    except Exception:
        # Bazı ortamlarda yalnızca "Bağlantı kuruluyor..." döngüsü olur; karşılama gelmez
        page.wait_for_timeout(2000)

    raw = _get_greeting_bubble_text(page, markers)
    if not raw:
        bubbles = page.locator(BOT_MESSAGE_PARAGRAPHS).filter(has_not_text=TYPING_INDICATOR_SUBSTRING)
        if bubbles.count() > 0:
            raw = bubbles.last.inner_text()
    return strip_trailing_meta_line(raw)


def dismiss_kvkk_overlay_if_present(
    page: Page,
    *,
    appear_timeout_ms: int = 3_000,
    click_timeout_ms: int = 15_000,
    hidden_timeout_ms: int = 5_000,
) -> None:
    """
    KVKK overlay'i chat input'un üzerinde pointer event'leri keser.
    Önce overlay içindeki butona tıklanır; kapanmazsa overlay DOM'dan kaldırılır (yedek).
    """
    overlay = page.locator(KVKK_OVERLAY)
    try:
        overlay.first.wait_for(state="visible", timeout=appear_timeout_ms)
    except Exception:
        return

    for sel in (KVKK_OVERLAY_BUTTONS, KVKK_OVERLAY_ROLE_BUTTONS):
        loc = page.locator(sel)
        if loc.count() == 0:
            continue
        try:
            loc.first.click(timeout=click_timeout_ms)
            break
        except Exception:
            continue

    try:
        overlay.first.wait_for(state="hidden", timeout=hidden_timeout_ms)
    except Exception:
        pass

    if not _kvkk_overlay_still_visible(page):
        return

    page.evaluate(
        """() => {
            document.querySelectorAll('.monster-kvkk-overlay').forEach((el) => el.remove());
        }"""
    )


def _kvkk_overlay_still_visible(page: Page) -> bool:
    loc = page.locator(KVKK_OVERLAY)
    try:
        if loc.count() == 0:
            return False
        return bool(loc.first.is_visible())
    except Exception:
        return False
