from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencias import get_current_user
from app.models.usuarios import Usuario
from app.models.bitacora import BitacoraEntrada
from app.database import get_db
from app.models.planaccion import PlanAccionAccion, PlanAccionResponsable
from app.models.estados import EstatusAccion
from app.schemas.planaccion import PlanAccionAccionUpdate, PlanAccionAccionOut

router = APIRouter()
CAMPOS_ESTATUS = {"tipo_accion", "estatus", "observaciones"}


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
    responsables_data = data.pop("responsables", None)
    datos_estatus = {k: data.pop(k) for k in list(data) if k in CAMPOS_ESTATUS}

    for campo, valor in data.items():
        actual = getattr(accion, campo)
        if actual != valor:
            BitacoraEntrada.registrar_cambio(db, accion_correctiva_id, current_user, campo, contexto)
        setattr(accion, campo, valor)

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
            

    if responsables_data is not None:
        actuales = [(r.nombre, r.email, r.proceso) for r in accion.responsables]
        nuevos = [(r.get("nombre"), r.get("email"), r.get("proceso")) for r in responsables_data]

        if actuales != nuevos:
            BitacoraEntrada.registrar_cambio(db, accion_correctiva_id, current_user, "responsables", contexto)

        for r in list(accion.responsables):
            db.delete(r)
        db.flush()

        for r in responsables_data:
            db.add(PlanAccionResponsable(
                plan_accion_accion_id=accion.id,
                nombre=r.get("nombre"),
                email=r.get("email"),
                proceso=r.get("proceso"),
            ))

    db.commit()
    db.refresh(accion)
    return accion