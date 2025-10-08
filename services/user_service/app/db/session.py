from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear el motor de conexión (SQLAlchemy Engine)
engine = create_engine(settings.DATABASE_URL)

# Crear una factoría de sesiones para interactuar con la BBDD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia de FastAPI para obtener una sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
