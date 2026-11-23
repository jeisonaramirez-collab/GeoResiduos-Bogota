"""API funcional de GeoResiduos Bogotá.

Uso: python -m uvicorn server:app --host 127.0.0.1 --port 8000
Datos creados por los usuarios son observaciones NO verificadas, no reportes oficiales.
"""
import base64
import binascii
import io
import json
import os
import secrets
import time
import uuid
from datetime import date
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from storage import ROOT, DATA_DIR, Report, StatusChange, SessionLocal, init_db, get_by_id, as_dict, CATEGORIES, LOCALITIES, STATUSES, seed_demo
from security import verify_admin, admin_ready

UPLOAD_DIR=Path(os.environ.get('GEORESIDUOS_UPLOAD_DIR', str(ROOT/'uploads')))
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
SECRET_PATH=DATA_DIR/'session_key.txt'
if os.environ.get('SESSION_SECRET'):
    secret=os.environ['SESSION_SECRET']
elif SECRET_PATH.exists():
    secret=SECRET_PATH.read_text().strip()
else:
    secret=secrets.token_urlsafe(48)
    SECRET_PATH.write_text(secret,encoding='utf-8')
    try: os.chmod(SECRET_PATH,0o600)
    except OSError: pass

app=FastAPI(title='GeoResiduos Bogotá',description='API académica de reportes ciudadanos no verificados',version='2.0.0')
app.add_middleware(SessionMiddleware,secret_key=secret,session_cookie='geo_session',max_age=3600*8,same_site='lax',https_only=os.environ.get('COOKIE_SECURE','false').lower()=='true')
app.mount('/static',StaticFiles(directory=str(ROOT/'static')),name='static')
app.mount('/uploads',StaticFiles(directory=str(UPLOAD_DIR)),name='uploads')

@app.on_event('startup')
def _start():
    init_db()
    if os.environ.get('LOAD_DEMO','').lower() in ('true','1','yes'): seed_demo()

def db():
    with SessionLocal() as session: yield session

class IncomingReport(BaseModel):
    description: str = Field(min_length=12,max_length=500)
    category: str
    locality: str
    date: date
    lat: float
    lng: float
    photo: str | None = None
    @field_validator('description')
    @classmethod
    def validate_description(cls,v):
        v=v.strip()
        if len(v)<12: raise ValueError('Descripción demasiado corta')
        return v
    @field_validator('category')
    @classmethod
    def validate_cat(cls,v):
        if v not in CATEGORIES: raise ValueError('Categoría no permitida')
        return v
    @field_validator('locality')
    @classmethod
    def validate_locality(cls,v):
        if v not in LOCALITIES: raise ValueError('Localidad no permitida')
        return v
    @field_validator('lat')
    @classmethod
    def validate_lat(cls,v):
        if not 4.35<=v<=4.90: raise ValueError('Latitud fuera del rango de Bogotá utilizado para el prototipo')
        return v
    @field_validator('lng')
    @classmethod
    def validate_lng(cls,v):
        if not -74.30<=v<=-73.85: raise ValueError('Longitud fuera del rango de Bogotá utilizado para el prototipo')
        return v
    @field_validator('date')
    @classmethod
    def validate_date(cls,v):
        if v>date.today(): raise ValueError('La fecha no puede ser futura')
        return v

class LoginBody(BaseModel):
    password: str = Field(min_length=1,max_length=200)
class StatusBody(BaseModel):
    status: str

recent_attempts:dict[str,list[float]]={}
def csrf_guard(req:Request):
    # Las cookies de sesión + token CSRF impiden cambios desde sitios externos.
    origin=req.headers.get('origin')
    if origin and origin.rstrip('/')!=str(req.base_url).rstrip('/'):
        raise HTTPException(403,'Origen no autorizado')
    token=req.session.get('csrf')
    if not token or not secrets.compare_digest(str(token),req.headers.get('X-CSRF-Token','')):
        raise HTTPException(403,'Token de seguridad ausente o no válido; actualiza la página')

def admin_guard(req:Request):
    csrf_guard(req)
    if req.session.get('admin') is not True: raise HTTPException(401,'Se requiere iniciar sesión como administrador')

def save_photo(data_uri:str|None):
    if not data_uri: return None
    if not data_uri.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):
        raise HTTPException(422,'Fotografía no admitida. Usa PNG, JPG o WEBP.')
    encoded=data_uri.split(',',1)[1]
    if len(encoded)>1_500_000: raise HTTPException(413,'La fotografía supera el tamaño permitido de 1 MB.')
    try: binary=base64.b64decode(encoded,validate=True)
    except (binascii.Error, ValueError): raise HTTPException(422,'Imagen dañada')
    if len(binary)>1024*1024: raise HTTPException(413,'La fotografía supera 1 MB')
    try:
        with Image.open(io.BytesIO(binary)) as src:
            if src.format not in ('JPEG','PNG','WEBP') or src.width*src.height>9_000_000:
                raise HTTPException(422,'Tipo o dimensiones de imagen no permitidas')
            img=ImageOps.exif_transpose(src)
            img.load()
            img=img.convert('RGB')
            img.thumbnail((1600,1600))
            target=UPLOAD_DIR/f'{uuid.uuid4().hex}.webp'
            img.save(target,format='WEBP',quality=78,method=4)
            return target.name
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError):
        raise HTTPException(422,'No se pudo verificar la imagen')

