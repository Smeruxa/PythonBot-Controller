from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from auth import get_agree
from json_utils import get_user_info, save_user_data, get_user_data
from websockets import socketio, emit_bot_status, monitor_bot, handle_start_bot, handle_stop_bot, get_active_bots

app = Flask(__name__)
socketio.init_app(app)

@app.route('/apibots/get-agree', methods=['POST'])
def get_agree_route():
    return get_agree(request)

@app.route('/apibots/get-user-info', methods=['POST'])
def get_user_info_route():
    return get_user_info(request)

@app.route('/apibots/save-bot-code', methods=['POST'])
def save_bot_code():
    api_key = request.json.get('apiKey')
    bot_name = request.json.get('botName')
    code = request.json.get('code')
    
    user_data = get_user_data(api_key)
    if user_data:
        bot_index = int(bot_name.split('№')[1].strip()) - 1
        user_data["bots"][bot_index][1] = code 
        save_user_data(api_key, user_data)
        return jsonify({"status": "success"})
        
    return jsonify({}), 403

@app.route('/apibots/start-bot', methods=['POST'])
def start_bot_route():
    return handle_start_bot(request)

@app.route('/apibots/stop-bot', methods=['POST'])
def stop_bot_route():
    return handle_stop_bot(request)

@app.route('/apibots/get-active-bots', methods=['POST'])
def get_active_bots_route():
    return get_active_bots(request)

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=1648, debug=True)