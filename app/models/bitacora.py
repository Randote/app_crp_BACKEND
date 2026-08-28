from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, Session
from app.database import Base


class BitacoraEntrada(Base):
    __tablename__ = "bitacora_entradas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    accion_correctiva_id = Column(Integer, ForeignKey("acciones_correctivas.id", ondelete="CASCADE"),nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # 'sistema' | 'comentario'
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    mensaje = Column(Text, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario = relationship("Usuario")

    @property
    def usuario_nombre(self) -> str:
        if self.usuario:
            return f"{self.usuario.nombre} {self.usuario.apellido}"
        return "Sistema"

    @classmethod
    def registrar_cambio(cls, db: Session, accion_correctiva_id: int, usuario, campo: str, contexto: str = ""):
        etiquetas = {
            "descripcion": "la acción correctiva",
            "fecha": "la fecha planificada",
            "responsable": "el responsable",
            "email": "el correo del responsable",
            "metodologia_descripcion": "la verificación de eficacia",
            "metodologia_fecha": "la fecha de verificación",
            "metodologia_responsable": "el responsable de verificación",
            "metodologia_email": "el correo del responsable de verificación",
            "tipo_accion": "el tipo de acción",
            "estatus": "el estatus",
            "observaciones": "las observaciones",
        }
        etiqueta = etiquetas.get(campo, campo)
        nombre = f"{usuario.nombre} {usuario.apellido}" if usuario else "Alguien"
        mensaje = f"{nombre} actualizó {etiqueta}{contexto}."

        entrada = cls(
            accion_correctiva_id=accion_correctiva_id,
            tipo="sistema",
            usuario_id=usuario.id if usuario else None,
            mensaje=mensaje
        )
        db.add(entrada)
        return entrada
    
    @classmethod
    def registrar_evento(cls, db: Session, accion_correctiva_id: int, usuario, mensaje: str):
        """
        Entrada de bitácora tipo 'sistema' genérica, para eventos que no encajan
        en el patrón campo-por-campo de registrar_cambio (ej. guardado de un
        formulario completo). No hace commit — se asume que el caller ya
        está dentro de una transacción que va a commitear.
        """
        entrada = cls(
            accion_correctiva_id=accion_correctiva_id,
            tipo="sistema",
            usuario_id=usuario.id if usuario else None,
            mensaje=mensaje
        )
        db.add(entrada)
        return entrada

    @classmethod
    def registrar_comentario(cls, db: Session, accion_correctiva_id: int, usuario, mensaje: str):
        entrada = cls(
            accion_correctiva_id=accion_correctiva_id,
            tipo="comentario",
            usuario_id=usuario.id,
            mensaje=mensaje.strip()
        )
        db.add(entrada)
        db.commit()
        db.refresh(entrada)
        return entrada