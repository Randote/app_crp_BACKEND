from pydantic import BaseModel
from datetime import date
from typing import Optional



class AccionMatrizOut(BaseModel):
    accion: str
    tipo_accion: Optional[str] = None
    tipo_hallazgo: Optional[str] = None
    responsables: list[str] = []  
    fecha_cierre: Optional[date] = None
    estatus: str
    observaciones: Optional[str] = None
 
    class Config:
        from_attributes = True


class MatrizCompletaOut(BaseModel):
    """Un codificador con el encabezado del hallazgo + todas sus acciones."""
    codificador: str
    proceso_afectado: str
    origen_deteccion: Optional[str] = None
    descripcion_hallazgo: Optional[str] = None 
    acciones: list[AccionMatrizOut]