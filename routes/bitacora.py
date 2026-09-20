# ══ BITÁCORA — mini blog interno (módulo independiente) ══
# Solo el superusuario crea/edita/elimina.
# Visibilidad: 'privada' = solo super; 'publica' = todos (incluso sin login);
# 'seleccion' = super + usuarios registrados elegidos.
from flask import render_template, session, request, redirect, url_for, jsonify
from routes import bp
from db import db
from models_core import User
from models_bitacora import BitacoraEntry, BitacoraPage, BitacoraShare

_VISIBILIDADES = ('privada', 'publica', 'seleccion')


def _is_super():
    return session.get('role') == 'Superusuario'


def _vis(entry):
    v = entry.visibilidad
    if v not in _VISIBILIDADES:
        v = 'seleccion' if entry.privada is False else 'privada'
    return v


def _puede_ver(entry):
    if _is_super() or _vis(entry) == 'publica':
        return True
    uid = session.get('user_id')
    if not uid or _vis(entry) != 'seleccion':
        return False
    return any(s.user_id == uid for s in entry.shares)


def _visibles():
    todas = BitacoraEntry.query.order_by(BitacoraEntry.creado.desc()).all()
    return [e for e in todas if _puede_ver(e)]


def _paginas(entry):
    """Páginas ordenadas; si no hay, el contenido legado es la página 1."""
    if entry.pages:
        return entry.pages
    if entry.contenido:
        return [BitacoraPage(orden=0, contenido=entry.contenido)]
    return [BitacoraPage(orden=0, contenido='')]


def _guardar(entry, data):
    entry.titulo = (data.get('titulo') or '').strip() or 'Sin título'
    entry.descripcion = (data.get('descripcion') or '').strip()
    vis = data.get('visibilidad')
    entry.visibilidad = vis if vis in _VISIBILIDADES else 'privada'
    entry.privada = entry.visibilidad == 'privada'
    if entry.visibilidad == 'seleccion':
        ids = {int(x) for x in (data.get('compartir') or [])
               if str(x).isdigit()}
        entry.shares = [BitacoraShare(user_id=u) for u in sorted(ids)]
    else:
        entry.shares = []
    paginas = [p for p in (data.get('paginas') or [])]
    if not paginas:
        paginas = [data.get('contenido') or '']
    entry.pages = [BitacoraPage(orden=i, contenido=h)
                   for i, h in enumerate(paginas)]
    db.session.commit()


@bp.route('/bitacora')
def bitacora_lista():
    return render_template('bitacora_lista.html', entradas=_visibles(),
                           is_super=_is_super(), page_title='Bitácora',
                           vis=_vis)


@bp.route('/bitacora/<int:entry_id>')
def bitacora_ver(entry_id):
    entry = BitacoraEntry.query.get_or_404(entry_id)
    if not _puede_ver(entry):
        return redirect(url_for('main.bitacora_lista'))
    return render_template('bitacora_ver.html', entry=entry,
                           paginas=_paginas(entry), is_super=_is_super(),
                           page_title=entry.titulo)


@bp.route('/bitacora/nueva')
def bitacora_nueva():
    if not _is_super():
        return redirect(url_for('main.bitacora_lista'))
    usuarios = User.query.order_by(User.name, User.last_name_1).all()
    return render_template('bitacora_form.html', entry=None, usuarios=usuarios,
                           compartidos=set(), paginas=[''],
                           page_title='Nueva entrada')


@bp.route('/bitacora/<int:entry_id>/editar')
def bitacora_editar(entry_id):
    if not _is_super():
        return redirect(url_for('main.bitacora_lista'))
    entry = BitacoraEntry.query.get_or_404(entry_id)
    usuarios = User.query.order_by(User.name, User.last_name_1).all()
    return render_template('bitacora_form.html', entry=entry, usuarios=usuarios,
                           compartidos={s.user_id for s in entry.shares},
                           paginas=[p.contenido for p in _paginas(entry)],
                           page_title='Editar entrada')


@bp.route('/api/bitacora/guardar', methods=['POST'])
@bp.route('/api/bitacora/<int:entry_id>/guardar', methods=['POST'])
def bitacora_guardar(entry_id=None):
    if not _is_super():
        return jsonify({'error': 'Sin permiso'}), 403
    if entry_id:
        entry = BitacoraEntry.query.get_or_404(entry_id)
    else:
        entry = BitacoraEntry()
        db.session.add(entry)
    _guardar(entry, request.get_json(silent=True) or {})
    return jsonify({'ok': True, 'id': entry.id,
                    'url': url_for('main.bitacora_ver', entry_id=entry.id)})


@bp.route('/api/bitacora/<int:entry_id>/eliminar', methods=['POST'])
def bitacora_eliminar(entry_id):
    if not _is_super():
        return jsonify({'error': 'Sin permiso'}), 403
    db.session.delete(BitacoraEntry.query.get_or_404(entry_id))
    db.session.commit()
    return jsonify({'ok': True})
