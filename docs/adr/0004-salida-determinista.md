# ADR-0004: Garantizar resultados deterministas en los rankings

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Decisores:** Ricardo Martinez B

## Contexto

Uno de los objetivos del proyecto es que el análisis produzca siempre el mismo
resultado cuando se ejecuta sobre el mismo dataset. Esto facilita la revisión
del código, la comparación de resultados y la ejecución de pruebas
automatizadas.

Durante el desarrollo surgió un detalle importante: `Counter.most_common()`
ordena correctamente por frecuencia, pero cuando varias palabras tienen el
mismo número de apariciones el orden entre ellas no está garantizado. En la
práctica, dos ejecuciones pueden generar rankings con el mismo contenido pero
en distinto orden.

Aunque el análisis siga siendo correcto, esa variación dificulta comparar
reportes y puede provocar fallos en pruebas que esperan una salida idéntica.

## Decisión

Definir un criterio de ordenamiento explícito para todos los rankings
generados por la aplicación.

Se aplican las siguientes reglas:

- **Palabras más frecuentes:** primero por cantidad de apariciones (de mayor a
  menor) y, en caso de empate, por orden alfabético.
- **Palabras distintivas (lift):** primero por valor de *lift* (de mayor a
  menor), luego por frecuencia y finalmente por orden alfabético.

De esta manera, un mismo conjunto de datos siempre produce exactamente el mismo
resultado.

## Consecuencias

### Positivas

- La salida es completamente reproducible entre ejecuciones.
- Los reportes en consola, JSON y Markdown mantienen siempre el mismo orden.
- Las pruebas automatizadas son estables y no presentan fallos intermitentes
  debido al orden de los empates.
- Facilita comparar cambios entre versiones del proyecto utilizando herramientas
  como `git diff`.

### Negativas

- El criterio alfabético en los empates es una decisión técnica y no aporta un
  significado adicional al análisis.
- Requiere un paso adicional de ordenamiento antes de generar los reportes,
  aunque su impacto en rendimiento es prácticamente nulo para el tamaño del
  dataset.

## Alternativas consideradas

| Alternativa | Motivo de descarte |
| --- | --- |
| Utilizar directamente `Counter.most_common()` | El orden de los empates no está garantizado y puede variar entre ejecuciones. |
| Mantener el orden de aparición en el dataset | El resultado dependería del orden de entrada y no sería consistente si el archivo cambia de orden. |
| Ordenar únicamente por frecuencia | Los empates seguirían produciendo resultados no deterministas. |