let selectedBot = null;
let activeBots = [];
let userInfo = null;
let apiKey = '';

const botList = ['Бот №1', 'Бот №2', 'Бот №3', 'Бот №4', 'Бот №5'];

const socket = io('http://localhost:1648');

socket.on('bot_status_update', (data) => {
    if (data.apiKey === apiKey) {
        alert(`Bot ${data.botName} status: ${data.status}` + (data.error ? ` (Error: ${data.error})` : ''));
        updateBotStatus();
    }
});

async function updateBotStatus() {
    const response = await fetch('/apibots/get-active-bots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey })
    });

    if (response.ok) {
        const data = await response.json();
        activeBots = data.activeBots || [];
        renderBotList();
    } else {
        alert("Ошибка получения данных о статусе ботов.");
    }
}

async function getUserInfo() {
    const response = await fetch('/apibots/get-user-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey })
    });

    if (response.ok) {
        const data = await response.json();
        userInfo = data;
        document.getElementById('subscription-info').innerText =
            `${data.level} - до конца привязки: ${data.remaining_hours} часов`;
        await updateBotStatus();
    } else {
        alert("Ошибка получения информации о пользователе.");
    }
}

async function checkApiKey() {
    const response = await fetch('/apibots/get-agree', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey })
    });

    const data = await response.json();
    if (data.agree) {
        document.getElementById('menu').style.display = 'none';
        document.getElementById('main-content').style.display = 'flex';
        await getUserInfo();
    } else {
        document.getElementById('login-error').innerText = 'Неверный API ключ';
    }
}

async function syncBotCode() {
    if (!selectedBot) return;
    await fetch('/apibots/save-bot-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey, botName: selectedBot, code: document.getElementById('bot-code').value })
    });
    userInfo.bots[botList.indexOf(selectedBot)][1] = document.getElementById('bot-code').value;
}

async function toggleBotStatus() {
    if (!selectedBot) return;
    const apiUrl = activeBots.includes(selectedBot) ? '/apibots/stop-bot' : '/apibots/start-bot';
    const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey, botName: selectedBot })
    });

    if (response.ok) {
        const data = await response.json();
        if (data.status === "error") {
            alert(`Ошибка при запуске бота: ${data.message || 'неизвестная ошибка'}`);
        } else {
            await updateBotStatus();
        }
    } else {
        alert("Ошибка соединения с сервером.");
    }
}

function isBotAvailableForUser(botIndex) {
    const maxIndex = { "Минимальный": 1, "Средний": 3, "Максимальный": 5 }[userInfo.level];
    return botIndex + 1 <= maxIndex;
}

function renderBotList() {
    const botListContainer = document.getElementById('bot-list');
    botListContainer.innerHTML = '';

    botList.forEach((botName, index) => {
        const botDiv = document.createElement('div');
        const isBotActive = activeBots.includes(botName);
        const isBotAvailable = isBotAvailableForUser(index); 

        botDiv.textContent = botName;

        if (selectedBot === botName) {
            botDiv.classList.add('selected');
        }
        if (isBotActive) {
            botDiv.classList.add('active-bot');
        } else {
            botDiv.classList.add('inactive-bot');
        }
        if (!isBotAvailable) {
            botDiv.classList.add('bot-unavailable');
        }

        if (isBotAvailable) {
            botDiv.onclick = () => {
                selectedBot = botName;
                document.getElementById('selected-bot-name').innerText = botName;
                document.getElementById('start-stop-button').innerText = isBotActive ? 'Остановить' : 'Запустить';
                document.getElementById('bot-code').value = userInfo.bots[index][1];
                renderBotList();
            };
        } else {
            botDiv.onclick = null;
        }

        botListContainer.appendChild(botDiv);
    });
}

document.getElementById('login-btn').onclick = () => {
    apiKey = document.getElementById('api-key').value;
    checkApiKey();
};

document.getElementById('bot-code').addEventListener('input', syncBotCode);
document.getElementById('start-stop-button').onclick = toggleBotStatus;
