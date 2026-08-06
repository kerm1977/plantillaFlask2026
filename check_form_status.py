import sqlite3

conn = sqlite3.connect('local_app.db')
cursor = conn.cursor()

# Verificar estado del formulario
cursor.execute("SELECT id, name, is_active, slug FROM form WHERE id = 1")
form = cursor.fetchone()
print("Formulario ID 1:", form)

# Verificar campos del formulario
cursor.execute("PRAGMA table_info(form_field)")
columns = cursor.fetchall()
print("\nColumnas de form_field:")
for col in columns:
    print(col)

cursor.execute("SELECT * FROM form_field WHERE form_id = 1")
print("\nCampos del formulario:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Label: {row[1]}, Tipo: {row[2]}, Orden: {row[3]}")

conn.close()
