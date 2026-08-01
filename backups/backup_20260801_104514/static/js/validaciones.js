// Archivo: js/validaciones.js

document.addEventListener("DOMContentLoaded", () => {
    // Forzar minúsculas en email
    document.querySelectorAll('.force-lowercase').forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toLowerCase();
        });
    });

    // Validar Nombres (1 espacio permitido, sin números/especiales, Title Case)
    document.querySelectorAll('.validate-name').forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]/g, ''); // Remueve inválidos
            let words = this.value.split(' ');
            if (words.length > 2) this.value = words.slice(0, 2).join(' '); // Max 1 espacio
            // Title case formatting on blur
        });
        input.addEventListener('blur', function() {
             this.value = this.value.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
        });
    });

    // Validar Apellidos (Sin espacios, sin números/especiales, Title Case)
    document.querySelectorAll('.validate-lastname').forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-ZáéíóúñÁÉÍÓÚÑ]/g, ''); // Sin espacios
        });
        input.addEventListener('blur', function() {
            this.value = this.value.charAt(0).toUpperCase() + this.value.slice(1).toLowerCase();
        });
    });
});

// Lógica de Select Dinámico en Registro
function handleDynamicSelect() {
    const select = document.getElementById('dynamicSelect').value;
    const container = document.getElementById('dynamicContainer');
    container.innerHTML = ''; // Limpiar previo

    if (select === 'Telefono' || select === 'Whatsapp') {
        container.innerHTML = `<input type="text" class="form-control mt-2" placeholder="Solo números" oninput="this.value = this.value.replace(/[^0-9]/g, '')">`;
    } 
    else if (select === 'Facebook' || select === 'Instagram' || select === 'Direccion') {
        container.innerHTML = `
            <input type="text" class="form-control mt-2 mb-2" placeholder="Descripción">
            <input type="url" class="form-control" placeholder="URL o Link">`;
    }
    else if (select === 'Fecha') {
        container.innerHTML = `
            <input type="text" class="form-control mt-2 mb-2" placeholder="Descripción de la fecha">
            <div class="d-flex gap-2">
                <input type="number" class="form-control" placeholder="Día" min="1" max="31">
                <input type="number" class="form-control" placeholder="Mes" min="1" max="12">
                <input type="number" class="form-control" placeholder="Año" min="1900">
            </div>`;
    }
    else if (select === 'Institucion') {
        container.innerHTML = `
            <input type="text" class="form-control mt-2 mb-2" placeholder="Nombre de la Institución">
            <input type="text" class="form-control mb-2" placeholder="Teléfono Institución" oninput="this.value = this.value.replace(/[^0-9]/g, '')">
            <input type="text" class="form-control mb-2" placeholder="Nombre del Contacto">
            <input type="text" class="form-control" placeholder="Teléfono Contacto" oninput="this.value = this.value.replace(/[^0-9]/g, '')">`;
    }
    else if (select === 'Otro') {
        container.innerHTML = `<input type="text" class="form-control mt-2" placeholder="Descripción" style="text-transform: capitalize;">`;
    }
}

// Exportar a Whatsapp (Omite vacíos y null)
function exportToWhatsapp(dataObj, phoneStr) {
    let mensaje = "Información del Usuario:\n";
    for (const [key, value] of Object.entries(dataObj)) {
        if (value && value !== "null" && value !== "None" && value.trim() !== "") {
            mensaje += `${key}: ${value}\n`;
        }
    }
    const url = `https://api.whatsapp.com/send?phone=${phoneStr}&text=${encodeURIComponent(mensaje)}`;
    window.open(url, '_blank');
}

// Confirmación de Borrado de 3 Pasos
let deleteStep = 0;
function confirmThreeStepDelete(itemId, btnElement) {
    if (deleteStep === 0) {
        btnElement.innerText = "¿Está seguro?";
        btnElement.classList.replace('btn-danger', 'btn-warning');
        deleteStep++;
    } else if (deleteStep === 1) {
        btnElement.innerText = "¿Completamente seguro?";
        btnElement.classList.replace('btn-warning', 'btn-danger');
        deleteStep++;
    } else {
        // Ejecutar borrado real
        alert("Eliminando elemento ID: " + itemId);
        deleteStep = 0;
    }
}