from pydantic import BaseModel
from datetime import date
from typing import Optional


class AccionPlanOut(BaseModel):
    """Una acción individual dentro del grupo de un codificador."""
    accion: str
    responsable: Optional[str] = None
    fecha: Optional[date] = None
    estatus: str

    class Config:
        from_attributes = True


class AccionesPorCodificadorOut(BaseModel):
    """Un codificador con todas sus acciones agrupadas."""
    codificador: str
    acciones: list[AccionPlanOut]