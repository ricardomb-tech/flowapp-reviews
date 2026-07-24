"""Punto de entrada por línea de comandos.

    python -m flowapp_reviews data/reviews.csv
    python -m flowapp_reviews data/reviews.csv --format json --output out.json
    python -m flowapp_reviews data/reviews.csv --top 15 --min-lift-count 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loading import DatasetFormatError
from .pipeline import EmptyDatasetError, NoValidRowsError, run_pipeline
from .reporting import render_console, render_json, render_markdown

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DATA = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowapp-reviews",
        description=(
            "Limpia el dataset de reseñas de FlowApp, calcula las palabras "
            "más frecuentes por nivel de rating y genera un resumen."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "dataset", type=Path, help="Ruta al CSV / JSON / JSONL de reseñas."
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("console", "json", "markdown"),
        default="console",
        help="Formato de salida (por defecto: console).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Archivo de salida. Si se omite, imprime en stdout.",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=10,
        help="Número de palabras a reportar por grupo (por defecto: 10).",
    )
    parser.add_argument(
        "--min-lift-count",
        type=int,
        default=2,
        help=(
            "Apariciones mínimas para considerar una palabra en el ranking "
            "de distintivas (por defecto: 2)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ejecuta el pipeline completo. Devuelve el código de salida del proceso."""
    args = build_parser().parse_args(argv)

    if args.top < 1:
        print("error: --top debe ser >= 1", file=sys.stderr)
        return EXIT_USAGE

    try:
        result = run_pipeline(
            args.dataset,
            top_n=args.top,
            min_count_for_lift=args.min_lift_count,
        )
    except FileNotFoundError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_USAGE
    except DatasetFormatError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_DATA
    except EmptyDatasetError:
        print("error: el dataset está vacío.", file=sys.stderr)
        return EXIT_DATA
    except NoValidRowsError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_DATA

    renderers = {
        "console": render_console,
        "json": render_json,
        "markdown": render_markdown,
    }
    output = renderers[args.format](result.cleaning, result.analysis)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Resultado escrito en {args.output}")
    else:
        print(output)

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
