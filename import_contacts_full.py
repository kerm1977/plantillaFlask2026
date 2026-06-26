"""
Script de importacion masiva de contactos a la base de datos.
Ejecutar: python import_contacts_full.py
"""
import sys, os

# ── Configurar Flask app context ────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app
from db import db
from models import Hiker
from import_contacts_utils import gen_pin, parse_line
app = create_app()

RAW = """
Kenneth Ruiz Matamoros 109840935
Jenny Miriam Ceciliano Córdoba 107620692
Miriam Astúa Calderón 110160520
Rosario Aguilar Elizondo 303390724
Tatiana salazar Zuñiga 303610914
William Aguilar Camacho 105340740
Santiago Aguilar Alvarez 122980110
Valeria Aguilar Alvarez 121610684
Monica Vega Rodriguez 116340444
Yadira Villalobos Rodríguez 105840217
Anabelle Ceciliano Córdoba 108550191
Natalia Batista Ceciliano 305410291
Eusebio Batista Reyes 602300244
Wilberth Esquivel Cubero 502260743
Cristhian Sanabria Vargas 108350273 cristhiansana29@gmail.com
María Matarrita Villalobos 111200884 bebucha13@gmail.com
Jorge Chinchilla Castro 106550281 Jechc@gmail.com
Alexandra Sanabria Vargas 107250301 Alek_xa@hotmail.com
Edith Ramírez Calderón 701010184 edith.ramirez71@live.com
Alberto Castro Rueda 601950978 1166jose.castro@gmail.com
Xinia Ramirez Calderón 700750392
Jacob Ignacio Gomez Redondo Ced 304670661
Ana Lorena Arias Zúñiga 107300501 anaarias10@gmail.com
Carmen Obando Andrade 107030160
Mario Picado Sanchez 302490909
Sandra Herrera Cerdas 3312636
Gerardo Zuñiga Esquivel 304150072
Karol Lucía Chacón Gonzalez 303820261
Gloriana Sofia Zúñiga Chacón 306090403
Lizeth Magally Ceciliano Cordoba 112380086
Julian Fernandez Ceciliano 306120914
Jorge Cascante Jimenez 107670436
Sharon Benavides Corrales 110110248
Clara Quirós Bogantes 302620462
Jacqueline Abarca Rodríguez 11023149
Maureen Vega Sánchez 108740505 maureenvegas@yahoo.com
Isabel Sánchez Sanabria 301920744 isabelsansana@gmail.com
Ingrid Isabella Arauz Useda 155810851401
Luis Steven Zuñiga Naranjo
Yessenia Meneses Segura 110010499
Carlos Manuel Berrocal Araya 204170616
Victor Hugo Zeledon Chinchilla 107580049
Mariana Vega Rivas 115490229
Stephanie Quesada Montero 113590683
Ana Perez Ureña 110030392
Lian Rivera Ugalde 109280687
Jorge Cordero Fernández 3-0241-0394
Guillermo Aguilar Vega 106700175
Morena Rivas Artiga 800770932
Fressy Calvo Fuentes 302780500
Anais Robles Rojas1-0712-0249
Esperanza del Socorro Castro Montes de oca Dimex 155809475426
Jorge Isaac Villalobos Rodríguez 302490739
María Madrigal Calvo 204300415
Laura Hernández Campos 109080064
Ana Teresa Rodriguez Arce 401210183
Johan Fernández Aguilar 304830672
Wálter Guzmán Granados 3240117
Viria Prado Segura 106240026
Luis Diego Cabezas Vargas 116730771
Guadalupe Hidalgo Arrieta 302500203
Sandra Guiselle López Gamboa 303250120
María Alejandra Solano Sánchez 114370608
Ivannia Hernández Sánchez 109380390
Xinia Zuñiga Piedra302970164
Anabelle Madrigal Calvo 109430205
Génesis Valenciano Murillo 118850686 jscvlncn3@gmail.com
Jessie Valenciano Murillo 11719481 jscvlncn3@gmail.com
Jacqueline Abarca Rodríguez 110230149
Gabriel Sanchez Abarca 1 1879 0294
Mary Paz Araya Zumbado 112890713
Adilia Zumbado Murillo 401250717
Katherine Sanabria Valverde 114660869
Ashley Sánchez Sanabria 305890574
Estefanny de los Angeles Villalobos Robles 304770572 villalobosestef06@gmail.com
Gerardo Zúñiga Rodríguez 302440937
Karina Porras Segura 118240861
Jose Alejandro Castro Ramirez 305080555
Karen Barrantes Ramirez 116060947
Maribelle De Los Angeles Salazar Flores 105940723
Juan Pablo Corrales Muñoz 108190745
Carlos Alejandro Mendéz Segura 304010039
Flor Marlene Fonseca Calderón 304050581
Jacqueline Herrera Sanabria 111450299 jacky1606@gmail.com
Marco Saborío Herrera 114130662 msaboriohe@credomatic.cr
Kattya Ulloa Calvo 110200590
Rocio Solano Molina 108330787
Juan Pablo Benavides Granados 1993087
Meriam Franciny Brenes Valverde 305460836
Yolenne Esquivel Zamora 106550180
Carlos Quirós Bogantes 302350332
Alejandra Bogantes Barboza 109500375
Jorge Enrique Abarca Rodríguez 105750392
Jonathan Castro Ramírez 116480417
Rodrigo González P26921214
Diego Ibarra Jara 108830555
Evelyn Segura Quirós 109930055
Ingrid Rodríguez Brenes 113709876
Karla Madrigal Guerrero 110770080
Stephanie Montoya Monge 304480314
Katthy Monge Morales 303020613
Olman Montoya Fernández 302700610
Maximo Richmond Obando 302130231
Jonathan Quesada Segura 117910841
Linda Cespedez Umaña 117940251
Jose Alfredo Tellez García 155827314618
Dita Raquel Solis Sanchez 302930219
Shirley Espino Contreras 205340430
Iliana Vega Martinez 303050983
Emilio Vargas Villalobos 106550733
Nuria Herrera Monge 108268042
Jorge Isaac Cascante Solano 115100797
Edgar Lopez Ramirez 302380782
Sandra Herrera Cerdas 303120636
Olga Martha Bogantes Barboza 108370617
Angeolett Ferdinand Cambronero 121400558
Dereck Fedinand Cambronero 122300003
Andrea Cambronero Castillo 110650930
Diego Mendez Chinchilla 11430300
Ronny Mendez León 401620127
Máximo Alberto Richmond Obando 302130231
Elida Matarrita Villalobos 111960419
Ronald Quesada Hernandez 302490477
Solange Ruiz Venegas 107230925
Kattia Brenes Viquez 303360312
"""

