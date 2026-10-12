# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_pdf.py - Descarga del estado de cuenta en PDF (Mis puntos)
from flask import request, session, Response, jsonify
from models import Hiker
from modules.estado_cuenta_pdf import build_estado_cuenta_pdf
from modules.points_helpers import build_estado_cuenta_whatsapp, token_descarga_ok
from routes import bp


def _hiker_autorizado():
    """Devuelve (cedula, hiker, error_response). Autoriza superusuario, persona
    verificada con su PIN o enlace con token de descarga firmado."""
    cedula = (request.args.get('cedula') or '').strip()
    if not cedula:
        return None, None, (jsonify({'ok': False, 'error': 'Falta la cedula'}), 400)
    if session.get('role') != 'Superusuario' and session.get('mis_puntos_ok') != cedula \
            and not token_descarga_ok(cedula, request.args.get('t')):
        return None, None, (jsonify({'ok': False, 'error': 'No autorizado'}), 403)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return None, None, (jsonify({'ok': False, 'error': 'Usuario no encontrado'}), 404)
    return cedula, hiker, None


@bp.route('/mis-puntos/estado-cuenta.pdf', methods=['GET'])
def estado_cuenta_pdf():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    # BLINDADO: no-store para que Cloudflare no sirva un PDF viejo con ceros
    return Response(build_estado_cuenta_pdf(cedula, hiker), mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.pdf',
                             'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'})


@bp.route('/mis-puntos/estado-cuenta-simple.txt', methods=['GET'])
def estado_cuenta_txt():
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    text = build_estado_cuenta_whatsapp(cedula, hiker, plain=True)
    return Response(text, mimetype='text/plain; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename=estado_cuenta_{cedula}.txt',
                             'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'})


@bp.route('/mis-puntos/estadisticas.txt', methods=['GET'])
def estadisticas_txt():
    """Descarga de la estadística personal (solo lectura)."""
    cedula, hiker, err = _hiker_autorizado()
    if err:
        return err
    from modules.estado_global import estadisticas_persona
    from datetime import datetime
    st = estadisticas_persona(cedula)
    sep = '=' * 60
    lines = [sep, 'MIS ESTADÍSTICAS - La Tribu de los Libres', sep,
             f'Nombre: {st["nombre"]}', f'Cédula: {cedula}',
             f'Generado: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}', sep,
             f'Estadísticas contando desde: {st["desde"] or "Siempre"}',
             f'Total de puntos (estadística): {st["total"]}',
             f'Puntos ganados: {st["ganados"]}',
             f'Puntos perdidos: {st["perdidos"]}',
             f'Puntos redimidos: {st["redimidos"]}',
             f'Puntos comprados: {st["comprados"]}',
             f'Puntos donados: {st["donados"]}',
             f'Excedente generado a la casa por compras: {st["casa"]}',
             f'Puntos posibles que pudo haber ganado: {st["posibles"]}',
             f'Carnet descargado: {"Sí (" + st["carnet_descargado"] + ")" if st["carnet_descargado"] else "No"}',
             f'Caminatas participadas: {len(st["caminatas_ok"])}',
             f'Caminatas no participadas: {len(st["caminatas_no"])}',
             '', 'CAMINATAS EN LAS QUE PARTICIPÉ:']
    lines += [f'  - {n}' for n in st['caminatas_ok']] or ['  (ninguna)']
    lines += ['', 'CAMINATAS EN LAS QUE NO PARTICIPÉ:']
    lines += [f'  - {n}' for n in st['caminatas_no']] or ['  (ninguna)']
    return Response('\n'.join(lines), mimetype='text/plain; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename=estadisticas_{cedula}.txt',
                             'Cache-Control': 'no-store, no-cache, must-revalidate', 'Pragma': 'no-cache'})
