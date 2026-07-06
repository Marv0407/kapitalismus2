export class ResourceDisplay extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                .panel { background: #2a2a2a; padding: 15px; border-radius: 5px; border: 1px solid #333; }
                .stat { font-size: 18px; margin: 5px 0; }
                .gold { color: #ffd700; }
                .wood { color: #deb887; }
            </style>
            <div class="panel">
                <div class="stat">Gold: <span class="gold" id="gold-val">0</span></div>
                <div class="stat">Holz: <span class="wood" id="wood-val">0</span></div>
            </div>
        `;
    }

    updateValues(gold, wood) {
        /* Aktualisiert die DOM-Elemente der Ressourcenanzeige mit neuen Werten. */
        this.shadowRoot.getElementById('gold-val').textContent = gold;
        this.shadowRoot.getElementById('wood-val').textContent = wood;
    }
}
