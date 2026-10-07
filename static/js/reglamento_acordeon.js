// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// reglamento_acordeon.js - Articulos del reglamento plegables al tocar su titulo
(function () {
  var cont = document.getElementById('reglamentoContenido');
  if (!cont) return;
  var flatHTML = cont.innerHTML;
  var RX_ART = /^art[ií]culo\s*\d+/i;
  var KEY_TODOS = 'rgTodosAbiertos';
  var todosAbiertos = false;
  var btnTodos = null;

  function esArticulo(el) {
    if (!el || el.tagName !== 'P') return false;
    var s = el.firstElementChild;
    if (!s || (s.tagName !== 'STRONG' && s.tagName !== 'B')) return false;
    return RX_ART.test((s.textContent || '').trim());
  }

  function cerrarTodos() {
    cont.querySelectorAll('.rg-art-cuerpo, .rg-art-titulo').forEach(function (e) {
      e.classList.add('rg-cerrado');
    });
  }

  function pintarBtnTodos() {
    if (!btnTodos) return;
    btnTodos.innerHTML = todosAbiertos
      ? '<i class="bi bi-eye-slash me-1"></i>Ocultar todo'
      : '<i class="bi bi-eye me-1"></i>Mostrar todo';
  }

  function guardarEstadoTodos() {
    try { sessionStorage.setItem(KEY_TODOS, todosAbiertos ? '1' : '0'); } catch (e) {}
  }

  function leerEstadoTodos() {
    try { return sessionStorage.getItem(KEY_TODOS) === '1'; } catch (e) { return false; }
  }

  function abrirCerrarTodos(abrir) {
    todosAbiertos = abrir;
    cont.querySelectorAll('.rg-art-cuerpo, .rg-art-titulo').forEach(function (e) {
      e.classList.toggle('rg-cerrado', !abrir);
    });
    pintarBtnTodos();
  }

  function insertarBtnTodos() {
    if (btnTodos) return;
    var barra = document.createElement('div');
    barra.className = 'rg-todos text-center mb-3';
    btnTodos = document.createElement('button');
    btnTodos.type = 'button';
    btnTodos.className = 'btn btn-outline-orange btn-sm rounded-pill fw-bold';
    btnTodos.addEventListener('click', function () {
      abrirCerrarTodos(!todosAbiertos);
      guardarEstadoTodos();
    });
    barra.appendChild(btnTodos);
    var h6 = cont.querySelector(':scope > h6');
    cont.insertBefore(barra, h6 || cont.firstElementChild);
    pintarBtnTodos();
  }

  function aplicar() {
    if (cont.classList.contains('editando')) return;
    if (cont.querySelector(':scope > .rg-articulo')) return;
    flatHTML = cont.innerHTML;
    var primero = true;
    var el = cont.firstElementChild;
    while (el) {
      var siguiente = el.nextElementSibling;
      if (!esArticulo(el)) { el = siguiente; continue; }
      var art = document.createElement('div');
      art.className = 'rg-articulo';
      var titulo = document.createElement('p');
      titulo.className = 'rg-art-titulo rg-cerrado';
      var strong = el.firstElementChild;
      var full = strong.textContent || '';
      var mNum = full.match(/^art[ií]culo\s*(\d+)\./i);
      var sub = mNum ? full.slice(mNum[0].length).trim() : '';
      var tNum = document.createElement('strong');
      tNum.textContent = mNum
        ? (mNum[1] + '.' + (sub ? ' ' + sub : ''))
        : full.trim();
      titulo.appendChild(tNum);
      el.removeChild(strong);
      var cuerpo = document.createElement('div');
      cuerpo.className = 'rg-art-cuerpo rg-cerrado';
      var resto = document.createElement('p');
      while (el.firstChild) resto.appendChild(el.firstChild);
      if (resto.textContent.trim() || resto.querySelector('br, a')) cuerpo.appendChild(resto);
      var sib = el.nextSibling;
      while (sib) {
        var nx = sib.nextSibling;
        if (sib.nodeType === 1 && (esArticulo(sib) || sib.tagName === 'H6')) break;
        if (sib.nodeType === 1) cuerpo.appendChild(sib);
        else if ((sib.textContent || '').trim() === '') cont.removeChild(sib);
        sib = nx;
      }
      (function (t, c) {
        t.addEventListener('click', function () {
          if (todosAbiertos) {
            var nc = c.classList.toggle('rg-cerrado');
            t.classList.toggle('rg-cerrado', nc);
            return;
          }
          var cerrado = c.classList.contains('rg-cerrado');
          cerrarTodos();
          if (cerrado) { c.classList.remove('rg-cerrado'); t.classList.remove('rg-cerrado'); }
        });
      })(titulo, cuerpo);
      art.appendChild(titulo);
      art.appendChild(cuerpo);
      cont.replaceChild(art, el);
      if (primero) { titulo.classList.remove('rg-cerrado'); cuerpo.classList.remove('rg-cerrado'); primero = false; }
      el = art.nextElementSibling;
    }
    if (cont.querySelector(':scope > .rg-articulo')) {
      insertarBtnTodos();
      if (leerEstadoTodos()) abrirCerrarTodos(true);
    }
  }

  aplicar();

  // Compatibilidad con el editor del superusuario:
  // - Al entrar a editar, restaurar el HTML plano ANTES de que el editor lo lea (fase capture).
  // - Al salir (guardar/cancelar), reaplicar el acordeon cuando termine el modo edicion.
  var btnEditar = document.getElementById('rgEditar');
  if (btnEditar) btnEditar.addEventListener('click', function () { cont.innerHTML = flatHTML; }, true);
  ['rgGuardar', 'rgCancelar'].forEach(function (id) {
    var b = document.getElementById(id);
    if (!b) return;
    b.addEventListener('click', function () {
      var t = setInterval(function () {
        if (!cont.classList.contains('editando')) { clearInterval(t); aplicar(); }
      }, 150);
      setTimeout(function () { clearInterval(t); }, 8000);
    });
  });
})();
