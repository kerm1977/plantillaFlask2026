#!/usr/bin/env python3
"""
Estandariza colores de botones Bootstrap en templates HTML
al esquema naranja de La Tribu.
Modo DRY-RUN por defecto; pasa --apply para aplicar.
"""

import os
import re
import sys
import argparse

# Mapeo de clases de botones a reemplazar
MAP = {
    # Botones sólidos
    r'\bbtn-primary\b': 'btn-warning-orange',
    r'\bbtn-success\b': 'btn-warning-orange',
    r'\bbtn-info\b': 'btn-orange',
    # Botones outline
    r'\bbtn-outline-primary\b': 'btn-outline-orange',
    r'\bbtn-outline-info\b': 'btn-outline-orange',
    r'\bbtn-outline-success\b': 'btn-outline-orange',
    r'\bbtn-outline-warning\b': 'btn-outline-orange',
    # btn-secondary y btn-outline-secondary se mantienen (gris)
}

# Archivos a excluir (no tocar)
EXCLUDE = {
    'partials',  # algunos parciales pueden tener botones comunes
}

def process_file(path, apply=False):
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    text = original
    changes = []
    for pattern, replacement in MAP.items():
        matches = list(re.finditer(pattern, text))
        if matches:
            # Evitar reemplazar si ya está en el target
            text = re.sub(pattern, replacement, text)
            changes.append(f'  {pattern} -> {replacement} ({len(matches)} veces)')
    if text != original:
        if apply:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        return True, changes
    return False, []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios')
    args = parser.parse_args()

    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    modified = 0
    for root, dirs, files in os.walk(templates_dir):
        # No excluimos nada por ahora, procesamos todo
        for fname in files:
            if not fname.endswith('.html'):
                continue
            path = os.path.join(root, fname)
            changed, changes = process_file(path, apply=args.apply)
            if changed:
                modified += 1
                print(f'{os.path.relpath(path, templates_dir)}')
                for c in changes:
                    print(c)
    if not args.apply:
        print(f'\nMODOS DRY-RUN. Archivos a modificar: {modified}')
        print('Pasa --apply para aplicar.')
    else:
        print(f'\nArchivos modificados: {modified}')

if __name__ == '__main__':
    main()
