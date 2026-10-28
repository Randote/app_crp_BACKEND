import logging
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
import asyncio 
from app.models.planaccion import PlanAccionAccion
from app.email.notifications import (
    notify_recordatorio_asignacion,
    notify_acciones_vencidas,
    notify_recordatorio_verificacion,
    notify_verificaciones_vencidas,
    notify_supervisor_acciones_vencidas
)

logger = logging.getLogger("email")
scheduler = AsyncIOScheduler()


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
        filas = PlanAccionAccion.obtener_para_notificaciones(db, vencidas=False)
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
        filas = PlanAccionAccion.obtener_para_notificaciones(db, vencidas=True)
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_acciones_vencidas(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
            await asyncio.sleep(1)
        logger.info(f"[scheduler] job_avisos_vencidos: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_avisos_vencidos: {e}")
    finally:
        db.close()


async def job_recordatorio_verificacion():
    """Corre los lunes: resumen para VERIFICADORES de tareas que aún no vencen."""
    db = SessionLocal()
    try:
        filas = PlanAccionAccion.obtener_verificaciones_para_notificaciones(db, vencidas=False)
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_recordatorio_verificacion(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
            await asyncio.sleep(1)
        logger.info(f"[scheduler] job_recordatorio_verificacion: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_recordatorio_verificacion: {e}")
    finally:
        db.close()



async def job_verificaciones_vencidas():
    """Corre todos los días: aviso para VERIFICADORES de tareas ya vencidas."""
    db = SessionLocal()
    try:
        filas = PlanAccionAccion.obtener_verificaciones_para_notificaciones(db, vencidas=True)
        grupos = _agrupar_por_email(filas)
        for email, items in grupos.items():
            await notify_verificaciones_vencidas(
                destinatario_email=email,
                responsable_nombre=items[0]["responsable"],
                items=items,
            )
            await asyncio.sleep(1)
        logger.info(f"[scheduler] job_verificaciones_vencidas: {len(grupos)} correo(s) procesado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_verificaciones_vencidas: {e}")
    finally:
        db.close()
        

async def job_supervisor_acciones_vencidas():
    """Corre todos los días: avisa a los supervisores de área si una acción tiene 5+ días vencida."""
    db = SessionLocal()
    try:
        resultados = PlanAccionAccion.obtener_supervisores_acciones_vencidas(db)

        supervisores_agrupados = {}

        for item in resultados:
            email_sup = item.supervisor_email
            if not email_sup:
                continue

            if email_sup not in supervisores_agrupados:
                supervisores_agrupados[email_sup] = {
                    "nombre": item.supervisor_nombre,
                    "acciones": {}
                }

            accion = item.PlanAccionAccion
            accion_id = accion.id

            # Si la acción ya está en la lista del supervisor, solo agregamos al responsable si no está repetido
            if accion_id not in supervisores_agrupados[email_sup]["acciones"]:
                supervisores_agrupados[email_sup]["acciones"][accion_id] = {
                    "id": accion_id,
                    "descripcion": accion.descripcion,
                    "fecha": str(accion.fecha),
                    "proceso": item.proceso,
                    "codificador": item.codificador,
                    "responsables": []
                }
            
            # Añadir responsable y su correo si tiene
            resp_info = f"{item.nombre_responsable} ({item.email_responsable})"
            if resp_info not in supervisores_agrupados[email_sup]["acciones"][accion_id]["responsables"]:
                supervisores_agrupados[email_sup]["acciones"][accion_id]["responsables"].append(resp_info)

        # Enviar correos agrupados a cada supervisor convirtiendo el dict de acciones a lista
        for email_sup, info in supervisores_agrupados.items():
            acciones_lista = list(info["acciones"].values())
            await notify_supervisor_acciones_vencidas(
                destinatario_email=email_sup,
                supervisor_nombre=info["nombre"],
                acciones=acciones_lista,
            )
            await asyncio.sleep(1)

        logger.info(f"[scheduler] job_supervisor_acciones_vencidas: {len(supervisores_agrupados)} supervisor(es) notificado(s)")
    except Exception as e:
        logger.error(f"[scheduler] Error en job_supervisor_acciones_vencidas: {e}")
    finally:
        db.close()







def iniciar_scheduler():
    scheduler.add_job(
        job_recordatorio_asignacion,
        CronTrigger(day_of_week="mon", hour=6, minute=30),
        id="recordatorio_asignacion",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_avisos_vencidos,
        CronTrigger(day_of_week="mon-fri", hour=6, minute=15),
        id="avisos_vencidos",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_recordatorio_verificacion,
        CronTrigger(day_of_week="mon", hour=6, minute=30),
        id="recordatorio_verificacion",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_verificaciones_vencidas,
        CronTrigger(day_of_week="mon-fri", hour=6, minute=15),
        id="verificaciones_vencidas",
        replace_existing=True,
        misfire_grace_time=60,
    )
    
    scheduler.add_job(
        job_supervisor_acciones_vencidas,
        CronTrigger(day_of_week="mon-fri", hour=6, minute=40), 
        id="Supervisor_vencidas",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.start()
    logger.info("[scheduler] Iniciado — recordatorio: lunes 6:00am | vencidas: diario 6:00am")