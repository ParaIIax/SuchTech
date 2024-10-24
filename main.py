from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests

app = Flask(__name__)

# Обмеження запитів (rate limiting)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

DEEPL_API_KEY = ''   # Ключ API

# Словник кодів мов
LANGUAGE_MAP = {
    "EN": "English", "UK": "Ukrainian", "BG": "Bulgarian", "CZ": "Czech", "DA": "Danish", "DE": "German",
    "EL": "Greek", "ES": "Spanish", "ET": "Estonian", "FI": "Finnish", "FR": "French", "HU": "Hungarian",
    "ID": "Indonesian", "IT": "Italian", "JA": "Japanese", "KO": "Korean", "LT": "Lithuanian",
    "LV": "Latvian", "NB": "Norwegian", "NL": "Dutch", "PL": "Polish", "PT": "Portuguese ", "RO": "Romanian",
    "RU": "Russian", "SK": "Slovak", "SL": "Slovenian", "SV": "Swedish", "TR": "Turkish", "ZH": "Chinese"
}


# Словник кодів мов
def get_language_name(language_code):
    return LANGUAGE_MAP.get(language_code.upper(), language_code)


# Ендпоінт для перекладу
@app.route('/translate', methods=['POST'])
@limiter.limit("10 per minute")
def translate_text():
    data = request.json
    text = data.get('text')
    source_lang = data.get('source_language', '')  # Якщо не вказано, мова визначається автоматично
    target_lang = data.get('target_language')
    large_text_translation = data.get('large_text_translation', False)

    max_length = 1000 if large_text_translation else 100
    if len(text) > max_length:
        return jsonify({"error": f"Text length exceeds the limit of {max_length} characters"}), 400

    if not text or not target_lang:
        return jsonify({"error": "Text and target language are required"}), 400

    url = "https://api-free.deepl.com/v2/translate"
    params = {
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'target_lang': target_lang.upper(),
    }
    if source_lang:
        params['source_lang'] = source_lang.upper()

    response = requests.post(url, data=params)

    if response.status_code == 200:
        result = response.json()
        translated_text = result['translations'][0]['text']
        detected_language = result['translations'][0].get('detected_source_language', '')

        return jsonify({
            'translated_text': translated_text.replace('\n', '<br>'),  # Зберігаємо форматування
            'detected_source_language': get_language_name(detected_language) if not source_lang else ''
        })
    else:
        return jsonify({"error": "Failed to translate text"}), response.status_code


# Ендпоінт для отримання доступних мов
@app.route('/languages', methods=['GET'])
@limiter.limit("10 per minute")
def get_languages():
    url = "https://api-free.deepl.com/v2/languages"
    params = {
        'auth_key': DEEPL_API_KEY,
        'type': 'target'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        languages = response.json()
        return jsonify({'languages': languages})
    else:
        return jsonify({"error": "Failed to retrieve languages"}), response.status_code


if __name__ == '__main__':
    app.run(debug=True)
