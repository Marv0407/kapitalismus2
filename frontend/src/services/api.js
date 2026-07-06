export async function registerUser(username, password) {
    /* Sendet eine POST-Anfrage an den Registrierungs-Endpunkt und gibt bei Erfolg die generierte player_id zurück. */
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.detail || 'Fehler bei der Registrierung.');
    }
    return result.player_id;
}

export async function loginUser(username, password) {
    /* Sendet eine POST-Anfrage an den Login-Endpunkt zur Authentifizierung und gibt bei Erfolg die verknüpfte player_id zurück. */
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.detail || 'Fehler beim Login.');
    }
    return result.player_id;
}
