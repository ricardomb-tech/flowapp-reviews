"""Análisis de frecuencia de palabras por nivel de rating.

El enunciado pide "las palabras más frecuentes por nivel de rating". Se
entrega eso, y además una segunda métrica: **palabras distintivas**.

Motivo: las palabras más frecuentes en rating 1 y en rating 5 suelen ser
casi las mismas ('app', 'flowapp', 'funciona'), porque son el tema del que
todos hablan. La pregunta útil de negocio no es qué se repite, sino qué se
dice en un nivel de rating **y no en los otros**. Eso se mide con lift:

    lift(palabra, nivel) = frecuencia_relativa_en_nivel / frecuencia_relativa_global

Un lift de 3.0 significa que la palabra aparece 3x más de lo esperado en ese
nivel. Se exige un mínimo de apariciones para no premiar el ruido de cola.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .models import Review, Sentiment
from .text import DEFAULT_STOPWORDS, tokenize


@dataclass(frozen=True, slots=True)
class WordScore:
    """Una palabra con su peso dentro de un grupo."""

    word: str
    count: int
    lift: float = 1.0


@dataclass(frozen=True, slots=True)
class GroupAnalysis:
    """Resultado del análisis para un grupo (un rating o una banda)."""

    label: str
    review_count: int
    token_count: int
    unique_tokens: int
    top_words: tuple[WordScore, ...]
    distinctive_words: tuple[WordScore, ...]
    average_length_words: float


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Resultado global del análisis."""

    by_rating: tuple[GroupAnalysis, ...]
    by_sentiment: tuple[GroupAnalysis, ...]
    global_top_words: tuple[WordScore, ...]
    average_rating: float
    rating_distribution: dict[int, int]


def _analyze_group(
    label: str,
    reviews: Sequence[Review],
    global_counter: Counter[str],
    global_total: int,
    top_n: int,
    min_count_for_lift: int,
    stopwords: frozenset[str],
) -> GroupAnalysis:
    counter: Counter[str] = Counter()
    lengths: list[int] = []

    for review in reviews:
        tokens = tokenize(review.text, stopwords=stopwords)
        counter.update(tokens)
        lengths.append(len(tokens))

    group_total = sum(counter.values())

    top_words = tuple(
        WordScore(word=word, count=count)
        # `most_common` no garantiza orden entre empates; se reordena por
        # (-count, word) para que la salida sea determinista entre ejecuciones.
        for word, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    )

    distinctive: list[WordScore] = []
    if group_total and global_total:
        for word, count in counter.items():
            if count < min_count_for_lift:
                continue
            group_freq = count / group_total
            global_freq = global_counter[word] / global_total
            if global_freq == 0:
                continue
            distinctive.append(
                WordScore(word=word, count=count, lift=group_freq / global_freq)
            )
        distinctive.sort(key=lambda score: (-score.lift, -score.count, score.word))

    return GroupAnalysis(
        label=label,
        review_count=len(reviews),
        token_count=group_total,
        unique_tokens=len(counter),
        top_words=top_words,
        distinctive_words=tuple(distinctive[:top_n]),
        average_length_words=(sum(lengths) / len(lengths)) if lengths else 0.0,
    )


def analyze(
    reviews: Iterable[Review],
    top_n: int = 10,
    min_count_for_lift: int = 2,
    stopwords: frozenset[str] = DEFAULT_STOPWORDS,
) -> AnalysisResult:
    """Ejecuta el análisis completo sobre las reseñas ya limpias.

    Args:
        reviews: Reseñas validadas.
        top_n: Cuántas palabras reportar por grupo.
        min_count_for_lift: Apariciones mínimas para entrar al ranking de
            palabras distintivas. Evita que un hápax con lift altísimo
            desplace señal real.
        stopwords: Conjunto de palabras funcionales a excluir.
    """
    materialized = list(reviews)

    global_counter: Counter[str] = Counter()
    for review in materialized:
        global_counter.update(tokenize(review.text, stopwords=stopwords))
    global_total = sum(global_counter.values())

    by_rating = tuple(
        _analyze_group(
            label=f"rating_{rating}",
            reviews=[r for r in materialized if r.rating == rating],
            global_counter=global_counter,
            global_total=global_total,
            top_n=top_n,
            min_count_for_lift=min_count_for_lift,
            stopwords=stopwords,
        )
        for rating in range(1, 6)
        # Un rating sin reseñas no genera grupo: reportar un grupo vacío
        # ensucia la salida sin aportar información.
        if any(r.rating == rating for r in materialized)
    )

    by_sentiment = tuple(
        _analyze_group(
            label=sentiment.value,
            reviews=[r for r in materialized if r.sentiment is sentiment],
            global_counter=global_counter,
            global_total=global_total,
            top_n=top_n,
            min_count_for_lift=min_count_for_lift,
            stopwords=stopwords,
        )
        for sentiment in Sentiment
        if any(r.sentiment is sentiment for r in materialized)
    )

    global_top = tuple(
        WordScore(word=word, count=count)
        for word, count in sorted(
            global_counter.items(), key=lambda kv: (-kv[1], kv[0])
        )[:top_n]
    )

    distribution = dict.fromkeys(range(1, 6), 0)
    for review in materialized:
        distribution[review.rating] += 1

    average = (
        sum(r.rating for r in materialized) / len(materialized)
        if materialized
        else 0.0
    )

    return AnalysisResult(
        by_rating=by_rating,
        by_sentiment=by_sentiment,
        global_top_words=global_top,
        average_rating=average,
        rating_distribution=distribution,
    )
