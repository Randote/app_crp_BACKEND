from app.models.usuarios import Usuario
from app.schemas.usarios import UsuarioCreate, UsuarioResponse, UsuarioUpdateAdmin, UsuarioPerfilOut, CambiarPasswordAdminRequest
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth.dependencias import get_admin_user
from app.email.notifications import notify_usuario_registrado

router = APIRouter()

from app.email.notifications import notify_usuario_registrado

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        datos_payload = payload.model_dump()
        password_plano = datos_payload.get("password")
        
        nuevo_usuario = Usuario.crear(db, **datos_payload)

        url_login = "http://10.10.0.32/app_crp/"  
        await notify_usuario_registrado(
            destinatario_email=nuevo_usuario.email,
            nombre=f"{nuevo_usuario.nombre} {nuevo_usuario.apellido}",
            usuario_red=nuevo_usuario.usuario,
            password_temporal=password_plano,
            url_login=url_login
        )

        return nuevo_usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese usuario de red o correo."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios_para_notificaciones(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_user)
):
    usuarios = db.query(Usuario).all()
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioPerfilOut)
def obtener_usuario_admin(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_user)
):
    usuario = Usuario.obtener_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioPerfilOut)
def actualizar_usuario_admin(
    usuario_id: int,
    payload: UsuarioUpdateAdmin,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_user)
):
    usuario = Usuario.obtener_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    data = payload.model_dump(exclude_unset=True)
    return Usuario.actualizar(db, usuario.id, **data)


@router.patch("/{usuario_id}/password")
def cambiar_password_admin(
    usuario_id: int,
    payload: CambiarPasswordAdminRequest,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_user)
):
    usuario = Usuario.obtener_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    Usuario.actualizar(db, usuario.id, password=payload.password_nueva)
    return {"message": "Contraseña actualizada por administrador."}


@router.patch("/{usuario_id}/estatus")
def cambiar_estatus_usuario(
    usuario_id: int, 
    data: dict, 
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_admin_user)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.activo = data.get("activo", True)
    db.commit()
    db.refresh(usuario)
    return {"mensaje": "Estatus actualizado con éxito", "activo": usuario.activo}