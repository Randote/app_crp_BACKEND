from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from datetime import date
from sqlalchemy import func, case, and_
from app.models.planaccion import PlanAccionAccion
from app.models.estados import EstatusAccion
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.usuarios import Usuario
from app.models.sesiones import Sesion
from app.schemas.auth import LoginRequest, TokenResponse, AccessTokenResponse
from app.models.resetcontraseña import PasswordResetCode
from app.auth.jwt_handler import crear_access_token
from app.auth.dependencias import get_current_user 
from app.schemas.usarios import UsuarioUpdateSelf, CambiarPasswordRequest, UsuarioPerfilOut, UsuarioCardOut, UsuarioPublicoOut
from app.schemas.auth import OlvidePasswordRequest, RestablecerPasswordRequest
from app.email.notifications import notify_codigo_recuperacion


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
    current_user: Usuario = Depends(get_current_user)
):
    conteo = PlanAccionAccion.contar_actividades_responsable(db)
    mapa = {email: {"asignadas": a, "cerradas": c, "vencidas": v} for email, a, c, v in conteo}

    usuarios = Usuario.obtener_todos(db)

    resultado = []
    for u in usuarios:
        stats = mapa.get(u.email, {"asignadas": 0, "cerradas": 0, "vencidas": 0})
        resultado.append({
            "id": u.id,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "email": u.email,
            "cargo": u.cargo,
            "ficha": u.ficha,
            **stats
        })

    return resultado




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



#RESET DE CONTRASEÑA

@router.post("/olvide-password")
def olvide_password(
    payload: OlvidePasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    usuario = Usuario.obtener_por_email(db, payload.email)
 
    if usuario:
        _, codigo = PasswordResetCode.generar(db, usuario.id)
        print(f"CÓDIGO DE PRUEBA: {codigo}")
        background_tasks.add_task(
            notify_codigo_recuperacion,
            destinatario_email=usuario.email,
            nombre=usuario.nombre,
            codigo=codigo,
        )
 
    return {"detail": "Si el correo existe en el sistema, se envió un código de verificación."}
 
 
@router.post("/restablecer-password")
def restablecer_password(payload: RestablecerPasswordRequest, db: Session = Depends(get_db)):
    usuario = Usuario.obtener_por_email(db, payload.email)
    if not usuario:
        raise HTTPException(status_code=400, detail="Código inválido o expirado.")
 
    entrada = PasswordResetCode.verificar(db, usuario.id, payload.codigo)
    if not entrada:
        raise HTTPException(status_code=400, detail="Código inválido o expirado.")
 
    Usuario.actualizar(db, usuario.id, password=payload.password_nueva)
 
    db.delete(entrada)
 
    db.query(Sesion).filter(Sesion.usuario_id == usuario.id).delete()
    db.commit()
    return {"detail": "Contraseña actualizada correctamente."}