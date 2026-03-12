import pytest
import pandas as pd
import allure
import json
import os
from datetime import datetime

# Test sonuçlarını biriktireceğimiz liste
results_table = []

def load_test_data():
    # Buraya kendi JSON veya Excel okuma kodunu koymalısın
    # Örnek:
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    # Testin ana gövdesi (call) bittiğinde hem pass hem fail için çalışır
    if report.when == "call":
        # Test fonksiyonundan gelen gerçek cevabı al (Excel için)
        actual = getattr(item, "actual_answer", "Cevap Alınamadı")
        
        # --- TÜM DURUMLARDA EKRAN GÖRÜNTÜSÜ AL ---
        page = item.funcargs.get("page")
        if page:
            # Duruma göre isim verelim (Pass mi Fail mi?)
            status_prefix = "GECEN_TEST" if report.passed else "HATALI_TEST"
            
            allure.attach(
                page.screenshot(full_page=True),
                name=f"{status_prefix}_Ekran_Goruntusu",
                attachment_type=allure.attachment_type.PNG
            )

        # Excel listesine ekleme mantığı (aynen kalıyor)
        test_data = item.callspec.params.get("item", {})
        results_table.append({
            "Soru": test_data.get("soru", "Bilinmiyor"),
            "Beklenen Cevap": test_data.get("cevap", "Bilinmiyor"),
            "Chatbot Cevabı": actual,
            "Durum": "GEÇTİ" if report.passed else "KALDI",
            "Tarih": datetime.now().strftime("%H:%M:%S")
        })

@pytest.fixture(scope="session", autouse=True)
def export_to_excel():
    yield
    # Testler bittikten sonra Excel'i kaydet
    if results_table:
        df = pd.DataFrame(results_table)
        output_path = "Chatbot_Test_Raporu.xlsx"
        df.to_excel(output_path, index=False)
        print(f"\n📊 Excel raporu kaydedildi: {output_path}")