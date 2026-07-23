"""Pruebas del pipeline de limpieza.

Cada defecto que el enunciado dice haber inyectado tiene aquí una prueba
que demuestra que se detecta y se contabiliza con el motivo correcto.
"""

from __future__ import annotations

import pytest

from flowapp_reviews.cleaning import clean, parse_rating
from flowapp_reviews.models import RawReview, RejectionReason


def raw(line: int, text: str | None, rating: str | None) -> RawReview:
    return RawReview(line_number=line, review_id=f"RV-{line}", text=text, rating=rating)


class TestParseRating:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("1", 1), ("5", 5), ("3", 3), (" 4 ", 4), ("4.0", 4), ("2,0", 2)],
    )
    def test_acepta_valores_validos(self, value: str, expected: int) -> None:
        rating, reason = parse_rating(value)
        assert rating == expected
        assert reason is None

    @pytest.mark.parametrize("value", ["cinco", "★★★", "abc", "N/A!"])
    def test_rechaza_no_numericos(self, value: str) -> None:
        rating, reason = parse_rating(value)
        assert rating is None
        assert reason is RejectionReason.RATING_NO_NUMERICO

    @pytest.mark.parametrize("value", ["0", "6", "10", "-1", "4.5", "99"])
    def test_rechaza_fuera_de_rango(self, value: str) -> None:
        rating, reason = parse_rating(value)
        assert rating is None
        assert reason is RejectionReason.RATING_FUERA_DE_RANGO


class TestClean:
    def test_descarta_texto_nulo_o_vacio(self) -> None:
        report = clean([raw(2, None, "5"), raw(3, "   ", "4")])
        assert report.total_valid == 0
        assert report.rejections_by_reason() == {RejectionReason.TEXTO_NULO: 2}

    def test_descarta_rating_nulo(self) -> None:
        report = clean([raw(2, "Buena app", None)])
        assert report.total_valid == 0
        assert report.rejections[0].reason is RejectionReason.RATING_NULO

    def test_descarta_duplicado_exacto(self) -> None:
        report = clean([raw(2, "Buena app", "5"), raw(3, "Buena app", "5")])
        assert report.total_valid == 1
        assert report.rejections[0].reason is RejectionReason.DUPLICADO_EXACTO

    def test_descarta_duplicado_normalizado(self) -> None:
        """Mismo contenido con distinto casing, tildes y espaciado."""
        report = clean([
            raw(2, "La aplicación es rápida", "5"),
            raw(3, "LA APLICACION  ES RAPIDA  ", "5"),
        ])
        assert report.total_valid == 1
        assert report.rejections[0].reason is RejectionReason.DUPLICADO_NORMALIZADO

    def test_mismo_texto_distinto_rating_no_es_duplicado(self) -> None:
        """Dos usuarios pueden escribir lo mismo y puntuar distinto."""
        report = clean([raw(2, "Buena app", "5"), raw(3, "Buena app", "3")])
        assert report.total_valid == 2

    def test_conserva_la_primera_aparicion(self) -> None:
        report = clean([raw(2, "Buena app", "5"), raw(9, "Buena app", "5")])
        assert report.reviews[0].line_number == 2

    def test_contabiliza_todo_lo_que_entra(self) -> None:
        """Invariante: válidas + rechazadas == total leído. Nada se pierde."""
        rows = [
            raw(2, "Excelente", "5"),
            raw(3, None, "4"),
            raw(4, "Mala", "0"),
            raw(5, "Excelente", "5"),
            raw(6, "Regular", None),
        ]
        report = clean(rows)
        assert report.total_input == 5
        assert report.total_valid + report.total_rejected == report.total_input

    def test_tasa_de_retencion(self) -> None:
        report = clean([raw(2, "Buena", "5"), raw(3, None, "5")])
        assert report.retention_rate == pytest.approx(0.5)

    def test_dataset_vacio_no_explota(self) -> None:
        report = clean([])
        assert report.total_input == 0
        assert report.retention_rate == 0.0
