# LLM Judge Chatbot Testing | [English](README.md) |

![CI](https://github.com/TuranAymis/llm-judge-chatbot-testing/actions/workflows/ci.yml/badge.svg)

Chatbot cevaplarını yapılandırılmış mock test verileri ve LLM tabanlı değerlendirme yaklaşımıyla test etmek için hazırlanmış Python tabanlı bir QA automation projesidir.

Bu repository, chatbot cevaplarının tekrar edilebilir bir test akışıyla nasıl kontrol edilebileceğini gösterir. Projede Playwright, Pytest, JSON test verisi, Allure raporlama ve opsiyonel LLM judge yaklaşımı kullanılır.

## Projenin Amacı

Bu projenin amacı, chatbot davranışlarını otomatik end-to-end testlerle doğrulamaktır.

Test akışı temel olarak şunları hedefler:

* Tarayıcıda chatbot widget’ını açmak
* Önceden tanımlanmış test sorularını göndermek
* Chatbot cevaplarını yakalamak
* Gerçek cevapları beklenen kriterlerle karşılaştırmak
* Cevap kalitesini LLM judge ile değerlendirmek
* Test sonuçları ve opsiyonel Allure raporları üretmek

Bu proje, public QA automation portfolio projesi olarak düzenlenmiştir.

## Kullanılan Teknolojiler

* Python
* Pytest
* Playwright
* pytest-playwright
* Allure Pytest
* JSON test verisi
* python-dotenv
* OpenAI / Gemini entegrasyonu ile LLM tabanlı değerlendirme

## Repository Yapısı

```text
.
├── chatbotKontrolAI/
├── data/
│   └── test-data.json
├── scripts/
│   └── converter.py
├── specs/
│   └── system_audit_v2.md
├── tests/
│   └── test_chatbot.py
├── utils/
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
├── README.md
└── README_TR.md
```

## Test Verisi

Projede güvenli mock test verisi kullanılır.

Test verisi şu dosyada tutulur:

```text
data/test-data.json
```

Mevcut mock data formatı:

```json
[
  {
    "soru": "What are the main benefits of automated testing in a software project?",
    "cevap": "Automated testing provides faster feedback, repeatable test execution, better regression coverage, and helps teams detect issues earlier."
  },
  {
    "soru": "What is the difference between smoke testing and regression testing?",
    "cevap": "Smoke testing checks whether the most critical functions work after a build, while regression testing checks that existing features still work after changes."
  }
]
```

Private, müşteriyle ilgili, şirkete ait veya gerçek production test verileri bu repository’ye commit edilmemelidir.

## Environment Variables

Local ortamda `.env.example` dosyası baz alınarak `.env` dosyası oluşturulmalıdır.

Örnek değişkenler:

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
LLM_TYPE=openai

CHATBOT_BASE_URL=
CHATBOT_WIDGET_TIMEOUT_MS=60000

CHATBOT_TEST_NAME=Test Automation
CHATBOT_TEST_EMAIL=test@example.com
```

`.env` dosyası repository’ye commit edilmemelidir.

## Kurulum

Repository’yi clone et:

```bash
git clone https://github.com/TuranAymis/llm-judge-chatbot-testing.git
cd llm-judge-chatbot-testing
```

Virtual environment oluştur:

```bash
python -m venv .venv
```

Virtual environment’ı aktive et.

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Bağımlılıkları yükle:

```bash
pip install -r requirements.txt
```

Playwright browser’larını yükle:

```bash
playwright install
```

## Testleri Çalıştırma

Tüm testleri çalıştır:

```bash
pytest
```

Verbose çıktı ile çalıştır:

```bash
pytest -v
```

Chatbot E2E testini Allure sonuçlarıyla çalıştır:

```bash
pytest tests/test_chatbot.py --alluredir=reports/allure-results --clean-alluredir
```

Allure raporunu local olarak aç:

```bash
allure serve reports/allure-results
```

Static Allure raporu oluştur:

```bash
allure generate reports/allure-results --clean
```

## QA Odağı

Bu proje aşağıdaki QA automation pratiklerini gösterir:

* Chatbot response validation
* Playwright ile end-to-end test
* JSON ile data-driven testing
* LLM destekli cevap değerlendirme
* Mock test data kullanımı
* Allure ile test raporlama
* Environment-based configuration
* Public repository hijyeni

## Repository Hijyeni

Aşağıdaki dosya ve klasörler commit edilmemelidir:

```text
.venv/
venv/
.env
allure-report/
allure-results/
reports/
*.docx
*.xlsx
*.csv
__pycache__/
.pytest_cache/
```

Repository’de yalnızca güvenli mock test verisi tutulmalıdır.

## Mevcut Durum

Bu repository portfolio kullanımı için temizlenmiş ve yeniden adlandırılmıştır.

Tamamlanan iyileştirmeler:

* Virtual environment dosyaları repository’den kaldırıldı
* Generated report dosyaları kaldırıldı
* Gerçek test verileri kaldırıldı
* Gerçek veriler güvenli mock sorularla değiştirildi
* Repository adı `llm-judge-chatbot-testing` olarak güncellendi
* Profesyonel README yapısı eklendi

Planlanan iyileştirmeler:

* `.gitignore` dosyasını temiz ve standart hale getirmek
* Test sonucu örneklerini daha açık göstermek
* Örnek Allure report ekran görüntüsü eklemek
* GitHub repository description ve topics alanlarını doldurmak
* `specs/` klasörü altında test dokümantasyonunu geliştirmek
