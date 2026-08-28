from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuarios import Usuario
from app.auth.jwt_handler import decodificar_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    payload = decodificar_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    usuario = Usuario.obtener_por_id(db, int(payload["sub"]))
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return usuario

def get_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.cargo !='Admin':
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    return current_user