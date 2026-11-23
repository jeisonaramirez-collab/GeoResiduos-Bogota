"""Persistencia de GeoResiduos. SQLite local o PostgreSQL mediante DATABASE_URL."""
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, LargeBinary, create_engine, select, func
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('GEORESIDUOS_DATA_DIR', str(ROOT / 'data')))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_URL = f"sqlite:///{(DATA_DIR / 'georesiduos.db').as_posix()}"
DATABASE_URL = os.environ.get('DATABASE_URL', DEFAULT_URL)
if os.environ.get('RENDER') and not os.environ.get('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL es obligatoria en Render para evitar pérdida de reportes.')
# Render / Heroku antiguos: postgres:// -> postgresql+psycopg://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite:') else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

CATEGORIES = ['Residuos ordinarios', 'Escombros (RCD)', 'Residuos voluminosos', 'Residuos mixtos', 'Otros']
STATUSES = ['Pendiente', 'En revisión', 'Cerrado']
LOCALITIES = ['Antonio Nariño','Barrios Unidos','Bosa','Chapinero','Ciudad Bolívar','Engativá','Fontibón','Kennedy','La Candelaria','Los Mártires','Puente Aranda','Rafael Uribe Uribe','San Cristóbal','Santa Fe','Suba','Sumapaz','Teusaquillo','Tunjuelito','Usaquén','Usme']

class Report(Base):
    __tablename__ = 'reports'
    pk = Column(Integer, primary_key=True)
    description = Column(String(500), nullable=False)
    category = Column(String(70), nullable=False)
    locality = Column(String(80), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='Pendiente')
    photo_file = Column(String(130), nullable=True)
    photo_data = Column(LargeBinary, nullable=True)  # Fotografía WEBP en base de datos (disco web efímero)
    demo = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

class StatusChange(Base):
    __tablename__ = 'status_changes'
    pk = Column(Integer, primary_key=True)
    report_pk = Column(Integer, ForeignKey('reports.pk'), nullable=False)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(bind=engine)

def as_dict(r):
    return dict(id=f'RPT-{r.pk:06d}', description=r.description,category=r.category,locality=r.locality,
                lat=r.lat,lng=r.lng,date=r.date.isoformat(),status=r.status,demo=r.demo,
                photo=(f'/api/reports/RPT-{r.pk:06d}/photo' if r.photo_data else (f'/uploads/{r.photo_file}' if r.photo_file else None)))

def get_by_id(s,code):
    match = re.fullmatch(r'RPT-(\d{6,})',str(code or ''))
    if not match: return None
    return s.get(Report,int(match.group(1)))

DEMO_ROWS = [
    ('Bolsas y residuos domésticos acumulados junto al andén (dato de ejemplo).','Residuos ordinarios','Suba',4.7434,-74.0873,'2026-10-11'),
    ('Materiales de construcción depositados en espacio abierto (dato de ejemplo).','Escombros (RCD)','Kennedy',4.6215,-74.1542,'2026-10-10'),
    ('Muebles y objetos de gran tamaño en zona peatonal (dato de ejemplo).','Residuos voluminosos','Chapinero',4.6527,-74.0632,'2026-10-09'),
    ('Acumulación de diferentes tipos de residuos en la vía (dato de ejemplo).','Residuos mixtos','Fontibón',4.6782,-74.1447,'2026-10-08'),
    ('Bolsas abandonadas sobre el separador vial (dato de ejemplo).','Residuos ordinarios','Teusaquillo',4.6364,-74.0837,'2026-10-07'),
    ('Restos de obra depositados cerca de un sendero (dato de ejemplo).','Escombros (RCD)','Bosa',4.6063,-74.1909,'2026-10-06'),
    ('Residuos variados en un sector del espacio público (dato de ejemplo).','Residuos mixtos','Usaquén',4.7048,-74.0398,'2026-10-05'),
    ('Acumulación de bolsas con residuos junto a la calzada (dato de ejemplo).','Residuos ordinarios','San Cristóbal',4.5679,-74.0835,'2026-10-04')]

def seed_demo():
    with SessionLocal() as s:
        if s.scalar(select(func.count(Report.pk)).where(Report.demo.is_(True))): return 0
        for i,row in enumerate(DEMO_ROWS):
            s.add(Report(description=row[0],category=row[1],locality=row[2],lat=row[3],lng=row[4],date=__import__('datetime').date.fromisoformat(row[5]),status=['Pendiente','En revisión','Pendiente','En revisión','Cerrado','Pendiente','Cerrado','Pendiente'][i],demo=True))
        s.commit()
        return len(DEMO_ROWS)
