export class OverworldMap extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: "open"});
        this.shadowRoot.innerHTML = `
        <style>
                .panel { background: #222; padding: 15px; border-radius: 5px; border: 1px solid #333; margin-top: 20px;}
                h3 { margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 5px; color: #eb720f; }
                .svg-container { width: 100%; height: 500px; overflow: auto; background-color: #1a1a1a; border: 1px solid #333; }
                svg { display: block; margin: auto; }
                polygon { stroke: #444; stroke-width: 1; cursor: pointer; transition: opacity 0.2s; }
                polygon:hover { opacity: 0.8; stroke: #fff; }
                .Wald { fill: #2e7d32; }
                .Ebene { fill: #8d6e63; }
                .Gebirge { fill: #546e7a; }
                .Küste { fill: #1e3a5f; }
                .owned { stroke: #eb720f; stroke-width: 3; }
                .owned-by-me { stroke: #2ecc71; stroke-width: 3; }
            </style>
            <div class="panel">
                <h3>Weltkarte - Wähle einen Startsektor</h3>
                <div class="svg-container">
                    <svg id="hex-svg" width="800" height="800"></svg>
                </div>
            </div>
        `;

        this.svgElement = this.shadowRoot.getElementById('hex-svg');
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
            polygon.classList.add(hex.terrain);

            if (hex.owner_id === parseInt(currentPlayerId)) {
                polygon.classList.add("owned-by-me");
            } else if (hex.owner_id !== null) {
                polygon.classList.add("owned")
            }

            polygon.addEventListener("click", () => {
                if (hex.owner_id === null) {
                    onHexClick(hex.q, hex.r);
                }
            })

            this.svgElement.appendChild(polygon)
        })
    }
}
