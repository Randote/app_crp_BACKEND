from .services import send_email


async def notify_accion_registrada(
    destinatarios: list[str],
    codigo_accion: str,
    area_responsable: str,
    origen_hallazgo: str,
    descripcion_hallazgo: str,
    url_accion: str,
):
    enviado = await send_email(
        to=destinatarios,
        subject=f"Nueva acción correctiva registrada: {codigo_accion}",
        template_name="accion_registrada.html",
        context={
            "codigo_accion": codigo_accion,
            "area_responsable": area_responsable,
            "origen_hallazgo": origen_hallazgo,
            "descripcion_hallazgo": descripcion_hallazgo,
            "url_accion": url_accion,
        },
    )
    if not enviado:
        pass


async def notify_recordatorio_asignacion(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    """Resumen semanal (lunes) de tareas abiertas que aún no vencen — para el RESPONSABLE."""
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
    if not enviado:
        pass


async def notify_acciones_vencidas(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    """Aviso diario de tareas abiertas que ya vencieron — para el RESPONSABLE."""
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
    if not enviado:
        pass


async def notify_recordatorio_verificacion(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    """Resumen semanal (lunes) para VERIFICADORES de tareas que aún no vencen."""
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
    if not enviado:
        pass


async def notify_verificaciones_vencidas(
    destinatario_email: str,
    responsable_nombre: str,
    items: list[dict],
):
    """Aviso diario para VERIFICADORES de tareas ya vencidas."""
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
    if not enviado:
        pass