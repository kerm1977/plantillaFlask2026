// ==========================================
// RENDERIZADO DE CALENDARIO
// ==========================================

function renderizarCalendario() {
    const filtroEl = document.getElementById('calFiltroCategoria');
    const subTituloEl = document.getElementById('cal-flyer-subtitulo');
    const grid = document.getElementById('cal-grid-meses');
    const tPrecio = document.getElementById('calTogglePrecio');
    
    if(!filtroEl || !subTituloEl || !grid) return;
    
    const categoriaSeleccionada = filtroEl.value;
    const mostrarPrecios = tPrecio ? tPrecio.checked : true;
    
    subTituloEl.innerText = categoriaSeleccionada === 'Todas' ? 'Todas las Actividades' : `Especial: ${categoriaSeleccionada}`;

    const filtrados = eventosDBCalendario.filter(ev => categoriaSeleccionada === 'Todas' || ev.categoria === categoriaSeleccionada);

    const agrupados = {};
    filtrados.forEach(ev => {
        if (!agrupados[ev.mes]) agrupados[ev.mes] = [];
        agrupados[ev.mes].push(ev);
    });

    grid.innerHTML = '';

    for (const [mes, eventos] of Object.entries(agrupados)) {
        let eventosHTML = eventos.map(ev => {
            let precioHtml = mostrarPrecios ? ` <span style="margin-left: 0.5em;"><i class="bi bi-tag-fill text-orange"></i> ${ev.precio}</span>` : '';
            
            return `
            <div class="evento-item d-flex justify-content-between align-items-center mb-2" style="background: rgba(255, 255, 255, 0.05); border-left: 0.3em solid #ff8c00; padding: 0.6em 0.8em; border-radius: 0 0.5em 0.5em 0;">
                <div class="pe-2">
                    <h4 class="fw-bold mb-0 text-white" style="font-size: 1.1em;">${ev.nombre}</h4>
                    <small class="text-white-50" style="font-size: 0.85em;">
                        <i class="bi bi-geo-alt-fill text-orange"></i> Dif: ${ev.dificultad} 
                        ${precioHtml}
                    </small>
                </div>
                <div class="bg-darker text-orange fw-bold rounded border border-secondary" style="font-size: 1.2em; padding: 0.3em 0.6em; white-space: nowrap;">
                    ${ev.dia}
                </div>
            </div>
            `;
        }).join('');

        grid.innerHTML += `
            <div style="background: rgba(30, 30, 30, 0.7); border: 1px solid rgba(255, 140, 0, 0.3); border-radius: 1em; padding: 1.2em; display: flex; flex-direction: column; height: 100%;">
                <h2 style="color: #ff8c00; border-bottom: 0.15em solid #ff8c00; padding-bottom: 0.3em; margin-bottom: 0.8em; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; font-size: 1.5em;">${mes}</h2>
                <div class="eventos-lista">
                    ${eventosHTML}
                </div>
            </div>
        `;
    }
    
    actualizarTamanoTarjetas();
}
