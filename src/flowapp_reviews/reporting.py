"""Generación del resumen en tres formatos.

Consola para el evaluador que solo corre el script, JSON para que la salida
sea consumible por otro proceso, y Markdown para pegar en un informe.
La lógica de análisis no sabe nada de formato: esta capa solo presenta.
"""

from __future__ import annotations

import json
from typing import Any

from .analysis import AnalysisResult, GroupAnalysis
from .models import CleaningReport

_BAR_WIDTH = 24


def _bar(value: int, maximum: int) -> str:
    """Barra ASCII proporcional, para leer la distribución de un vistazo."""
    if maximum <= 0:
        return ""
    filled = round(_BAR_WIDTH * value / maximum)
    return "█" * filled + "·" * (_BAR_WIDTH - filled)


def render_console(cleaning: CleaningReport, analysis: AnalysisResult) -> str:
    """Resumen legible en terminal."""
    lines: list[str] = []
    add = lines.append

    add("=" * 68)
    add("  FLOWAPP · ANÁLISIS DE RESEÑAS DE USUARIOS")
    add("=" * 68)

    add("")
    add("── 1. LIMPIEZA ".ljust(68, "─"))
    add(f"  Filas leídas          : {cleaning.total_input}")
    add(f"  Reseñas válidas       : {cleaning.total_valid}")
    add(f"  Filas descartadas     : {cleaning.total_rejected}")
    add(f"  Tasa de retención     : {cleaning.retention_rate:.1%}")

    reasons = cleaning.rejections_by_reason()
    if reasons:
        add("")
        add("  Motivos de descarte:")
        for reason, count in sorted(
            reasons.items(), key=lambda kv: (-kv[1], kv[0].value)
        ):
            add(f"    · {reason.value:<26} {count:>4}")

    add("")
    add("── 2. DISTRIBUCIÓN DE RATINGS ".ljust(68, "─"))
    peak = max(analysis.rating_distribution.values(), default=0)
    for rating, count in sorted(analysis.rating_distribution.items()):
        share = count / cleaning.total_valid if cleaning.total_valid else 0.0
        add(f"  {rating} ★  {_bar(count, peak)}  {count:>4}  ({share:>5.1%})")
    add(f"\n  Rating promedio       : {analysis.average_rating:.2f} / 5.00")
    add(f"  Rating mediana        : {analysis.median_rating:.2f} / 5.00")

    add("")
    add("── 3. PALABRAS MÁS FRECUENTES POR NIVEL DE RATING ".ljust(68, "─"))
    for group in analysis.by_rating:
        add("")
        add(f"  ▸ {group.label.upper()}  "
            f"({group.review_count} reseñas · {group.token_count} tokens · "
            f"{group.average_length_words:.1f} palabras/reseña)")
        if not group.top_words:
            add("      (sin tokens analizables)")
            continue
        add("      Frecuentes : "
            + ", ".join(f"{w.word} ({w.count})" for w in group.top_words))
        if group.distinctive_words:
            add("      Distintivas: "
                + ", ".join(
                    f"{w.word} (×{w.lift:.1f})" for w in group.distinctive_words[:6]
                ))

    add("")
    add("── 4. PALABRAS MÁS FRECUENTES POR SENTIMIENTO ".ljust(68, "─"))
    for group in analysis.by_sentiment:
        top = ", ".join(f"{w.word} ({w.count})" for w in group.top_words[:8])
        add(f"  ▸ {group.label.upper():<10} ({group.review_count} reseñas): {top}")

    add("")
    add("── 5. CONCLUSIONES ".ljust(68, "─"))
    for line in build_insights(cleaning, analysis):
        add(f"  • {line}")

    add("")
    add("=" * 68)
    return "\n".join(lines)


def build_insights(
    cleaning: CleaningReport, analysis: AnalysisResult
) -> list[str]:
    """Deriva conclusiones en lenguaje natural a partir de los números.

    Son reglas deterministas sobre los agregados, no interpretación libre:
    cada frase se puede rastrear al dato que la produce.
    """
    insights: list[str] = []

    insights.append(
        f"Se descartó el {1 - cleaning.retention_rate:.1%} del dataset "
        f"({cleaning.total_rejected} de {cleaning.total_input} filas) por "
        f"nulos, ratings inválidos o duplicados."
    )

    reasons = cleaning.rejections_by_reason()
    if reasons:
        top_reason, top_count = max(reasons.items(), key=lambda kv: kv[1])
        insights.append(
            f"El defecto dominante fue '{top_reason.value}' con {top_count} casos."
        )

    if analysis.average_rating:
        verdict = (
            "percepción mayoritariamente positiva"
            if analysis.average_rating >= 3.5
            else "percepción mayoritariamente negativa"
            if analysis.average_rating <= 2.5
            else "percepción dividida"
        )
        insights.append(
            f"Rating promedio {analysis.average_rating:.2f}/5 → {verdict}."
        )

    negatives = next(
        (g for g in analysis.by_sentiment if g.label == "negativo"), None
    )
    if negatives and negatives.distinctive_words:
        words = ", ".join(w.word for w in negatives.distinctive_words[:4])
        insights.append(
            f"Los detractores se diferencian por hablar de: {words}. "
            f"Ahí está el backlog de producto."
        )

    positives = next(
        (g for g in analysis.by_sentiment if g.label == "positivo"), None
    )
    if positives and positives.distinctive_words:
        words = ", ".join(w.word for w in positives.distinctive_words[:4])
        insights.append(
            f"Los promotores se diferencian por hablar de: {words}. "
            f"Ahí está el mensaje de marketing."
        )

    if (
        negatives
        and positives
        and negatives.average_length_words
        and positives.average_length_words
        and negatives.average_length_words > positives.average_length_words * 1.2
    ):
        insights.append(
            f"Las reseñas negativas son más largas "
            f"({negatives.average_length_words:.1f} vs "
            f"{positives.average_length_words:.1f} palabras): el usuario "
            f"molesto explica, el satisfecho solo aprueba."
        )

    return insights


