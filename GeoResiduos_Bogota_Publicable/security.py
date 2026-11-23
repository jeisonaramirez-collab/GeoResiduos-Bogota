"""Gestión local de credenciales administrativas. No guarda contraseñas planas."""
import base64
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

ADMIN_FILE = Path(os.environ.get('GEORESIDUOS_DATA_DIR',str(Path(__file__).resolve().parent / 'data'))) / 'admin.json'

def create_admin(password):
    if len(password) < 10:
        raise ValueError('La contraseña debe tener al menos 10 caracteres.')
    ADMIN_FILE.parent.mkdir(parents=True,exist_ok=True)
    if ADMIN_FILE.exists():
        raise FileExistsError('Ya existe un administrador. No se sobrescribe automáticamente.')
    salt=os.urandom(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
    ADMIN_FILE.write_text(json.dumps({'salt':base64.b64encode(salt).decode(),'digest':base64.b64encode(digest).decode()}),encoding='utf-8')
    try: os.chmod(ADMIN_FILE,0o600)
    except OSError: pass

def verify_admin(password):
    admin_from_env = os.environ.get('ADMIN_PASSWORD','')
    if len(admin_from_env)>=10:
        return hmac.compare_digest(password.encode('utf-8'),admin_from_env.encode('utf-8'))
    if not ADMIN_FILE.is_file(): return False
    try:
        cred=json.loads(ADMIN_FILE.read_text(encoding='utf-8'))
        salt=base64.b64decode(cred['salt']);old=base64.b64decode(cred['digest'])
        candidate=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
        return hmac.compare_digest(candidate,old)
    except (ValueError,KeyError,TypeError, OSError): return False

def admin_ready(): return len(os.environ.get('ADMIN_PASSWORD',''))>=10 or ADMIN_FILE.is_file()
