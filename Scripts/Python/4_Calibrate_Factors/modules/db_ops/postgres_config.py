from pydantic import BaseModel, Field, field_validator
import os

class PostgresConfig(BaseModel):
    username: str | None =  Field(description="Postgres username, if Not provided will use the environment variable: POSTGRES_USERNAME")
    password: str | None =  Field(description="Postgres password, if Not provided will use the environment variable: POSTGRES_PASSWORD")
    host: str | None =  Field(description="Postgres host, if Not provided will use the environment variable: POSTGRES_HOST")
    port: str | None =  Field(description="Postgres port, if Not provided will use the environment variable: POSTGRES_PORT")
    database: str | None =  Field(description="Postgres Database Name, if Not provided will use the environment variable: POSTGRES_DATABASE")
    # validates username
    @field_validator("username", mode="after")
    @classmethod
    def get_username(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_USERNAME"]
        except KeyError:
            return None
    @field_validator("password", mode="after")
    @classmethod
    def get_password(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_PASSWORD"]
            return v
        except KeyError:
            return None
    @field_validator("host", mode="after")
    @classmethod
    def get_host(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_HOST"]
            return v
        except KeyError:
            return None
    @field_validator("port", mode="after")
    @classmethod
    def get_port(cls, v) -> str:
        try:
            if not v:
                return os.environ["POSTGRES_PORT"]
            return v
        except KeyError:
            return None
    @field_validator("database", mode="after")
    @classmethod
    def get_db(cls, v) -> str:
        if not v:
            try:           
                return os.environ["POSTGRES_DATABASE"]
            except KeyError:
                return None            
        return v
