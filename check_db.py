import sqlite3

conn = sqlite3.connect('local_app.db')
cursor = conn.cursor()

# Buscar eventos con chirripo
cursor.execute("SELECT id, nombre_lugar FROM event WHERE nombre_lugar LIKE '%chirripo%' OR nombre_lugar LIKE '%Chirripo%'")
print("Eventos con Chirripo:", cursor.fetchall())

# Listar todos los eventos
cursor.execute("SELECT id, nombre_lugar FROM event")
print("\nTodos los eventos:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Nombre: {row[1]}")

# Buscar formularios
cursor.execute("SELECT id, name FROM form")
print("\nTodos los formularios:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Nombre: {row[1]}")

conn.close()
