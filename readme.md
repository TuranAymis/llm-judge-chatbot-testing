cd "C:\turan-yazilim\playwright\chatbot"

# Sanal ortam (varsa tekrar gerekmez)

python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Gerekli paketler (Allure dahil)

pip install -r requirements.txt

pip install pytest-playwright allure-pytest

pip install allure-pytest

pip install python-dotenv

# Chatbot E2E: varsayılan canlı URL https://monster.widget.aistudio.com.tr/
# İsteğe bağlı .env: CHATBOT_BASE_URL=...  CHATBOT_WIDGET_TIMEOUT_MS=60000

# Playwright browser kurulumları (bir kere)

playwright install

# Testi çalıştır

pytest

# Altyapı testleri (Excel birim vb.):

pytest tests/test_infra.py tests/test_logic_audit.py tests/test_reporting_logic.py

# Üretim: yalnızca chatbot E2E + temiz Allure (specs/system_audit_v2.md §5b)

pytest tests/test_chatbot.py --alluredir=reports/allure-results --clean-alluredir

# Canlı widget duman (sadece yükleme + .AR-asistan-mini); ağ gerekir:

# set RUN_LIVE_WIDGET_SMOKE=1
# pytest tests/test_live_widget_smoke.py

# Rapor oluştur. 2. olan raporu tek bir index.html dosyasına sığdırıyor.

allure serve reports/allure-results

allure generate reports/allure-results --clean --single-file

# Mock soru-cevap verileri data/test-data.json içinde tutulur

python .\scripts\converter.py
