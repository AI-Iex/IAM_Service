from sqlalchemy.orm import declarative_base

# Clase base de todos los modelos SQLAlchemy
Base = declarative_base()

def init_db(engine):
    """
    Crea las tablas en la base de datos a partir de los modelos importados.
    """
    # import app.models.user  # importa tus modelos aquí
    Base.metadata.create_all(bind=engine)
