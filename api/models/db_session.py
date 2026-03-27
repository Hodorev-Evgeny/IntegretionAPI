import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy_utils import database_exists, create_database


load_dotenv()
settings = {
    'pguser': os.getenv("PGUSER"),
    'password': os.getenv("PASSWORD"),
    'host': os.getenv("HOST"),
    'port': os.getenv("PORT"),
    'pgdatabase': os.getenv("PGDATABASE"),
}



def get_engine(user:str, password:str, host:str, port:int, database:str):
    pgQuery = 'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}'.format(
        user=user, password=password, host=host, port=port, db=database
    )

    nrurl = pgQuery.replace('+asyncpg', '')
    if not database_exists(nrurl):
        create_database(nrurl)

    engine = create_async_engine(pgQuery)
    return engine

def get_settings_from_engine():
    keys = ['pguser', 'password', 'host', 'port', 'pgdatabase']
    if not all(key in keys for key in settings):
        raise 'Not correct settings'

    return get_engine(settings['pguser'],
                      settings['password'],
                      settings['host'],
                      settings['port'],
                      settings['pgdatabase'])

def get_session():
    engine = get_settings_from_engine()
    return async_sessionmaker(engine, expire_on_commit=False)
