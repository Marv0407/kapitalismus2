export class ScoreBoard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                .panel { background: #222; padding: 15px; border-radius: 5px; border: 1px solid #333; }
                h3 { margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 5px; color: #eb720f; }
                .player-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #2a2a2a; font-size: 14px; }
                .name-wrapper { display: flex; align-items: center; gap: 8px; }
                .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
                .online { background-color: #2ecc71; box-shadow: 0 0 6px #2ecc71; }
                .offline { background-color: #95a5a6; }
                .gold { color: #ffd700; font-weight: bold; }
            </style>
            <div class="panel">
                <h3>Rangliste</h3>
                <div id="rows-container"></div>
            </div>
        `;
    }

    renderData(players) {
        /* Baut die Ranglisten-Tabelle basierend auf dem übergebenen Array neu auf. */
        const container = this.shadowRoot.getElementById('rows-container');
        container.innerHTML = '';

        players.forEach(p => {
            const row = document.createElement('div');
            row.className = 'player-row';
            row.innerHTML = `
                <div class="name-wrapper">
                    <span class="status-dot ${p.online ? 'online' : 'offline'}"></span>
                    <span>${p.username}</span>
                </div>
                <div class="gold">${p.gold} G</div>
            `;
            container.appendChild(row);
        });
    }
}
