from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional


class CausaIshikawaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str
    valor: int

    @field_validator("texto")
    @classmethod
    def texto_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La causa no puede estar vacía.")
        return v.strip()

    # @field_validator("valor")
    # @classmethod
    # def valor_positivo(cls, v: int) -> int:
    #     if v <= 0:
    #         raise ValueError("El valor debe ser mayor a 0.")
    #     return v


class IshikawaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problema_enfocado: str

    mano_obra: list[CausaIshikawaIn] = []
    maquina: list[CausaIshikawaIn] = []
    material: list[CausaIshikawaIn] = []
    metodo: list[CausaIshikawaIn] = []
    medicion: list[CausaIshikawaIn] = []
    medio_ambiente: list[CausaIshikawaIn] = []

    @field_validator("problema_enfocado")
    @classmethod
    def problema_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El problema enfocado es obligatorio.")
        return v.strip()

    @field_validator(
        "mano_obra", "maquina", "material", "metodo", "medicion", "medio_ambiente"
    )
    @classmethod
    def al_menos_una_causa(cls, v: list, info) -> list:
        if len(v) == 0:
            raise ValueError(f"Debe agregar al menos una causa en '{info.field_name}'.")
        return v


class CausaIshikawaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria: str
    texto: Optional[str] = None
    valor: Optional[int] = None
    orden: int



class IshikawaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    problema_enfocado: Optional[str] = None
    causas: list[CausaIshikawaOut] = []
