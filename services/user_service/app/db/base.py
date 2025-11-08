from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine

Base = declarative_base()

async def init_db(engine: AsyncEngine):
    
    """ Initialize the database by creating all tables defined in the models """

    import app.models.user 
    import app.models.user_role 
    import app.models.role
    import app.models.refresh_token
    import app.models.client
    import app.models.permission
    import app.models.role_permission
    import app.models.client_permission
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)