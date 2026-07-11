import { TopBar } from './components/TopBar.js';
import { PlayerInfo } from './components/PlayerInfo.js';
import { ScoreBoard } from './components/ScoreBoard.js'; // (Optional später in die UI einbauen)
import { SectorGrid } from './components/SectorGrid.js';
import { OverworldMap } from "./components/OverworldMap.js";
import { connectWebSocket, disconnectWebSocket, gatherManualAction, claimHexAction } from './services/socketManager.js';
import { registerUser, loginUser } from './services/api.js';

customElements.define('top-bar', TopBar);
customElements.define('player-info', PlayerInfo);
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
        const playerId = localStorage.getItem('player_id');
        if (!playerId) { return; }

        document.getElementById('auth-view').classList.add('hidden');
        document.getElementById('game-view').classList.remove('hidden');

        const topBarUi = document.getElementById("top-bar-ui");
        const playerInfoUi = document.getElementById("player-info-ui");
        const overworldUi = document.getElementById("overworld-ui");
        const mapUi = document.getElementById('map-ui');

        // Button Listener für manuelles Sammeln
        document.getElementById('gather-wood-btn').addEventListener('click', () => gatherManualAction('wood'));
        document.getElementById('gather-stone-btn').addEventListener('click', () => gatherManualAction('stone'));

        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('player_id');
            disconnectWebSocket();
            location.reload();
        });

        connectWebSocket(
            playerId,
            (resourceData) => {
                topBarUi.updateResources(resourceData);
                playerInfoUi.updateInfo(resourceData);
            },
            (scoreboardData) => { /* Aktuell ausgeblendet, Platz für später */ },
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
