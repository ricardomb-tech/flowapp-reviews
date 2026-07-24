# ADR-0001: Uso exclusivo de la librería estándar de Python

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Autor:** Ricardo Martinez B

## Contexto

El reto consiste en limpiar y analizar un conjunto de reseñas con texto y calificaciones. Para este tipo de tareas, una opción común habría sido utilizar **pandas**, ya que simplifica la lectura del archivo y varias operaciones de análisis.

Sin embargo, el dataset del reto tiene un tamaño reducido y el objetivo principal no es trabajar con grandes volúmenes de datos, sino implementar correctamente el proceso de limpieza, validación y análisis.

Además, la solución debía ser fácil de ejecutar por cualquier evaluador, idealmente sin pasos adicionales de instalación.

## Decisión

Se implementó la solución utilizando únicamente módulos de la librería estándar de Python, principalmente:

- `csv`
- `json`
- `collections`
- `statistics`
- `argparse`
- `re`
- `unicodedata`

De esta forma, el proyecto puede ejecutarse con una instalación estándar de Python 3.11 o superior, sin depender de paquetes externos.

## Justificación

Para el volumen de datos del reto, la librería estándar ofrece todas las herramientas necesarias para:

- leer el dataset;
- validar y limpiar los registros;
- eliminar duplicados;
- normalizar el texto;
- calcular estadísticas descriptivas;
- obtener las palabras más frecuentes.

Incorporar una librería adicional habría simplificado algunas operaciones, pero no aportaría una ventaja significativa para este escenario.

## Consecuencias

### Ventajas

- El proyecto no requiere instalar dependencias para ejecutarse.
- La ejecución es inmediata en cualquier entorno con Python 3.11+.
- El proceso de limpieza queda implementado de forma explícita y es fácil de seguir durante una revisión técnica.

### Desventajas

- Algunas operaciones de análisis requieren más código que con pandas.
- Si el volumen de datos creciera considerablemente, sería recomendable migrar a una solución basada en pandas o Polars.

## Alternativas consideradas

| Alternativa | Motivo para no adoptarla |
|-------------|--------------------------|
| **pandas** | Muy adecuado para análisis de datos, pero el tamaño del dataset no justificaba añadir una dependencia externa. |
| **Polars** | También habría resuelto el problema correctamente, aunque para este reto no ofrecía una ventaja clara frente a una implementación con la librería estándar. |