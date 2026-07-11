export class TopBar extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                .resource-container { display: flex; flex-wrap: wrap; gap: 15px; font-size: 13px; width: 100%; justify-content: flex-start; align-items: center; }
                .group { display: flex; gap: 10px; padding-right: 15px; border-right: 1px solid #444; }
                .group:last-child { border-right: none; }
                .res { display: flex; align-items: center; gap: 4px; color: #ccc; }
                .storage { color: #e74c3c; font-size: 14px; margin-left: auto; font-weight: bold; border-left: 1px solid #444; padding-left: 15px; }

                .mat-bau { color: #deb887; }
                .mat-erz { color: #e67e22; }
                .mat-food { color: #2ecc71; }
                .mat-goods { color: #9b59b6; }
            </style>
            <div class="resource-container">
                <!-- Rohstoffe & Bau -->
                <div class="group">
                    <div class="res mat-bau">Holz: <span id="wood-val">0</span></div>
                    <div class="res mat-bau">Stein: <span id="stone-val">0</span></div>
                    <div class="res mat-erz">Kohle: <span id="coal-val">0</span></div>
                    <div class="res mat-erz">Eisenerz: <span id="iron_ore-val">0</span></div>
                    <div class="res mat-erz">Eisen: <span id="iron-val">0</span></div>
                    <div class="res mat-erz">Stahl: <span id="steel-val">0</span></div>
                </div>

                <!-- Agrar & Nahrung -->
                <div class="group">
                    <div class="res mat-food">Saat: <span id="seed-val">0</span></div>
                    <div class="res mat-food">Frucht: <span id="fruit-val">0</span></div>
                    <div class="res mat-food">Gemüse: <span id="vegetable-val">0</span></div>
                    <div class="res mat-food">Vieh: <span id="livestock-val">0</span></div>
                    <div class="res mat-food">Fleisch: <span id="meat-val">0</span></div>
                    <div class="res mat-food">Getreide: <span id="grain-val">0</span></div>
                    <div class="res mat-food">Brot: <span id="bread-val">0</span></div>
                </div>

                <!-- Textilien -->
                <div class="group">
                    <div class="res mat-goods">Wolle: <span id="wool-val">0</span></div>
                    <div class="res mat-goods">Baumwolle: <span id="cotton-val">0</span></div>
                    <div class="res mat-goods">Stoff: <span id="fabric-val">0</span></div>
                    <div class="res mat-goods">Kleidung: <span id="clothes-val">0</span></div>
                </div>

                <div class="res storage">Lager: <span id="storage-val">0 / 100</span></div>
            </div>
        `;
    }

    updateResources(data) {
        /* Iteriert über alle bekannten Ressourcen-Keys, aktualisiert das DOM und summiert das Gesamtgewicht für das Lagerlimit. */
        const resources = [
            'wood', 'stone', 'coal', 'iron_ore', 'iron', 'steel',
            'seed', 'fruit', 'vegetable', 'livestock', 'meat', 'grain', 'bread',
            'wool', 'cotton', 'fabric', 'clothes'
        ];

        let totalResources = 0;

        resources.forEach(res => {
            const el = this.shadowRoot.getElementById(`${res}-val`);
            if (el && data[res] !== undefined) {
                el.textContent = data[res];
                totalResources += data[res];
            }
        });

        const storageEl = this.shadowRoot.getElementById('storage-val');
        storageEl.textContent = `${totalResources} / ${data.max_storage}`;
        storageEl.style.color = totalResources >= data.max_storage ? '#e74c3c' : '#2ecc71';
    }
}
