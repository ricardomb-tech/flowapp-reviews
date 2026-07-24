"""Modelos de dominio del análisis de reseñas de FlowApp.

Se usan `dataclasses` inmutables (`frozen=True`) para que una reseña validada
no pueda mutar después de pasar el pipeline de limpieza. Esto hace que el
estado del programa sea razonable: si tengo un `Review`, es válido. Punto.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

# Rango válido de rating declarado por el enunciado (escala 1-5).
MIN_RATING: Final[int] = 1
MAX_RATING: Final[int] = 5


class Sentiment(StrEnum):
    """Agrupación de ratings en bandas de sentimiento.

    Se reporta tanto por rating individual (1..5) como por banda, porque
    con datasets pequeños los conteos por rating suelen ser demasiado
    dispersos para ver patrones.
    """

    NEGATIVO = "negativo"  # 1-2
    NEUTRO = "neutro"      # 3
    POSITIVO = "positivo"  # 4-5

    @classmethod
    def from_rating(cls, rating: int) -> Sentiment:
        if rating <= 2:
            return cls.NEGATIVO
        if rating == 3:
            return cls.NEUTRO
        return cls.POSITIVO


class RejectionReason(StrEnum):
    """Motivo por el que un registro crudo no llegó al análisis.

    Nunca se descarta una fila en silencio: cada rechazo queda contabilizado
    y trazable. Es la diferencia entre "limpié el dataset" y "puedo demostrar
    exactamente qué quité y por qué".
    """

    TEXTO_NULO = "texto_nulo_o_vacio"
    RATING_NULO = "rating_nulo_o_vacio"
    RATING_NO_NUMERICO = "rating_no_numerico"
    RATING_FUERA_DE_RANGO = "rating_fuera_de_rango"
    DUPLICADO_EXACTO = "duplicado_exacto"
    DUPLICADO_NORMALIZADO = "duplicado_normalizado"


@dataclass(frozen=True, slots=True)
class RawReview:
    """Fila tal como viene del archivo de entrada, sin interpretar."""

    line_number: int
    review_id: str | None
    text: str | None
    rating: str | None


@dataclass(frozen=True, slots=True)
class Review:
    """Reseña ya validada. Si existe esta instancia, el dato es confiable."""

    line_number: int
    review_id: str | None
    text: str
    rating: int

    @property
    def sentiment(self) -> Sentiment:
        return Sentiment.from_rating(self.rating)


@dataclass(frozen=True, slots=True)
class Rejection:
    """Registro auditable de una fila descartada."""

    line_number: int
    reason: RejectionReason
    detail: str = ""


@dataclass(slots=True)
class CleaningReport:
    """Resultado completo de la fase de limpieza."""

    total_input: int = 0
    reviews: list[Review] = field(default_factory=list)
    rejections: list[Rejection] = field(default_factory=list)

    @property
    def total_valid(self) -> int:
        return len(self.reviews)

    @property
    def total_rejected(self) -> int:
        return len(self.rejections)

    @property
    def retention_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.total_valid / self.total_input

    def rejections_by_reason(self) -> dict[RejectionReason, int]:
        counts: Counter[RejectionReason] = Counter()
        for rejection in self.rejections:
            counts[rejection.reason] += 1
        return dict(counts)
