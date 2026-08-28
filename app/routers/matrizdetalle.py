from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.planaccion import PlanAccionGrupo, PlanAccionAccion
from app.models.estados import EstatusAccion
from app.schemas.matrizdetalle import MatrizCompletaOut
from app.models.accionescorrectivas import AccionCorrectiva
from sqlalchemy.orm import joinedload
from datetime import date
router = APIRouter()




@router.get("/matriz-completa", response_model=list[MatrizCompletaOut])
def listar_matriz_completa(db: Session = Depends(get_db)):
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
    print(hoy)

    resultado = []
    for ac in todas:
        acciones_planas = []
        for grupo in ac.plan_accion_grupos:
            for accion in grupo.acciones:
                est = accion.estatus_accion
                estatus_real = est.estatus if est else "Abierto"

                if estatus_real == "Abierto" and accion.fecha and accion.fecha < hoy:
                    estatus_final = "Vencido"
                else:
                    estatus_final = estatus_real

                acciones_planas.append({
                    "accion": accion.descripcion,
                    "tipo_accion": est.tipo_accion if est else None,
                    "tipo_hallazgo": est.tipo_hallazgo if est else None,
                    "responsable": accion.responsable,
                    "fecha_cierre": accion.fecha,
                    "estatus": estatus_final,
                    "observaciones": est.observaciones if est else None,
                })

        if acciones_planas:
            resultado.append({
                "codificador": ac.codificador,
                "proceso_afectado": ac.proceso_afectado,
                "origen_deteccion": ac.origen_deteccion,
                "descripcion_hallazgo": ac.problema_detectado,
                "acciones": acciones_planas,
            })

    return resultado