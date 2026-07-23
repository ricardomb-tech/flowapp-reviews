"""Pruebas de carga de archivos y del pipeline completo end-to-end."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flowapp_reviews.analysis import analyze
from flowapp_reviews.cleaning import clean
from flowapp_reviews.cli import EXIT_DATA, EXIT_OK, EXIT_USAGE, main
from flowapp_reviews.loading import DatasetFormatError, load_records

CSV_CONTENT = """review_id,review_text,rating
RV-1,La aplicación es rapidísima y muy intuitiva,5
RV-2,Se cierra sola todo el tiempo pésima,1
RV-3,,4
RV-4,Buena app pero le faltan funciones,3
RV-5,Cobraron sin avisar terrible soporte,1
RV-6,La aplicación es rapidísima y muy intuitiva,5
RV-7,Excelente diseño muy intuitiva,
RV-8,Aplicación regular sin más,siete
RV-9,Muy lenta y consume batería,2
RV-10,Increíble organización de tareas,5
"""


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    path = tmp_path / "reviews.csv"
    path.write_text(CSV_CONTENT, encoding="utf-8")
    return path


class TestLoading:
    def test_lee_csv(self, csv_path: Path) -> None:
        rows = load_records(csv_path)
        assert len(rows) == 10
        assert rows[0].text.startswith("La aplicación")
        assert rows[0].rating == "5"

    def test_numeracion_de_linea_coincide_con_el_archivo(self, csv_path: Path) -> None:
        """La fila 1 es el header, así que la primera reseña es la línea 2."""
        assert load_records(csv_path)[0].line_number == 2

    def test_celda_vacia_se_convierte_en_none(self, csv_path: Path) -> None:
        rows = load_records(csv_path)
        assert rows[2].text is None   # RV-3
        assert rows[6].rating is None  # RV-7

    def test_detecta_alias_de_columnas(self, tmp_path: Path) -> None:
        path = tmp_path / "alt.csv"
        path.write_text("comentario;estrellas\nMuy buena;5\n", encoding="utf-8")
        rows = load_records(path)
        assert rows[0].text == "Muy buena"
        assert rows[0].rating == "5"

    def test_lee_json(self, tmp_path: Path) -> None:
        path = tmp_path / "reviews.json"
        path.write_text(
            json.dumps([{"text": "Excelente app", "rating": 5}]), encoding="utf-8"
        )
        assert load_records(path)[0].text == "Excelente app"

    def test_lee_jsonl(self, tmp_path: Path) -> None:
        path = tmp_path / "reviews.jsonl"
        path.write_text(
            '{"text": "Buena", "rating": 4}\n{"text": "Mala", "rating": 1}\n',
            encoding="utf-8",
        )
        assert len(load_records(path)) == 2

    def test_columnas_irreconocibles_fallan_con_mensaje_claro(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "bad.csv"
        path.write_text("columna_a,columna_b\n1,2\n", encoding="utf-8")
        with pytest.raises(DatasetFormatError, match="columna_a"):
            load_records(path)

    def test_archivo_inexistente(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_records(tmp_path / "no_existe.csv")


class TestEndToEnd:
    def test_pipeline_completo(self, csv_path: Path) -> None:
        report = clean(load_records(csv_path))
        # 10 filas: 1 texto nulo, 1 rating nulo, 1 rating no numérico,
        # 1 duplicado exacto → 6 válidas.
        assert report.total_input == 10
        assert report.total_valid == 6
        assert report.total_rejected == 4

        result = analyze(report.reviews)
        assert result.average_rating > 0
        assert sum(result.rating_distribution.values()) == 6


class TestCli:
    def test_salida_ok(self, csv_path: Path, capsys: pytest.CaptureFixture) -> None:
        assert main([str(csv_path)]) == EXIT_OK
        assert "LIMPIEZA" in capsys.readouterr().out

    def test_json_es_parseable(self, csv_path: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.json"
        assert main([str(csv_path), "--format", "json", "-o", str(out)]) == EXIT_OK
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["cleaning"]["total_valid"] == 6
        assert payload["by_rating"]

    def test_markdown_se_genera(self, csv_path: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.md"
        assert main([str(csv_path), "-f", "markdown", "-o", str(out)]) == EXIT_OK
        assert "# FlowApp" in out.read_text(encoding="utf-8")

    def test_archivo_inexistente_devuelve_codigo_de_uso(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "nope.csv")]) == EXIT_USAGE

    def test_dataset_sin_filas_validas(self, tmp_path: Path) -> None:
        path = tmp_path / "todo_malo.csv"
        path.write_text("review_text,rating\n,\n,\n", encoding="utf-8")
        assert main([str(path)]) == EXIT_DATA

    def test_top_invalido(self, csv_path: Path) -> None:
        assert main([str(csv_path), "--top", "0"]) == EXIT_USAGE
