let ws = null;

export function connectWebSocket(playerId, onResourceUpdate, onScoreboardUpdate, onMapUpdate, onOverworldUpdate, onConnectionError) {
    /* Baut die WebSocket-Verbindung auf und registriert die Callback-Funktionen für eingehende Nachrichten. */
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws?player_id=${playerId}`);

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);

        if (response.type === 'resource_update') {
            onResourceUpdate(response.data);

            const exportList = document.getElementById('export-resource-list');
            if (exportList) {
                const resources = [
                    "wood", "stone", "coal", "iron_ore", "iron", "steel",
                    "seed", "fruit", "vegetable", "livestock", "meat", "grain", "bread",
                    "wool", "cotton", "fabric", "clothes"
                ];

                const exportSettings = response.data.export_settings || {};

                // 1. Wenn die Liste komplett leer ist, bauen wir das Grundgerüst EINMALIG auf
                if (exportList.children.length === 0) {
                    resources.forEach(res => {
                        const currentAmount = response.data[res] || 0;
                        const isChecked = exportSettings[res] ? 'checked' : '';

                        const row = document.createElement('div');
                        row.id = `export-row-${res}`;
                        row.style.display = 'flex';
                        row.style.justifyContent = 'space-between';
                        row.style.alignItems = 'center';
                        row.style.marginBottom = '6px';
                        row.style.paddingBottom = '4px';
                        row.style.borderBottom = '1px solid #34495e';

                        row.innerHTML = `
                            <span style="font-family: monospace;">${res}: <strong class="res-amount">${currentAmount}</strong></span>
                            <label style="cursor: pointer; font-size: 11px;">
                                <input type="checkbox" class="export-toggle" data-res="${res}" ${isChecked}> Export
                            </label>
                        `;
                        exportList.appendChild(row);
                    });

                    // Event-Listener NUR EINMALIG binden
                    exportList.querySelectorAll('.export-toggle').forEach(checkbox => {
                        checkbox.addEventListener('change', (e) => {
                            const res = e.target.getAttribute('data-res');
                            const enabled = e.target.checked;

                            ws.send(JSON.stringify({
                                action: 'toggle_export',
                                resource: res,
                                enabled: enabled
                            }));
                        });
                    });
                } else {
                    // 2. Die Liste existiert bereits: Wir aktualisieren NUR die Zahlenwerte und die Checkboxen
                    resources.forEach(res => {

                        const row = document.getElementById(`export-row-${res}`);
                        if (row) {
                            // Textwert updaten
                            const amountEl = row.querySelector('.res-amount');
                            if (amountEl) {
                                amountEl.textContent = response.data[res] || 0;
                                if (amountEl <= 0) row.style.display = "none"
                                else row.style.display = "flex"

                            }

                            // Checkbox nur anpassen, wenn der Benutzer gerade nicht interagiert
                            const checkbox = row.querySelector('.export-toggle');
                            if (checkbox && document.activeElement !== checkbox) {
                                checkbox.checked = !!exportSettings[res];
                            }
                        }
                    });
                }
            }
        } else if (response.type === 'scoreboard_update') {
            onScoreboardUpdate(response.data);
        } else if (response.type === 'map_update') {
            onMapUpdate(response.data);
        } else if (response.type === 'overworld_update') {
            onOverworldUpdate(response.data);
        } else if (response.type === 'error') {
            alert(response.message);
        } else if (response.type === 'market_update') {
            const marketList = document.getElementById('market-list');
            if (marketList) {
                marketList.innerHTML = ''; // Liste leeren

                // Iteriert durch die erhaltenen Marktpreise und baut das UI auf
                for (const [resource, data] of Object.entries(response.data)) {
                    const itemDiv = document.createElement('div');
                    itemDiv.style.marginBottom = '5px';
                    itemDiv.style.display = 'flex';
                    itemDiv.style.justifyContent = 'space-between';

                    itemDiv.innerHTML = `
                        <span>${resource}: ${data.price} Gold (Bestand: ${data.stock})</span>
                        <button class="sell-btn" data-res="${resource}" style="background: #e74c3c; color: white; border: none; border-radius: 3px; cursor: pointer;">10 Verkaufen</button>
                    `;
                    marketList.appendChild(itemDiv);
                }

                // Klick-Listener an die neu generierten Verkaufs-Buttons binden
                document.querySelectorAll('.sell-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const res = e.target.getAttribute('data-res');
                        // Sendet den Verkaufsbefehl an das Backend
                        ws.send(JSON.stringify({
                            action: 'sell_to_npc',
                            resource: res,
                            amount: 10
                        }));
                    });
                });
            }
        } else if (response.type === 'dev_console_output') {
            const consoleLog = document.getElementById('dev-console-log');
            if (consoleLog) {
                consoleLog.textContent = response.data.message;
                consoleLog.scrollTop = consoleLog.scrollHeight; // Automatisch nach unten scrollen
            }
        }
    }

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

export function devCheatResources() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'dev_cheat_resources' }));
    }
}

export function devRunCode(code) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'dev_execute_code', code: code }));
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
        ws.send(JSON.stringify({action: 'claim_hex', q: q, r: r}));
    }
}

export function assignWorkersAction(buildingId, amount) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'assign_workers', building_id: buildingId, amount: amount }));
    }
}

// NEU: Funktion um Gebäude-Bau-Anfragen an den Server zu schicken
export function buildBuildingAction(regionId, buildingType, terrainType) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'build_building',
            region_id: regionId,
            building_type: buildingType,
            terrain_type: terrainType
        }));
    }
}
