// Archivo: js/eye.js
// Función exclusiva para mostrar/ocultar contraseñas.

function toggleEye(inputId, iconElement) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        iconElement.innerHTML = "👁️‍🗨️"; // Cambia el icono para indicar visible (Reemplazar por SVG local si se desea)
        iconElement.style.color = "var(--primary-orange)";
    } else {
        input.type = "password";
        iconElement.innerHTML = "👁️"; 
        iconElement.style.color = "#aaa";
    }