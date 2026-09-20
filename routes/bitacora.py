# ══ BLINDADO — BITÁCORA (mini blog independiente) ══
# Código probado y estable. NO modificar sin revisar el flujo completo.
# Solo el superusuario crea/edita/elimina.
# Visibilidad: 'privada' = solo super; 'publica' = todos (incluso sin login);
# 'seleccion' = super + usuarios registrados elegidos.
from datetime import datetime, timedelta
from flask import render_template, session, request, redirect, url_for, jsonify
from routes import bp
from db import db
from models_core import User
from models_bitacora import BitacoraEntry, BitacoraPage, BitacoraShare

_VISIBILIDADES = ('privada', 'publica', 'seleccion')
_CR_OFFSET = timedelta(hours=6)  # Costa Rica = UTC-6 (sin horario de verano)


def _cr(dt):
    """Fecha/hora UTC -> Costa Rica, formato dd/mm/yyyy hh:mm."""
    if not dt:
        return ''
    return (dt - _CR_OFFSET).strftime('%d/%m/%Y %H:%M')


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
    u = User.query.get(session.get('user_id') or 0)
    if u:
        entry.editado_por = (f'{u.name} {u.last_name_1} '
                             f'{u.last_name_2}').strip()
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
    editado = entry.actualizado and entry.actualizado != entry.creado
    return render_template(
        'bitacora_ver.html', entry=entry, paginas=_paginas(entry),
        is_super=_is_super(),
        vista_usuario=(request.args.get('vista') == 'usuario'),
        creado_cr=_cr(entry.creado),
        editado_cr=_cr(entry.actualizado) if editado else '',
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
