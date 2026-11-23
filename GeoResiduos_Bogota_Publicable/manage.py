"""Configura admin y datos de demostración. Ej.: python manage.py init"""
import argparse
import getpass
from storage import init_db, seed_demo
from security import create_admin, admin_ready
p=argparse.ArgumentParser(description='Gestión del proyecto GeoResiduos Bogotá')
p.add_argument('command',choices=['init','seed-demo','init-db'])
a=p.parse_args()
init_db()
if a.command=='init':
    if admin_ready(): print('Administrador ya configurado.')
    else:
        pw=getpass.getpass('Crea una contraseña de administrador (mínimo 10 caracteres): ')
        confirm=getpass.getpass('Confirma la contraseña: ')
        if pw!=confirm: raise SystemExit('Las contraseñas no coinciden.')
        create_admin(pw);print('Administrador creado. Guarda la contraseña en un lugar seguro.')
    if input('¿Cargar 8 puntos ficticios de ejemplo? [s/N]: ').strip().lower() in ('s','si','sí','y'):
        print('Reportes de demostración añadidos:',seed_demo())
elif a.command=='seed-demo': print('Reportes ficticios añadidos:',seed_demo())
else: print('Base de datos inicializada.')
