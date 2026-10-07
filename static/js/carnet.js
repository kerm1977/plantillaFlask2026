// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// carnet.js - "Enviar mi carnet por WhatsApp" en Mis puntos.
// wa.me no puede adjuntar imágenes: en celulares se usa la Web Share
// API para compartir el PNG directo; si no está soportada se descarga
// el PNG y se abre el WhatsApp del usuario registrado para adjuntarlo.
(function() {
    var btn = document.getElementById('btnCarnetWa');
    if (!btn) return;
    btn.addEventListener('click', function() {
        var url = btn.getAttribute('data-url');
        var wa = btn.getAttribute('data-wa');
        btn.disabled = true;
        fetch(url).then(function(r) { return r.blob(); }).then(function(blob) {
            var file = new File([blob], 'carnet.png', { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                navigator.share({
                    files: [file],
                    title: 'Mi carnet - La Tribu de los Libres',
                    text: 'Mi carnet de identificación de La Tribu de los Libres.'
                }).catch(function() {});
            } else {
                var a = document.createElement('a');
                a.href = url;
                a.download = 'carnet.png';
                document.body.appendChild(a);
                a.click();
                a.remove();
                if (wa) window.open(wa, '_blank');
            }
        }).catch(function() {
            if (wa) window.open(wa, '_blank');
        }).finally(function() { btn.disabled = false; });
    });
})();
