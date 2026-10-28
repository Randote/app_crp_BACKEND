from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class LoginRequest(BaseModel):
    usuario: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    apellido: str
    email: str
    cargo: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
    
    

#reset de contraseña

class OlvidePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class RestablecerPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    codigo: str
    password_nueva: str
    confirmar_password_nueva: str

    @field_validator("codigo")
    @classmethod
    def codigo_valido(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("El código debe tener 6 dígitos.")
        return v

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
