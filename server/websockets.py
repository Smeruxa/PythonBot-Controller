import subprocess
import threading
import time
import psutil
from flask_socketio import SocketIO, emit
from json_utils import get_user_data, save_user_data
from auth import check_subscription_active
from flask import jsonify
import tempfile

socketio = SocketIO()

bot_processes = {}

def get_active_bots(request):
    """Возвращает список активных ботов для пользователя."""
    api_key = request.json.get('apiKey')
    user_data = get_user_data(api_key)
    
    if user_data and check_subscription_active(user_data):
        active_bots = [f"Бот №{i + 1}" for i, bot in enumerate(user_data["bots"]) if bot[0]]
        return jsonify({"activeBots": active_bots})
    
    return jsonify({"activeBots": []}), 403

def monitor_bot(api_key, bot_name, pid):
    """Мониторим процесс бота и уведомляем клиента о завершении работы."""
    try:
        process = psutil.Process(pid)
        process.wait()
        emit_bot_status(api_key, bot_name, "stopped", error="Process terminated unexpectedly")
    except psutil.NoSuchProcess:
        emit_bot_status(api_key, bot_name, "stopped", error="Process not found")

def emit_bot_status(api_key, bot_name, status, error=None):
    """Отправка статуса бота клиенту через WebSocket."""
    socketio.emit(
        'bot_status_update',
        {'apiKey': api_key, 'botName': bot_name, 'status': status, 'error': error},
        broadcast=True
    )

def handle_start_bot(request):
    """Обработчик старта бота."""
    api_key = request.json.get('apiKey')
    bot_name = request.json.get('botName')
    user_data = get_user_data(api_key)

    if user_data:
        max_bots = {"Минимальный": 1, "Средний": 3, "Максимальный": 5}[user_data["level"]]
        bot_index = int(bot_name.split('№')[1].strip()) - 1

        if bot_index < max_bots and not user_data["bots"][bot_index][0]:
            try:
                with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                    temp_file.write(user_data["bots"][bot_index][1].encode())
                    temp_file.flush()

                    process = subprocess.Popen(["python3", temp_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    pid = process.pid

                    threading.Thread(target=monitor_bot, args=(api_key, bot_name, pid), daemon=True).start()

                    user_data["bots"][bot_index][0] = True
                    user_data["bots"][bot_index].append(pid)
                    save_user_data(api_key, user_data)
                    
                    emit_bot_status(api_key, bot_name, "started")
                    return {'status': 'started'}

            except Exception as e:
                return {'status': 'error', 'message': str(e)}, 500
    return {'status': 'failed'}, 403

def handle_stop_bot(request):
    """Обработчик остановки бота."""
    api_key = request.json.get('apiKey')
    bot_name = request.json.get('botName')
    user_data = get_user_data(api_key)
    bot_index = int(bot_name.split('№')[1].strip()) - 1

    if user_data and user_data["bots"][bot_index][0]:
        try:
            pid = user_data["bots"][bot_index][2] if len(user_data["bots"][bot_index]) > 2 else None
            if pid and psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)

            user_data["bots"][bot_index][0] = False
            if len(user_data["bots"][bot_index]) > 2:
                user_data["bots"][bot_index].pop(2)
            save_user_data(api_key, user_data)

            emit_bot_status(api_key, bot_name, "stopped")
            return {'status': 'stopped'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500
    return {'status': 'failed'}, 403

def sync_bot_status(api_key, bot_name):
    """Синхронизация состояния бота с клиентом."""
    user_data = get_user_data(api_key)
    if user_data:
        bot_index = int(bot_name.split('№')[1].strip()) - 1
        if user_data["bots"][bot_index][0]:
            emit_bot_status(api_key, bot_name, "started")
        else:
            emit_bot_status(api_key, bot_name, "stopped")
