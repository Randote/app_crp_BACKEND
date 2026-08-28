from pydantic import BaseModel
from datetime import date
from typing import Optional



class AccionMatrizOut(BaseModel):
    """Una acción individual, con todos los detalles para la matriz completa."""
    accion: str
    tipo_hallazgo: Optional[str] = None
    tipo_accion: Optional[str] = None
    responsable: Optional[str] = None
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