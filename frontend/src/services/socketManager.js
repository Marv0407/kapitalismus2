let ws = null;

export function connectWebSocket(playerId, onResourceUpdate, onScoreboardUpdate) {
    /* Baut die WebSocket-Verbindung auf und registriert die Callback-Funktionen für eingehende Nachrichten. */
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws?player_id=${playerId}`);

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);

        if (response.type === 'resource_update') {
            onResourceUpdate(response.data.gold, response.data.wood);
        } else if (response.type === 'scoreboard_update') {
            onScoreboardUpdate(response.data);
        }
    };

    ws.onclose = () => {
        console.log('Verbindung verloren.');
    };
}

export function disconnectWebSocket() {
    /* Schließt die aktive WebSocket-Verbindung sicher. */
    if (ws) {
        ws.close();
        ws = null;
    }
}

export function sellWoodAction() {
    /* Sendet die Anforderung zum Holzverkauf an den Server. */
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'sell_wood' }));
    }
}
