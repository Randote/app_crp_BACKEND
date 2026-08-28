from app.models.accionescorrectivas import AccionCorrectiva
from app.models.usuarios import Usuario
from app.schemas.accionescorrectivas import AccionCorrectivaCreate, AccionCorrectivaOut,AccionCorrectivaResumenOut,AccionCorrectivaUpdate
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth.dependencias import get_current_user

router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.email.notifications import notify_accion_registrada

router = APIRouter()


@router.post("/", response_model=AccionCorrectivaOut, status_code=status.HTTP_201_CREATED)
def registrar_accion_correctiva(
    payload: AccionCorrectivaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        data = payload.model_dump()
        acciones_inmediatas = data.pop("acciones_inmediatas", [])
        ishikawa = data.pop("ishikawa", None)
        analisis_5porques = data.pop("analisis_5porques", [])
        plan_accion_grupos = data.pop("plan_accion_grupos", [])

        nueva_accion = AccionCorrectiva.crear(
            db,
            acciones_inmediatas=acciones_inmediatas,
            ishikawa=ishikawa,
            analisis_5porques=analisis_5porques,
            plan_accion_grupos=plan_accion_grupos,
            **data
        )

        destinatarios = Usuario.obtener_todos_emails(db)

        background_tasks.add_task(
            notify_accion_registrada,
            destinatarios=destinatarios,
            codigo_accion=nueva_accion.codificador,
            area_responsable=nueva_accion.proceso_afectado,        
            origen_hallazgo=nueva_accion.origen_deteccion, 
            descripcion_hallazgo=nueva_accion.problema_detectado, 
            url_accion=f"http://10.10.0.32/app_crp/Matriz/{nueva_accion.codificador}"  ,
        )

        return nueva_accion

    except IntegrityError as e:
        db.rollback()
        mensaje = str(e.orig)
        if "codificador" in mensaje:
            detalle = "Ya existe una acción correctiva con ese codificador."
        elif "not-null constraint" in mensaje or "null value" in mensaje:
            detalle = f"Falta un campo obligatorio: {mensaje}"
        else:
            detalle = f"Error de integridad en la base de datos: {mensaje}"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detalle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resumen", response_model=list[AccionCorrectivaResumenOut])
def listar_resumen(db: Session = Depends(get_db)):
    return (
        db.query(AccionCorrectiva)
        .order_by(AccionCorrectiva.creado_en.desc())
        .all()
    )


@router.get("/{codificador}", response_model=AccionCorrectivaOut)
def obtener_accion_correctiva(codificador: str, db: Session = Depends(get_db)):
    accion = AccionCorrectiva.obtener_por_codificador(db, codificador)
    if not accion:
        raise HTTPException(status_code=404, detail="Acción correctiva no encontrada.")
    return accion



 
@router.put("/Actualizar/{codificador}", response_model=AccionCorrectivaOut)
def actualizar_accion_correctiva(
    codificador: str,
    payload: AccionCorrectivaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    accion = AccionCorrectiva.obtener_por_codificador(db, codificador)
    if not accion:
        raise HTTPException(status_code=404, detail="Acción correctiva no encontrada.")
 
    try:
        data = payload.model_dump()
        acciones_inmediatas = data.pop("acciones_inmediatas", [])
        ishikawa = data.pop("ishikawa", None)
        analisis_5porques = data.pop("analisis_5porques", [])
 
        accion.actualizar(
            db,
            acciones_inmediatas=acciones_inmediatas,
            ishikawa=ishikawa,
            analisis_5porques=analisis_5porques,
            usuario=current_user,
            **data
        )
        return accion
 
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
 