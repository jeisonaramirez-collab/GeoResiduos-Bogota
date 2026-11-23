"""Servidor Flask compatible con la propuesta metodológica de la Fase 3.

Ejecutar: python -m flask --app flask_backend run --host 127.0.0.1 --port 8000
Comparte tablas y formato API con el servidor FastAPI verificado en las pruebas.
"""
import os
import io
import secrets
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, session, jsonify, send_from_directory, send_file
from pydantic import ValidationError
from sqlalchemy import select
from storage import ROOT, DATA_DIR, SessionLocal, Report, StatusChange, init_db, get_by_id, as_dict, seed_demo, STATUSES
from security import admin_ready, verify_admin
# Validaciones compartidas con la aplicación probada
from server import IncomingReport, encode_photo

app=Flask(__name__, static_folder=None)
if os.environ.get('RENDER'):
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app=ProxyFix(app.wsgi_app,x_proto=1,x_host=1)
key_file=DATA_DIR/'session_key.txt'
if os.environ.get('SESSION_SECRET'):
    app.secret_key=os.environ['SESSION_SECRET']
elif key_file.exists():
    app.secret_key=key_file.read_text().strip()
else:
    app.secret_key=secrets.token_urlsafe(48)
    key_file.write_text(app.secret_key, encoding='utf-8')
    try: os.chmod(key_file, 0o600)
    except OSError: pass
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','false').lower()=='true')
init_db()
if os.environ.get('LOAD_DEMO','').lower() in ('true','1','yes'):
    seed_demo()
failed_logins={}

def output(data, code=200):return jsonify(data),code

def require_csrf():
    from flask import abort
    origin=request.headers.get('Origin','').rstrip('/')
    if origin and origin!=request.host_url.rstrip('/'): abort(403,description='Origen no autorizado')
    token=session.get('csrf')
    if not token or not secrets.compare_digest(str(token),request.headers.get('X-CSRF-Token','')):
        abort(403,description='Token de seguridad inválido. Actualiza la página.')

def require_admin():
    from flask import abort
    require_csrf()
    if not session.get('admin'): abort(401,description='Se requiere iniciar sesión')

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(422)
@app.errorhandler(429)
@app.errorhandler(503)
def api_error(e): return output({'detail':e.description},e.code)

@app.get('/')
def homepage():return send_from_directory(str(ROOT/'static'),'index.html')
@app.get('/static/<path:name>')
def asset(name):return send_from_directory(str(ROOT/'static'),name)
@app.get('/uploads/<path:name>')
def picture(name):return send_from_directory(str(ROOT/'uploads'),name)
@app.get('/api/reports/<rid>/photo')
def photo_by_id(rid):
    from flask import abort
    with SessionLocal() as s:
        r=get_by_id(s,rid)
        if not r or not r.photo_data: abort(404,description='Fotografía no encontrada')
        return send_file(io.BytesIO(r.photo_data),mimetype='image/webp',max_age=300)
@app.get('/api/health')
def health():return output({'ok':True,'name':'GeoResiduos Bogotá','mode':'academic','database':'postgresql' if 'postgresql' in str(__import__('storage').engine.url) else 'sqlite'})
@app.get('/api/session')
def get_session():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return output({'admin':bool(session.get('admin')),'adminConfigured':admin_ready(),'csrf':session['csrf']})
@app.get('/api/reports')
def all_reports():
    with SessionLocal() as s:
        data=s.scalars(select(Report).order_by(Report.date.desc(),Report.pk.desc()).limit(2000)).all()
        return output({'items':[as_dict(r) for r in data],'count':len(data),'disclaimer':'Reportes no verificados; no son datos oficiales.'})
@app.get('/api/reports/<rid>')
def one_report(rid):
    from flask import abort
    with SessionLocal() as s:
        r=get_by_id(s,rid)
        if not r:abort(404,description='Reporte no encontrado')
        return output({'item':as_dict(r)})
@app.post('/api/reports')
def new_report():
    from flask import abort
    require_csrf()
    try: body=IncomingReport.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:return output({'detail':'; '.join(str(x['msg']) for x in e.errors())},422)
    try: photo=encode_photo(body.photo)
    except Exception as e:
        if hasattr(e,'status_code'):return output({'detail':getattr(e,'detail','Imagen inválida')},e.status_code)
        raise
    with SessionLocal() as s:
        obj=Report(description=body.description,category=body.category,locality=body.locality,date=body.date,
                   lat=body.lat,lng=body.lng,status='Pendiente',photo_data=photo,demo=False)
        try:s.add(obj);s.commit();s.refresh(obj)
        except Exception:
            s.rollback()
            raise
        return output({'item':as_dict(obj)},201)
@app.post('/api/admin/login')
def login():
    from flask import abort
    require_csrf()
    pwd=str((request.get_json(silent=True) or {}).get('password',''))
    ip=request.remote_addr or 'localhost'
    now=time.monotonic();timestamps=[t for t in failed_logins.get(ip,[]) if now-t<60]
    if len(timestamps)>=8:abort(429,description='Demasiados intentos; vuelve a intentarlo después')
    if not admin_ready():abort(503,description='Configura ADMIN_PASSWORD en el alojamiento o crea un administrador local')
    if not verify_admin(pwd):
        timestamps.append(now);failed_logins[ip]=timestamps
        abort(401,description='Contraseña incorrecta')
    session['admin']=True;failed_logins.pop(ip,None)
    return output({'admin':True})
@app.post('/api/admin/logout')
def logout():
    require_csrf();session.pop('admin',None)
    return output({'admin':False})
@app.patch('/api/admin/reports/<rid>')
def update(rid):
    from flask import abort
    require_admin()
    new=str((request.get_json(silent=True) or {}).get('status',''))
    if new not in STATUSES:return output({'detail':'Estado no permitido'},422)
    with SessionLocal() as s:
        r=get_by_id(s,rid)
        if not r:abort(404,description='Reporte no encontrado')
        if r.status!=new:
            s.add(StatusChange(report_pk=r.pk,old_status=r.status,new_status=new))
            r.status=new;s.commit();s.refresh(r)
        return output({'item':as_dict(r)})
@app.post('/api/admin/seed-demo')
def demos():
    require_admin();return output({'inserted':seed_demo()})
@app.get('/api/admin/audit')
def history():
    from flask import abort
    if not session.get('admin'):abort(401,description='Se requiere iniciar sesión')
    with SessionLocal() as s:
        rows=s.scalars(select(StatusChange).order_by(StatusChange.created_at.desc()).limit(100)).all()
        return output({'items':[{'report':f'RPT-{r.report_pk:06d}','previous':r.old_status,'new':r.new_status,'date':r.created_at.isoformat()} for r in rows]})
