import pytest
import json
import os
import allure
from allure_commons.types import AttachmentType
from playwright.sync_api import Page, expect

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
    # 1. Sayfa ve Chatbot Hazırlığı
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "..", "chatbot-widget.html")
    page.goto(f"file://{os.path.abspath(html_path)}")

    # 2. Chatbot'u aç
    page.locator("//div[@class='AR-asistan-mini']").click()
    chat_input = page.get_by_placeholder("Herhangi bir şey sor.")
    expect(chat_input).to_be_visible(timeout=10000)

    # 3. Selamlama mesajının gelmesini bekle ve mevcut mesaj sayısını al
    page.wait_for_selector("//div[@class='AI-message-2']", timeout=10000)
    prev_message_count = page.locator("//div[@class='AI-message-2']").count()

    # 4. Soruyu sor
    chat_input.click()
    chat_input.fill(item["soru"])
    chat_input.press("Enter")
    
    # 5. Yeni bir mesaj gelene kadar bekle
    try:
        page.wait_for_function(
            f"document.querySelectorAll('.AI-message-2').length > {prev_message_count}",
            timeout=30000,
        )
    except Exception:
        pytest.fail("Bot belirlenen sürede cevap vermedi!")

    # 6. En son gelen (gerçek cevap) mesajını al
    bot_response_locator = page.locator("//div[@class='AI-message-2']").last
    actual_answer = bot_response_locator.inner_text()

    # --- KRİTİK: EXCEL RAPORU İÇİN VERİYİ AKTAR ---
    request.node.actual_answer = actual_answer 

    # 7. Allure Detaylarını Ekle
    with allure.step("Soru ve cevap detayları"):
        allure.attach(item.get("soru", ""), name="Soru", attachment_type=AttachmentType.TEXT)
        allure.attach(item.get("cevap", ""), name="Beklenen Cevap", attachment_type=AttachmentType.TEXT)
        allure.attach(actual_answer, name="Chatbot Cevabı", attachment_type=AttachmentType.TEXT)

    # 8. Doğrulama (Keywords bazlı)
    keywords = item.get("keywords", [])
    bulunanlar = [k for k in keywords if k.lower() in actual_answer.lower()]

    unique_found = len(bulunanlar)
    min_esik = 2 if len(keywords) >= 5 else 1

    hata_detayi = f"Arananlar: {keywords} | Bulunanlar: {bulunanlar}"
    
    # Assert
    assert unique_found >= min_esik, f"Anlamsal uyuşmazlık! {hata_detayi}"