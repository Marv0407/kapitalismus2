export class OverworldMap extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: "open"});
        this.shadowRoot.innerHTML = `
        <style>
                .panel { background: #222; padding: 15px; border-radius: 5px; border: 1px solid #333; margin-top: 20px;}
                h3 { margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 5px; color: #eb720f; }
                .svg-container { width: 100%; height: 800px; overflow: auto; background-color: #1a1a1a; border: 1px solid #333; position: relative; }
                svg { display: block; margin: auto; }
                polygon { stroke: #444; stroke-width: 1; cursor: pointer; transition: opacity 0.2s; }
                polygon:hover { opacity: 0.8; stroke: #fff; }
                .Wald { fill: #2e7d32; }
                .Ebene { fill: #8d6e63; }
                .Gebirge { fill: #546e7a; }
                .Küste { fill: #1e3a5f; }

                .details {
                    position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.8);
                    padding: 10px; border: 1px solid #eb720f; border-radius: 4px; min-width: 150px;
                    pointer-events: auto; z-index: 100;
                }
                .claim-btn {
                    background: #eb720f; color: white; border: none; padding: 5px 10px;
                    cursor: pointer; width: 100%; margin-top: 5px; border-radius: 3px; font-weight: bold;
                }
                .claim-btn:hover { background: #d6630a; }
            </style>
            <div class="panel">
                <h3>Weltkarte</h3>
                <div class="svg-container" id="container">
                    <div id="hex-details" class="details hidden"></div>
                    <svg id="hex-svg" width="800" height="800"></svg>
                </div>
            </div>
        `;

        this.svgElement = this.shadowRoot.getElementById('hex-svg');
        this.detailsElement = this.shadowRoot.getElementById('hex-details');
        this.hexSize = 25;
    }

    getHexPoints(cx, cy, size) {
        /* Generiet die sechs Eckpunkte eines hexagons */
        let points = [];
        for (let i = 0; i < 6; i++) {
           const angle_deg = 60 * i - 30;
           const angle_rad = Math.PI / 180 * angle_deg;
           points.push(`${cx + size * Math.cos(angle_rad)}, ${cy + size * Math.sin(angle_rad)}`)
        }
        return points.join(" ")
    }

    renderOverworld(hexData, currentPlayerId, onHexClick) {
        this.svgElement.innerHTML = "";

        const offsetX = 400;
        const offsetY = 400;

        hexData.forEach(hex => {
            const cx = offsetX + this.hexSize * Math.sqrt(3) * (hex.q + hex.r /2);
            const cy = offsetY + this.hexSize * 3 / 2 * hex.r;

            const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon")
            polygon.setAttribute("points", this.getHexPoints(cx, cy, this.hexSize));

            // Wenn besetzt, Farbe des Besitzers nutzen, sonst Terrain-Klasse
            if (hex.owner_id) {
                polygon.style.fill = hex.owner_color || "#eb720f";
                polygon.style.stroke = hex.owner_id === parseInt(currentPlayerId) ? "#2ecc71" : "#444";
                polygon.style.strokeWidth = hex.owner_id === parseInt(currentPlayerId) ? "3" : "1";
            } else {
                polygon.classList.add(hex.terrain);
            }

            polygon.addEventListener("click", () => {
                this.showDetails(hex, currentPlayerId, onHexClick);
            })

            this.svgElement.appendChild(polygon)
        })
    }

    showDetails(hex, currentPlayerId, onHexClick) {
        this.detailsElement.classList.remove('hidden');
        const isOwner = hex.owner_id === parseInt(currentPlayerId);
        const hasOwner = hex.owner_id !== null;

        this.detailsElement.innerHTML = `
            <div style="font-weight: bold; color: #eb720f; margin-bottom: 5px;">Sektor [${hex.q}, ${hex.r}]</div>
            <div style="font-size: 12px;">Terrain: ${hex.terrain}</div>
            <div style="font-size: 12px;">Besitzer: ${hex.owner_name || 'Niemand'}</div>
            ${!hasOwner ? `<button class="claim-btn" id="claim-btn">Stadt gründen</button>` : ''}
            ${isOwner ? `<button class="claim-btn" style="background: #2ecc71;" id="view-city-btn">Stadt betreten</button>` : ''}
            <button class="claim-btn" style="background: #444; margin-top: 10px;" id="close-details">Schließen</button>
        `;

        if (!hasOwner) {
            this.shadowRoot.getElementById('claim-btn').onclick = () => onHexClick(hex.q, hex.r);
        }
        if (isOwner) {
            this.shadowRoot.getElementById('view-city-btn').onclick = () => {
                // Event für main.js zum Umschalten der Ansicht
                this.dispatchEvent(new CustomEvent('view-city', { detail: { q: hex.q, r: hex.r } }));
            };
        }
        this.shadowRoot.getElementById('close-details').onclick = () => this.detailsElement.classList.add('hidden');
    }
}
