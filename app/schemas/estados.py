from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal


class EstatusAccionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo_accion: Optional[Literal["correctiva", "preventiva", "inmediata"]] = None
    estatus: Optional[Literal["abierto", "cerrado"]] = None
    observaciones: Optional[str] = None


class EstatusAccionOut(BaseModel):
    id: int
    plan_accion_accion_id: int
    tipo_accion: Optional[str] = None
    tipo_hallazgo: Optional[str] = None
    estatus: str
    observaciones: Optional[str] = None
    actualizado_por_id: Optional[int] = None
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True