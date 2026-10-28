from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.accionescorrectivas import AccionCorrectiva
from app.models.planaccion import PlanAccionAccion
from app.models.estados import EstatusAccion
from datetime import datetime, date



router = APIRouter()

PROCESOS = [
    'Dirección Estratégica (GGG)',
    'Gestión de Negocios (GNE)',
    'Gestión de Control de Producción (GCP)',
    'Gestión de Producción (GPR)',
    'Gestión de Logística de Salida (GLS)',
    'Gestión de diseño y desarrollo de productos (GDP)',
    'Gestión de Compras (GCO)',
    'Gestión de Control De Calidad (GCC)',
    'Gestión de Logística de Entrada (GLE)',
    'Gestión de Calidad (GCA)',
    'Gestión de Finanzas (GFI)',
    'Gestión de Mantenimiento (GMT)',
    'Gestión de TI(GTI)',
    'Gestión de Seguridad y Salud en el Trabajo (GSL)',
    'Gestión de Proyectos (GPY)',
    'Gestión de Personal (GPE)',
    'Gestión de Talento Humano (GTH)',
]

ORIGENES = [
    'Auditoria Proceso/Producto',
    'Quejas y Reclamos',
    'Auditoria Interna',
    'Auditoria Externa',
    'Indicadores',
    'Otros'
]


MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TIPOS_ACCION = ["Preventiva", "Inmediata", "Correctiva"]
TIPOS_HALLAZGO = ["No Conforme", "Oportunidad de Mejora", "Observacion"]


def _armar_series(resultados, categorias):
    matriz = {cat: [0] * 12 for cat in categorias}

    for mes, valor, cantidad in resultados:
        if valor in matriz:
            matriz[valor][int(mes) - 1] = cantidad

    return {
        "meses": MESES,
        "series": [{"tipo": cat, "data": matriz[cat]} for cat in categorias]
    }
    
    

@router.get("/dashboard")
def obtener_indicadores(db: Session = Depends(get_db)):
    total_procesos = AccionCorrectiva.contar_total(db)
    conteo = PlanAccionAccion.contar_por_estado(db)
    total_acciones = PlanAccionAccion.contar_total(db)

    return {
        "total_procesos": total_procesos,
        "total_acciones": total_acciones,
        "abiertas": conteo.abiertas,
        "cerradas": conteo.cerradas,
        "vencidas": conteo.vencidas,
    }
    
    

@router.get("/indicadores/proceso-afectado")
def obtener_proceso_afectado(db: Session = Depends(get_db)):
    conteo = AccionCorrectiva.contar_por_proceso_afectado(db)
    total = sum(conteo.values()) or 1
    data = [
        {
            "proceso": proceso,
            "cantidad": conteo.get(proceso, 0),
            "porcentaje": round((conteo.get(proceso, 0) / total) * 100, 1),
        }
        for proceso in PROCESOS
    ]
    data.sort(key=lambda x: x["cantidad"], reverse=True)

    return {"total": total, "procesos": data}





@router.get("/indicadores/origen-deteccion")
def obtener_origen_deteccion(db: Session = Depends(get_db)):
    conteo = AccionCorrectiva.contar_por_origen_deteccion(db)
    total = sum(conteo.values()) or 1

    data = [
        {
            "origen": origen,
            "cantidad": conteo.get(origen, 0),
            "porcentaje": round((conteo.get(origen, 0) / total) * 100, 1),
        }
        for origen in ORIGENES
    ]
    data.sort(key=lambda x: x["cantidad"], reverse=True)

    return {"total": total, "origenes": data}


@router.get("/indicadores/acciones-por-tipo")
def acciones_por_tipo(anio: int = datetime.now().year, db: Session = Depends(get_db)):
    resultados = EstatusAccion.contar_por_mes_y_campo(db, "tipo_accion", anio)
    return _armar_series(resultados, TIPOS_ACCION)


@router.get("/indicadores/hallazgos-por-tipo")
def hallazgos_por_tipo(anio: int = datetime.now().year, db: Session = Depends(get_db)):
    resultados = AccionCorrectiva.contar_por_mes_tipo_hallazgo(db, anio)
    return _armar_series(resultados, TIPOS_HALLAZGO)



@router.get("/indicadores/no-conformidades-por-proceso")
def no_conformidades_por_proceso(
    solo_abiertas: bool = False,
    db: Session = Depends(get_db)
):
    conteo = EstatusAccion.contar_no_conformidades_por_proceso(db, solo_abiertas=solo_abiertas)
    total = sum(conteo.values()) or 1

    data = [
        {
            "proceso": proceso,
            "cantidad": conteo.get(proceso, 0),
            "porcentaje": round((conteo.get(proceso, 0) / total) * 100, 1),
        }
        for proceso in PROCESOS
    ]
    data.sort(key=lambda x: x["cantidad"], reverse=True)

    return {"total": total, "procesos": data}

@router.get("/indicadores/no-conformidades-por-proceso/detalle")
def detalle_no_conformidades(proceso: str, db: Session = Depends(get_db)):
    resultados = EstatusAccion.detalle_no_conformidades_por_proceso(db, proceso)
    hoy = date.today()

    detalle = []
    for codificador, descripcion, fecha in resultados:
        dias_vencido = (hoy - fecha).days if fecha and fecha < hoy else 0
        detalle.append({
            "codificador": codificador,
            "descripcion": descripcion,
            "fecha": fecha.isoformat() if fecha else None,
            "dias_vencido": dias_vencido,
        })

    return {"proceso": proceso, "acciones": detalle}