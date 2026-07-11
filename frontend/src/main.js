import {TopBar} from './components/TopBar.js';
import {PlayerInfo} from './components/PlayerInfo.js';
import {SectorGrid} from './components/SectorGrid.js';
import {OverworldMap} from "./components/OverworldMap.js";
import {
    assignWorkersAction,
    claimHexAction,
    connectWebSocket,
    disconnectWebSocket,
    gatherManualAction,
    devCheatResources,
    devRunCode
} from './services/socketManager.js';
import {loginUser, registerUser} from './services/api.js';

customElements.define('top-bar', TopBar);
customElements.define('player-info', PlayerInfo);
customElements.define('sector-grid', SectorGrid);
customElements.define('overworld-map', OverworldMap);

document.addEventListener('DOMContentLoaded', () => {
    const scoreboardUi = document.getElementById('scoreboard-ui');
    const logoutBtn = document.getElementById('logout-btn');
    const worldBtn = document.getElementById('world-btn');

    const authTitle = document.getElementById('auth-title');
    const errorMsg = document.getElementById('error-msg');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const submitAuthBtn = document.getElementById('submit-auth-btn');
    const toggleAuthBtn = document.getElementById('toggle-auth-btn');

    let isLoginMode = true;

    function initGameSession() {
        const playerId = localStorage.getItem('player_id');
        if (!playerId) {
            return;
        }

        document.getElementById('auth-view').classList.add('hidden');
        document.getElementById('game-view').classList.remove('hidden');

        const topBarUi = document.getElementById("top-bar-ui");
        const playerInfoUi = document.getElementById("player-info-ui");
        const overworldUi = document.getElementById("overworld-ui");
        const mapUi = document.getElementById('map-ui');

        // Button Listener
        document.getElementById('gather-wood-btn').addEventListener('click', () => gatherManualAction('wood'));
        document.getElementById('gather-stone-btn').addEventListener('click', () => gatherManualAction('stone'));
        document.getElementById('world-btn').addEventListener('click', () => {
            overworldUi.classList.remove('hidden');
            mapUi.classList.add('hidden');
        });

        document.getElementById("toggle-dev-btn").addEventListener("click", () => {
            const devToolsPanel = document.getElementById("dev-tools-panel");
            devToolsPanel.classList.toggle("hidden");
        })

        // Event Listener für Custom Events aus Komponenten
        overworldUi.addEventListener('view-city', () => {
            overworldUi.classList.add('hidden');
            mapUi.classList.remove('hidden');
        });

        mapUi.addEventListener('assign-workers', (e) => {
            assignWorkersAction(e.detail.building_id, e.detail.amount);
        });

        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('player_id');
            disconnectWebSocket();
            location.reload();
        });

        // Listener für DevTools


        document.getElementById('dev-cheat-btn').addEventListener('click', () => {
            devCheatResources()
        });

        document.getElementById('dev-run-code-btn').addEventListener('click', () => {
            const code = document.getElementById('dev-code-input').value;
            devRunCode(code);
        });

        connectWebSocket(
            playerId,
            (resourceData) => {
                topBarUi.updateResources(resourceData);
                playerInfoUi.updateInfo(resourceData);
            },
            (scoreboardData) => { /* Scoreboard Logic */
            },
            (mapData) => {
                mapUi.renderMap(mapData);
                // Wenn wir Sektoren haben, aber die Overworld noch offen ist (beim Start),
                // umschalten, falls wir gerade erst geclaimt haben?
                // Für den Moment lassen wir die manuelle Umschaltung via "Stadt betreten"
            },
            (overworldData) => {
                overworldUi.renderOverworld(overworldData, playerId, claimHexAction);
            },
            () => {
                // Bei Verbindungsfehler/ungültiger ID (z.B. nach DB-Reset) ausloggen
                localStorage.removeItem('player_id');
                location.reload();
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
