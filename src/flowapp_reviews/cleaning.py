"""Pipeline de limpieza del dataset.

Tres defectos inyectados a propósito por el enunciado, tres reglas explícitas:

1. **Nulos** — texto o rating ausentes. Se descarta la fila: una reseña sin
   texto no aporta palabras, y una sin rating no se puede agrupar. No se
   imputa nada; inventar un rating promedio sería falsear el análisis.
2. **Ratings inválidos** — se intenta coerción razonable (`"4"`, `"4.0"`,
   `" 5 "` son válidos) y se rechaza lo que quede fuera de 1-5.
3. **Duplicados** — dos niveles: exacto (mismo texto literal + mismo rating)
   y normalizado (mismo texto sin acentos/casing/espacios + mismo rating).
   Se conserva la primera aparición.

Ninguna fila se pierde en silencio: todo rechazo queda en `CleaningReport`.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    MAX_RATING,
    MIN_RATING,
    CleaningReport,
    RawReview,
    Rejection,
    RejectionReason,
    Review,
)
from .text import normalize


def parse_rating(raw: str) -> tuple[int | None, RejectionReason | None]:
    """Convierte un rating crudo a entero validado.

    Acepta enteros ('4'), flotantes con parte decimal nula ('4.0') y valores
    con espacios. Rechaza texto no numérico, decimales reales ('4.5') y todo
    lo que caiga fuera del rango 1-5.

    Returns:
        `(rating, None)` si es válido, `(None, motivo)` si no.
    """
    candidate = raw.strip().replace(",", ".")
    try:
        numeric = float(candidate)
    except ValueError:
        return None, RejectionReason.RATING_NO_NUMERICO

    if numeric != int(numeric):
        # '4.5' no es un nivel de rating de la escala; no se redondea porque
        # eso movería la reseña a un grupo al que no pertenece.
        return None, RejectionReason.RATING_FUERA_DE_RANGO

    value = int(numeric)
    if not MIN_RATING <= value <= MAX_RATING:
        return None, RejectionReason.RATING_FUERA_DE_RANGO
    return value, None


def clean(raw_reviews: Iterable[RawReview]) -> CleaningReport:
    """Aplica el pipeline completo de limpieza sobre las filas crudas."""
    report = CleaningReport()
    seen_exact: set[tuple[str, int]] = set()
    seen_normalized: set[tuple[str, int]] = set()

    for raw in raw_reviews:
        report.total_input += 1

        if raw.text is None:
            report.rejections.append(
                Rejection(raw.line_number, RejectionReason.TEXTO_NULO)
            )
            continue

        if raw.rating is None:
            report.rejections.append(
                Rejection(raw.line_number, RejectionReason.RATING_NULO)
            )
            continue

        rating, reason = parse_rating(raw.rating)
        if rating is None:
            assert reason is not None
            report.rejections.append(
                Rejection(raw.line_number, reason, detail=raw.rating)
            )
            continue

        text = raw.text.strip()
        if not text:
            report.rejections.append(
                Rejection(raw.line_number, RejectionReason.TEXTO_NULO)
            )
            continue

        exact_key = (text, rating)
        if exact_key in seen_exact:
            report.rejections.append(
                Rejection(
                    raw.line_number,
                    RejectionReason.DUPLICADO_EXACTO,
                    detail=text[:60],
                )
            )
            continue

        normalized_key = (normalize(text), rating)
        if normalized_key in seen_normalized:
            report.rejections.append(
                Rejection(
                    raw.line_number,
                    RejectionReason.DUPLICADO_NORMALIZADO,
                    detail=text[:60],
                )
            )
            continue

        seen_exact.add(exact_key)
        seen_normalized.add(normalized_key)
        report.reviews.append(
            Review(
                line_number=raw.line_number,
                review_id=raw.review_id,
                text=text,
                rating=rating,
            )
        )

    return report
