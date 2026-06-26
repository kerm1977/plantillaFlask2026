"""
Utilidades para importación de contactos.
"""
import re
import random
import string

def gen_pin():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def parse_line(raw):
    line = raw.strip()
    if not line:
        return None

    # Remove parenthetical comments
    line = re.sub(r'\([^)]*\)', '', line)

    # Extract email
    email = ''
    m = re.search(r'[\w.\-]+@[\w.\-]+\.\w+', line)
    if m:
        email = m.group(0)
        line = (line[:m.start()] + line[m.end():]).strip()

    # Remove keywords before cedula
    line = re.sub(r'\b[Cc][eé][ée]?dulas?\b', '', line)
    line = re.sub(r'\bCed\b', '', line)
    line = re.sub(r'\bDimex\b', '', line, flags=re.IGNORECASE)
    line = line.replace(',', ' ')
    line = re.sub(r'\s+', ' ', line).strip()

    cedula = ''
    name   = line

    # Case: spaces inside cedula like "1 1879 0294" — three digit groups at end
    m = re.search(r'\s(\d{1,3})\s+(\d{3,4})\s+(\d{3,4})\s*$', line)
    if m:
        cedula = m.group(1) + m.group(2) + m.group(3)
        name   = line[:m.start()].strip()
    else:
        # Case: cedula (digits + optional dashes) possibly glued to last name word
        line2 = re.sub(r'([a-záéíóúüñA-ZÁÉÍÓÚÜÑ])(\d)', r'\1 \2', line)
        m = re.search(r'\s([A-Z]?\d[\d\-]*)\s*$', line2)
        if m:
            raw_ced = re.sub(r'[\-\s]', '', m.group(1))
            if len(raw_ced.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')) >= 5:
                cedula = raw_ced
                name = line2[:m.start()].strip()
                name = re.sub(r'\s+', ' ', name).strip()

    if not name:
        return None

    if not cedula:
        cedula = 'SC-' + ''.join(random.choices(string.digits, k=8))

    return {'nombre_completo': name, 'cedula': cedula, 'email': email}
