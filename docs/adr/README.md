# Architecture Decision Records (ADR)

Este directorio reúne las principales decisiones de arquitectura tomadas durante
el desarrollo del proyecto. Cada ADR documenta el contexto en el que surgió una
decisión, la alternativa seleccionada y las consecuencias que tuvo en el diseño
de la solución.

El objetivo es dejar registro del razonamiento detrás de decisiones que serían
costosas de cambiar o que influyen directamente en la forma en que funciona la
aplicación.

## Estructura de un ADR

Todos los documentos siguen la misma estructura:

- **Estado:** indica si la decisión está propuesta, aceptada o reemplazada.
- **Contexto:** describe el problema o la necesidad que motivó la decisión.
- **Decisión:** explica la solución elegida y las razones para adoptarla.
- **Consecuencias:** resume los beneficios, limitaciones y compromisos
  asumidos.

## Índice

| ADR | Decisión | Estado |
| --- | --- | --- |
| [0001](0001-solo-libreria-estandar.md) | Usar únicamente la librería estándar de Python | ✅ Aceptado |
| [0002](0002-descartar-en-lugar-de-imputar.md) | Descartar filas inválidas en lugar de imputar datos | ✅ Aceptado |
| [0003](0003-deduplicacion-dos-niveles.md) | Implementar deduplicación exacta y normalizada | ✅ Aceptado |
| [0004](0004-salida-determinista.md) | Garantizar resultados deterministas en los rankings | ✅ Aceptado |
| [0005](0005-normalizacion-agresiva-texto.md) | Normalizar el texto antes del análisis | ✅ Aceptado |
| [0006](0006-metrica-lift-distintivas.md) | Incorporar la métrica *lift* para identificar palabras distintivas | ✅ Aceptado |

## ¿Por qué existen estos documentos?

El README explica **qué hace** el proyecto y cómo utilizarlo. En cambio, los
ADR responden a una pregunta diferente: **¿por qué se implementó de esa manera?**

Aquí se documentan decisiones como:

- por qué se optó por la librería estándar en lugar de utilizar `pandas`;
- por qué las filas inválidas se descartan en vez de corregirse automáticamente;
- por qué se implementó una deduplicación en dos niveles;
- por qué los rankings siempre producen el mismo orden;
- por qué el texto se normaliza antes de analizarlo;
- y por qué se añadió la métrica *lift* como complemento al análisis solicitado
  por el reto.

Mantener este historial facilita comprender la evolución del proyecto y ayuda a
que cualquier persona pueda entender el criterio técnico detrás de la solución
sin tener que revisar el código fuente en detalle.