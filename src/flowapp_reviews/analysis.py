"""Herramientas para analizar las reseñas ya limpias.

Además de obtener las palabras más frecuentes por rating, también se calcula
una lista de palabras distintivas usando la métrica *lift*. Esto ayuda a
identificar términos que aparecen con mucha más frecuencia en un grupo de
ratings que en el resto del conjunto de datos.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import median

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
    median_rating: float
    rating_distribution: dict[int, int]


@dataclass(frozen=True, slots=True)
class _TokenizedReview:
    """Reseña con tokens precalculados para evitar re-tokenizar."""

    review: Review
    tokens: tuple[str, ...]


def _top_word_scores(counter: Counter[str], top_n: int) -> tuple[WordScore, ...]:
    return tuple(
        WordScore(word=word, count=count)
        for word, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[
            :top_n
        ]
    )


def _distinctive_words(
    counter: Counter[str],
    group_total: int,
    global_counter: Counter[str],
    global_total: int,
    top_n: int,
    min_count_for_lift: int,
) -> tuple[WordScore, ...]:
    if not group_total or not global_total:
        return ()

    distinctive: list[WordScore] = []
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
    return tuple(distinctive[:top_n])


def _analyze_group(
    label: str,
    entries: Sequence[_TokenizedReview],
    global_counter: Counter[str],
    global_total: int,
    top_n: int,
    min_count_for_lift: int,
) -> GroupAnalysis:
    counter: Counter[str] = Counter()
    lengths: list[int] = []

    for entry in entries:
        counter.update(entry.tokens)
        lengths.append(len(entry.tokens))

    group_total = sum(counter.values())

    return GroupAnalysis(
        label=label,
        review_count=len(entries),
        token_count=group_total,
        unique_tokens=len(counter),
        top_words=_top_word_scores(counter, top_n),
        distinctive_words=_distinctive_words(
            counter,
            group_total,
            global_counter,
            global_total,
            top_n,
            min_count_for_lift,
        ),
        average_length_words=(sum(lengths) / len(lengths)) if lengths else 0.0,
    )


def _empty_result() -> AnalysisResult:
    return AnalysisResult(
        by_rating=(),
        by_sentiment=(),
        global_top_words=(),
        average_rating=0.0,
        median_rating=0.0,
        rating_distribution=dict.fromkeys(range(1, 6), 0),
    )


def analyze(
    reviews: Iterable[Review],
    top_n: int = 10,
    min_count_for_lift: int = 2,
    stopwords: frozenset[str] = DEFAULT_STOPWORDS,
) -> AnalysisResult:
    """Ejecuta el análisis completo sobre las reseñas ya limpias.

    Cada reseña se tokeniza una sola vez; los contadores por rating y por
    banda de sentimiento se construyen en un único recorrido.
    """
    materialized = list(reviews)
    if not materialized:
        return _empty_result()

    tokenized = [
        _TokenizedReview(
            review=review,
            tokens=tuple(tokenize(review.text, stopwords=stopwords)),
        )
        for review in materialized
    ]

    global_counter: Counter[str] = Counter()
    by_rating: dict[int, list[_TokenizedReview]] = {rating: [] for rating in range(1, 6)}
    by_sentiment: dict[Sentiment, list[_TokenizedReview]] = {
        sentiment: [] for sentiment in Sentiment
    }
    distribution = dict.fromkeys(range(1, 6), 0)
    ratings: list[int] = []

    for entry in tokenized:
        review = entry.review
        global_counter.update(entry.tokens)
        by_rating[review.rating].append(entry)
        by_sentiment[review.sentiment].append(entry)
        distribution[review.rating] += 1
        ratings.append(review.rating)

    global_total = sum(global_counter.values())

    rating_groups = tuple(
        _analyze_group(
            label=f"rating_{rating}",
            entries=by_rating[rating],
            global_counter=global_counter,
            global_total=global_total,
            top_n=top_n,
            min_count_for_lift=min_count_for_lift,
        )
        for rating in range(1, 6)
        if by_rating[rating]
    )

    sentiment_groups = tuple(
        _analyze_group(
            label=sentiment.value,
            entries=by_sentiment[sentiment],
            global_counter=global_counter,
            global_total=global_total,
            top_n=top_n,
            min_count_for_lift=min_count_for_lift,
        )
        for sentiment in Sentiment
        if by_sentiment[sentiment]
    )

    return AnalysisResult(
        by_rating=rating_groups,
        by_sentiment=sentiment_groups,
        global_top_words=_top_word_scores(global_counter, top_n),
        average_rating=sum(ratings) / len(ratings),
        median_rating=float(median(ratings)),
        rating_distribution=distribution,
    )
