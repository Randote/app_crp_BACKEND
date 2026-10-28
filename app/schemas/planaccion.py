from pydantic import BaseModel, field_validator, ConfigDict
from datetime import date
from typing import Optional
from app.schemas.estados import EstatusAccionOut


class ResponsableIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    nombre: Optional[str] = None
    email: Optional[str] = None
    proceso: Optional[str] = None
 
 
class ResponsableOut(BaseModel):
    id: int
    nombre: Optional[str] = None
    email: Optional[str] = None
    proceso: Optional[str] = None
    orden: int
 
    class Config:
        from_attributes = True
 

class PlanAccionAccionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    descripcion: str
    fecha: Optional[date] = None
    responsables: list[ResponsableIn] = []
    metodologia_descripcion: Optional[str] = None
    metodologia_fecha: Optional[date] = None
    metodologia_responsable: Optional[str] = None
    metodologia_email: Optional[str] = None
 
    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La descripción de la acción es obligatoria.")
        return v.strip()
    

    @field_validator("fecha", "metodologia_fecha", mode="before")
    @classmethod
    def vacio_a_none(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        return v


class PlanAccionGrupoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
 
    causa_raiz_numero: Optional[int] = None
    acciones: list[PlanAccionAccionIn]
 
    @field_validator("acciones")
    @classmethod
    def al_menos_una_accion(cls, v: list) -> list:
        if len(v) == 0:
            raise ValueError("Cada grupo debe tener al menos una acción.")
        return v
 
 
class PlanAccionAccionOut(BaseModel):
    id: int
    descripcion: str
    fecha: Optional[date] = None
    responsables: list[ResponsableOut] = []
    metodologia_descripcion: Optional[str] = None
    metodologia_fecha: Optional[date] = None
    metodologia_responsable: Optional[str] = None
    metodologia_email: Optional[str] = None
    orden: int
    estatus_accion: Optional["EstatusAccionOut"] = None

    class Config:
        from_attributes = True
 
 
class PlanAccionGrupoOut(BaseModel):
    id: int
    causa_raiz_numero: Optional[int] = None
    orden: int
    acciones: list[PlanAccionAccionOut] = []
    class Config:
        from_attributes = True


class PlanAccionAccionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    responsables: Optional[list[ResponsableIn]] = None
    metodologia_descripcion: Optional[str] = None
    metodologia_fecha: Optional[date] = None
    metodologia_responsable: Optional[str] = None
    metodologia_email: Optional[str] = None
    tipo_accion: Optional[str] = None
    estatus: Optional[str] = None
    observaciones: Optional[str] = None