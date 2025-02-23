from pydantic import BaseModel, Field, field_validator
from typing import Optional
import os

class PostgresConfig(BaseModel):
    username: Optional[str] =  Field(description="Postgres username, if Not provided will use the environment variable: POSTGRES_USERNAME")
    password: Optional[str] =  Field(description="Postgres password, if Not provided will use the environment variable: POSTGRES_PASSWORD")
    host: Optional[str] =  Field(description="Postgres host, if Not provided will use the environment variable: POSTGRES_HOST")
    port: Optional[str] =  Field(description="Postgres port, if Not provided will use the environment variable: POSTGRES_PORT")
    database: Optional[str] =  Field(description="Postgres Database Name, if Not provided will use the environment variable: POSTGRES_DATABASE")
    # validates username
    @field_validator("username", mode="after")
    @classmethod
    def get_username(cls, v) -> int:
        try:
            if not v:
                return os.environ["POSTGRES_USERNAME"]
        except KeyError:
            return None
    @field_validator("password", mode="after")
    @classmethod
    def get_username(cls, v) -> int:
        try:
            if not v:
                return os.environ["POSTGRES_PASSWORD"]
        except KeyError:
            return None
    @field_validator("host", mode="after")
    @classmethod
    def get_host(cls, v) -> int:
        try:
            if not v:
                return os.environ["POSTGRES_HOST"]
        except KeyError:
            return None
    @field_validator("port", mode="after")
    @classmethod
    def get_port(cls, v) -> int:
        try:
            if not v:
                return os.environ["POSTGRES_PORT"]
        except KeyError:
            return None
    @field_validator("database", mode="after")
    @classmethod
    def get_db(cls, v) -> int:
        try:
            if not v:
                return os.environ["POSTGRES_DATABASE"]
        except KeyError:
            return None
