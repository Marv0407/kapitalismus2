import { ResourceDisplay } from './components/ResourceDisplay.js';
import { ScoreBoard } from './components/ScoreBoard.js';
import { connectWebSocket, disconnectWebSocket, sellWoodAction } from './services/socketManager.js';
import { registerUser, loginUser } from './services/api.js';

customElements.define('resource-display', ResourceDisplay);
customElements.define('score-board', ScoreBoard);

document.addEventListener('DOMContentLoaded', () => {
    const ui = document.getElementById('economy-ui');
    const scoreboardUi = document.getElementById('scoreboard-ui');
    const sellBtn = document.getElementById('sell-btn');
    const logoutBtn = document.getElementById('logout-btn');

    function initGameSession() {
        /* Prüft die Session und initialisiert bei Erfolg die Game-Komponenten. */
        const playerId = localStorage.getItem('player_id');
        if (!playerId) {
            document.getElementById('auth-view').classList.remove('hidden');
            document.getElementById('game-view').classList.add('hidden');
            return;
        }

        document.getElementById('auth-view').classList.add('hidden');
        document.getElementById('game-view').classList.remove('hidden');

        connectWebSocket(
            playerId,
            (gold, wood) => ui.updateValues(gold, wood),
            (data) => scoreboardUi.renderData(data)
        );
    }

    sellBtn.addEventListener('click', sellWoodAction);

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('player_id');
        disconnectWebSocket();
        document.getElementById('game-view').classList.add('hidden');
        document.getElementById('auth-view').classList.remove('hidden');
    });

    submitAuthBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    errorMsg.textContent = '';

    if (!username || !password) {
        errorMsg.textContent = 'Bitte alle Felder ausfüllen.';
        return;
    }

    try {
        let playerId;
        if (isLoginMode) {
            playerId = await loginUser(username, password);
        } else {
            playerId = await registerUser(username, password);
        }

        localStorage.setItem('player_id', playerId);
        initGameSession();
    } catch (err) {
        errorMsg.textContent = err.message;
    }
});

    initGameSession();
});
