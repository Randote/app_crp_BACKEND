from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.accionescorrectivas import AccionCorrectiva
from app.models.bitacora import BitacoraEntrada
from app.schemas.bitacora import BitacoraEntradaOut, ComentarioCreate
from app.auth.dependencias import get_current_user
from app.models.usuarios import Usuario

router = APIRouter()

@router.get("/{codificador}", response_model=list[BitacoraEntradaOut])
def listar_bitacora(codificador: str, db: Session = Depends(get_db)):
    ac = AccionCorrectiva.obtener_por_codificador(db, codificador)
    if not ac:
        raise HTTPException(status_code=404, detail="No encontrado.")
    return (
        db.query(BitacoraEntrada)
        .filter(BitacoraEntrada.accion_correctiva_id == ac.id)
        .order_by(BitacoraEntrada.creado_en.asc())
        .all()
    )

@router.post("/{codificador}", response_model=BitacoraEntradaOut, status_code=201)
def agregar_comentario(
    codificador: str,
    payload: ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    ac = AccionCorrectiva.obtener_por_codificador(db, codificador)
    if not ac:
        raise HTTPException(status_code=404, detail="No encontrado.")
    if not payload.mensaje.strip():
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío.")
    return BitacoraEntrada.registrar_comentario(db, ac.id, current_user, payload.mensaje)