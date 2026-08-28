from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, Session
from datetime import date
from app.database import Base


class IshikawaAnalisis(Base):
    __tablename__ = "ishikawa_analisis"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    accion_correctiva_id = Column(Integer, ForeignKey("acciones_correctivas.id", ondelete="CASCADE"),nullable=False, unique=True, index=True)
    problema_enfocado = Column(Text, nullable=True)
    accion_correctiva = relationship("AccionCorrectiva", back_populates="ishikawa_analisis")
    causas = relationship("IshikawaCausa", back_populates="ishikawa_analisis",cascade="all, delete-orphan", order_by="IshikawaCausa.orden")

    @classmethod
    def crear(cls, db: Session, accion_correctiva_id: int, problema_enfocado: str = None, **categorias) -> "IshikawaAnalisis":
        """
        Crea el análisis de Ishikawa junto con todas sus causas.
        `categorias` recibe listas de dicts, ej: mano_obra=[{"texto": "...", "valor": 3}, ...]
        """
        nuevo = cls(
            accion_correctiva_id=accion_correctiva_id,
            problema_enfocado=problema_enfocado,
        )
        db.add(nuevo)
        db.flush()

        orden = 0
        for categoria, causas in categorias.items():
            for causa in (causas or []):
                db.add(IshikawaCausa(
                    ishikawa_analisis_id=nuevo.id,
                    categoria=categoria,
                    texto=causa.get("texto"),
                    valor=causa.get("valor"),
                    orden=orden,
                ))
                orden += 1

        return nuevo


class IshikawaCausa(Base):
    __tablename__ = "ishikawa_causas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ishikawa_analisis_id = Column(Integer, ForeignKey("ishikawa_analisis.id", ondelete="CASCADE"),nullable=False, index=True)
    categoria = Column(String(30), nullable=False)  # mano_obra, maquina, material, metodo, medicion, medio_ambiente
    texto = Column(Text, nullable=True)
    valor = Column(Integer, nullable=True)
    orden = Column(Integer, nullable=False, default=0)
    
    ishikawa_analisis = relationship("IshikawaAnalisis", back_populates="causas")