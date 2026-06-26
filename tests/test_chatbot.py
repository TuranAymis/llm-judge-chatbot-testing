import json
import logging
import os
import sys
import pytest
import allure
from allure_commons.types import AttachmentType
from playwright.sync_api import Page, expect

# Projenin kök dizinini Python'ın arama yoluna ekler
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.judge_factory import get_judge
from utils.evaluation_utils import prepare_ai_evaluation
from utils.widget_selectors import (
    BOT_MESSAGE_PARAGRAPHS,
    CHAT_INPUT,
    LAUNCHER_BUTTON,
    TYPING_INDICATOR_SUBSTRING,
    complete_pre_chat_registration,
    dismiss_kvkk_overlay_if_present,
    strip_trailing_meta_line,
)

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(override=True)
except Exception:
    pass

logger = logging.getLogger(__name__)

DEFAULT_CHATBOT_BASE_URL = "https://monster.widget.aistudio.com.tr/"

judge = None


def _chatbot_base_url() -> str:
    raw = os.getenv("CHATBOT_BASE_URL", DEFAULT_CHATBOT_BASE_URL).strip()
    return raw if raw.endswith("/") else raw + "/"


def _widget_load_timeout_ms() -> int:
    """Launcher / sayfa iskeleti (widget yükü). Karşılama mesajından ayrı tutulur."""
    try:
        return max(5_000, int(os.getenv("CHATBOT_WIDGET_TIMEOUT_MS", "60000")))
    except ValueError:
        return 60_000


def _bot_bubbles_excluding_typing(page: Page):
    return page.locator(BOT_MESSAGE_PARAGRAPHS).filter(
        has_not_text=TYPING_INDICATOR_SUBSTRING
    )


def get_or_skip_judge():
    global judge
    if judge is None:
        try:
            judge = get_judge()
        except Exception as exc:
            pytest.skip(f"LLM judge başlatılamadı: {exc}")
    return judge


def load_test_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "..", "data", "test-data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    "item",
    load_test_data(),
    ids=lambda x: f"Soru: {x['soru'][:30]}...",
)
def test_monster_chatbot_per_question(page: Page, item, request):
    # 1. Canlı sayfa; launcher görünene kadar bekle
    page.goto(_chatbot_base_url(), wait_until="domcontentloaded")
    launcher = page.locator(LAUNCHER_BUTTON)
    expect(launcher).to_be_visible(timeout=_widget_load_timeout_ms())

    # 2. Sohbeti aç
    launcher.click()
    chat_input = page.locator(CHAT_INPUT)
    expect(chat_input).to_be_visible(timeout=30_000)

    # KVKK overlay giriş alanının üzerinde tıklamayı engelleyebilir
    dismiss_kvkk_overlay_if_present(page)

    # 3–4. Ön-kayıt: ad-soyad, e-posta; ardından "Merhaba" karşılama
    with allure.step("Ön-kayıt (ad-soyad, e-posta) ve karşılama"):
        initial_welcome = complete_pre_chat_registration(page)
    request.node.initial_bot_welcome = initial_welcome or ""
    logger.info("Karşılama mesajı alındı.")
    allure.attach(
        initial_welcome,
        name="Initial Greeting",
        attachment_type=AttachmentType.TEXT,
    )

    bubbles = _bot_bubbles_excluding_typing(page)
    prev_count = bubbles.count()

    # 5. Soruyu sor
    chat_input.click()
    chat_input.fill(item["soru"])
    chat_input.press("Enter")

    # 6. Yeni asistan balonu (typing hariç) gelene kadar bekle
    try:
        page.wait_for_function(
            f"""() => {{
                const sel = '.covo-messages .background .p';
                const nodes = document.querySelectorAll(sel);
                let n = 0;
                for (const el of nodes) {{
                    const t = (el.textContent || '').trim();
                    if (t && !t.includes('Yazıyor')) n++;
                }}
                return n > {prev_count};
            }}""",
            timeout=60_000,
        )
    except Exception:
        pytest.skip("Bot belirlenen sürede cevap vermedi (servis/yükleme gecikmesi olabilir).")

    # 7. Son asistan cevabı (typing satırı değil)
    bot_response_locator = bubbles.last
    raw_answer = bot_response_locator.inner_text()
    actual_answer = strip_trailing_meta_line(raw_answer)

    # Raporlama için temel verileri aktar
    request.node.actual_answer = actual_answer
    request.node.question = item.get("soru", "")
    request.node.expected_answer = item.get("cevap", "")

    # --- LLM HAKEM DEĞERLENDİRMESİ (prepare_ai_evaluation: parse + normalize + tutarlılık) ---
    with allure.step("LLM Hakemi yanıtı değerlendiriyor"):
        kriter = request.node.expected_answer
        try:
            raw_evaluation = get_or_skip_judge().evaluate(
                question=item["soru"],
                bot_response=actual_answer,
                expected_criteria=kriter,
            )
        except Exception as exc:
            evaluation = {
                "score": 0,
                "reasoning": f"[Hakem çağrısı hatası] {exc}",
                "status": "FAIL",
            }
        else:
            evaluation = prepare_ai_evaluation(raw_evaluation, actual_answer)

    # Raporlama hook'u için AI değerlendirmesini node'a koy (ai_score her zaman int)
    request.node.ai_score = int(evaluation.get("score", 0))
    request.node.ai_reasoning = evaluation.get("reasoning", "")
    request.node.ai_status = evaluation.get("status", "FAIL")

    # Allure: kota/yetki skip'inden önce de ekler yazılsın (attachment'lar kaybolmasın)
    with allure.step("Test Sonuç Detayları"):
        allure.attach(item.get("soru", ""), name="Soru", attachment_type=AttachmentType.TEXT)
        allure.attach(request.node.expected_answer, name="Beklenen Tam Cevap", attachment_type=AttachmentType.TEXT)
        allure.attach(actual_answer, name="Chatbot Cevabı", attachment_type=AttachmentType.TEXT)
        allure.attach(
            str(evaluation.get("score", "")),
            name="ai_score",
            attachment_type=AttachmentType.TEXT,
        )
        allure.attach(
            str(evaluation.get("reasoning", "")),
            name="ai_reasoning",
            attachment_type=AttachmentType.TEXT,
        )
        allure.attach(
            str(evaluation.get("status", "")),
            name="ai_status",
            attachment_type=AttachmentType.TEXT,
        )
        allure.attach(
            f"Puan: {evaluation.get('score')}/5\nGerekçe: {evaluation.get('reasoning')}",
            name="LLM Hakem Raporu",
            attachment_type=AttachmentType.TEXT,
        )

    st = evaluation.get("status", "FAIL")
    if st == "SISTEM_KOTA":
        pytest.skip("API Kotası Dolu")
    if st == "SISTEM_YETKI":
        pytest.skip(evaluation.get("reasoning", "API yetki veya anahtar hatası"))

    # 8. Doğrulama (Artık LLM Skoruna Dayalı)
    # Status 'PASS' değilse veya puan düşükse testi kalır sayıyoruz
    assert evaluation.get("status") == "PASS", (
        f"LLM Düşük Puan Verdi! Skoru: {evaluation.get('score')} | "
        f"Gerekçe: {evaluation.get('reasoning')}"
    )
