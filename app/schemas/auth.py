from pydantic import BaseModel

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
    


