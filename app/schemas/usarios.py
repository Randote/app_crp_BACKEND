from pydantic import BaseModel, EmailStr, Field,ConfigDict,field_validator
from typing import Optional, List
from datetime import datetime

class UsuarioBase(BaseModel):
    ficha: str
    nombre: str
    apellido: str
    usuario: str
    email: EmailStr  
    cargo: str
    permisos: List[str] = []  


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Mínimo 6  caracteres")

class UsuarioResponse(UsuarioBase):
    id: int
    creado_en: datetime
    activo: bool

    class Config:
        from_attributes = True  
        
class UsuarioPerfilOut(BaseModel):
    id: int
    usuario: str
    nombre: str
    apellido: str
    email: str
    cargo: str
    ficha: int
    permisos: list[str]

    class Config:
        from_attributes = True


class UsuarioCardOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    cargo: str
    email: str
    ficha: int
    asignadas: int = 0
    cerradas: int = 0
    vencidas: int = 0

    class Config:
        from_attributes = True

    
class UsuarioUpdateSelf(BaseModel):
    """Lo que un usuario puede cambiar de sí mismo — sin ficha ni permisos."""
    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None


class CambiarPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password_actual: str
    password_nueva: str
    confirmar_password_nueva: str

    @field_validator("password_nueva")
    @classmethod
    def password_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres.")
        return v

    @field_validator("confirmar_password_nueva")
    @classmethod
    def coinciden(cls, v: str, info) -> str:
        if "password_nueva" in info.data and v != info.data["password_nueva"]:
            raise ValueError("Las contraseñas nuevas no coinciden.")
        return v


PERMISOS_VALIDOS = {"noConformidades", "causaRaiz", "planesAccion", "efectividad"}  

class UsuarioUpdateAdmin(BaseModel):
    """Lo que un admin puede cambiar de OTRO usuario — todo, incluida ficha y permisos."""
    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    ficha: Optional[int] = None
    cargo: Optional[str] = None
    permisos: Optional[list[str]] = None



    @field_validator("permisos")
    @classmethod
    def permisos_validos(cls, v):
        if v is None:
            return v
        invalidos = set(v) - PERMISOS_VALIDOS
        if invalidos:
            raise ValueError(f"Permisos no válidos: {', '.join(invalidos)}")
        return v



class CambiarPasswordAdminRequest(BaseModel):
    password_nueva: str
    confirmar_password_nueva: str

    @field_validator("password_nueva")
    @classmethod
    def password_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres.")
        return v

    @field_validator("confirmar_password_nueva")
    @classmethod
    def coinciden(cls, v: str, info) -> str:
        if "password_nueva" in info.data and v != info.data["password_nueva"]:
            raise ValueError("Las contraseñas nuevas no coinciden.")
        return v
    
    
    
class UsuarioPublicoOut(BaseModel):
    nombre: str
    apellido: str
    email: str

    class Config:
        from_attributes = True