from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta

from db.database import SessionLocal, init_db
from db.models import Ejercicio, Pago, SesionEntrenamiento, Socio


FIRST_NAMES = [
    "Lucas",
    "Mateo",
    "Thiago",
    "Bruno",
    "Santiago",
    "Martin",
    "Franco",
    "Nicolas",
    "Joaquin",
    "Valentin",
    "Emma",
    "Olivia",
    "Sofia",
    "Martina",
    "Julia",
    "Camila",
    "Isabella",
    "Abril",
    "Valeria",
    "Renata",
]

LAST_NAMES = [
    "Gomez",
    "Perez",
    "Diaz",
    "Lopez",
    "Sosa",
    "Romero",
    "Alvarez",
    "Torres",
    "Ruiz",
    "Molina",
    "Castro",
    "Suarez",
    "Acosta",
    "Rojas",
    "Vega",
    "Herrera",
    "Medina",
    "Silva",
    "Ramos",
    "Benitez",
]

EXERCISE_NAMES = [
    "Burpees",
    "Sentadillas",
    "Flexiones",
    "Plancha",
    "Mountain Climbers",
    "Skipping",
    "Lunges",
    "Abdominales",
    "Jumping Jacks",
    "Soga",
    "Remo",
    "Press Militar",
    "Peso Muerto",
    "Bicicleta",
    "Trote",
]


def random_birthdate() -> date:
    today = date.today()
    age_years = random.randint(16, 60)
    extra_days = random.randint(0, 364)
    return today - timedelta(days=(age_years * 365) + extra_days)


def random_phone(index: int) -> str:
    base = 1100000000 + index
    return str(base)


def reset_data(session: SessionLocal) -> None:
    session.query(SesionEntrenamiento).delete()
    session.query(Pago).delete()
    session.query(Ejercicio).delete()
    session.query(Socio).delete()
    session.commit()


def create_socios(session: SessionLocal, amount: int) -> list[Socio]:
    socios: list[Socio] = []
    for idx in range(amount):
        nombre = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        socio = Socio(
            nombre_apellido=nombre,
            fecha_nacimiento=random_birthdate(),
            telefono=random_phone(idx + random.randint(0, 9999)),
            planilla_medica_path=None,
            activo=True,
        )
        socios.append(socio)

    session.add_all(socios)
    session.commit()
    return socios


def create_pagos(session: SessionLocal, socios: list[Socio], min_per_socio: int, max_per_socio: int) -> int:
    total = 0
    today = date.today()

    for socio in socios:
        payments_count = random.randint(min_per_socio, max_per_socio)
        start_offset = random.randint(120, 540)
        current_date = today - timedelta(days=start_offset)

        for _ in range(payments_count):
            monto = random.choice([15000, 18000, 20000, 22000, 25000, 28000, 30000])
            next_date = current_date + timedelta(days=random.choice([28, 30, 31]))
            pago = Pago(
                socio_id=socio.id,
                monto=float(monto),
                fecha_pago=current_date,
                fecha_proximo_pago=next_date,
            )
            session.add(pago)
            total += 1

            # Move to the next monthly cycle with a little randomness.
            current_date = next_date + timedelta(days=random.choice([0, 1, 2, 4, 7]))
            if current_date > today:
                break

    session.commit()
    return total


def create_ejercicios(session: SessionLocal, amount: int) -> list[Ejercicio]:
    ejercicios: list[Ejercicio] = []
    for idx in range(amount):
        base_name = random.choice(EXERCISE_NAMES)
        ejercicio = Ejercicio(
            nombre=f"{base_name} #{idx + 1}",
            duracion_segundos=random.randint(20, 180),
            descanso_segundos=random.randint(10, 60),
            rondas=random.randint(2, 8),
            descripcion="Rutina de prueba generada automaticamente",
        )
        ejercicios.append(ejercicio)

    session.add_all(ejercicios)
    session.commit()
    return ejercicios


def create_sesiones(session: SessionLocal, ejercicios: list[Ejercicio], per_exercise_min: int, per_exercise_max: int) -> int:
    total = 0
    now = datetime.now()

    for ejercicio in ejercicios:
        count = random.randint(per_exercise_min, per_exercise_max)
        for _ in range(count):
            days_back = random.randint(1, 120)
            start = now - timedelta(days=days_back, minutes=random.randint(0, 1000))
            duration = random.randint(max(5, ejercicio.duracion_segundos - 10), ejercicio.duracion_segundos + 20)
            end = start + timedelta(seconds=duration)

            sesion = SesionEntrenamiento(
                ejercicio_id=ejercicio.id,
                fecha_inicio=start,
                fecha_fin=end,
                duracion_real_segundos=duration,
            )
            session.add(sesion)
            total += 1

    session.commit()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos fake para pruebas de volumen.")
    parser.add_argument("--socios", type=int, default=250)
    parser.add_argument("--ejercicios", type=int, default=40)
    parser.add_argument("--min-pagos", type=int, default=4)
    parser.add_argument("--max-pagos", type=int, default=14)
    parser.add_argument("--min-sesiones", type=int, default=8)
    parser.add_argument("--max-sesiones", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true", help="Borra datos previos antes de cargar.")
    args = parser.parse_args()

    random.seed(args.seed)
    init_db()

    with SessionLocal() as session:
        if args.reset:
            reset_data(session)

        socios = create_socios(session, args.socios)
        total_pagos = create_pagos(session, socios, args.min_pagos, args.max_pagos)
        ejercicios = create_ejercicios(session, args.ejercicios)
        total_sesiones = create_sesiones(session, ejercicios, args.min_sesiones, args.max_sesiones)

    print("Carga completada")
    print(f"Socios creados: {len(socios)}")
    print(f"Pagos creados: {total_pagos}")
    print(f"Ejercicios creados: {len(ejercicios)}")
    print(f"Sesiones creadas: {total_sesiones}")


if __name__ == "__main__":
    main()
