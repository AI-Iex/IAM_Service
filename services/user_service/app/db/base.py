from sqlalchemy.orm import declarative_base

Base = declarative_base()

def init_db(engine):

    # Import all modules here that might define models so that
    import app.models.user 
    import app.models.user_role 
    import app.models.role
    Base.metadata.create_all(bind=engine)
