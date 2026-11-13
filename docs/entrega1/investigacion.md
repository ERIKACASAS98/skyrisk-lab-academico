# Rigor técnico y potencial investigativo

## Pregunta del proyecto

¿Cómo construir planes comerciales de aeronaves que mantengan continuidad física
y compromisos entre ventanas, haciendo recuperables y verificables las decisiones
del optimizador?

El problema combina asignación, secuenciación temporal, restricciones de recursos
y trazabilidad de software. CP-SAT permite expresar decisiones discretas y buscar
soluciones factibles u óptimas para un modelo definido. El proyecto no utiliza un
modelo predictivo entrenado ni presenta un porcentaje de precisión de aprendizaje.

## Evidencia disponible y límites

| Elemento | Evidencia disponible | Interpretación permitida |
| --- | --- | --- |
| Modelo comercial | Código de variables, restricciones y objetivo | Implementación real de optimización por restricciones |
| Validación previa | 112 pruebas aprobadas y aceptadas en la etapa anterior, no reejecutadas en esta preparación | Corrección para los casos cubiertos, no certificación operacional |
| Reglas internacionales | Pruebas previas de tránsito y permanencia | Evidencia de límites en los escenarios probados |
| Trazabilidad | Pruebas de hashes, fallos, recuperación y consulta | Recuperabilidad del formato bajo los fallos de aplicación probados |
| Paso 1 con SQLite temporal real | Arnés y 12 guardas preparados | Ejecución y resultados todavía pendientes |
| Modalidad interactiva del demostrador | Botón y controles probados con procesos simulados | No representa aún una solución real ejecutada desde Streamlit |
| Resultados semanales | Sin instantánea individual recuperable del resumen 896/966 | No usar ese agregado para comparar algoritmos ni reconstruir IDs |
| Cloud académico | Diseño y preparación | Despliegue y funcionamiento real todavía pendientes |

No se infiere que todo vuelo pendiente sea imposible. `UNKNOWN` significa que
no se ha determinado una solución o una prueba de inviabilidad antes de una
condición de parada. `FEASIBLE` tampoco demuestra optimalidad. Los estados se
interpretan según la [documentación oficial de CP-SAT](https://developers.google.com/optimization/cp/cp_solver).

## Hipótesis investigables posteriores

Estas hipótesis definen experimentos futuros; no son conclusiones obtenidas.

| Hipótesis | Comparación propuesta | Métricas |
| --- | --- | --- |
| La continuidad entre ventanas evita asignaciones físicamente inconsistentes | Planificación continua frente a ventanas aisladas, con los mismos datos y reglas | Conflictos de posición, duplicados y compromisos incumplidos |
| Las ventanas con apoyo conservan operaciones internacionales futuras | Diferentes horizontes de apoyo sin cambiar compromisos confirmados | Trayectos asignados, regresos protegidos y diagnósticos por ID |
| La configuración experimental reduce variación entre repeticiones | Repeticiones con misma entrada, versión y equipo | Diferencias de asignación, objetivo, cota y causa de terminación |
| La persistencia individual mejora la auditabilidad | Resultados con eventos y hashes frente a resúmenes agregados | IDs recuperables, detección de corrupción y tiempo de recuperación |

No se autoriza aquí ejecutar esas comparaciones ni la planificación de 966 vuelos.
El perfil experimental continúa pendiente de calibración.

## Diseño experimental mínimo de la entrega

El primer experimento utilizará dos vuelos nacionales sintéticos del 9 de
noviembre de 2026 y un almacén temporal aislado, con 47 regulares y tres reservas
excluidas de las variables de decisión. Como
resultado esperado manual, ambos vuelos pueden formar una rotación con una misma
regular y tránsito de 60 minutos. Este cálculo esperado no es un resultado
observado del software.

La modalidad interactiva activa ese experimento mediante un botón explícito,
después de la admisión y confirmación. La consulta histórica
servirá como respaldo de resultados que realmente hayan sido obtenidos y
verificados; no sustituye la validación de la modalidad interactiva. En cloud se
deberá comprobar la disponibilidad efectiva de al menos 2 GiB dentro del límite
del contenedor antes de resolver, manteniendo ese umbral.

El ensayo deberá registrar:

1. Identidad del escenario, entradas completas y procedencia SINTETICO.
2. Versión de código, entorno y parámetros efectivos del solver.
3. Candidatos, restricciones, compromisos y diagnósticos por ventana.
4. IDs y matrícula de cada resultado, sin duplicación ni uso de reservas.
5. Estado del solver, objetivo, cota y tiempos disponibles.
6. Memoria del proceso, tiempo total y almacenamiento de artefactos.
7. Hashes antes/después y recuperación desde otro proceso sin optimizador.

Se conserva el modelo profesional: no se retiran restricciones para mejorar
artificialmente la cobertura. Mantenimiento vacío es una característica declarada
del caso básico, no evidencia de validación de todos los estados técnicos.

## Variables de control y medición

Para comparar ejecuciones se mantendrán constantes entradas, inventario, estado
inicial, reglas, compromisos, objetivo y versión del código. Se identificarán por
separado cambios de perfil, parámetros, entorno y tamaño de ventana.

La cobertura se calculará sobre IDs del objetivo declarado. Los resultados
confirmados, pendientes y con estado inicial incompleto se separarán; propuestas
y compromisos futuros no se sumarán como vuelos confirmados. No se publicará una
cobertura obtenida antes de ejecutar y validar el ensayo.

Las mediciones de memoria deben incluir memoria nativa del solver. Los límites
de reloj y los presupuestos supervisados no sustituyen una medición observada.
El tiempo determinista no tiene unidades de segundos reales y no prueba por sí
solo identidad de resultados entre equipos o versiones.

## Amenazas a la validez

- Dos vuelos permiten verificar la cadena técnica; no representan la dificultad
  combinatoria de una red semanal.
- Los datos sintéticos no certifican una reconstrucción histórica operacional.
- Fixtures de pruebas y errores inyectados no prueban resistencia a cualquier
  fallo del proceso, sistema de archivos o suministro eléctrico.
- La disponibilidad de recursos y la escritura de trazas pueden afectar el tiempo
  de reloj observado.
- Los óptimos por ventana no implican un óptimo global del horizonte completo.

El potencial investigativo se sustenta en preguntas contrastables, un modelo
inspeccionable, conservación de entradas y decisiones y un protocolo repetible.
La contribución empírica dependerá de ejecutar los experimentos y publicar sus
evidencias con los límites correspondientes.

## Fuentes y artefactos

- [Programación con restricciones en OR-Tools](https://developers.google.com/optimization/cp).
- [CP-SAT y significado de sus estados](https://developers.google.com/optimization/cp/cp_solver).
- [Código fuente oficial de OR-Tools](https://github.com/google/or-tools).
- [Validación pública de la entrega](validacion.md). El registro profesional de
  auditoría se conserva localmente fuera del paquete publicado.
- [Arquitectura de la entrega](arquitectura.md).
