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

    try:
        template = jinja_env.get_template(template_name)
        html_content = template.render(**context)

        message = EmailMessage()
        message["From"] = f"{mail_settings.MAIL_FROM_NAME} <{mail_settings.MAIL_FROM}>"
        message["To"] = ", ".join(to)
        message["Subject"] = subject
        message.set_content("Este correo requiere un cliente compatible con HTML.")
        message.add_alternative(html_content, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=mail_settings.MAIL_SERVER,
            port=mail_settings.MAIL_PORT,
            start_tls=mail_settings.MAIL_STARTTLS,
            username=mail_settings.MAIL_USERNAME,
            password=mail_settings.MAIL_PASSWORD,
        )

        logger.info(f"Correo enviado correctamente a {to} — asunto: {subject}")
        return True

    except Exception as e:
        logger.error(f"Fallo al enviar correo a {to} — asunto: {subject} — error: {e}")
        return False