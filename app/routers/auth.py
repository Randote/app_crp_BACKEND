from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.usuarios import Usuario
from app.models.sesiones import Sesion
from app.schemas.auth import LoginRequest, TokenResponse, AccessTokenResponse
from app.auth.jwt_handler import crear_access_token
from app.auth.dependencias import get_current_user 
from app.schemas.usarios import UsuarioUpdateSelf, CambiarPasswordRequest, UsuarioPerfilOut, UsuarioCardOut, UsuarioPublicoOut


router = APIRouter()

REFRESH_COOKIE_PATH = "/"
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 4

def set_refresh_cookie(response: Response, valor: str):
    response.set_cookie(
        key="refresh_token",
        value=valor,
        httponly=True,
        secure=False,  # True en prod con HTTPS
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        max_age=REFRESH_COOKIE_MAX_AGE
    )

#POST
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    usuario = Usuario.obtener_por_usuario(db, payload.usuario)
    if not usuario or not usuario.verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    sesion, refresh_plano = Sesion.crear(
        db,
        usuario_id=usuario.id,
        user_agent=request.headers.get("user-agent", "")
    )

    access_token = crear_access_token({"sub": str(usuario.id)})

    set_refresh_cookie(response,refresh_plano )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "cargo": usuario.cargo
    }


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No hay sesión activa")

    sesion = Sesion.obtener_valida_por_token(db, refresh_token)
    if not sesion:
        Sesion.eliminar_si_expirada(db, refresh_token)
        raise HTTPException(status_code=401, detail="Sesión expirada, vuelve a iniciar sesión")

    usuario_id = sesion.usuario_id
    sesion.eliminar(db)
    nueva_sesion, nuevo_refresh_plano = Sesion.crear(db, usuario_id=usuario_id, user_agent=request.headers.get("user-agent", ""))

    access_token = crear_access_token({"sub": str(usuario_id)})

    set_refresh_cookie(response, nuevo_refresh_plano)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        sesion = Sesion.obtener_valida_por_token(db, refresh_token)
        if sesion:
            sesion.eliminar(db)

    response.delete_cookie(key="refresh_token", path=REFRESH_COOKIE_PATH)
    return {"message": "Sesión cerrada"}




#GET
@router.get("/me", response_model=UsuarioPerfilOut)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user

@router.get("/usuarios/publico", response_model=List[UsuarioPublicoOut])
def listar_usuarios_publico(db: Session = Depends(get_db)):
    return Usuario.obtener_todos(db)

@router.get("/usuarios", response_model=List[UsuarioCardOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  # protegido, solo usuarios logueados
):
    return Usuario.obtener_todos(db)




#PACHT
@router.patch("/me", response_model=UsuarioPerfilOut)
def actualizar_mi_perfil(
    payload: UsuarioUpdateSelf,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = payload.model_dump(exclude_unset=True)
    return Usuario.actualizar(db, current_user.id, **data)


@router.patch("/me/password")
def cambiar_mi_password(
    payload: CambiarPasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.verify_password(payload.password_actual):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta.")

    Usuario.actualizar(db, current_user.id, password=payload.password_nueva)
    return {"message": "Contraseña actualizada."}