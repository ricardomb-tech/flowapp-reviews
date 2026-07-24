"""Análisis de reseñas de usuarios de FlowApp — EPAM Python Run, Reto 1."""

from .analysis import AnalysisResult, analyze
from .cleaning import clean
from .loading import load_records
from .models import CleaningReport, RejectionReason, Review, Sentiment
from .pipeline import PipelineResult, run_pipeline

__version__ = "1.0.0"
__all__ = [
    "AnalysisResult",
    "CleaningReport",
    "PipelineResult",
    "RejectionReason",
    "Review",
    "Sentiment",
    "analyze",
    "clean",
    "load_records",
    "run_pipeline",
]
