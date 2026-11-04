# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Página autónoma de personas: HTML offline, ordenado y compartible.

Genera un archivo .html con todas las respuestas del formulario, con un
botón fijo "Descargar datos del formulario" que permite a quien la recibe
guardarla como PDF desde el navegador (funciona sin conexión al sitio).
"""
from datetime import datetime
from flask import Response, render_template
from routes.forms_responses_utils import _build_answers_map, _fmt_tel, _fmt_tel_resp
from routes.forms_export_singlepage import _static_img_b64


def _build_personas_html(form, fields, responses):
    logo_b64 = _static_img_b64('logo.png') if getattr(form, 'show_logo', False) else None

    personas = []
    for i, r in enumerate(responses, 1):
        datos = []

        def add(label, val):
            if val not in (None, ''):
                datos.append({'label': label, 'value': str(val)})

        if form.show_cedula:
            add('Cédula', r.cedula)
        add('Email', r.email)
        add('Teléfono', _fmt_tel_resp(r, form))
        add('Edad', r.edad)
        if form.show_pasaporte:
            add('Pasaporte', r.pasaporte)
        if form.show_fecha_nacimiento and r.fecha_nacimiento_dia:
            add('Fecha de Nacimiento',
                f"{r.fecha_nacimiento_dia}/{r.fecha_nacimiento_mes}/{r.fecha_nacimiento_anio}")
        if form.show_residencia:
            add('Provincia', r.provincia)
            add('Dirección exacta', r.direccion)
        add('Número de Reserva', r.reservation_number)
        if form.show_ficha_medica:
            add('Tipo de Sangre', r.tipo_sangre)
            add('Alergias', r.alergias)
            add('Enfermedades Crónicas', r.enfermedades_cronicas)
            emerg = (r.contacto_emergencia_nombre or '')
            if r.contacto_emergencia_telefono:
                emerg += f" — {_fmt_tel(r.contacto_emergencia_telefono, form)}"
            add('Contacto de Emergencia', emerg.strip())
        if form.form_type == 'examen' and r.score is not None:
            add('Calificación', f"{r.score}%")
        if r.submitted_at:
            add('Fecha de registro', r.submitted_at.strftime('%d/%m/%Y %H:%M'))

        respuestas = []
        for f in fields:
            val = _build_answers_map(r, [f]).get(str(f.id), '')
            if isinstance(val, list):
                val = ', '.join(val)
            if val:
                respuestas.append({'label': f.label, 'value': str(val)})

        personas.append({'num': i, 'nombre': r.nombre_completo or 'Sin nombre',
                         'datos': datos, 'respuestas': respuestas})

    return render_template(
        'form_personas.html', form=form, personas=personas,
        logo_b64=logo_b64,
        membrete=form.membrete if getattr(form, 'show_membrete', False) else '',
        generado=datetime.now().strftime('%d/%m/%Y %H:%M'))


def _export_personas_page(form, fields, responses):
    html = _build_personas_html(form, fields, responses)
    return Response(
        html, mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename="{form.name} - personas.html"'})