def encode_photo(data_uri: str | None) -> bytes | None:
    """Procesa imagen y devuelve WEBP para persistir en PostgreSQL."""
    if not data_uri:
        return None
    if not data_uri.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):
        raise HTTPException(422, 'Fotografía no admitida. Usa PNG, JPG o WEBP.')
    encoded = data_uri.split(',', 1)[1]
    if len(encoded) > 1_500_000:
        raise HTTPException(413,'La fotografía supera el tamaño permitido de 1 MB.')
    try:
        binary = base64.b64decode(encoded, validate=True)
    except (binascii.Error,ValueError):
        raise HTTPException(422, 'Imagen dañada')
    if len(binary) > 1024 * 1024:
        raise HTTPException(413, 'La fotografía supera 1 MB')
    try:
        with Image.open(io.BytesIO(binary)) as src:
            if src.format not in ('JPEG','PNG','WEBP') or src.width * src.height > 9_000_000:
                raise HTTPException(422,'Tipo o dimensiones de imagen no permitidas')
            img = ImageOps.exif_transpose(src)
            img.load()
            img = img.convert('RGB')
            img.thumbnail((1600,1600))
            buffer = io.BytesIO()
            img.save(buffer,format='WEBP',quality=78,method=4)
            return buffer.getvalue()
    except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):
        raise HTTPException(422,'No se pudo verificar la imagen')

@app.get('/')
def home(): return FileResponse(ROOT/'static'/'index.html')

@app.get('/api/health')
def health(): return {'ok':True,'name':'GeoResiduos Bogotá','mode':'academic','database':'postgresql' if 'postgresql' in str(__import__('storage').engine.url) else 'sqlite'}

@app.get('/api/session')
def session_status(req:Request):
    if 'csrf' not in req.session: req.session['csrf']=secrets.token_urlsafe(32)
    return {'admin':bool(req.session.get('admin')),'adminConfigured':admin_ready(),'csrf':req.session['csrf']}

@app.get('/api/reports')
def list_reports(session:Session=Depends(db)):
    rows=session.scalars(select(Report).order_by(Report.date.desc(),Report.pk.desc()).limit(2000)).all()
    return {'items':[as_dict(r) for r in rows],'count':len(rows),'disclaimer':'Reportes de prueba o ciudadanos no verificados; no representan información oficial de la UAESP.'}

@app.post('/api/reports',status_code=201)
def create_report(body:IncomingReport,req:Request,session:Session=Depends(db)):
    csrf_guard(req)
    photo=encode_photo(body.photo)
    obj=Report(description=body.description,category=body.category,locality=body.locality,date=body.date,
        lat=body.lat,lng=body.lng,photo_data=photo,status='Pendiente',demo=False)
    try:
        session.add(obj);session.commit();session.refresh(obj)
    except Exception:
        session.rollback()
        raise
    return {'item':as_dict(obj)}

@app.get('/api/reports/{report_id}/photo')
def get_report_photo(report_id:str, session:Session=Depends(db)):
    r=get_by_id(session,report_id)
    if not r or not r.photo_data:
        raise HTTPException(404,'Fotografía no encontrada')
    return Response(content=r.photo_data,media_type='image/webp',headers={'Cache-Control':'private, max-age=300'})

@app.get('/api/reports/{report_id}')
def get_report(report_id:str,session:Session=Depends(db)):
    r=get_by_id(session,report_id)
    if not r: raise HTTPException(404,'Reporte no encontrado')
    return {'item':as_dict(r)}

@app.post('/api/admin/login')
def login(body:LoginBody,req:Request):
    csrf_guard(req)
    ip=req.client.host if req.client else 'localhost'
    now=time.monotonic()
    attempts=[t for t in recent_attempts.get(ip,[]) if now-t<60]
    if len(attempts)>=8: raise HTTPException(429,'Demasiados intentos. Vuelve a intentarlo más tarde.')
    if not admin_ready(): raise HTTPException(503,'Configura el administrador con: python manage.py init')
    if not verify_admin(body.password):
        attempts.append(now);recent_attempts[ip]=attempts
        raise HTTPException(401,'Contraseña incorrecta')
    req.session['admin']=True
    recent_attempts.pop(ip,None)
    return {'admin':True}

@app.post('/api/admin/logout')
def logout(req:Request):
    csrf_guard(req)
    req.session.pop('admin',None)
    return {'admin':False}

@app.patch('/api/admin/reports/{report_id}')
def update_report(report_id:str,body:StatusBody,req:Request,session:Session=Depends(db)):
    admin_guard(req)
    if body.status not in STATUSES: raise HTTPException(422,'Estado no permitido')
    r=get_by_id(session,report_id)
    if not r: raise HTTPException(404,'Reporte no encontrado')
    if r.status!=body.status:
        session.add(StatusChange(report_pk=r.pk,old_status=r.status,new_status=body.status))
        r.status=body.status
        session.commit();session.refresh(r)
    return {'item':as_dict(r)}

@app.post('/api/admin/seed-demo')
def seed(req:Request):
    admin_guard(req)
    return {'inserted':seed_demo()}

@app.get('/api/admin/audit')
def audit(req:Request,session:Session=Depends(db)):
    if not req.session.get('admin'): raise HTTPException(401,'Se requiere administrador')
    rows=session.scalars(select(StatusChange).order_by(StatusChange.created_at.desc()).limit(100)).all()
    return {'items':[{'report':f'RPT-{r.report_pk:06d}','previous':r.old_status,'new':r.new_status,'date':r.created_at.isoformat()} for r in rows]}

@app.exception_handler(Exception)
async def unhandled(req:Request,exc:Exception):
    # No divulgar trazas ni datos internos al navegador. La excepción se registra en consola.
    if isinstance(exc,HTTPException):return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
    import logging
    logging.exception('Error inesperado atendiendo %s',req.url.path,exc_info=exc)
    return JSONResponse({'detail':'Error interno del servidor'},status_code=500)
