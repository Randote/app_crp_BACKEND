from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuarios import Usuario
from app.auth.jwt_handler import decodificar_access_token

class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str:
        # 1. Intentar obtener el token de la cabecera Authorization
        authorization = request.headers.get("Authorization")
        if authorization:
            parts = authorization.split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        
        # 2. Si no está en la cabecera, buscarlo en la cookie 'access_token'
        token = request.cookies.get("access_token")
        if token:
            return token
            
        if self.auto_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    payload = decodificar_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    usuario = Usuario.obtener_por_id(db, int(payload["sub"]))
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")


    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está inactiva. Comunícate con el administrador."
        )

    return usuario

def get_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.cargo != 'Admin':
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user

