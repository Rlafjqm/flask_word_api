import requests

API_URL = "https://flask-word-api.onrender.com/generate"

data = {"word": "happy"}
response = requests.post(API_URL, json=data)

print(response.json())  # OpenAI GPT 응답 + Flask API 데이터 출력
