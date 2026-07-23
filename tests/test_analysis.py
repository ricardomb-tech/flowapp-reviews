"""Pruebas de normalización de texto y del motor de análisis."""

from __future__ import annotations

import pytest

from flowapp_reviews.analysis import analyze
from flowapp_reviews.models import Review, Sentiment
from flowapp_reviews.text import normalize, strip_accents, tokenize


def review(text: str, rating: int, line: int = 1) -> Review:
    return Review(line_number=line, review_id=None, text=text, rating=rating)


class TestText:
    def test_strip_accents(self) -> None:
        assert strip_accents("aplicación rápida ñ") == "aplicacion rapida n"

    def test_normalize_colapsa_espacios_y_casing(self) -> None:
        assert normalize("  La   APLICACIÓN  ") == "la aplicacion"

    def test_tokenize_filtra_stopwords(self) -> None:
        tokens = tokenize("La aplicación es muy rápida y buena")
        assert "la" not in tokens
        assert "muy" not in tokens
        assert "aplicacion" in tokens
        assert "rapida" in tokens

    def test_tokenize_conserva_repeticiones(self) -> None:
        """'lento lento lento' expresa intensidad; no se deduplica."""
        assert tokenize("lento lento lento").count("lento") == 3

    def test_tokenize_descarta_tokens_cortos(self) -> None:
        assert tokenize("ok ya app") == ["app"]

    def test_tokenize_ignora_puntuacion(self) -> None:
        assert tokenize("¡Pésima!, terrible... app.") == [
            "pesima", "terrible", "app"
        ]


class TestSentiment:
    @pytest.mark.parametrize(
        ("rating", "expected"),
        [
            (1, Sentiment.NEGATIVO),
            (2, Sentiment.NEGATIVO),
            (3, Sentiment.NEUTRO),
            (4, Sentiment.POSITIVO),
            (5, Sentiment.POSITIVO),
        ],
    )
    def test_bandas(self, rating: int, expected: Sentiment) -> None:
        assert Sentiment.from_rating(rating) is expected


class TestAnalyze:
    def test_agrupa_por_rating(self) -> None:
        result = analyze([
            review("aplicacion lenta pesima", 1),
            review("aplicacion excelente rapida", 5),
        ])
        assert {g.label for g in result.by_rating} == {"rating_1", "rating_5"}

    def test_omite_ratings_sin_reseñas(self) -> None:
        result = analyze([review("aplicacion buena", 5)])
        assert [g.label for g in result.by_rating] == ["rating_5"]

    def test_frecuencia_correcta(self) -> None:
        result = analyze([
            review("lenta lenta pesima", 1),
            review("lenta terrible", 1),
        ])
        group = result.by_rating[0]
        counts = {w.word: w.count for w in group.top_words}
        assert counts["lenta"] == 3
        assert counts["pesima"] == 1

    def test_orden_determinista_en_empates(self) -> None:
        """Empates a igual conteo se ordenan alfabéticamente, siempre igual."""
        reviews = [review("zebra alpha", 5)]
        first = [w.word for w in analyze(reviews).by_rating[0].top_words]
        second = [w.word for w in analyze(reviews).by_rating[0].top_words]
        assert first == second == ["alpha", "zebra"]

    def test_lift_detecta_palabra_exclusiva(self) -> None:
        """Una palabra que solo aparece en un nivel debe tener lift alto."""
        result = analyze([
            review("crashea crashea aplicacion", 1),
            review("crashea crashea aplicacion", 1, line=2),
            review("aplicacion excelente aplicacion", 5),
            review("aplicacion excelente aplicacion", 5, line=4),
        ], min_count_for_lift=2)
        negativos = next(g for g in result.by_rating if g.label == "rating_1")
        top_distinctive = negativos.distinctive_words[0]
        assert top_distinctive.word == "crashea"
        assert top_distinctive.lift > 1.5

    def test_rating_promedio(self) -> None:
        result = analyze([review("a b c", 1), review("d e f", 5)])
        assert result.average_rating == pytest.approx(3.0)

    def test_distribucion_incluye_todos_los_niveles(self) -> None:
        result = analyze([review("buena app", 5)])
        assert result.rating_distribution == {1: 0, 2: 0, 3: 0, 4: 0, 5: 1}

    def test_sin_reseñas_no_explota(self) -> None:
        result = analyze([])
        assert result.by_rating == ()
        assert result.average_rating == 0.0
