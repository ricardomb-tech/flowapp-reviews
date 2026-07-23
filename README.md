# FlowApp — Análisis de reseñas de usuarios

Limpieza y análisis de un dataset de reseñas de FlowApp (texto libre + rating 1-5)
que contiene **datos nulos, ratings inválidos y duplicados inyectados a propósito**.

El programa limpia el dataset, calcula las palabras más frecuentes por nivel de
rating y produce un resumen ejecutable en consola, JSON o Markdown.

> EPAM · Python Run, Debug the Future — Reto 1 "Bienvenida al Reto".

---

## Ejecución rápida

Requiere **Python 3.11+**. No hay que instalar nada.

```bash
# 1. Generar un dataset de muestra con los mismos defectos que el original
python scripts/generate_sample_data.py data/reviews_sample.csv

# 2. Analizarlo
python -m flowapp_reviews data/reviews_sample.csv
```

Con el dataset oficial:

```bash
python -m flowapp_reviews ruta/al/dataset.csv
```

### Opciones

```
python -m flowapp_reviews DATASET [-f {console,json,markdown}] [-o SALIDA]
                                  [-n TOP] [--min-lift-count N]
```

| Opción | Descripción | Defecto |
| --- | --- | --- |
| `-f, --format` | Formato de salida | `console` |
| `-o, --output` | Archivo destino (si se omite, stdout) | — |
| `-n, --top` | Palabras a reportar por grupo | `10` |
| `--min-lift-count` | Apariciones mínimas para el ranking de distintivas | `2` |

Códigos de salida: `0` OK · `2` error de uso (archivo inexistente, argumento
inválido) · `3` error de datos (dataset vacío, columnas irreconocibles,
ninguna fila válida).

### Verificación

```bash
make check     # ruff + mypy --strict + pytest con cobertura
```

**Estado actual: 59 pruebas en verde · 94% de cobertura · `mypy --strict` sin
errores · `ruff` sin advertencias.**

---

## Formatos de entrada

Se aceptan **CSV** (delimitador autodetectado: `,` `;` `\t` `|`), **JSON**
(array de objetos) y **JSONL**. Los nombres de columna se resuelven por alias,
así que el script funciona con `review_text`, `texto`, `comment`, `body`…
y con `rating`, `stars`, `estrellas`, `calificacion`… sin tocar código.

---

## Reglas de limpieza

| Defecto | Regla | Motivo registrado |
| --- | --- | --- |
| Texto ausente o en blanco | Se descarta la fila | `texto_nulo_o_vacio` |
| Rating ausente | Se descarta la fila | `rating_nulo_o_vacio` |
| Rating no numérico (`"cinco"`, `"★★★"`) | Se descarta | `rating_no_numerico` |
| Rating fuera de 1-5 (`0`, `6`, `-1`, `4.5`) | Se descarta | `rating_fuera_de_rango` |
| Texto y rating idénticos a una fila previa | Se conserva la primera | `duplicado_exacto` |
| Igual tras normalizar (tildes, casing, espacios) | Se conserva la primera | `duplicado_normalizado` |

Se aceptan como válidos: `"4"`, `"4.0"`, `"4,0"`, `" 5 "`.

**Ninguna fila se descarta en silencio.** Cada rechazo queda registrado con su
número de línea y su motivo, y el reporte final verifica el invariante
`válidas + rechazadas == total leído`.

---

## Análisis

Además de las palabras más frecuentes por nivel de rating (lo que pide el
enunciado), se reportan las **palabras distintivas** de cada nivel:

```
lift(palabra, nivel) = frecuencia relativa en el nivel / frecuencia relativa global
```

**Por qué.** Las palabras más frecuentes en rating 1 y en rating 5 tienden a ser
casi las mismas — `app`, `flowapp`, `funciona` — porque son el tema del que
todos hablan. La pregunta útil de negocio no es qué se repite, sino qué se dice
en un nivel **y no en los otros**. Un lift de 3.0 indica que la palabra aparece
3 veces más de lo esperado en ese grupo. `--min-lift-count` evita que una
palabra que aparece una sola vez, con lift altísimo, desplace señal real.

También se agrupa por bandas de sentimiento (negativo 1-2, neutro 3, positivo 4-5),
porque con datasets pequeños los conteos por rating individual quedan demasiado
dispersos para ver patrones.

---

## Arquitectura

