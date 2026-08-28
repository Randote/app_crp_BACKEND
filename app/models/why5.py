from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.database import Base


class Analisis5Porques(Base):
    __tablename__ = "analisis_5porques"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    accion_correctiva_id = Column(Integer, ForeignKey("acciones_correctivas.id", ondelete="CASCADE"),nullable=False, index=True)
    causa_potencial = Column(Text, nullable=False)
    orden = Column(Integer, nullable=False, default=0)

    # Tablas relacionadas
    accion_correctiva = relationship("AccionCorrectiva", back_populates="analisis_5porques")
    porques = relationship("Porque", back_populates="analisis_5porques",cascade="all, delete-orphan", order_by="Porque.numero")

    @classmethod
    def crear(cls, db: Session, accion_correctiva_id: int, causa_potencial: str, porques: list, orden: int = 0) -> "Analisis5Porques":
        """
        Crea una causa potencial junto con sus porqués asociados.
        `porques` es una lista de dicts: [{"numero": 1, "pregunta": "...", "respuesta": "...", "es_raiz": False}, ...]
        """
        nueva = cls(
            accion_correctiva_id=accion_correctiva_id,
            causa_potencial=causa_potencial,
            orden=orden,
        )
        db.add(nueva)
        db.flush()  # para tener nueva.id

        for item in (porques or []):
            db.add(Porque(
                analisis_5porques_id=nueva.id,
                numero=item.get("numero"),
                pregunta=item.get("pregunta"),
                respuesta=item.get("respuesta"),
                es_raiz=item.get("es_raiz", False),
            ))

        return nueva


class Porque(Base):
    __tablename__ = "porques"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analisis_5porques_id = Column(Integer, ForeignKey("analisis_5porques.id", ondelete="CASCADE"),nullable=False, index=True)
    numero = Column(Integer, nullable=False)
    pregunta = Column(Text, nullable=True)
    respuesta = Column(Text, nullable=True)
    es_raiz = Column(Boolean, nullable=False, default=False)

    # Tablas relacionadas
    analisis_5porques = relationship("Analisis5Porques", back_populates="porques")