// ==========================================
// CARGA Y PROCESAMIENTO DE EVENTOS
// ==========================================

async function cargarEventosCalendario() {
    try {
        const response = await fetch('/api/get_events');
        const eventosRaw = await response.json();

        const meses_es = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

        eventosDBCalendario = eventosRaw.map(ev => {
            let fechaCorta = ev.fecha ? ev.fecha.split(' ')[0] : '';
            let mesTxt = "S/M";
            let diaTxt = "--";
            let ms = 0;
            
            if (fechaCorta && fechaCorta.includes('-')) {
                let partes = fechaCorta.split('-'); 
                let d = new Date(partes[0], partes[1] - 1, partes[2]);
                mesTxt = meses_es[d.getMonth()];
                diaTxt = d.getDate().toString();
                ms = d.getTime();
            }

            return {
                mes: mesTxt,
                dia: diaTxt,
                nombre: ev.nombreLugar,
                categoria: ev.actividad || 'Caminata',
                dificultad: ev.dificultad || 'Moderada',
                precio: ev.precio || 'PENDIENTE',
                _timestamp: ms
            };
        });

        eventosDBCalendario.sort((a, b) => a._timestamp - b._timestamp);
        renderizarCalendario();
    } catch(e) {
        console.error("Error al cargar caminatas:", e);
    }
}
