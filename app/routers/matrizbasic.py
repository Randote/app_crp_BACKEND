from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.accionescorrectivas import AccionCorrectiva
from app.models.planaccion import PlanAccionGrupo, PlanAccionAccion
from app.models.estados import EstatusAccion
from app.schemas.matrizbasic import AccionPlanOut,AccionesPorCodificadorOut
from sqlalchemy.orm import joinedload
from datetime import date


router = APIRouter()

@router.get("/acciones-detalle", response_model=list[AccionesPorCodificadorOut])
def listar_acciones_detalle(db: Session = Depends(get_db)):
    todas = (
        db.query(AccionCorrectiva)
        .join(AccionCorrectiva.plan_accion_grupos)
        .options(
            joinedload(AccionCorrectiva.plan_accion_grupos)
            .joinedload(PlanAccionGrupo.acciones)
            .joinedload(PlanAccionAccion.estatus_accion)
        )
        .all()
    )

    hoy = date.today()
    resultado = []

    for accion_correctiva in todas:
        acciones_planas = []
        for grupo in accion_correctiva.plan_accion_grupos:
            for accion in grupo.acciones:
                est = accion.estatus_accion
                estatus_real = (est.estatus if est else "abierto").lower()

                if estatus_real == "abierto" and accion.fecha and accion.fecha < hoy:
                    estatus_final = "vencido"
                else:
                    estatus_final = estatus_real

                acciones_planas.append({
                    "accion": accion.descripcion,
                    "responsable": accion.responsable,
                    "fecha": accion.fecha,
                    "estatus": estatus_final,
                })

        if acciones_planas:
            resultado.append({
                "codificador": accion_correctiva.codificador,
                "acciones": acciones_planas
            })

    return resultado