def main():
    lines = [l.strip() for l in RAW.strip().split('\n') if l.strip()]
    contacts = [parse_line(l) for l in lines]
    contacts = [c for c in contacts if c]

    with app.app_context():
        existing_cedulas = {h.cedula.strip().lower() for h in Hiker.query.all() if h.cedula}
        existing_names   = {h.nombre_completo.strip().lower() for h in Hiker.query.all() if h.nombre_completo}

        added = skipped = 0
        for c in contacts:
            ced  = (c['cedula'] or '').strip().lower()
            name = (c['nombre_completo'] or '').strip()

            if ced and not ced.startswith('sc-') and ced in existing_cedulas:
                print(f'  OMITIDO (cedula dup): {name} [{c["cedula"]}]')
                skipped += 1; continue
            if name.lower() in existing_names:
                print(f'  OMITIDO (nombre dup): {name}')
                skipped += 1; continue

            h = Hiker(
                cedula         = c['cedula'],
                nombre_completo= name,
                pin_secreto    = gen_pin()
            )
            db.session.add(h)
            existing_cedulas.add(ced)
            existing_names.add(name.lower())
            added += 1
            print(f'  + {name} [{c["cedula"]}]')

        db.session.commit()
        print(f'\n✓ Importados: {added} | Omitidos: {skipped} | Total procesados: {added+skipped}')


if __name__ == '__main__':
    main()
