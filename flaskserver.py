import requests
import openai
import pandas as pd
import qrcode
import pyttsx3
import nltk
from nltk.corpus import wordnet
from flask import Flask, request, send_file, jsonify

# NLTK 데이터 다운로드 (한 번만 실행하면 됨)
nltk.download('wordnet')
nltk.download('omw-1.4')

app = Flask(__name__)

# OpenAI API 키 설정 (🔴 본인의 API 키 입력 🔴)
OPENAI_API_KEY = "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"

def call_openai_api(prompt):
    """ OpenAI API 호출 함수 """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
    return response["choices"][0]["message"]["content"]

def generate_family_words(word):
    """
    입력한 단어의 Family Words 10개 자동 생성 (WordNet 사용)
    """
    synonyms = set()
    
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())

    family_words = list(synonyms - {word})[:10]
    
    while len(family_words) < 10:
        family_words.append(f"{word}_{len(family_words)}")
    
    return family_words

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    word = data.get("word")

    # Flask API 호출
    flask_api_url = "https://flask-word-api.onrender.com/generate"
    flask_response = requests.post(flask_api_url, json={"word": word})
    
    if flask_response.status_code == 200:
        flask_data = flask_response.json()
    else:
        return jsonify({"error": "Flask API 호출 실패"}), 500

    # OpenAI GPT 호출
    gpt_prompt = f"Please generate 10 related words for '{word}' and explain their meanings."
    gpt_response = call_openai_api(gpt_prompt)

    return jsonify({
        "related_words": gpt_response,
        "excel_file": flask_data["excel_file"],
        "mp3_file": flask_data["mp3_file"],
        "qr_code": flask_data["qr_code"]
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_file(f"/tmp/{filename}", as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

