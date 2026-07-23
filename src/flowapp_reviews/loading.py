"""Carga del dataset de entrada.

Soporta CSV y JSON/JSONL, y detecta los nombres de columna automáticamente.
Esto es deliberado: el dataset real puede traer `review`, `texto`, `comment`
o `body` como columna de texto. En vez de hardcodear un esquema y romperme
con el archivo real, mapeo alias conocidos y fallo con un mensaje claro si
no reconozco nada.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, Final

from .models import RawReview

# Alias aceptados por campo, en orden de preferencia.
TEXT_ALIASES: Final[tuple[str, ...]] = (
    "review_text", "reviewtext", "text", "texto", "review", "resena",
    "reseña", "comment", "comentario", "body", "content", "opinion",
)
RATING_ALIASES: Final[tuple[str, ...]] = (
    "rating", "score", "stars", "estrellas", "puntuacion", "puntuación",
    "calificacion", "calificación", "nota", "valoracion",
)
ID_ALIASES: Final[tuple[str, ...]] = (
    "id", "review_id", "reviewid", "uuid", "identificador", "user_id",
)


class DatasetFormatError(ValueError):
    """El archivo no tiene columnas reconocibles de texto y/o rating."""


def _canonical(name: str) -> str:
    """Normaliza un nombre de columna para comparar contra los alias."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _resolve_column(
    headers: Sequence[str], aliases: Sequence[str]
) -> str | None:
    """Devuelve el header original que corresponde al primer alias que exista."""
    lookup = {_canonical(h): h for h in headers}
    for alias in aliases:
        if alias in lookup:
            return lookup[alias]
    # Fallback: coincidencia parcial ('star_rating' contiene 'rating').
    for alias in aliases:
        for canonical, original in lookup.items():
            if alias in canonical:
                return original
    return None


def _as_optional_str(value: Any) -> str | None:
    """Convierte un valor crudo a str, tratando null/NaN/'' como ausencia.

    Los datasets sucios expresan 'nulo' de muchas formas: `None`, cadena
    vacía, `"null"`, `"NaN"`, `"N/A"`. Todas colapsan aquí a `None` para que
    la capa de limpieza tenga un único caso que manejar.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "nan", "n/a", "na", "-"}:
        return None
    return text


def load_records(path: Path) -> list[RawReview]:
    """Lee el dataset y devuelve filas crudas sin validar.

    Raises:
        FileNotFoundError: Si la ruta no existe.
        DatasetFormatError: Si no se reconocen las columnas requeridas.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {path}")

    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl", ".ndjson"}:
        rows = list(_iter_json_rows(path))
    else:
        rows = list(_iter_csv_rows(path))

    if not rows:
        return []

    headers = list(rows[0].keys())
    text_col = _resolve_column(headers, TEXT_ALIASES)
    rating_col = _resolve_column(headers, RATING_ALIASES)
    id_col = _resolve_column(headers, ID_ALIASES)

    if text_col is None or rating_col is None:
        raise DatasetFormatError(
            "No se identificaron las columnas de texto y/o rating. "
            f"Columnas encontradas: {headers}. "
            f"Alias esperados para texto: {TEXT_ALIASES[:5]}... "
            f"Alias esperados para rating: {RATING_ALIASES[:5]}..."
        )

    return [
        RawReview(
            line_number=index,
            review_id=_as_optional_str(row.get(id_col)) if id_col else None,
            text=_as_optional_str(row.get(text_col)),
            rating=_as_optional_str(row.get(rating_col)),
        )
        # enumerate desde 2: la línea 1 del CSV es el header, así el número
        # reportado coincide con lo que ve el evaluador si abre el archivo.
        for index, row in enumerate(rows, start=2)
    ]


def _iter_csv_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Lee CSV detectando el delimitador (coma, punto y coma o tab)."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # Fallback razonable: CSV con comas.
        yield from csv.DictReader(handle, dialect=dialect)


def _iter_json_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Lee JSON (array de objetos) o JSONL (un objeto por línea)."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return
    if raw.lstrip().startswith("["):
        payload = json.loads(raw)
        yield from (row for row in payload if isinstance(row, dict))
        return
    for line in raw.splitlines():
        line = line.strip()
        if line:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                yield parsed
