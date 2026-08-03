import sqlite3
c = sqlite3.connect('local_app.db')
cur = c.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE name IN ('cotizador','cotizador_lugar')")
for r in cur.fetchall():
    print(r[0])
    print('---')
cur.execute('SELECT COUNT(*) FROM cotizador')
print('cotizador count:', cur.fetchone())
