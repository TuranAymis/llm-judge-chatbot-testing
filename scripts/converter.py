import json
import os
import re
from docx import Document


QUESTION_NUMBER_RE = re.compile(r"^\d+[\.\)]\s*")
STEP_PREFIX_RE = re.compile(r"^\d+[️⃣]\s*")
PHONE_OR_TIME_LINE_RE = re.compile(r"^[\d\s\-\–:\(\)]+$")


def clean_text(text):
    return QUESTION_NUMBER_RE.sub("", text).strip()


def is_question_line(text):
    """
    Sadece gerçek soru başlıklarını yakalamaya çalışır.
    Cevap içindeki adım/liste satırlarını ve teknik satırları dışlar.
    """
    t = text.strip()
    if not t:
        return False

    # Güvenli tarafta kalmak için soru cümlesi sonu zorunlu.
    if not t.endswith("?"):
        return False

    lowered = t.lower()
    if lowered.startswith(("http://", "https://", "www.")) or "@" in t:
        return False
    if t.startswith(("🔗", "-", "•")):
        return False
    if STEP_PREFIX_RE.match(t):
        return False
    if PHONE_OR_TIME_LINE_RE.fullmatch(t):
        return False

    without_index = QUESTION_NUMBER_RE.sub("", t).strip()
    if len(without_index) < 8:
        return False
    if without_index.count("?") > 1:
        return False

    return True


def append_qa_record(qa_list, question_text, answer_lines):
    if not question_text:
        return
    full_answer = "\n".join(answer_lines).strip()
    if not full_answer:
        return
    qa_list.append({
        "soru": clean_text(question_text),
        "cevap": full_answer,
    })

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
        if not text:
            continue

        if is_question_line(text):
            append_qa_record(qa_list, current_question, current_answer)
            current_question = text
            current_answer = []
            continue

        # Henüz soru yakalanmadıysa cevap biriktirme.
        if current_question is None:
            continue
        current_answer.append(text)

    append_qa_record(qa_list, current_question, current_answer)

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(qa_list, f, ensure_ascii=False, indent=4)

    print(f"İşlem tamam! {len(qa_list)} soru-cevap kaydedildi.")

if __name__ == "__main__":
    convert_word_to_json()