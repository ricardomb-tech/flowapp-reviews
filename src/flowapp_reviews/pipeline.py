"""Orquestación del pipeline de punta a punta.

Separa la lógica de negocio (cargar → limpiar → analizar) de la capa CLI,
de modo que tests, notebooks y scripts reutilicen el mismo flujo sin duplicar
validaciones ni manejo de errores.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analysis import AnalysisResult, analyze
from .cleaning import clean
from .loading import load_records
from .models import CleaningReport, RawReview


class PipelineError(Exception):
    """Error base del pipeline."""


class EmptyDatasetError(PipelineError):
    """El archivo existe pero no contiene filas legibles."""


class NoValidRowsError(PipelineError):
    """Ninguna fila superó la validación de limpieza."""

    def __init__(self, rejected: int) -> None:
        self.rejected = rejected
        super().__init__(
            f"Ninguna fila superó la validación. Se descartaron {rejected} filas."
        )


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Resultado completo de una ejecución exitosa."""

    cleaning: CleaningReport
    analysis: AnalysisResult


def run_pipeline(
    dataset: Path,
    *,
    top_n: int = 10,
    min_count_for_lift: int = 2,
) -> PipelineResult:
    """Ejecuta carga, limpieza y análisis sobre un dataset.

    Raises:
        FileNotFoundError: Si la ruta no existe.
        DatasetFormatError: Si las columnas no son reconocibles.
        EmptyDatasetError: Si no hay filas.
        NoValidRowsError: Si todas las filas fueron descartadas.
    """
    raw_reviews: list[RawReview] = load_records(dataset)
    if not raw_reviews:
        raise EmptyDatasetError("El dataset está vacío.")

    cleaning = clean(raw_reviews)
    if not cleaning.reviews:
        raise NoValidRowsError(cleaning.total_rejected)

    analysis = analyze(
        cleaning.reviews,
        top_n=top_n,
        min_count_for_lift=min_count_for_lift,
    )
    return PipelineResult(cleaning=cleaning, analysis=analysis)
