from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Socio(Base):
    __tablename__ = "socios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_apellido: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha_nacimiento: Mapped[Date] = mapped_column(Date, nullable=False)
    telefono: Mapped[str] = mapped_column(String(50), nullable=False)
    planilla_medica_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    pagos: Mapped[list["Pago"]] = relationship(
        "Pago",
        back_populates="socio",
        cascade="all, delete-orphan",
    )


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False, index=True)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    fecha_pago: Mapped[Date] = mapped_column(Date, nullable=False)
    fecha_proximo_pago: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    socio: Mapped["Socio"] = relationship("Socio", back_populates="pagos")


class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    duracion_segundos: Mapped[int] = mapped_column(Integer, nullable=False)
    descanso_segundos: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    rondas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    sesiones: Mapped[list["SesionEntrenamiento"]] = relationship(
        "SesionEntrenamiento",
        back_populates="ejercicio",
        cascade="all, delete-orphan",
    )


class SesionEntrenamiento(Base):
    __tablename__ = "sesiones_entrenamiento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ejercicio_id: Mapped[int] = mapped_column(ForeignKey("ejercicios.id"), nullable=False, index=True)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duracion_real_segundos: Mapped[int] = mapped_column(Integer, nullable=False)

    ejercicio: Mapped["Ejercicio"] = relationship("Ejercicio", back_populates="sesiones")