```
src/flowapp_reviews/
├── models.py      Tipos del dominio (frozen dataclasses, enums)
├── loading.py     Lectura de CSV/JSON/JSONL y resolución de columnas
├── cleaning.py    Validación, coerción de ratings y deduplicación
├── text.py        Normalización, tokenización y stopwords ES + EN
├── analysis.py    Frecuencias por grupo y cálculo de lift
├── reporting.py   Presentación en consola, JSON y Markdown
└── cli.py         Argumentos, orquestación y códigos de salida
```

Cada capa depende solo de las anteriores. `analysis.py` no sabe nada de
archivos; `reporting.py` no sabe nada de formatos de entrada. Eso permite
probar la lógica sin tocar disco — y es la razón de que 59 pruebas corran en
menos de un segundo.

---

## Decisiones técnicas

### 1. Cero dependencias: solo librería estándar

Lo natural sería pandas. **No se usó, deliberadamente.**

`csv`, `collections.Counter`, `unicodedata` y `re` resuelven este problema
completo sin traer 30 MB de dependencias transitivas. A cambio se gana: el
proyecto corre en cualquier Python 3.11+ sin instalar nada, el arranque es
inmediato, y no hay riesgo de que el evaluador se quede atascado en un
`pip install`.

El intercambio es real y lo asumo: con un dataset de millones de filas, pandas
o Polars ganarían por rendimiento y expresividad. Para un dataset de reseñas
de una app, la librería estándar es suficiente y la simplicidad operativa vale
más que el rendimiento que no se necesita.

### 2. Descartar, no imputar

Las filas con rating nulo o inválido **se descartan, no se rellenan**. Imputar
el rating promedio movería reseñas a grupos a los que no pertenecen y
contaminaría exactamente lo que se está midiendo: qué palabras corresponden a
qué nivel de satisfacción. Un dataset más pequeño y correcto vale más que uno
completo e inventado.

Por la misma razón, `4.5` se rechaza en vez de redondearse: no es un nivel de
la escala, y redondear lo asignaría arbitrariamente a un grupo.

### 3. Deduplicación en dos niveles

El duplicado exacto es el caso obvio. El interesante es el "casi duplicado":
el mismo texto con distinto casing, tildes o espaciado, que un `==` no detecta
pero que es claramente el mismo contenido. Se resuelve comparando la forma
normalizada.

La clave de deduplicación incluye el rating: **dos usuarios pueden escribir
"Muy buena app" y puntuar 5 y 3 respectivamente**. Eso no es un duplicado, son
dos opiniones distintas y ambas deben contar.

### 4. Salida determinista

`Counter.most_common()` no garantiza el orden entre elementos empatados. Todos
los rankings se reordenan explícitamente por `(-conteo, palabra)`, de modo que
dos ejecuciones sobre el mismo dataset producen byte por byte la misma salida.
Sin eso, las pruebas serían intermitentes y el resultado no sería reproducible.

### 5. Normalización agresiva del texto

Se eliminan tildes antes de tokenizar: en un dataset real de usuarios
hispanohablantes, `aplicación` y `aplicacion` son la misma palabra y la mitad
de la gente no pone tildes. Se filtran stopwords en español **e inglés**, porque
las reseñas de apps suelen venir mezcladas.

Se conservan las repeticiones dentro de una misma reseña: que alguien escriba
"lento lento lento" es información sobre intensidad, no ruido.

---

## Pruebas

```
tests/
├── test_cleaning.py   Validación de ratings, nulos, duplicados, invariantes
├── test_analysis.py   Normalización, tokenización, frecuencias, lift
└── test_pipeline.py   Carga de archivos, end-to-end y CLI
```

Cada defecto que el enunciado declara haber inyectado tiene su prueba
correspondiente. Se cubren además los casos borde: dataset vacío, dataset sin
ninguna fila válida, columnas irreconocibles, archivo inexistente y empates en
los rankings.

---

## Limitaciones conocidas

- **No hay stemming ni lematización**: `lento` y `lenta` se cuentan por separado.
  Resolverlo bien exige NLTK o spaCy, lo que rompería la decisión de cero
  dependencias. Con el volumen de un dataset de reseñas, el impacto es menor.
- **No hay detección de n-gramas**: `no funciona` se cuenta como `funciona`
  (`no` es stopword). Es la limitación más relevante y sería la primera mejora:
  bigramas resolverían las negaciones, que son justamente lo que importa en
  reseñas negativas.
- **El idioma no se detecta**: se filtran stopwords de ambos idiomas siempre.
  Es una simplificación que funciona bien mientras el vocabulario no colisione.

---

Ricardo Martinez B · [`ricardomb-tech`](https://github.com/ricardomb-tech)
