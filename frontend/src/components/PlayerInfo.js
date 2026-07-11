export class PlayerInfo extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                .info-panel { font-size: 15px; }
                .val { font-weight: bold; }
                .gold { color: #ffd700; font-size: 18px; margin-top: 15px; display: block;}
                .stats { color: #888; font-size: 12px; margin-top: 5px; }
            </style>
            <div class="info-panel">
                <div style="color: #eb720f; font-weight: bold; font-size: 18px; border-bottom: 1px solid #444; padding-bottom: 10px; margin-bottom: 10px;">Stadtverwaltung</div>
                <div>Status: <span class="val" style="color: #2ecc71;">Online</span></div>
                <div class="gold">Kasse: <span id="gold-val">0</span> G</div>
                <div class="stats">Umsatz total: <span id="sales-val">0</span> G</div>
            </div>
        `;
    }

    updateInfo(data) {
        this.shadowRoot.getElementById('gold-val').textContent = data.gold;
        this.shadowRoot.getElementById('sales-val').textContent = data.total_sales;
    }
}
