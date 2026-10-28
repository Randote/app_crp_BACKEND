from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.procesosupervisor import ProcesoSupervisor  
from app.auth.dependencias import get_admin_user

router = APIRouter()


class EstatusUpdate(BaseModel):
    activo: bool

@router.get("/")
def listar_supervisores(db: Session = Depends(get_db), current_user = Depends(get_admin_user)):
    return ProcesoSupervisor.obtener_todos(db)

@router.patch("/{supervisor_id}/estatus")
def actualizar_estatus_supervisor(
    supervisor_id: int, 
    payload: EstatusUpdate, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_admin_user)
):
    supervisor = ProcesoSupervisor.obtener_por_id(db, supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor no encontrado")
    
    supervisor.activo = payload.activo
    db.commit()
    db.refresh(supervisor)
    
    return {"mensaje": "Estatus actualizado con éxito", "activo": supervisor.activo}