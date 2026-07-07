import { ResourceDisplay } from './components/ResourceDisplay.js';
import { ScoreBoard } from './components/ScoreBoard.js';
import { SectorGrid } from './components/SectorGrid.js';
import { connectWebSocket, disconnectWebSocket, sellWoodAction, claimHexAction } from './services/socketManager.js';
import { registerUser, loginUser } from './services/api.js';
import { OverworldMap } from "./components/OverworldMap.js";

customElements.define('resource-display', ResourceDisplay);
customElements.define('score-board', ScoreBoard);
customElements.define('sector-grid', SectorGrid);
customElements.define('overworld-map', OverworldMap);

document.addEventListener('DOMContentLoaded', () => {
    const scoreboardUi = document.getElementById('scoreboard-ui');
    const logoutBtn = document.getElementById('logout-btn');
    const gameLayoutLeft = document.getElementById('game-layout-left');

    const authTitle = document.getElementById('auth-title');
    const errorMsg = document.getElementById('error-msg');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitAuthBtn = document.getElementById('submit-auth-btn');
    const toggleAuthBtn = document.getElementById('toggle-auth-btn');

    let isLoginMode = true;

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

        gameLayoutLeft.innerHTML = `
            <resource-display id="economy-ui"></resource-display>
            <overworld-map id="overworld-ui"></overworld-map>
            <sector-grid id="map-ui" class="hidden"></sector-grid>
            <button id="sell-btn" style="margin-top: 20px;">10 Holz für 5 Gold an NPC verkaufen</button>
        `;

        const ui = document.getElementById("economy-ui");
        const overworldUi = document.getElementById("overworld-ui");
        const mapUi = document.getElementById('map-ui');

        /* Bindet den Klick-Event-Listener an den dynamisch neu erstellten Button */
        document.getElementById('sell-btn').addEventListener('click', sellWoodAction);

        connectWebSocket(
            playerId,
            (gold, wood) => ui.updateValues(gold, wood),
            (data) => scoreboardUi.renderData(data),
            (mapData) => {
                if (mapData.length > 0) {
                    overworldUi.classList.add('hidden');
                    mapUi.classList.remove('hidden');
                    mapUi.renderMap(mapData);
                }
            },
            (overworldData) => {
                overworldUi.renderOverworld(overworldData, playerId, claimHexAction);
            }
        );
    }

    toggleAuthBtn.addEventListener('click', () => {
        isLoginMode = !isLoginMode;
        authTitle.textContent = isLoginMode ? 'Anmelden' : 'Registrieren';
        submitAuthBtn.textContent = isLoginMode ? 'Einloggen' : 'Konto erstellen';
        toggleAuthBtn.textContent = isLoginMode ? 'Konto erstellen' : 'Bereits registriert?';
        errorMsg.textContent = '';
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

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('player_id');
        disconnectWebSocket();
        document.getElementById('game-view').classList.add('hidden');
        document.getElementById('auth-view').classList.remove('hidden');
    });

    initGameSession();
});
