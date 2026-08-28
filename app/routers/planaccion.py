from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencias import get_current_user
from app.models.usuarios import Usuario
from app.models.bitacora import BitacoraEntrada
from app.database import get_db
from app.models.planaccion import PlanAccionAccion
from app.models.estados import EstatusAccion
from app.schemas.planaccion import PlanAccionAccionUpdate, PlanAccionAccionOut

router = APIRouter()
CAMPOS_ESTATUS = {"tipo_accion", "tipo_hallazgo", "estatus", "observaciones"}

@router.patch("/{accion_id}", response_model=PlanAccionAccionOut)
def actualizar_accion_plan(
    accion_id: int,
    payload: PlanAccionAccionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    accion = db.query(PlanAccionAccion).filter(PlanAccionAccion.id == accion_id).first()
    if not accion:
        raise HTTPException(status_code=404, detail="Acción no encontrada.")

    accion_correctiva_id = accion.grupo.accion_correctiva_id
    contexto = f' en la acción "{accion.descripcion[:40]}"' if accion.descripcion else ""

    data = payload.model_dump(exclude_unset=True)
    datos_estatus = {k: data.pop(k) for k in list(data) if k in CAMPOS_ESTATUS}

    # Campos planos de PlanAccionAccion
    for campo, valor in data.items():
        actual = getattr(accion, campo)
        if actual != valor:
            BitacoraEntrada.registrar_cambio(db, accion_correctiva_id, current_user, campo, contexto)
        setattr(accion, campo, valor)

    # Campos de EstatusAccion
    if datos_estatus:
        est = accion.estatus_accion
        if not est:
            est = EstatusAccion(plan_accion_accion_id=accion.id)
            db.add(est)
        for campo, valor in datos_estatus.items():
            actual = getattr(est, campo, None)
            if actual != valor:
                BitacoraEntrada.registrar_cambio(db, accion_correctiva_id, current_user, campo, contexto)
            setattr(est, campo, valor)

    db.commit()
    db.refresh(accion)
    return accion