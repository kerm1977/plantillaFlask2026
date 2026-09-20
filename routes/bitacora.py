# ══ BITÁCORA — mini blog interno (módulo independiente) ══
# Solo el superusuario crea/edita/elimina. Lectura: superusuarios siempre;
# usuarios registrados solo si la entrada no es privada y fueron compartidos.
from flask import render_template, session, request, redirect, url_for, jsonify
from routes import bp
from db import db
from models_core import User
from models_bitacora import BitacoraEntry, BitacoraShare


def _is_super():
    return session.get('role') == 'Superusuario'


def _puede_ver(entry):
    """Superusuario ve todo; usuario registrado ve solo lo compartido no privado."""
    if _is_super():
        return True
    uid = session.get('user_id')
    if not uid or entry.privada:
        return False
    return any(s.user_id == uid for s in entry.shares)


def _visibles():
    """Entradas visibles para el usuario actual, más recientes primero."""
    todas = BitacoraEntry.query.order_by(BitacoraEntry.creado.desc()).all()
    return [e for e in todas if _puede_ver(e)]


def _guardar(entry, data):
    entry.titulo = (data.get('titulo') or '').strip() or 'Sin título'
    entry.descripcion = (data.get('descripcion') or '').strip()
    entry.contenido = data.get('contenido') or ''
    entry.privada = bool(data.get('privada'))
    if _is_super():
        ids = {int(x) for x in (data.get('compartir') or [])
               if str(x).isdigit()}
        entry.shares = [BitacoraShare(user_id=u) for u in sorted(ids)]
    db.session.commit()


@bp.route('/bitacora')
def bitacora_lista():
    if not session.get('user_id'):
        return redirect(url_for('main.home'))
    entradas = _visibles()
    return render_template('bitacora_lista.html', entradas=entradas,
                           is_super=_is_super(), page_title='Bitácora')


@bp.route('/bitacora/<int:entry_id>')
def bitacora_ver(entry_id):
    entry = BitacoraEntry.query.get_or_404(entry_id)
    if not _puede_ver(entry):
        return redirect(url_for('main.bitacora_lista'))
    return render_template('bitacora_ver.html', entry=entry,
                           is_super=_is_super(), page_title=entry.titulo)


@bp.route('/bitacora/nueva')
def bitacora_nueva():
    if not _is_super():
        return redirect(url_for('main.bitacora_lista'))
    usuarios = User.query.order_by(User.name, User.last_name_1).all()
    return render_template('bitacora_form.html', entry=None, usuarios=usuarios,
                           compartidos=set(), page_title='Nueva entrada')


@bp.route('/bitacora/<int:entry_id>/editar')
def bitacora_editar(entry_id):
    if not _is_super():
        return redirect(url_for('main.bitacora_lista'))
    entry = BitacoraEntry.query.get_or_404(entry_id)
    usuarios = User.query.order_by(User.name, User.last_name_1).all()
    compartidos = {s.user_id for s in entry.shares}
    return render_template('bitacora_form.html', entry=entry, usuarios=usuarios,
                           compartidos=compartidos,
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
    entry = BitacoraEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'ok': True})
