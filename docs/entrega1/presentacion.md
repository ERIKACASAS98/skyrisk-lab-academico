# Presentación ejecutiva — Entrega 1 ABP

Guion propuesto para una presentación profesional de siete diapositivas. Ajustar
duración y formato al enunciado oficial. La fecha límite es el 16 de noviembre de
2026. La exposición debe diferenciar implementación, evidencia observada y trabajo
pendiente.

La entrega objetivo incluye dos modalidades: optimización interactiva de dos
trayectos mediante botón explícito y consulta histórica como respaldo. Ambas están
implementadas; el primer ensayo real y el despliegue siguen pendientes.

## 1. Problema y valor

**Mensaje:** planificar vuelos exige que cada aeronave esté en el lugar correcto,
en el horario correcto y sin comprometer mantenimiento ni operaciones futuras.

- Usuario objetivo: planificación comercial y análisis de continuidad de flota.
- Decisiones: qué trayectos asignar y a qué matrícula regular.
- Beneficio esperado: planes verificables y decisiones recuperables por ID.
- Alcance de la entrega: caso sintético pequeño; proyecto profesional conservado.

**Visual:** una rotación BOG–MDE–BOG con su intervalo de tránsito.

## 2. Solución de IA y selección tecnológica

**Mensaje:** el problema se formula mediante decisiones discretas y restricciones.

- Python 3.14 para implementación y validación.
- OR-Tools CP-SAT para selección de asignaciones.
- Objetivo actual: maximizar trayectos seleccionados sin retirar restricciones.
- Streamlit para explorar entradas y consultar resultados trazables.
- Almacén temporal por ensayo, aislado de SQLite operacional y de históricos profesionales.
- psutil para la supervisión propuesta de recursos del ensayo controlado.

Explicar variables, objetivo y dos restricciones mediante el ejemplo. Presentar
el enfoque como optimización con restricciones; no atribuir entrenamiento o
predicciones inexistentes.

## 3. Arquitectura modular y seguridad

**Mensaje:** la demostración académica separa consulta, ejecución y operación real.

- Entrada independiente `app_academica.py`.
- Visor sin optimización automática ni acceso a SQLite operacional.
- Ensayo productor controlado y recuperación en otro proceso.
- Datos sintéticos, hashes e identidad `run_id`.
- Repositorio publicado mediante selección explícita de archivos.

**Visual:** diagrama de [arquitectura.md](arquitectura.md). Identificar qué existe
localmente y qué se ha desplegado realmente en la nube.

## 4. Demostración y evidencia

**Mensaje:** cada cifra mostrada debe corresponder a un artefacto verificable.

Secuencia de exposición:

1. Abrir la aplicación académica y mostrar procedencia sintética.
2. Revisar los dos IDs, rutas, horarios y flota elegible.
3. Mostrar la admisión de recursos. Ejecutar únicamente después de autorizar el
   primer ensayo y con al menos 2 GiB libres; si falla, explicar el botón deshabilitado.
4. Mostrar SIN_EJECUCION si no hay un resultado validado. Cuando el ensayo esté
   validado, abrir su run y presentar matrícula, horarios,
   diagnósticos, perfil y comprobaciones de integridad.
5. Demostrar que consultar no vuelve a invocar el solver.

No sustituir el paso pendiente por una tabla rellenada manualmente. No pulsar la
optimización semanal profesional durante la presentación.

## 5. Validación y resultados

**Mensaje:** la evidencia tiene alcance concreto y límites explícitos.

| Evidencia | Contenido actual para la diapositiva |
| --- | --- |
| Regresión profesional previa | 112 pruebas aprobadas y aceptadas en la etapa anterior, no reejecutadas en esta preparación |
| Guardas del paso 1 | 12 casos preparados, pendientes de ejecución |
| Cadena básica con SQLite real temporal | Pendiente; completar solo tras admisión de recursos y autorización |
| Modalidad interactiva con botón | Implementada y probada con proceso simulado; CP-SAT real pendiente |
| Memoria, tiempo y almacenamiento | No medidos todavía para ese ensayo |
| Despliegue cloud | Pendiente; completar con URL, commit y captura verificables |

Actualizar esta diapositiva con el informe real antes de entregar. Un resultado
esperado o un fixture de test no se contabiliza como resultado observado.

## 6. Rigor técnico y potencial investigativo

**Mensaje:** el proyecto permite formular y contrastar preguntas de investigación.

- Continuidad entre ventanas y conservación de compromisos futuros.
- Efecto del horizonte de apoyo y los parámetros del solver.
- Comparación por IDs, objetivo, cota, recursos y causa de terminación.
- Recuperación verificable frente a resúmenes agregados.

Presentar hipótesis y protocolo de [investigacion.md](investigacion.md).
Explicar que todavía no hay comparación experimental semanal reproducible ni
evidencia de escalabilidad a 966 trayectos.

## 7. Entrega verificable y siguiente fase

**Mensaje:** se entrega un alcance académico identificable y se conserva la ruta
profesional de V5.2.

- URL GitHub: pendiente de publicación y verificación.
- Commit o etiqueta de entrega: pendiente.
- URL cloud: pendiente de despliegue y prueba real.
- README, arquitectura, validación y limitaciones vinculados desde el repositorio.
- Después de la entrega: cobertura semanal, calibración y desarrollo profesional
  mediante autorizaciones separadas.

No mostrar enlaces simulados. Cuando estén publicados, probarlos desde una sesión
nueva antes de la exposición.

## Cobertura de la rúbrica

| Criterio | Peso | Diapositivas |
| --- | ---: | --- |
| Problema y justificación tecnológica | 20 % | 1–2 |
| Arquitectura y buenas prácticas | 25 % | 3–4 |
| Repositorio GitHub | 20 % | 7 y recorrido del README |
| Presentación | 15 % | Secuencia completa y ensayo del guion |
| Rigor técnico e investigación | 20 % | 5–6 |

## Material que debe quedar listo antes de exponer

- Captura del despliegue con URL y fecha, sin información privada.
- Identificación de la versión de entrega y entorno utilizado.
- Informe del ensayo pequeño si se ha ejecutado; en caso contrario, declarar su
  estado pendiente sin inventar asignaciones ni métricas.
- Video breve del recorrido validado como respaldo de la demostración en vivo.
- Fuentes primarias enlazadas y legibles en la documentación.
- Ensayo de navegación sobre el paquete público, sin rutas operacionales ni
  acciones de mantenimiento o tripulaciones.
