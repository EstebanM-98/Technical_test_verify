from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str
