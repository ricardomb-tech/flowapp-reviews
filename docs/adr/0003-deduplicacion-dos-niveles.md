# ADR-0003: Deduplicación de reseñas mediante comparación exacta y normalizada

- **Estado:** Aceptado
- **Fecha:** 2026-07-23
- **Autor:** Ricardo Martinez B

## Contexto

Durante la limpieza del dataset se identificó la necesidad de eliminar registros duplicados antes de realizar el análisis.

Algunos duplicados son idénticos, mientras que otros solo difieren en detalles como el uso de mayúsculas, acentos o espacios adicionales. Comparar únicamente el texto original no permite detectar estos casos.

También era importante considerar el rating como parte de la comparación. Dos usuarios pueden escribir exactamente la misma reseña y asignar calificaciones diferentes; en ese caso representan opiniones distintas y ambas deben conservarse.

## Decisión

Se implementó un proceso de deduplicación en dos etapas, conservando siempre la primera aparición de cada reseña.

1. **Duplicado exacto**

   Se compara el texto original (tras eliminar espacios al inicio y al final) junto con el rating.

   ```text
   (texto.strip(), rating)
   ```

2. **Duplicado normalizado**

   Si el registro supera la primera validación, se compara una versión normalizada del texto, donde:

   - se eliminan los acentos;
   - se convierte todo a minúsculas;
   - se reducen los espacios consecutivos a uno solo.

   La clave utilizada es:

   ```text
   (normalize(texto), rating)
   ```

## Justificación

Este enfoque permite eliminar tanto los duplicados evidentes como aquellos que solo presentan diferencias de formato, sin eliminar reseñas que realmente representan opiniones distintas.

Incluir el rating en la clave evita perder información cuando el mismo comentario aparece asociado a diferentes niveles de satisfacción.

## Consecuencias

### Ventajas

- Detecta tanto duplicados exactos como variaciones del mismo texto.
- Reduce el riesgo de contar varias veces una misma opinión.
- Conserva reseñas con el mismo contenido cuando tienen ratings diferentes.

### Desventajas

- No detecta textos con el mismo significado escritos de forma diferente (por ejemplo, *"muy lenta"* y *"va muy lento"*).
- Requiere mantener un conjunto de claves ya procesadas durante la ejecución del pipeline.

## Alternativas consideradas

| Alternativa | Motivo para no adoptarla |
|-------------|--------------------------|
| Comparar únicamente el texto original | No detecta diferencias de mayúsculas, acentos o espacios. |
| Comparar solo el texto normalizado | Eliminaría reseñas con el mismo texto pero ratings distintos, perdiendo información relevante para el análisis. |