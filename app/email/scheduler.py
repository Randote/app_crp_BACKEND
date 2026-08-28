import logging
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
from app.database import SessionLocal
from app.email.notifications import notify_recordatorio_asignacion, notify_acciones_vencidas, notify_recordatorio_verificacion, notify_verificaciones_vencidas

logger = logging.getLogger("email")

# Tareas abiertas que AÚN NO vencen -> resumen semanal (lunes)
QUERY_RECORDATORIO = text("""
    SELECT pa.email, pa.responsable, pa.descripcion, pa.fecha, ac.codificador
    FROM plan_accion_acciones pa
    JOIN estatus_acciones ea ON ea.plan_accion_accion_id = pa.id
    JOIN plan_accion_grupos pg ON pg.id = pa.grupo_id
    JOIN acciones_correctivas ac ON ac.id = pg.accion_correctiva_id
    WHERE pa.fecha >= CURRENT_DATE
      AND ea.estatus = 'Abierto'
      AND pa.email IS NOT NULL AND pa.email <> ''
""")

# Tareas abiertas que YA vencieron -> aviso diario
QUERY_VENCIDAS = text("""
    SELECT pa.email, pa.responsable, pa.descripcion, pa.fecha, ac.codificador
    FROM plan_accion_acciones pa
    JOIN estatus_acciones ea ON ea.plan_accion_accion_id = pa.id
    JOIN plan_accion_grupos pg ON pg.id = pa.grupo_id
    JOIN acciones_correctivas ac ON ac.id = pg.accion_correctiva_id
    WHERE pa.fecha < CURRENT_DATE
      AND ea.estatus = 'Abierto'
      AND pa.email IS NOT NULL AND pa.email <> ''
""")


# Verificaciones abiertas que AÚN NO vencen -> resumen semanal (lunes)
QUERY_RECORDATORIO_VERIFICACION = text("""
    SELECT pa.metodologia_email AS email, pa.metodologia_responsable AS responsable,
           pa.metodologia_descripcion AS descripcion, pa.metodologia_fecha AS fecha, ac.codificador
    FROM plan_accion_acciones pa
    JOIN estatus_acciones ea ON ea.plan_accion_accion_id = pa.id
    JOIN plan_accion_grupos pg ON pg.id = pa.grupo_id
    JOIN acciones_correctivas ac ON ac.id = pg.accion_correctiva_id
    WHERE pa.metodologia_fecha >= CURRENT_DATE
      AND ea.estatus = 'Abierto'
      AND pa.metodologia_email IS NOT NULL AND pa.metodologia_email <> ''
""")

# Verificaciones abiertas que YA vencieron -> aviso diario
QUERY_VENCIDAS_VERIFICACION = text("""
    SELECT pa.metodologia_email AS email, pa.metodologia_responsable AS responsable,
           pa.metodologia_descripcion AS descripcion, pa.metodologia_fecha AS fecha, ac.codificador
    FROM plan_accion_acciones pa
    JOIN estatus_acciones ea ON ea.plan_accion_accion_id = pa.id
    JOIN plan_accion_grupos pg ON pg.id = pa.grupo_id
    JOIN acciones_correctivas ac ON ac.id = pg.accion_correctiva_id
    WHERE pa.metodologia_fecha < CURRENT_DATE
      AND ea.estatus = 'Abierto'
      AND pa.metodologia_email IS NOT NULL AND pa.metodologia_email <> ''
""")


def _agrupar_por_email(filas):
    """Agrupa filas del query por email para mandar un solo correo por persona."""
    grupos = defaultdict(list)
    for fila in filas:
        grupos[fila.email].append({
            "responsable": fila.responsable,
            "descripcion": fila.descripcion,
            "fecha": str(fila.fecha),
            "codificador": fila.codificador,
        })
    return grupos

async def job_recordatorio_asignacion():
    """Corre los lunes: resumen de tareas abiertas que todavía no vencen."""
    db = SessionLocal()
    try:
        filas = db.execute(QUERY_RECORDATORIO).fetchall()
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_recordatorio_asignacion(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
        logger.info(f"[scheduler] job_recordatorio_asignacion: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_recordatorio_asignacion: {e}")
    finally:
        db.close()


async def job_avisos_vencidos():
    """Corre todos los días: aviso de tareas abiertas ya vencidas."""
    db = SessionLocal()
    try:
        filas = db.execute(QUERY_VENCIDAS).fetchall()
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_acciones_vencidas(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
        logger.info(f"[scheduler] job_avisos_vencidos: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_avisos_vencidos: {e}")
    finally:
        db.close()


async def job_recordatorio_verificacion():
    """Corre los lunes: resumen para VERIFICADORES de tareas que aún no vencen."""
    db = SessionLocal()
    try:
        filas = db.execute(QUERY_RECORDATORIO_VERIFICACION).fetchall()
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_recordatorio_verificacion(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
        logger.info(f"[scheduler] job_recordatorio_verificacion: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_recordatorio_verificacion: {e}")
    finally:
        db.close()


async def job_verificaciones_vencidas():
    """Corre todos los días: aviso para VERIFICADORES de tareas ya vencidas."""
    db = SessionLocal()
    try:
        filas = db.execute(QUERY_VENCIDAS_VERIFICACION).fetchall()
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_verificaciones_vencidas(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
        logger.info(f"[scheduler] job_verificaciones_vencidas: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_verificaciones_vencidas: {e}")
    finally:
        db.close()


scheduler = AsyncIOScheduler()



def iniciar_scheduler():
    scheduler.add_job(
        job_recordatorio_asignacion,
        CronTrigger(day_of_week="mon", hour=6, minute=0),
        id="recordatorio_asignacion",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_avisos_vencidos,
        CronTrigger(hour=6, minute=0),
        id="avisos_vencidos",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_recordatorio_verificacion,
        CronTrigger(day_of_week="mon", hour=6, minute=0),
        id="recordatorio_verificacion",
        replace_existing=True,
        misfire_grace_time=3,
    )
    
    scheduler.add_job(
        job_verificaciones_vencidas,
        CronTrigger(hour=6, minute=0),
        id="verificaciones_vencidas",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.start()
    logger.info("[scheduler] Iniciado — recordatorio: lunes 6:00am | vencidas: diario 6:00am")