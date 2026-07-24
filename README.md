# FlowApp Reviews Analyzer

Herramienta para limpiar y analizar un dataset de reseñas de **FlowApp**. El
programa detecta datos inválidos, elimina duplicados, analiza las palabras más
frecuentes por nivel de calificación y genera reportes en consola, JSON o
Markdown.

> Solución desarrollada para el reto **EPAM · Python Run, Debug the Future –
> Reto 1 "Bienvenida al Reto"**.

---

## Características

- Limpieza de datos con reglas explícitas.
- Validación de ratings y eliminación de registros inválidos.
- Detección de duplicados exactos y normalizados.
- Análisis de palabras más frecuentes por nivel de rating.
- Identificación de palabras distintivas mediante la métrica **lift**.
- Reportes en consola, JSON y Markdown.
- Implementado únicamente con la librería estándar de Python.

---

# Requisitos

- Python **3.11** o superior.

No es necesario instalar dependencias adicionales.

---

# Ejecución

Con el dataset proporcionado por EPAM:

```bash
python -m flowapp_reviews data/resenas_flowapp.csv
```

También es posible analizar archivos **CSV**, **JSON** (array de objetos) y
**JSONL**.

## Opciones disponibles

```text
python -m flowapp_reviews DATASET \
    [-f {console,json,markdown}] \
    [-o SALIDA] \
    [-n TOP] \
    [--min-lift-count N]
```

| Opción | Descripción | Valor por defecto |
| ------- | ----------- | ----------------- |
| `-f`, `--format` | Formato de salida | `console` |
| `-o`, `--output` | Archivo de salida | stdout |
| `-n`, `--top` | Número de palabras por grupo | `10` |
| `--min-lift-count` | Mínimo de apariciones para calcular lift | `2` |

### Códigos de salida

| Código | Significado |
| ------- | ----------- |
| `0` | Ejecución correcta |
| `2` | Error de uso (archivo inexistente, argumentos inválidos, etc.) |
| `3` | Error de datos (dataset vacío, columnas inválidas o ninguna fila válida) |

---

# Formatos de entrada

Se aceptan:

- CSV (delimitador autodetectado: `,`, `;`, `|` o tabulador).
- JSON (array de objetos).
- JSONL.

Las columnas pueden tener distintos nombres gracias a un sistema de alias.
Por ejemplo:

| Texto | Rating |
| ------ | ------ |
| `review_text` | `rating` |
| `texto` | `calificacion` |
| `comment` | `stars` |
| `body` | `estrellas` |

---

# Reglas de limpieza

| Defecto encontrado | Acción |
| ------------------ | ------ |
| Texto vacío o nulo | Se descarta |
| Rating vacío | Se descarta |
| Rating no numérico | Se descarta |
| Rating fuera del rango 1–5 | Se descarta |
| Duplicado exacto | Se conserva la primera aparición |
| Duplicado normalizado | Se conserva la primera aparición |

Se aceptan como válidos valores como:

```
4
4.0
4,0
 5
```

Cada registro descartado queda documentado con el motivo correspondiente.
Ninguna fila se elimina de forma silenciosa.

---

# Análisis realizado

El programa calcula:

- palabras más frecuentes por rating;
- palabras distintivas mediante **lift**;
- distribución de ratings;
- promedio y mediana;
- agrupación por sentimiento:

| Banda | Ratings |
| ------ | ------- |
| Negativo | 1–2 |
| Neutro | 3 |
| Positivo | 4–5 |

La métrica **lift** permite identificar palabras que aparecen con una frecuencia
mayor de la esperada dentro de un grupo determinado.

```
lift = frecuencia relativa en el grupo / frecuencia relativa global
```

---

# Arquitectura

```
src/flowapp_reviews/
├── cli.py
├── loading.py
├── cleaning.py
├── analysis.py
├── reporting.py
├── text.py
└── models.py
```

La descripción detallada de la arquitectura, los diagramas y las decisiones de
diseño se encuentran en la carpeta **docs/**.

---


# Calidad

El proyecto incluye verificaciones automáticas para mantener la calidad del
código.

```bash
make check
```

Este comando ejecuta:

- **Ruff** para análisis de estilo y posibles errores.
- **mypy --strict** para la verificación estática de tipos.
- **pytest** para ejecutar la suite de pruebas automatizadas.

---

# Limitaciones conocidas

- No se realiza stemming ni lematización.
- No se detectan n-gramas como `"no funciona"`.
- No se detecta automáticamente el idioma de la reseña.

Estas limitaciones fueron aceptadas para mantener el proyecto libre de
dependencias externas y centrado en los objetivos del reto.

---

# Documentación

| Documento | Descripción |
| ---------- | ----------- |
| `docs/ARCHITECTURE.md` | Arquitectura del proyecto. |
| `docs/adr/` | Registro de decisiones de arquitectura (Architecture Decision Records). |


---

## Nota

El proyecto incluye el script `scripts/generate_sample_data.py`, que permite
crear un dataset de ejemplo para realizar pruebas locales. Sin embargo, para la
evaluación del reto debe utilizarse el dataset proporcionado por EPAM.

---

## Autor

**Ricardo Martinez B**

GitHub: https://github.com/ricardomb-tech