from .services import send_email
import logging
from app.database import SessionLocal
from app.models.usuarios import Usuario
from app.models.procesosupervisor import  ProcesoSupervisor

logger = logging.getLogger(__name__)


def _usuario_esta_activo(email: str) -> bool:
    """Verifica el estatus activo del usuario mediante el classmethod."""
    if not email:
        return False
    db = SessionLocal()
    try:
        return Usuario.esta_activo_por_email(db, email)
    except Exception as e:
        logger.error(f"Error verificando estatus de usuario {email}: {e}")
        return False
    finally:
        db.close()


def _supervisor_esta_activo(email: str) -> bool:
    """Verifica el estatus activo del supervisor mediante el classmethod."""
    if not email:
        return False
    db = SessionLocal()
    try:
        return ProcesoSupervisor.esta_activo_por_email(db, email)
    except Exception as e:
        logger.error(f"Error verificando estatus de supervisor {email}: {e}")
        return False
    finally:
        db.close()


async def notify_accion_registrada(
    destinatarios: list[str],
    codigo_accion: str,
    area_responsable: str,
    origen_hallazgo: str,
    descripcion_hallazgo: str,
    url_accion: str,
):
    # Filtrar solo los destinatarios que tengan su usuario activo
    db = SessionLocal()
    try:
        activos = Usuario.filtrar_activos_por_emails(db, destinatarios)
        destinatarios_validos = [u.email for u in activos]
    except Exception:
        destinatarios_validos = destinatarios
    finally:
        db.close()

    if not destinatarios_validos:
        logger.info(f"Notificación de acción registrada omitida: todos los destinatarios están inactivos ({codigo_accion}).")
        return False

    enviado = await send_email(
        to=destinatarios_validos,
        subject=f"Nueva acción correctiva registrada: {codigo_accion}",
        template_name="nuevo-registro.html",
        context={
            "codigo_accion": codigo_accion,
            "area_responsable": area_responsable,
            "origen_hallazgo": origen_hallazgo,
            "descripcion_hallazgo": descripcion_hallazgo,
            "url_accion": url_accion,
        },
    )
    return enviado


async def notify_recordatorio_asignacion(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Recordatorio omitido (Usuario inactivo): {destinatario_email}")
        return False

    enviado = await send_email(
        to=[destinatario_email],
        subject=f"Resumen semanal: tienes {len(items)} tarea(s) pendiente(s)",
        template_name="recordatorio.html",
        context={
            "responsable_nombre": responsable_nombre,
            "items": items,
            "etiqueta_plural": "tareas",
        },
    )
    return enviado


async def notify_acciones_vencidas(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Aviso de vencidas omitido (Usuario inactivo): {destinatario_email}")
        return False

    enviado = await send_email(
        to=[destinatario_email],
        subject=f"Tienes {len(items)} tarea(s) vencida(s) en el sistema CAPA",
        template_name="vencidas.html",
        context={
            "responsable_nombre": responsable_nombre,
            "items": items,
            "etiqueta_plural": "tareas",
        },
    )
    return enviado


async def notify_recordatorio_verificacion(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Recordatorio verificación omitido (Usuario inactivo): {destinatario_email}")
        return False

    enviado = await send_email(
        to=[destinatario_email],
        subject=f"Resumen semanal: tienes {len(items)} verificación(es) pendiente(s)",
        template_name="recordatorio.html",
        context={
            "responsable_nombre": responsable_nombre,
            "items": items,
            "etiqueta_plural": "verificaciones",
        },
    )
    return enviado


async def notify_verificaciones_vencidas(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Verificaciones vencidas omitido (Usuario inactivo): {destinatario_email}")
        return False

    enviado = await send_email(
        to=[destinatario_email],
        subject=f"Tienes {len(items)} verificación(es) vencida(s) en el sistema CAPA",
        template_name="vencidas.html",
        context={
            "responsable_nombre": responsable_nombre,
            "items": items,
            "etiqueta_plural": "verificaciones",
        },
    )
    return enviado


async def notify_codigo_recuperacion(
    destinatario_email: str,
    nombre: str,
    codigo: str,
    minutos_validez: int = 5,
):
    enviado = await send_email(
        to=[destinatario_email],
        subject="Código para restablecer tu contraseña — CAPA",
        template_name="codigo-recuperacion.html",
        context={
            "nombre": nombre,
            "codigo": codigo,
            "minutos_validez": minutos_validez,
        },
    )
    return enviado


async def notify_accion_asignada(
    destinatario_email: str,
    nombre: str,
    acciones: list[dict],
    codigo_accion: str,
    url_accion: str,
):
    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Acción asignada omitida (Usuario inactivo): {destinatario_email}")
        return False

    enviado = await send_email(
        to=[destinatario_email],
        subject=f"Nueva(s) tarea(s) asignada(s) — {codigo_accion}",
        template_name="accion_asignada.html",
        context={
            "nombre": nombre or "Responsable",
            "acciones": acciones,
            "codigo_accion": codigo_accion,
            "url_accion": url_accion,
        },
    )
    return enviado


async def notify_verificacion_asignada(
    destinatario_email: str,
    nombre: str,
    acciones: list[dict],
    codigo_accion: str,
    url_accion: str,
):
    if not destinatario_email:
        return False

    if not _usuario_esta_activo(destinatario_email):
        logger.info(f"Verificación asignada omitida (Usuario inactivo): {destinatario_email}")
        return False

    try:
        enviado = await send_email(
            to=[destinatario_email],
            subject=f"Nueva(s) Verificación(es) de Eficacia asignada(s) — {codigo_accion}",
            template_name="verificacion_asignada.html",
            context={
                "nombre": nombre or "Responsable",
                "acciones": acciones,
                "codigo_accion": codigo_accion,
                "url_accion": url_accion,
            },
        )
        return enviado
    except Exception as e:
        logger.exception(f"Error inesperado al notificar verificación a {destinatario_email}: {e}")
        return False


async def notify_supervisor_acciones_vencidas(
    destinatario_email: str,
    supervisor_nombre: str,
    acciones: list[dict],
):
    if not destinatario_email:
        return False

    if not _supervisor_esta_activo(destinatario_email):
        logger.info(f"Alerta a supervisor omitida (Proceso/Supervisor inactivo): {destinatario_email}")
        return False

    try:
        enviado = await send_email(
            to=[destinatario_email],
            subject="Alerta: Acciones Correctivas con 5+ días de retraso en su área",
            template_name="supervisor_acciones_vencidas.html", 
            context={
                "nombre": supervisor_nombre or "Supervisor",
                "acciones": acciones,
            },
        )
        return enviado
    except Exception as e:
        logger.exception(f"Error inesperado al notificar al supervisor {destinatario_email}: {e}")
        return False




async def notify_usuario_registrado(
    destinatario_email: str,
    nombre: str,
    usuario_red: str,
    password_temporal: str,
    url_login: str,
):
    """Envía un correo de bienvenida al nuevo usuario registrado en el sistema CAPA."""
    if not destinatario_email:
        return False
    try:
        enviado = await send_email(
            to=[destinatario_email],
            subject="Bienvenido al Sistema de Acciones Correctivas — CAPA",
            template_name="bienvenida_usuario.html", 
            context={
                "nombre": nombre or "Usuario",
                "usuario_red": usuario_red,
                "password_temporal": password_temporal,
                "url_login": url_login,
            },
        )
        return enviado
    except Exception as e:
        logger.exception(f"Error inesperado al enviar bienvenida a {destinatario_email}: {e}")
        return False
