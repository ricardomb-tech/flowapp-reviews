"""Genera un dataset de muestra con los mismos defectos que el del reto.

Sirve para dos cosas: que el proyecto sea ejecutable sin el archivo oficial,
y para verificar que el pipeline detecta cada tipo de defecto inyectado.

    python scripts/generate_sample_data.py data/reviews_sample.csv
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

POSITIVE = [
    "La aplicación es rapidísima y la sincronización funciona perfecto",
    "Excelente diseño, muy intuitiva, la recomiendo totalmente",
    "Me encanta la interfaz, todo fluye sin problemas",
    "Buenísima app, el soporte respondió en minutos",
    "Increíble lo bien que organiza mis tareas, muy intuitiva",
    "Great app, the sync works flawlessly and the design is clean",
]
NEUTRAL = [
    "Está bien pero le faltan funciones importantes",
    "Cumple lo básico, aunque la interfaz podría mejorar",
    "Regular, a veces funciona bien y a veces no",
    "It works but the free plan is quite limited",
]
NEGATIVE = [
    "Se cierra sola todo el tiempo, pésima experiencia",
    "Muy lenta, consume mucha batería y se congela al abrir",
    "Cobraron la suscripción sin avisar, terrible el soporte",
    "No sincroniza nada, perdí todos mis datos, pésima",
    "La publicidad es insoportable, se cierra y se congela",
    "Crashes constantly, terrible support, they charged me twice",
]

INVALID_RATINGS = ["0", "6", "10", "-1", "cinco", "4.5", "", "N/A", "★★★"]

# Coletillas para dar variación léxica: sin esto, un pool corto de frases
# genera duplicados accidentales y el dataset de muestra deja de parecerse
# a uno real (los duplicados deben ser los inyectados a propósito).
SUFFIXES = [
    "", " Llevo meses usándola.", " Ojalá lo arreglen pronto.",
    " La uso a diario en el trabajo.", " Desde la última actualización.",
    " La instalé hace poco.", " Ya se lo escribí al soporte.",
    " En Android me pasa igual.", " Espero que mejore.",
]


def build_rows(count: int, seed: int = 42) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    next_id = 1

    def emit(text: str | None, rating: str | None) -> None:
        nonlocal next_id
        rows.append({
            "review_id": f"RV-{next_id:04d}",
            "review_text": "" if text is None else text,
            "rating": "" if rating is None else rating,
        })
        next_id += 1

    for _ in range(count):
        bucket = rng.random()
        if bucket < 0.45:
            base, rating = rng.choice(POSITIVE), str(rng.choice([4, 5]))
        elif bucket < 0.65:
            base, rating = rng.choice(NEUTRAL), "3"
        else:
            base, rating = rng.choice(NEGATIVE), str(rng.choice([1, 2]))
        emit(base + rng.choice(SUFFIXES), rating)

    # Defecto 1: nulos.
    for _ in range(6):
        emit(None, str(rng.randint(1, 5)))
    for _ in range(5):
        emit(rng.choice(POSITIVE), None)
    emit("   ", "4")

    # Defecto 2: ratings inválidos.
    for invalid in INVALID_RATINGS:
        emit(rng.choice(POSITIVE + NEGATIVE), invalid)

    # Defecto 3: duplicados exactos y con variación de casing/espacios.
    for row in rng.sample(rows[:count], k=8):
        rows.append(dict(row, review_id=f"RV-{next_id:04d}"))
        next_id += 1
    for row in rng.sample(rows[:count], k=5):
        mutated = row["review_text"].upper() + "  "
        rows.append({
            "review_id": f"RV-{next_id:04d}",
            "review_text": mutated,
            "rating": row["rating"],
        })
        next_id += 1

    rng.shuffle(rows)
    return rows


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "data/reviews_sample.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = build_rows(count=120)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["review_id", "review_text", "rating"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} filas escritas en {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
