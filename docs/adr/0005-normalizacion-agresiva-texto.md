# ADR-0005: Normalización del texto para un análisis consistente

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Decisores:** Ricardo Martinez B

## Contexto

El objetivo principal del proyecto es identificar patrones en las reseñas de
los usuarios. Para que el análisis sea confiable, palabras que representan la
misma idea deben contabilizarse como una sola.

En un conjunto de reseñas reales es común encontrar diferencias como:

- `Aplicación` y `aplicación`.
- `aplicación` y `aplicacion`.
- Espacios repetidos o puntuación innecesaria.
- Comentarios mezclando español e inglés.

Si cada una de estas variantes se tratara como una palabra distinta, las
frecuencias perderían precisión y el análisis sería menos representativo.

## Decisión

Antes de realizar cualquier conteo, todas las reseñas pasan por un proceso de
normalización compuesto por los siguientes pasos:

1. Eliminar acentos utilizando `unicodedata.normalize("NFKD")`.
2. Convertir todo el texto a minúsculas.
3. Reducir múltiples espacios consecutivos a un único espacio.
4. Extraer únicamente palabras y números mediante expresiones regulares,
   descartando signos de puntuación y otros caracteres.
5. Filtrar una lista de *stopwords* en español e inglés para eliminar palabras
   con poco valor informativo.
6. Ignorar tokens de menos de tres caracteres.
7. Conservar las repeticiones dentro de una misma reseña, ya que pueden aportar
   información sobre el énfasis del usuario (por ejemplo: *"lento lento lento"*).

## Consecuencias

### Positivas

- Palabras con diferencias de acentuación o mayúsculas se contabilizan como un
  único término.
- Se reduce el ruido generado por palabras muy frecuentes pero poco
  representativas, como artículos o preposiciones.
- El análisis refleja mejor los temas de los que realmente hablan los usuarios.
- Toda la implementación se realiza con la librería estándar de Python, sin
  incorporar dependencias adicionales.

### Negativas

- No se realiza lematización ni stemming, por lo que palabras como `lento` y
  `lenta` siguen considerándose diferentes.
- Expresiones como `no funciona` pierden parte de su significado al eliminar la
  palabra `no` como *stopword*.
- Los emojis y otros símbolos no participan en el análisis, aunque puedan
  transmitir información sobre el sentimiento del usuario.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
| --- | --- |
| Analizar el texto sin normalizar | Variantes de escritura se contabilizarían como palabras distintas, reduciendo la calidad del análisis. |
| Incorporar NLTK o spaCy para lematización | Mejoraría el procesamiento lingüístico, pero añadiría dependencias innecesarias para el alcance del reto. |
| Conservar signos de puntuación y emojis | Incrementaría el ruido en los conteos y requeriría un tratamiento específico del lenguaje natural. |