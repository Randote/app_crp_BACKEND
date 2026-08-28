from app.models.usuarios import Usuario
from app.schemas.usarios import UsuarioCreate, UsuarioResponse,UsuarioUpdateAdmin, UsuarioPerfilOut,CambiarPasswordAdminRequest
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth.dependencias import get_admin_user

router = APIRouter()

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    try:
        nuevo_usuario = Usuario.crear(db, **payload.model_dump())
        return nuevo_usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese usuario de red o correo."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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