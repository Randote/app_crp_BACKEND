from email.message import EmailMessage
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import aiosmtplib
from app.core.config import mail_settings
import logging

logger = logging.getLogger("email")

TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


async def send_email(to: list[str], subject: str, template_name: str, context: dict):
    print(f"-> [DEBUG] Intentando enviar correo a: {to} | Asunto: {subject}")
    try:
        template = jinja_env.get_template(template_name)
        html_content = template.render(**context)

        message = EmailMessage()
        message["From"] = f"{mail_settings.MAIL_FROM_NAME} <{mail_settings.MAIL_FROM}>"
        message["To"] = ", ".join(to)
        message["Subject"] = subject
        message.set_content("Este correo requiere un cliente compatible con HTML.")
        message.add_alternative(html_content, subtype="html")

        # aiosmtplib maneja la conexión y STARTTLS de forma nativa y segura
        async with aiosmtplib.SMTP(
            hostname=mail_settings.MAIL_SERVER,
            port=mail_settings.MAIL_PORT,
            start_tls=mail_settings.MAIL_STARTTLS,  # True para el puerto 587
            timeout=15
        ) as client:
            if mail_settings.MAIL_USERNAME and mail_settings.MAIL_PASSWORD:
                await client.login(
                    mail_settings.MAIL_USERNAME, 
                    mail_settings.MAIL_PASSWORD
                )

            await client.send_message(message)

        print(f"-> [DEBUG] Correo enviado con éxito a {to}")
        logger.info(f"Correo enviado correctamente a {to} — asunto: {subject}")
        return True

    except Exception as e:
        print(f"-> [DEBUG] ERROR al enviar correo: {e}")
        logger.error(f"Fallo al enviar correo a {to} — asunto: {subject} — error: {e}")
        return False