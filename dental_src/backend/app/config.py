from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url:str='postgresql+psycopg://postgres:postgres@localhost:5432/dental_hospital'
    jwt_secret:str='CHANGE_THIS_IN_PRODUCTION_TO_A_LONG_RANDOM_SECRET'
    cors_origins:str='http://localhost:5500,http://127.0.0.1:5500'
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
