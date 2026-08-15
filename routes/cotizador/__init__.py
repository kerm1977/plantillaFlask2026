import re
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, make_response
from models_cotizador import Cotizador, CotizadorLugar
from db import db

bp = Blueprint('cotizador', __name__)

def _slugify(text):
    text = text.lower().strip()
    for src, dst in [('[áàäâ]','a'),('[éèëê]','e'),('[íìïî]','i'),('[óòöô]','o'),('[úùüû]','u'),('[ñ]','n')]:
        text = re.sub(src, dst, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text

def _unique_slug(text, exclude_id=None):
    slug = _slugify(text)
    counter = 1
    while True:
        query = Cotizador.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(Cotizador.id != exclude_id)
        existing = query.first()
        if not existing:
            return slug
        slug = f"{slug}-{counter}"
        counter += 1

from . import public, admin, lugar, import_export
