from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BitacoraEntradaOut(BaseModel):
    id: int
    tipo: str
    mensaje: str
    usuario_nombre: str
    creado_en: datetime

    class Config:
        from_attributes = True

class ComentarioCreate(BaseModel):
    mensaje: str