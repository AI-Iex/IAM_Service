from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine

Base = declarative_base()

async def init_db(engine: AsyncEngine):
    # Import all modules that might define the models
    import app.models.user 
    import app.models.user_role 
    import app.models.role
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)