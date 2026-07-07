export class SectorGrid extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: 'open'});
        this.shadowRoot.innerHTML = `
            <style>
                .panel { background: #222; padding: 15px; border-radius: 5px; border: 1px solid #333; margin-top: 20px;}
                h3 { margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 5px; color: #eb720f; }
                .grid-container {
                    display: grid;
                    grid-template-columns: repeat(5, 60px);
                    grid-template-rows: repeat(5, 60px);
                    gap: 4px;
                    width: max-content;
                }
                .tile {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    cursor: pointer;
                    color: #777;
                    border-radius: 3px;
                }
                .tile:hover {
                    background-color: #3a3a3a;
                }
                .tile.Küste { background-color: #1e3a5f; color: #fff; }
                .building { font-weight: bold; color: #deb887; text-transform: uppercase; }
            </style>
            <div class="panel">
                <h3>Sektoren</h3>
                <div class="grid-container" id="grid"></div>
            </div>
        `;

        this.gridElement = this.shadowRoot.getElementById("grid");
        this.gridSize = 2;
    }

    renderMap(mapData) {
        /* Zeichnet das Raster iterativ und verknüpft vorhandene Map-Daten mit den koordinaten */
        this.gridElement.innerHTML = ``;

        for (let y = -this.gridSize; y <= this.gridSize; y++) {
            for (let x = -this.gridSize; x <= this.gridSize; x++) {
                const tile = document.createElement("div");
                tile.className = "tile";
                tile.dataset.x = x;
                tile.dataset.y = y;

                const cellData = mapData.find(d => d.x === x && d.y === y);

                if(cellData) {
                    tile.classList.add(cellData.type)
                    if(cellData.buidling) {
                        tile.innerHTML += `<span class="building">${cellData.building.substring(0, 4)}</span>`
                    } else {
                        tile.textContent = cellData.type;
                    }
                } else {
                    tile.textContent = `${x}, ${y}`
                }

                this.gridElement.appendChild(tile)
            }
        }
    }
}

