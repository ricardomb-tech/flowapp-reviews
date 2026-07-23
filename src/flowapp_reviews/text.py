"""Normalización y tokenización de texto.

Sin dependencias externas: `unicodedata` + `re` de la librería estándar
resuelven acentos, mayúsculas y puntuación sin traer NLTK ni spaCy.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Final

# Un token es una secuencia de letras (ya sin acentos) o dígitos, de 2+ chars.
# El mínimo de 2 evita que "a", "y", "e" ensucien los conteos.
_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-z0-9]{2,}")
_WHITESPACE: Final[re.Pattern[str]] = re.compile(r"\s+")

# Stopwords ES + EN. El dataset de FlowApp puede venir mezclado, así que se
# filtran ambos idiomas. Lista curada a mano: corta, auditable, sin dependencias.
SPANISH_STOPWORDS: Final[frozenset[str]] = frozenset("""
al algo algunas algunos ante antes aqui como con contra cual cuando de del desde
donde dos el ella ellas ellos en entre era erais eran eres es esa esas ese eso
esos esta estaba estado estan estar estas este esto estos estoy fue fueron fui
ha habia han has hasta hay la las le les lo los mas me mi mia mis mucho muy nada
ni no nos nosotros o os otra otras otro otros para pero poco por porque que
quien se sea ser si siempre sin sobre solo son su sus tambien tan tanto te
tener tengo ti tiene tienen todo todos tu tus un una uno unos usted ustedes va
vamos van vez y ya yo lo les mientras hacer hace hizo etc
""".split())

ENGLISH_STOPWORDS: Final[frozenset[str]] = frozenset("""
about after all also am an and any are as at be because been before being but by
can could did do does doing don for from had has have having he her here hers
him his how if in into is it its just me more most my no nor not of off on once
only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up very was we
were what when where which while who why will with would you your
""".split())

DEFAULT_STOPWORDS: Final[frozenset[str]] = SPANISH_STOPWORDS | ENGLISH_STOPWORDS


def strip_accents(value: str) -> str:
    """Elimina tildes y diéresis vía descomposición Unicode NFKD.

    'aplicación' y 'aplicacion' deben contar como la misma palabra; en un
    dataset real de usuarios hispanohablantes, la mitad no pone tildes.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(value: str) -> str:
    """Forma canónica de un texto: sin acentos, minúsculas, espacios colapsados.

    Se usa para dos cosas distintas: tokenizar y detectar duplicados
    "casi iguales" (mismo texto con distinto casing o espaciado).
    """
    return _WHITESPACE.sub(" ", strip_accents(value).lower()).strip()


def tokenize(
    value: str,
    stopwords: Iterable[str] = DEFAULT_STOPWORDS,
    min_length: int = 3,
) -> list[str]:
    """Convierte un texto libre en la lista de tokens analizables.

    Args:
        value: Texto crudo de la reseña.
        stopwords: Palabras funcionales a excluir del análisis.
        min_length: Longitud mínima del token. Por defecto 3 porque con 2
            se cuelan restos como 'ok', 'ya', 'mm' que no aportan señal.

    Returns:
        Tokens normalizados, en orden de aparición (se conservan repeticiones:
        que alguien diga 'lento lento lento' es información).
    """
    stopword_set = frozenset(stopwords)
    return [
        token
        for token in _TOKEN_PATTERN.findall(normalize(value))
        if len(token) >= min_length and token not in stopword_set
    ]
