from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional


class PorqueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    numero: int  # 1 al 5
    pregunta: Optional[str] = None
    respuesta: Optional[str] = None
    es_raiz: bool = False

class Analisis5PorquesIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    causa_potencial: str
    porques: list[PorqueIn]

    @field_validator("causa_potencial")
    @classmethod
    def causa_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La causa potencial no puede estar vacía.")
        return v.strip()

    @field_validator("porques")
    @classmethod
    def maximo_cinco(cls, v: list) -> list:
        if len(v) > 5:
            raise ValueError("Cada causa potencial no puede tener más de 5 porqués.")
        return v


class PorqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: int
    pregunta: Optional[str] = None
    respuesta: Optional[str] = None
    es_raiz: bool




class Analisis5PorquesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    causa_potencial: str
    orden: int
    porques: list[PorqueOut] = []