import time
from flask import jsonify
from json_utils import get_user_data

RATE_LIMIT_SECONDS = 1
last_access = {}

def rate_limit(api_key):
    """Проверяет лимит частоты запросов для API-ключа."""
    global last_access
    current_time = time.time()
    if api_key in last_access and current_time - last_access[api_key] < RATE_LIMIT_SECONDS:
        return False

    last_access[api_key] = current_time
    return True

def check_subscription_active(user_data):
    """Проверяет, активна ли подписка у пользователя."""
    end_time = user_data['time_start'] + user_data['duration_hours'] * 3600
    return time.time() < end_time

def get_agree(request):
    """Обработчик `/apibots/get-agree`."""
    api_key = request.json.get('apiKey')
    if not rate_limit(api_key):
        return jsonify({"agree": False}), 429

    user_data = get_user_data(api_key)
    if user_data and check_subscription_active(user_data):
        return jsonify({"agree": True})

    return jsonify({"agree": False})