def _group_to_dict(group: GroupAnalysis) -> dict[str, Any]:
    return {
        "label": group.label,
        "review_count": group.review_count,
        "token_count": group.token_count,
        "unique_tokens": group.unique_tokens,
        "average_length_words": round(group.average_length_words, 2),
        "top_words": [
            {"word": w.word, "count": w.count} for w in group.top_words
        ],
        "distinctive_words": [
            {"word": w.word, "count": w.count, "lift": round(w.lift, 3)}
            for w in group.distinctive_words
        ],
    }


def render_json(cleaning: CleaningReport, analysis: AnalysisResult) -> str:
    """Serializa el resultado completo. `ensure_ascii=False` conserva tildes."""
    payload: dict[str, Any] = {
        "cleaning": {
            "total_input": cleaning.total_input,
            "total_valid": cleaning.total_valid,
            "total_rejected": cleaning.total_rejected,
            "retention_rate": round(cleaning.retention_rate, 4),
            "rejections_by_reason": {
                reason.value: count
                for reason, count in cleaning.rejections_by_reason().items()
            },
        },
        "summary": {
            "average_rating": round(analysis.average_rating, 3),
            "median_rating": round(analysis.median_rating, 3),
            "rating_distribution": analysis.rating_distribution,
            "global_top_words": [
                {"word": w.word, "count": w.count}
                for w in analysis.global_top_words
            ],
        },
        "by_rating": [_group_to_dict(g) for g in analysis.by_rating],
        "by_sentiment": [_group_to_dict(g) for g in analysis.by_sentiment],
        "insights": build_insights(cleaning, analysis),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_markdown(cleaning: CleaningReport, analysis: AnalysisResult) -> str:
    """Informe en Markdown, listo para pegar en el correo de entrega."""
    lines: list[str] = ["# FlowApp — Análisis de reseñas\n"]

    lines.append("## Limpieza\n")
    lines.append("| Métrica | Valor |")
    lines.append("| --- | ---: |")
    lines.append(f"| Filas leídas | {cleaning.total_input} |")
    lines.append(f"| Reseñas válidas | {cleaning.total_valid} |")
    lines.append(f"| Descartadas | {cleaning.total_rejected} |")
    lines.append(f"| Retención | {cleaning.retention_rate:.1%} |")
    for reason, count in sorted(
        cleaning.rejections_by_reason().items(), key=lambda kv: -kv[1]
    ):
        lines.append(f"| ↳ {reason.value} | {count} |")

    lines.append("\n## Resumen estadístico\n")
    lines.append("| Métrica | Valor |")
    lines.append("| --- | ---: |")
    lines.append(f"| Rating promedio | {analysis.average_rating:.2f} / 5.00 |")
    lines.append(f"| Rating mediana | {analysis.median_rating:.2f} / 5.00 |")
    for rating, count in sorted(analysis.rating_distribution.items()):
        share = count / cleaning.total_valid if cleaning.total_valid else 0.0
        lines.append(f"| Distribución {rating} ★ | {count} ({share:.1%}) |")

    lines.append("\n## Palabras por nivel de rating\n")
    lines.append("| Nivel | Reseñas | Más frecuentes | Más distintivas |")
    lines.append("| --- | ---: | --- | --- |")
    for group in analysis.by_rating:
        frequent = ", ".join(f"{w.word} ({w.count})" for w in group.top_words[:6])
        distinctive = ", ".join(
            f"{w.word}" for w in group.distinctive_words[:4]
        ) or "—"
        lines.append(
            f"| {group.label} | {group.review_count} | {frequent} | {distinctive} |"
        )

    lines.append("\n## Conclusiones\n")
    for insight in build_insights(cleaning, analysis):
        lines.append(f"- {insight}")

    return "\n".join(lines) + "\n"
