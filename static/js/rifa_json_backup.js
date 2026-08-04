// ==========================================
// FUNCIONES DE RESPALDO JSON PARA RIFAS
// ==========================================
// Archivo independiente para exportar/importar JSON
// NO TOCA DATOS EXISTENTES - Solo lectura/escritura controlada
// ==========================================

// ==========================================
// EXPORTAR RIFA INDIVIDUAL A JSON
// ==========================================
async function exportRifaJSON() {
    try {
        const raffleId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
        const response = await fetch(`/api/rifas/${raffleId}/export-json`);
        if (!response.ok) throw new Error('Error al exportar');
        const data = await response.json();

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rifa_${data.raffle.name.replace(/\s+/g, '_')}_${data.raffle.raffle_number}_backup.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Error al exportar rifa a JSON');
    }
}

// ==========================================
// IMPORTAR RIFA INDIVIDUAL DESDE JSON
// ==========================================
function importRifaJSON() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.raffle || !data.selections) {
                alert('El archivo JSON no tiene el formato correcto para importar.');
                return;
            }

            const raffleId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
            const response = await fetch(`/api/rifas/${raffleId}/import-json`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Error al importar');
            const result = await response.json();
            if (result.success) {
                alert('Importación exitosa. La página se recargará para mostrar los cambios.');
                window.location.reload();
            } else {
                alert('Error: ' + (result.error || 'No se pudo importar los datos'));
            }
        } catch (error) {
            alert('Error al leer el archivo JSON. Verifica que el formato sea correcto.');
        }
    };
    input.click();
}

// ==========================================
// EXPORTAR TODAS LAS RIFAS A JSON
// ==========================================
async function exportAllRifasJSON() {
    try {
        const response = await fetch('/api/rifas/export-all-json');
        if (!response.ok) throw new Error('Error al exportar');
        const data = await response.json();

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rifas_completo_backup_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Error al exportar todas las rifas a JSON');
    }
}

// ==========================================
// IMPORTAR TODAS LAS RIFAS DESDE JSON
// ==========================================
function importAllRifasJSON() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.rifas) {
                alert('El archivo JSON no tiene el formato correcto para importar todas las rifas.');
                return;
            }

            const response = await fetch('/api/rifas/import-all-json', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Error al importar');
            const result = await response.json();
            if (result.success) {
                alert('Importación exitosa. La página se recargará.');
                window.location.reload();
            } else {
                alert('Error: ' + (result.error || 'No se pudo importar'));
            }
        } catch (error) {
            alert('Error al leer el archivo JSON. Verifica que el formato sea correcto.');
        }
    };
    input.click();
}
