"""
Utilidades para manejo de respuestas de formularios.
"""
import json
from models import FormField, FormAnswer


def _build_answers_map(response, fields):
    """Retorna dict {field_id: parsed_value} para una respuesta."""
    raw = {a.field_id: a.value for a in response.answers}
    result = {}
    for f in fields:
        val = raw.get(f.id, '')
        try:
            val = json.loads(val)
        except Exception:
            pass
        result[str(f.id)] = val
    return result


def _update_response_answers(resp, answers_data, form_id):
    """Actualiza las respuestas de un formulario."""
    existing = {a.field_id: a for a in resp.answers}
    fields = FormField.query.filter_by(form_id=form_id).order_by(FormField.order).all()
    for field in fields:
        answer_value = answers_data.get(str(field.id), '')
        val = (json.dumps(answer_value, ensure_ascii=False)
               if isinstance(answer_value, list) else str(answer_value))
        if field.id in existing:
            existing[field.id].value = val
        else:
            resp.answers.append(FormAnswer(field_id=field.id, value=val))
