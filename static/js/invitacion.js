// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// invitacion.js - Invitación personalizada 9:16 por WhatsApp.
// Vista previa DOM + html2canvas (misma técnica del editor de flyers):
// los controles mueven CSS en vivo, sin recargar imágenes del servidor.
const Invitacion = (function () {
    let personas = [];
    let eventos = [];
    const FAV_KEY = 'inv_favs_v1';
    const PARAM_KEY = 'inv_params_v1';
    // Sliders -> ids; los de fuente tienen su tamaño base en em.
    const PARAM_IDS = { fglobal: 'invFglobal', pos: 'invPos', band: 'invBand', soft: 'invSoft',
                        blur: 'invBlur', fnombre: 'invFnombre', finfo: 'invFinfo', fboton: 'invFboton' };
    let _msgAuto = '';   // último mensaje generado (si el usuario no editó, se regenera)

    function $(id) { return document.getElementById(id); }
    function norm(s) {
        return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }
    function params() {
        const p = {};
        for (const k in PARAM_IDS) p[k] = parseInt($(PARAM_IDS[k]).dataset.value, 10) || 0;
        return p;
    }
    function eventoSel() {
        const v = $('invEvento').value;
        return eventos.find(function (e) { return String(e.id) === v; }) || null;
    }
    function personaSel() {
        const v = $('invCedula').value;
        return personas.find(function (x) { return x.cedula === v; }) || null;
    }

    // ── Diseño en vivo (CSS, sin parpadeo) ─────────────────────
    function renderDiseno() {
        const p = params();
        $('invPosVal').textContent = p.pos + '%';
        $('invBandVal').textContent = p.band + '%';
        $('invSoftVal').textContent = p.soft + '%';
        $('invBlurVal').textContent = p.blur + '%';
        $('invFglobalVal').textContent = p.fglobal + '%';
        $('invFnombreVal').textContent = p.fnombre + '%';
        $('invFinfoVal').textContent = p.finfo + '%';
        $('invFbotonVal').textContent = p.fboton + '%';

        $('invBlock').style.top = p.pos + '%';
        $('invBlock').style.fontSize = (10 * p.fglobal / 100) + 'px';
        const band = $('invBandDiv');
        band.style.top = p.band + '%';
        const soft = Math.max(2, Math.min(100, p.soft));
        band.style.background = 'linear-gradient(to bottom, rgba(230,110,0,0) 0%, rgba(230,110,0,0.96) ' +
            soft + '%, rgba(230,110,0,0.97) 100%)';
        const blurPx = p.blur / 100 * 12;
        const img = $('invBgImg');
        img.style.filter = blurPx ? 'blur(' + blurPx + 'px)' : 'none';
        img.style.transform = blurPx ? 'scale(' + (1 + blurPx * 0.02) + ')' : 'none';
        $('invTxtNombre').style.fontSize = (2.9 * p.fnombre / 100) + 'em';
        $('invTxtEvento').style.fontSize = (2.2 * p.finfo / 100) + 'em';
        $('invTxtDetalle').style.fontSize = (1.5 * p.finfo / 100) + 'em';
        $('invTxtPuntos').style.fontSize = (1.8 * p.fboton / 100) + 'em';
    }
    function ajuste() {
        renderDiseno();
        localStorage.setItem(PARAM_KEY, JSON.stringify(params()));
        precapturarDebounced();
    }
    // Pre-render del PNG en segundo plano: al tocar WhatsApp la imagen ya
    // está lista y navigator.share sale dentro de la activación del toque
    // (si se captura al hacer click, la espera larga invalida el share y
    // el navegador cae a descargar el archivo).
    let _preTimer = null, _blobPendiente = null;
    function precapturarDebounced() {
        clearTimeout(_preTimer);
        _preTimer = setTimeout(precapturar, 600);
    }
    function precapturar() {
        if (!eventoSel() || !personaSel()) { _blobPendiente = null; return; }
        _blobPendiente = capturar().then(canvasBlob).catch(function () { return null; });
    }
    function blobInvitacion() {
        if (!_blobPendiente) precapturar();
        return _blobPendiente;
    }
    function cargarParams() {
        let saved = {};
        try { saved = JSON.parse(localStorage.getItem(PARAM_KEY)) || {}; } catch (e) {}
        for (const k in PARAM_IDS) {
            const el = $(PARAM_IDS[k]);
            sliderSet(el, saved[k] !== undefined ? saved[k] : parseInt(el.dataset.value, 10));
        }
    }

    // Escala el canvas 540x960 al espacio del modal (patrón flyer_setup)
    function scalePreview() {
        const wrap = $('invPreviewWrap'), area = $('invCanvas');
        if (!wrap || !area) return;
        const s = Math.min((wrap.clientWidth - 10) / 540, (wrap.clientHeight - 10) / 960);
        area.style.transform = 'scale(' + s + ')';
    }

    // ── Datos en la invitación ─────────────────────────────────
    function linkEvento(ev) {
        // ██ BLINDADO — NO CAMBIAR NUNCA ██
        // Enlace del código QR de cada caminata: es el MISMO que genera la
        // ventana "Compartir código QR" (url_for main.puntos_scan _external).
        // Dominio público fijo: aunque se genere desde localhost el invitado
        // recibe el link real. Orden del dueño: este enlace NO se toca.
        return 'https://www.latribu.top/puntos-scan/' + ev.id;
    }
    function mensajeAuto(ev, p) {
        return '¡' + (p ? p.nombre_completo : 'Hola') + ', estás invitado(a) a "' +
            (ev ? ev.nombre : 'nuestra actividad') + '"' +
            (ev && ev.fecha ? ' el ' + ev.fecha : '') +
            (ev && ev.puntos ? '. ¡Ganás ' + ev.puntos + ' puntos por participar!' : '.') +
            (ev ? '\n\nSi participás de esta caminata, abrí este enlace y presentá el código QR a los coordinadores de La Tribu para ganar tus puntos:\n' + linkEvento(ev) : '') +
            '\n\nTe adjuntamos tu invitación personalizada. — latribu.top';
    }
    function actualizar() {
        const ev = eventoSel(), p = personaSel();
        $('invBgImg').src = (ev && ev.flyer) ? ev.flyer : '/static/default.png';
        $('invTxtNombre').textContent = p ? p.nombre_completo : 'Nombre de la persona';
        $('invTxtEvento').textContent = ev ? ev.nombre : '';
        $('invTxtDetalle').textContent = ev ? [ev.fecha, ev.lugar].filter(Boolean).join(' · ') : '';
        const pill = $('invTxtPuntos');
        if (ev && ev.puntos) { pill.textContent = 'Ganá ' + ev.puntos + ' puntos al participar'; pill.parentElement.style.display = ''; }
        else { pill.parentElement.style.display = 'none'; }
        $('invResumen').textContent = ev ? (ev.nombre + (ev.puntos ? ' · +' + ev.puntos + ' puntos' : '')) : '';
        // Mensaje: solo se regenera si el usuario no lo personalizó
        const msg = $('invMsg');
        const nuevo = (ev && p) ? mensajeAuto(ev, p) : '';
        if (!msg.value || msg.value === _msgAuto) { msg.value = nuevo; }
        _msgAuto = nuevo;
        renderDiseno();
        precapturarDebounced();
    }

    // ── Persona (buscador en vivo) ─────────────────────────────
    function pintarLista() {
        const lista = $('invLista');
        const t = norm($('invBuscar').value);
        const res = personas.filter(function (p) {
            return !t || norm(p.nombre_completo + ' ' + p.cedula + ' ' + (p.telefono || '')).indexOf(t) !== -1;
        }).slice(0, 25);
        lista.innerHTML = res.map(function (p) {
            return '<button type="button" class="list-group-item list-group-item-action py-1 px-3 small" ' +
                'onclick="Invitacion.elegir(\'' + p.cedula + '\')">' +
                (p.nombre_completo || '') + ' <span class="text-muted">(' + p.cedula + ')</span></button>';
        }).join('');
    }
    // Sliders propios: la barra no tiene handlers (tocarla no hace nada y el
    // scroll pasa por encima); SOLO el thumb responde, con arrastre manual.
    function sliderSet(el, val) {
        const min = +el.dataset.min, max = +el.dataset.max;
        val = Math.round(Math.min(Math.max(val, min), max));
        el.dataset.value = val;
        const frac = (val - min) / (max - min);
        el.querySelector('.inv-slider-thumb').style.left = (frac * 100) + '%';
        el.querySelector('.inv-slider-fill').style.width = (frac * 100) + '%';
        const lab = $(el.id + 'Val');
        if (lab) lab.textContent = val + '%';
    }
    function bindSliders() {
        document.querySelectorAll('#invAjustes .inv-slider').forEach(function (el) {
            const thumb = el.querySelector('.inv-slider-thumb');
            thumb.addEventListener('pointerdown', function (e) {
                e.preventDefault();
                try { thumb.setPointerCapture(e.pointerId); } catch (err) {}
                el._drag = true;
            });
            thumb.addEventListener('pointermove', function (e) {
                if (!el._drag) return;
                const r = el.getBoundingClientRect();
                const frac = Math.min(Math.max((e.clientX - r.left) / r.width, 0), 1);
                sliderSet(el, +el.dataset.min + frac * (+el.dataset.max - +el.dataset.min));
                ajuste();
            });
            ['pointerup', 'pointercancel'].forEach(function (ev) {
                thumb.addEventListener(ev, function () { el._drag = false; });
            });
            sliderSet(el, parseInt(el.dataset.value, 10));
        });
    }

    function colapsar(id, expandir) {
        const el = document.getElementById(id);
        if (el && window.bootstrap) bootstrap.Collapse.getOrCreateInstance(el)[expandir ? 'show' : 'hide']();
    }

    function elegir(cedula) {
        const p = personas.find(function (x) { return x.cedula === cedula; });
        $('invCedula').value = cedula;
        $('invBuscar').value = p ? (p.nombre_completo + ' (' + p.cedula + ')') : cedula;
        $('invLista').innerHTML = '';
        colapsar('invAccPersona', false);   // se colapsa solo al elegir
        actualizar();
    }

    // ── Invitaciones recientes (localStorage) ──────────────────
    function favs() {
        try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; }
        catch (e) { return []; }
    }
    function pintarFavs() {
        const c = $('invFavs');
        const f = favs();
        c.innerHTML = f.length ? f.map(function (x) {
            return '<span class="btn-group btn-group-sm">' +
                '<button type="button" class="btn btn-outline-success rounded-start-pill" ' +
                'onclick="Invitacion.usarFav(\'' + x.id + '\')" title="Usar esta invitación">' +
                '<i class="bi bi-envelope-paper me-1"></i>' + x.nombre + '</button>' +
                '<button type="button" class="btn btn-outline-danger rounded-end-pill px-2" ' +
                'onclick="Invitacion.borrarFav(\'' + x.id + '\')" title="Quitar">&times;</button></span>';
        }).join('') : '<span class="text-muted small">Las invitaciones que envíes o descargues quedan aquí para reutilizarlas.</span>';
    }
    function usarFav(id) {
        $('invEvento').value = id;
        $('invCedula').value = '';
        $('invBuscar').value = '';
        actualizar();
        colapsar('invAccPersona', true);    // expande personas para elegir la nueva
        $('invBuscar').focus();
    }
    function borrarFav(id) {
        localStorage.setItem(FAV_KEY, JSON.stringify(favs().filter(function (x) { return String(x.id) !== String(id); })));
        pintarFavs();
    }
    function usada() {
        const ev = eventoSel();
        if (!ev) return;
        const f = favs().filter(function (x) { return String(x.id) !== String(ev.id); });
        f.unshift({ id: ev.id, nombre: ev.nombre, puntos: ev.puntos, fecha: ev.fecha });
        localStorage.setItem(FAV_KEY, JSON.stringify(f.slice(0, 10)));
        pintarFavs();
    }

    // ── Abrir modal ────────────────────────────────────────────
    async function abrir() {
        const modal = new bootstrap.Modal($('invitacionModal'));
        modal.show();
        if (!eventos.length) {
            try {
                const [r1, r2] = await Promise.all([
                    fetch('/api/invitacion/eventos').then(function (r) { return r.json(); }),
                    fetch('/api/admin/hikers').then(function (r) { return r.json(); })
                ]);
                eventos = r1.eventos || [];
                personas = r2.hikers || r2 || [];
            } catch (e) { /* sin datos */ }
            const sel = $('invEvento');
            sel.innerHTML = '<option value="">Elegí el evento...</option>' +
                eventos.map(function (e) {
                    return '<option value="' + e.id + '">' + e.nombre +
                        (e.puntos ? ' (+' + e.puntos + ' pts)' : '') + '</option>';
                }).join('');
        }
        // Preselección: la persona del expediente abierto (si viene del dashboard)
        const ced = (window.currentSelectedUserObj && currentSelectedUserObj.crm_cedula) || '';
        if (ced) elegir(ced);
        cargarParams();
        pintarLista();
        pintarFavs();
        actualizar();
        setTimeout(scalePreview, 60);
        if (!window._invResizeBound) {
            window.addEventListener('resize', scalePreview);
            $('invitacionModal').addEventListener('shown.bs.modal', scalePreview);
            bindSliders();
            window._invResizeBound = true;
        }
    }

    // ── Captura html2canvas a 1080x1920 ────────────────────────
    // html2canvas NO soporta filter:blur() — el blur se rasteriza antes
    // en un canvas offscreen y se restaura después de la captura.
    function _pintarBlur(fuente, cv, blurPx) {
        const cx = cv.getContext('2d');
        const s = Math.max(cv.width / fuente.width, cv.height / fuente.height);
        const w = fuente.width * s * (1 + blurPx * 0.02), h = fuente.height * s * (1 + blurPx * 0.02);
        const dx = (cv.width - w) / 2, dy = (cv.height - h) / 2;
        if (typeof cx.filter === 'string') {
            cx.filter = 'blur(' + blurPx + 'px)';
            cx.drawImage(fuente, dx, dy, w, h);
        } else {
            // Fallback universal (sin ctx.filter): bajar la resolución y
            // subirla con suavizado produce un blur real en cualquier browser.
            const f = Math.max(2, Math.round(blurPx * 0.7));
            const tmp = document.createElement('canvas');
            tmp.width = Math.max(4, Math.round(cv.width / f));
            tmp.height = Math.max(4, Math.round(cv.height / f));
            const tc = tmp.getContext('2d');
            const s2 = Math.max(tmp.width / fuente.width, tmp.height / fuente.height);
            const w2 = fuente.width * s2 * (1 + blurPx * 0.02), h2 = fuente.height * s2 * (1 + blurPx * 0.02);
            tc.drawImage(fuente, (tmp.width - w2) / 2, (tmp.height - h2) / 2, w2, h2);
            cx.imageSmoothingEnabled = true;
            try { cx.imageSmoothingQuality = 'high'; } catch (e) {}
            cx.drawImage(tmp, 0, 0, cv.width, cv.height);
        }
        try { return cv.toDataURL('image/png'); } catch (e) { return null; }
    }
    function _rasterizarBlur() {
        const area = $('invCanvas'), img = $('invBgImg');
        const blurPx = params().blur / 100 * 12;
        if (blurPx <= 0 || !img.src) return Promise.resolve(null);
        const cv = document.createElement('canvas');
        cv.width = area.offsetWidth || 540; cv.height = area.offsetHeight || 960;
        // Si el <img> ya cargó el flyer se dibuja directo: sin recargar la
        // imagen, sin CORS y sin pasar por el service worker (que podía
        // romper la carga en silencio y exportar la foto nítida).
        if (img.complete && img.naturalWidth) return Promise.resolve(_pintarBlur(img, cv, blurPx));
        return new Promise(function (res) {
            const im = new Image();
            im.onload = function () { res(_pintarBlur(im, cv, blurPx)); };
            im.onerror = function () { res(null); };
            im.src = img.src;
        });
    }
    async function capturar() {
        const area = $('invCanvas'), img = $('invBgImg');
        const prevSrc = img.src, prevFilter = img.style.filter, prevTrans = img.style.transform;
        const blurred = await _rasterizarBlur();
        if (blurred) {
            img.src = blurred;
            img.style.filter = 'none';
            img.style.transform = 'none';
        }
        const t = area.style.transform;
        area.style.transform = 'none';   // capturar a tamaño real
        try {
            return await html2canvas(area, { scale: 2, useCORS: true, backgroundColor: '#121218' });
        } finally {
            area.style.transform = t;
            img.src = prevSrc;
            img.style.filter = prevFilter;
            img.style.transform = prevTrans;
        }
    }
    function canvasBlob(canvas) {
        return new Promise(function (res) { canvas.toBlob(res, 'image/png'); });
    }
    function listo() {
        if (!$('invEvento').value || !$('invCedula').value) {
            alert('Elegí evento y persona primero.');
            return false;
        }
        return true;
    }

    async function descargar() {
        if (!listo()) return;
        usada();
        const blob = await blobInvitacion();
        if (!blob) { alert('No se pudo generar la imagen de la invitación.'); return; }
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'invitacion.png';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
    }

    // Tras enviar: limpia la persona y reabre el acordeón de personas para
    // encadenar invitaciones seguidas sin salir del modal.
    function siguiente() {
        $('invCedula').value = '';
        $('invBuscar').value = '';
        pintarLista();
        actualizar();
        colapsar('invAccPersona', true);
        setTimeout(function () { $('invBuscar').focus(); }, 400);
    }

    async function whatsapp() {
        if (!listo()) return;
        usada();
        const p = personaSel();
        const tel = p && p.telefono ? '506' + String(p.telefono).replace(/\D/g, '') : '';
        const texto = $('invMsg').value || _msgAuto || '';
        const blob = await blobInvitacion();
        if (!blob) { alert('No se pudo generar la imagen de la invitación.'); return; }
        const file = new File([blob], 'invitacion.png', { type: 'image/png' });
        // 1) Share nativo con archivo: la única vía web para adjuntar la
        //    imagen a WhatsApp como cualquier otro archivo. Se intenta
        //    directo (canShare da falsos negativos en varios navegadores).
        if (navigator.share) {
            let conImagen = false;
            for (const data of [{ files: [file], text: texto, title: 'Invitación' },
                                { files: [file], text: texto },
                                { files: [file] }]) {
                try { await navigator.share(data); conImagen = true; break; }
                catch (e) { if (e && e.name === 'AbortError') return; }
            }
            if (conImagen) { siguiente(); return; }
            // El navegador no comparte archivos: al menos el mensaje+link
            // sale por el share nativo (texto plano).
            let soloTexto = false;
            try { await navigator.share({ text: texto }); soloTexto = true; }
            catch (e) { if (e && e.name === 'AbortError') return; }
            // El mensaje ya salió: dejar la imagen en portapapeles/descarga
            // para adjuntarla en el chat y NO abrir WhatsApp otra vez.
            if (soloTexto) {
                try { await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]); } catch (e) {}
                const b = document.createElement('a');
                b.href = URL.createObjectURL(blob);
                b.download = 'invitacion.png';
                document.body.appendChild(b); b.click(); b.remove();
                setTimeout(function () { URL.revokeObjectURL(b.href); }, 4000);
                alert('El mensaje salió. La imagen quedó en el portapapeles/descargas para adjuntarla en el chat.');
                siguiente();
                return;
            }
        }
        // 2) Sin share API (PC): imagen al portapapeles + descarga + wa.me.
        let pegable = false;
        try {
            await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
            pegable = true;
        } catch (e) { /* portapapeles no disponible */ }
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'invitacion.png';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
        const movil = /Android|iPhone|iPad/i.test(navigator.userAgent);
        if (movil) {
            // location.href dispara el deep-link a la app (window.open lo bloquean)
            window.location.href = 'whatsapp://send?phone=' + tel + '&text=' + encodeURIComponent(texto);
        } else {
            window.open('https://wa.me/' + tel + '?text=' + encodeURIComponent(texto), '_blank');
        }
        alert(pegable
            ? 'La invitación quedó en el portapapeles: pegala en el chat de WhatsApp (también se descargó como respaldo).'
            : 'Se descargó la imagen de la invitación: adjuntala en el chat de WhatsApp.');
        siguiente();
    }

    return { abrir: abrir, filtrar: pintarLista, elegir: elegir, actualizar: actualizar,
             whatsapp: whatsapp, descargar: descargar, usarFav: usarFav,
             borrarFav: borrarFav, usada: usada, ajuste: ajuste };
})();

function mostrarInvitacion() { Invitacion.abrir(); }
