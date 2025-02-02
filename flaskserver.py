import os
import pandas as pd
import qrcode
import pyttsx3
import nltk
from nltk.corpus import wordnet
from flask import Flask, request, send_file, jsonify

# NLTK 데이터 다운로드 (한 번만 실행하면 됨)
nltk.download('wordnet')
nltk.download('omw-1.4')

# 운영 체제에 따라 임시 디렉터리 설정
TEMP_DIR = os.path.join(os.getcwd(), "tmp")  # 현재 디렉토리 + tmp 폴더
os.makedirs(TEMP_DIR, exist_ok=True)  # 디렉터리가 없으면 생성

app = Flask(__name__)

def generate_family_words(word):
    """
    WordNet을 활용하여 단어의 동의어, 유사 단어, 상위 개념, 하위 개념을 찾아서 10개 확보
    """
    synonyms = set()

    # 1️⃣ WordNet에서 동의어(synonyms) 가져오기
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))  # _ 제거하여 자연스럽게 표시

    # 2️⃣ WordNet에서 관련 단어(hypernym, hyponym) 추가
    related_words = set()
    for syn in wordnet.synsets(word):
        for hypernym in syn.hypernyms():  # 상위 개념
            for lemma in hypernym.lemmas():
                related_words.add(lemma.name().replace("_", " "))

        for hyponym in syn.hyponyms():  # 하위 개념
            for lemma in hyponym.lemmas():
                related_words.add(lemma.name().replace("_", " "))

    # 3️⃣ 추가적인 관련 단어(어근, 파생어) 가져오기
    derived_words = set()
    for syn in wordnet.synsets(word):
        for related in syn.lemmas():
            if related.derivationally_related_forms():
                for lemma in related.derivationally_related_forms():
                    derived_words.add(lemma.name().replace("_", " "))

    # ✅ 최종적으로 모든 단어를 합치고 중복 제거
    all_words = list(synonyms | related_words | derived_words)  # 합집합
    all_words = [w for w in all_words if w.lower() != word.lower()]  # 입력 단어 제외

    # ✅ 부족한 경우 일반적인 유사 단어 추가
    if len(all_words) < 10:
        fallback_words = ["joyful", "cheerful", "delightful", "content", "pleased",
                          "jubilant", "elated", "blissful", "ecstatic", "euphoric"]
        for fw in fallback_words:
            if fw not in all_words:
                all_words.append(fw)
            if len(all_words) == 10:
                break

    return all_words[:10]  # 최대 10개만 반환

def generate_audio(word_list, file_path):
    """
    단어 리스트를 MP3 파일로 변환 (미국식 발음 적용)
    """
    engine = pyttsx3.init()

    # 1️⃣ Windows에서 미국식 목소리 찾기
    voices = engine.getProperty("voices")
    for voice in voices:
        if "Zira" in voice.name or "David" in voice.name:  # 미국식 기본 음성 찾기
            engine.setProperty("voice", voice.id)
            break

    engine.setProperty("rate", 150)  # 음성 속도 조정
    engine.save_to_file(", ".join(word_list), file_path)  # 쉼표 추가하여 자연스럽게 읽음
    engine.runAndWait()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True, silent=True)
    if not data or "word" not in data:
        return jsonify({"error": "Missing 'word' in request"}), 400

    word = data["word"]
    family_words = generate_family_words(word)

    # ✅ OS에 맞는 임시 폴더에 파일 저장
    file_path = os.path.join(TEMP_DIR, f"{word}_Family_Words.xlsx")
    df = pd.DataFrame({"Family Words": family_words})
    df.to_excel(file_path, index=False)

    audio_path = os.path.join(TEMP_DIR, f"{word}_Family_Words.mp3")
    generate_audio(family_words, audio_path)

    qr_path = os.path.join(TEMP_DIR, f"{word}_QR.png")
    qr = qrcode.make(f"http://localhost:5000/download/{word}_Family_Words.mp3")
    qr.save(qr_path)

    return jsonify({
        "excel_file": f"http://localhost:5000/download/{word}_Family_Words.xlsx",
        "mp3_file": f"http://localhost:5000/download/{word}_Family_Words.mp3",
        "qr_code": f"http://localhost:5000/download/{word}_QR.png"
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)


