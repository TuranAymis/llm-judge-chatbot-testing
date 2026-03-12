import json
import os
import re
from docx import Document

def clean_text(text):
    return re.sub(r'^\d+[\.\)]\s*', '', text).strip()

def extract_keywords(text):
    """Metinden gerçekten ayırt edici olan (sayı, telefon, teknik terim) anahtar kelimeleri seçer."""
    text = text.lower()
    
    # 1. Önce sayıları yakala (15, 0850, 255 vb. - Bunlar botun cevabındaki en kesin verilerdir)
    numbers = re.findall(r'\d+', text)
    
    # 2. Kelimeleri ayıkla (En az 4 karakterli ve sadece harfler)
    words = re.findall(r'\b[a-zçğıöşü]{4,}\b', text)
    
    # 3. "Stopwords" - Botun her cümlede kullandığı ama ayırt edici olmayan kelimeleri ele
    ignored_words = {
        "aldığınız", "içerisinde", "itibaren", "edebilirsiniz", "yeterlidir", 
        "sağlayacaktır", "durumda", "olmaktan", "şunları", "yapılan", "işlemleri",
        "genellikle", "kapsamında", "ilgili", "boyu", "sırasında", "olan", "veya",
        "kadar", "yeterli", "tarafından", "mevcut", "üzerinden", "gerekli", "için"
    }
    
    filtered_words = [w for w in words if w not in ignored_words]
    
    # 4. Sayıları ve önemli kelimeleri birleştir (Sayılar öncelikli)
    all_keywords = list(dict.fromkeys(numbers + filtered_words))
    
    # En vurucu 12 anahtar kelimeyi döndür
    return all_keywords[:12]

def convert_word_to_json():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    word_file_name = "testData.docx" 
    docx_path = os.path.join(current_dir, '..', word_file_name)
    json_path = os.path.join(current_dir, '..', 'data', 'test-data.json')

    if not os.path.exists(docx_path):
        print(f"Hata: '{docx_path}' bulunamadı!")
        return

    doc = Document(docx_path)
    qa_list = []
    current_question = None
    current_answer = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        if re.match(r'^\d+[\.\)]', text) or text.endswith('?'):
            if current_question:
                full_answer = "\n".join(current_answer).strip()
                qa_list.append({
                    "soru": clean_text(current_question),
                    "cevap": full_answer,
                    "keywords": extract_keywords(full_answer)
                })
            current_question = text
            current_answer = []
        else:
            if current_question:
                current_answer.append(text)

    if current_question:
        full_answer = "\n".join(current_answer).strip()
        qa_list.append({
            "soru": clean_text(current_question),
            "cevap": full_answer,
            "keywords": extract_keywords(full_answer)
        })

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(qa_list, f, ensure_ascii=False, indent=4)

    print(f"İşlem tamam! {len(qa_list)} soru ve akıllı anahtar kelimeler kaydedildi.")

if __name__ == "__main__":
    convert_word_to_json()