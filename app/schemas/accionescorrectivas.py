from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from app.schemas.ishikawa import IshikawaIn, IshikawaOut
from app.schemas.why5 import Analisis5PorquesIn, Analisis5PorquesOut
from app.schemas.planaccion import PlanAccionGrupoIn, PlanAccionGrupoOut


class AccionInmediataIn(BaseModel):
    accion: str
    fecha: date
    responsable: str
    estatus: str


class AccionCorrectivaCreate(BaseModel):
    fecha_deteccion: date
    proceso_afectado: str
    proceso_interaccion: Optional[str] = None
    dueno_proceso: str
    participantes: Optional[str] = None
    origen_deteccion: Optional[str] = None
    especificacion: Optional[str] = None
    problema_detectado: Optional[str] = None
    que_ocurre: Optional[str] = None
    tipo_hallazgo: Optional[str] = None 
    cuando_ocurre: Optional[str] = None
    donde_ocurre: Optional[str] = None
    usa_ishikawa: bool = False
    usa_5porques: bool = False
    acciones_inmediatas: list[AccionInmediataIn] = []
    ishikawa: Optional[IshikawaIn] = None
    analisis_5porques: list[Analisis5PorquesIn] = []
    plan_accion_grupos: list[PlanAccionGrupoIn] = []


class AccionCorrectivaOut(AccionCorrectivaCreate):
    id: int
    codificador: str
    creado_en: datetime
    ishikawa_analisis: Optional[IshikawaOut] = None
    analisis_5porques: list[Analisis5PorquesOut] = []
    plan_accion_grupos: list[PlanAccionGrupoOut] = []

    class Config:
        from_attributes = True

class AccionCorrectivaResumenOut(BaseModel):
    """Vista rápida para el dashboard básico."""
    id: int
    codificador: str
    origen_deteccion: Optional[str] = None
    proceso_afectado: str

    class Config:
        from_attributes = True
        
        
    
    
        
class AccionInmediataItem(BaseModel):
    accion: str
    fecha: date
    responsable: str
    estatus: str
 
 
class CausaIshikawaItem(BaseModel):
    texto: Optional[str] = None
    valor: Optional[int] = None
 
 
class IshikawaUpdateItem(BaseModel):
    problema_enfocado: Optional[str] = None
    mano_obra: list[CausaIshikawaItem] = []
    maquina: list[CausaIshikawaItem] = []
    material: list[CausaIshikawaItem] = []
    metodo: list[CausaIshikawaItem] = []
    medicion: list[CausaIshikawaItem] = []
    medio_ambiente: list[CausaIshikawaItem] = []
 
 
class PorqueItem(BaseModel):
    numero: int
    pregunta: Optional[str] = None
    respuesta: Optional[str] = None
    es_raiz: bool = False
 
 
class Analisis5PorquesItem(BaseModel):
    causa_potencial: str
    porques: list[PorqueItem]
 
 
class AccionCorrectivaUpdate(BaseModel):
    fecha_deteccion: date
    proceso_afectado: str
    proceso_interaccion: Optional[str] = None
    dueno_proceso: str
    participantes: Optional[str] = None
    origen_deteccion: Optional[str] = None
    especificacion: Optional[str] = None
    tipo_hallazgo: Optional[str] = None 
    problema_detectado: Optional[str] = None
    que_ocurre: Optional[str] = None
    cuando_ocurre: Optional[str] = None
    donde_ocurre: Optional[str] = None
    usa_ishikawa: bool = False
    usa_5porques: bool = False
 
    acciones_inmediatas: list[AccionInmediataItem] = []
    ishikawa: Optional[IshikawaUpdateItem] = None
    analisis_5porques: list[Analisis5PorquesItem] = []
    
    
class TipoHallazgoUpdate(BaseModel):
    tipo_hallazgo: Optional[str] = None