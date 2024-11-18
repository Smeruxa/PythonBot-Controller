



from flask import jsonify
import time
import json

JSON_FILE = 'data.json'

def get_user_data(api_key):
    """Получает данные пользователя по API-ключу."""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(api_key, {})

def save_user_data(api_key, user_data):
    """Сохраняет данные пользователя в файл."""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data[api_key] = user_data
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_info(request):
    """Обработчик `/apibots/get-user-info`."""
    api_key = request.json.get('apiKey')
    user_data = get_user_data(api_key)
    if user_data:
        remaining_hours = (user_data['time_start'] + user_data['duration_hours'] * 3600 - time.time()) / 3600
        return jsonify({"level": user_data["level"], "remaining_hours": round(remaining_hours), "bots": user_data["bots"]})
    
    return jsonify({}), 403