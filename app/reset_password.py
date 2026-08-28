
from app.database import SessionLocal
from app.models.usuarios import Usuario

db = SessionLocal()

USUARIO_A_RESETEAR = ""  # ajusta esto
NUEVA_PASSWORD = "Corimon.CA"         # ajusta estos

usuario = Usuario.obtener_por_usuario(db, USUARIO_A_RESETEAR)
if not usuario:
    usuario = Usuario.obtener_por_email(db, USUARIO_A_RESETEAR)

if not usuario:
    print("Usuario no encontrado.")
else:
    usuario.set_password(NUEVA_PASSWORD)
    db.commit()
    print(f"Contraseña reseteada para {usuario.usuario} ({usuario.email}).")

db.close()