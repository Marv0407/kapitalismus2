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
                .tile.Wald { background-color: #2e7d32; color: #fff; }
                .tile.Ebene { background-color: #8d6e63; color: #fff; }
                .tile.Gebirge { background-color: #546e7a; color: #fff; }
                
                .building { font-weight: bold; color: #ffd700; text-transform: uppercase; font-size: 10px; }
                .workers-tag { font-size: 9px; color: #fff; background: rgba(0,0,0,0.5); padding: 1px 3px; border-radius: 2px; margin-top: 2px; }
                
                .details-panel { 
                    margin-top: 20px; padding: 15px; background: #2a2a2a; border: 1px solid #444; border-radius: 5px;
                }
                .btn-worker { 
                    background: #eb720f; border: none; color: white; padding: 5px 10px; 
                    cursor: pointer; font-weight: bold; border-radius: 3px; margin: 0 5px;
                }
                .btn-worker:hover { background: #d6630a; }
            </style>
            <div class="panel">
                <h3>Sektoren</h3>
                <div class="grid-container" id="grid"></div>
                
                <div id="sector-details" class="details-panel hidden">
                    <h4 id="det-title" style="margin-top:0; color: #eb720f;">Sektor Details</h4>
                    <div id="det-info"></div>
                    <div id="worker-mgmt" class="hidden" style="margin-top: 10px; border-top: 1px solid #444; padding-top: 10px;">
                        <span>Arbeiter: </span>
                        <button class="btn-worker" id="btn-minus">-</button>
                        <span id="worker-count" style="font-weight: bold; font-size: 16px;">0</span>
                        <button class="btn-worker" id="btn-plus">+</button>
                        <span style="color: #888; font-size: 12px; margin-left: 10px;">(Max: <span id="worker-max">0</span>)</span>
                    </div>
                </div>
            </div>
        `;

        this.gridElement = this.shadowRoot.getElementById("grid");
        this.detailsPanel = this.shadowRoot.getElementById("sector-details");
        this.gridSize = 2;
    }

    renderMap(mapData) {
        this.gridElement.innerHTML = ``;

        for (let y = -this.gridSize; y <= this.gridSize; y++) {
            for (let x = -this.gridSize; x <= this.gridSize; x++) {
                const tile = document.createElement("div");
                tile.className = "tile";
                
                const cellData = mapData.find(d => d.x === x && d.y === y);

                if(cellData) {
                    tile.classList.add(cellData.type)
                    if(cellData.building) {
                        tile.innerHTML = `
                            <div class="building">${cellData.building.substring(0, 6)}</div>
                            <div class="workers-tag">${cellData.building_data.workers || 0} / ${cellData.building_data.max_workers || 5}</div>
                        `;
                    } else {
                        tile.textContent = cellData.type;
                    }
                    
                    tile.onclick = () => this.showSectorDetails(cellData);
                } else {
                    tile.textContent = `${x}, ${y}`;
                }

                this.gridElement.appendChild(tile);
            }
        }
    }

    showSectorDetails(data) {
        this.detailsPanel.classList.remove('hidden');
        this.shadowRoot.getElementById('det-title').textContent = `${data.type}-Sektor [${data.x}, ${data.y}]`;
        
        const info = this.shadowRoot.getElementById('det-info');
        const workerMgmt = this.shadowRoot.getElementById('worker-mgmt');
        
        if (data.building) {
            info.innerHTML = `Gebäude: <strong>${data.building.toUpperCase()}</strong> (Level ${data.level})`;
            workerMgmt.classList.remove('hidden');
            
            const countEl = this.shadowRoot.getElementById('worker-count');
            const maxEl = this.shadowRoot.getElementById('worker-max');
            
            countEl.textContent = data.building_data.workers || 0;
            maxEl.textContent = data.building_data.max_workers || 5;
            
            this.shadowRoot.getElementById('btn-plus').onclick = () => {
                this.dispatchEvent(new CustomEvent('assign-workers', { 
                    detail: { building_id: data.building_id || data.id, amount: 1 } 
                }));
            };
            
            this.shadowRoot.getElementById('btn-minus').onclick = () => {
                this.dispatchEvent(new CustomEvent('assign-workers', { 
                    detail: { building_id: data.building_id || data.id, amount: -1 } 
                }));
            };
        } else {
            info.innerHTML = `Kein Gebäude errichtet.`;
            workerMgmt.classList.add('hidden');
        }
    }
}

