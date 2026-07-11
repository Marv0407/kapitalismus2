let ws = null;

export function connectWebSocket(playerId, onResourceUpdate, onScoreboardUpdate, onMapUpdate, onOverworldUpdate, onConnectionError) {
    /* Baut die WebSocket-Verbindung auf und registriert die Callback-Funktionen für eingehende Nachrichten. */
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws?player_id=${playerId}`);

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);

        if (response.type === 'resource_update') {
            onResourceUpdate(response.data);
        } else if (response.type === 'scoreboard_update') {
            onScoreboardUpdate(response.data);
        } else if (response.type === 'map_update') {
            onMapUpdate(response.data);
        } else if (response.type === 'overworld_update') {
            onOverworldUpdate(response.data);
        } else if (response.type === 'error') {
            alert(response.message);
        }
        else if (response.type === 'dev_console_output') {
            const consoleLog = document.getElementById('dev-console-log');
            if (consoleLog) {
                consoleLog.textContent = response.data.message;
                consoleLog.scrollTop = consoleLog.scrollHeight; // Automatisch nach unten scrollen
            }
        }
    };

    ws.onclose = (event) => {
        console.log('Verbindung verloren.', event.code);
        if (event.code === 1008 && onConnectionError) {
            onConnectionError();
        }
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

export function gatherManualAction(resourceType) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'gather_manual', resource: resourceType }));
    }
}


export function claimHexAction(q, r) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'claim_hex', q: q, r: r}))
    }
}

export function assignWorkersAction(buildingId, amount) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'assign_workers', building_id: buildingId, amount: amount }));
    }
}
