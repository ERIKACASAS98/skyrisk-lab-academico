# Validación del demostrador académico

Fecha de preparación local: 12 de noviembre de 2026, America/Bogota.
Entorno local: Windows, Python 3.14.3 y Streamlit 1.66.1.

Durante la preparación local se aprobaron 48 pruebas automatizadas.
La ejecución real de CP-SAT no pudo realizarse en ese equipo porque
la memoria disponible era inferior al mínimo de 2 GiB establecido.

El 13 de noviembre de 2026 se ejecutó el demostrador académico en
Google Colab, utilizando Linux, Python 3.13.18 y OR-Tools 9.15.6755.

El solver obtuvo el estado OPTIMAL, con objetivo 2/2, cota 2,
94 variables, 49 restricciones y dos trayectos confirmados
mediante la aeronave HK-049.

El resultado fue recuperado y declarado COMPLETA y publicable.
La evidencia pública se conserva en
`docs/evidencias/evidencia_cpsat_publica.json`.

Esta validación corresponde al escenario sintético de dos trayectos.
No demuestra la ejecución desde la interfaz Streamlit desplegada
ni la optimización de la operación semanal completa.

El repositorio público y el despliegue de la aplicación continúan
pendientes de verificación y publicación.

## Resultados observados en esta preparación

| Grupo | Resultado final | Tiempo de unittest |
| --- | --- | --- |
| Lector y validadores académicos | 24 correctas, cero fallidas | 0,514 s |
| Política de publicación | 9 correctas, cero fallidas | 0,173 s |
| Interfaz Streamlit AppTest | 7 correctas, cero fallidas | 2,546 s |
| Ejecutor académico sin solver | 8 correctas, cero fallidas | 0,140 s |
| Total académico de esta preparación | **48 correctas, cero fallidas** | Ejecuciones separadas |

Comandos realmente ejecutados:

```powershell
py -B -m unittest discover -s tests -p 'test_escenarios_academicos.py' -q
py -B -m unittest discover -s tests -p 'test_publicacion_academica.py' -q
py -B -m unittest discover -s tests -p 'test_app_academica.py' -q
py -B -m unittest discover -s tests -p 'test_ejecucion_academica.py' -q
```

El primer intento de las pruebas de lectura dentro del sandbox produjo errores
de permisos de directorios temporales. Se repitieron con permisos normales de
ejecución para temporales, sin acceder a SQLite operacional. Los resultados de
la tabla corresponden a las ejecuciones finales verificadas.

Las 112 pruebas profesionales aceptadas previamente no se reejecutaron, porque
esta preparación prohíbe ejecutar optimizaciones. Los 12 casos de seguridad del
ensayo local permanecen preparados, no ejecutados. No se suman esos grupos a una
regresión nueva ni se presenta el total académico como evidencia de CP-SAT.

## Ejecución real del optimizador CP-SAT

Fecha: 13 de noviembre de 2026.
Entorno: Google Colab, Linux, Python 3.13.18.
Motor: OR-Tools CP-SAT 9.15.6755.

El escenario académico fue ejecutado con datos sintéticos,
respetando el umbral mínimo de memoria de 2 GiB.

| Indicador | Resultado |
| --- | --- |
| Estado del solver | OPTIMAL |
| Objetivo alcanzado | 2 de 2 trayectos |
| Cota superior | 2 |
| Variables | 94 |
| Restricciones | 49 |
| Tiempo de resolución | 0.012 segundos |
| Trabajadores configurados | 4 |
| Límite de tiempo del solver | 30 segundos |
| Aeronave asignada | HK-049 |
| Trayectos pendientes | 0 |
| Estado de recuperación | COMPLETA |
| Evidencia publicable | Sí |

La solución confirmó los trayectos BOG-MDE y MDE-BOG,
con un intervalo de tránsito de 60 minutos.

El resultado fue recuperado mediante el mecanismo académico
de trazabilidad y quedó registrado en:

`docs/evidencias/evidencia_cpsat_publica.json`

Esta ejecución demuestra la resolución óptima del escenario
sintético ensayado. No constituye evidencia de optimización
semanal ni de ejecución desde Streamlit Community Cloud.
## Recursos de la prueba UI sin solver

En la comprobación final se observaron 904.437.760 bytes disponibles, menos de los 2 GiB
exigidos para CP-SAT. Solo se autorizó el recorrido de consulta sin solver.
La prueba UI exigió un margen de al menos 256 MiB entre interacciones y un
presupuesto supervisado RSS de 384 MiB. Estos controles **no modifican** el
umbral de 2 GiB del ensayo CP-SAT.

AppTest registró 2,546 s de medición interna y un pico RSS muestreado cada
100 ms de **149.295.104 bytes** (aproximadamente 142,38 MiB).
`cp_sat_ejecutado=False`. No es una medición de memoria del solver ni una prueba
de rendimiento cloud. No se utilizó navegador o servidor público.

## Qué se comprobó

- Entradas SINTETICO/SIN_EJECUCION, dos IDs, 47 regulares, tres reservas excluidas,
  horarios con zona, tránsito de 60 minutos y ausencia de resultados inventados.
- Rechazo de entradas MIXTO/OPERACIONAL, rutas de run_id inválidas, límites de
  archivos/bytes/directorios y alteraciones de hashes.
- Consulta mediante el lector de trazabilidad real sobre fixtures temporales,
  preservando bytes. Los fixtures se identifican FIXTURE_TEST_NO_SOLVER y no
  son resultados de optimización ni están incluidos en demo/escenarios.
- Rechazo de reservas, IDs internos inconsistentes y resultados individuales
  contradictorios. Un cierre sin escenario no se declara publicable.
- Arranque y cambios de vista con imports del motor y conexiones SQLite
  bloqueados por pruebas; selección de la página profesional rechazada.
- Botón dentro de un formulario explícito: abrir, navegar y filtrar no llaman al
  ejecutor; la prueba usa un proceso simulado y no importa OR-Tools.
- Admisión previa de 2 GiB, comprobación de cgroup Linux, alcance exacto de dos
  trayectos/94 candidatos y parámetros ORIGINAL de cuatro trabajadores/30 s.
- Productor y recuperador independientes, coincidencia de `run_id` y hash,
  conservación del último histórico válido y rechazo de recuperación divergente.
- Cancelación cooperativa mediante marcador y `stop_search()`; se verifica que
  el código no invoque terminación forzada.
- Consulta vacía sin porcentaje de cobertura ficticio; errores de integridad
  visibles; consulta de fixture sin reescribir sus archivos.
- Política de archivos públicos explícitos, revisión de hashes, detección
  limitada de secretos sin revelar valores y rechazo de archivos no permitidos.

Se corrigieron durante la revisión tres inconsistencias del lector académico
nuevo: cierre sin escenario marcado publicable, IDs internos no contrastados y
resultados individuales no contrastados con el escenario. El formato profesional
y sus módulos no se modificaron.

## Protección de datos

La SQLite operacional conserva el SHA-256 previo. Su ruta, hash completo e
inventario de históricos profesionales se comprueban localmente y no se incluyen
en el paquete público como datos de demostración. No se abrió conexión a esa base.
Los históricos profesionales se mantuvieron fuera del alcance del lector.

La política pública permite solo archivos académicos revisados y el lector de
trazabilidad compartido. No publica bases, sidecars, datos de personas,
credenciales, respaldos, páginas profesionales o conversaciones guardadas.
Un escaneo sin hallazgos no demuestra ausencia absoluta de información privada;
antes de publicar faltan revisión humana e inspección del índice y del historial Git.

## Registro por archivo y alcance de la evidencia

| Archivo o grupo | Estado |
| --- | --- |
| `app_academica.py` | AUDITADO + PROBADO: siete AppTest de navegación, entrada, filtros, botón explícito simulado, conservación histórica, consulta y errores. El motor CP-SAT fue validado por separado en Google Colab; su ejecución desde la interfaz pública continúa pendiente. |
| `academico/ejecucion.py`, `academico/worker.py` | AUDITADO + PROBADO SIN SOLVER: admisión, aislamiento, perfil ORIGINAL, supervisión, cancelación cooperativa, persistencia temporal y recuperación independiente. |
| `academico/escenarios.py` | AUDITADO + PROBADO: 24 pruebas de lectura, procedencia, límites e integridad. Adicionalmente, se obtuvo una ejecución real de CP-SAT en Google Colab y se conservó su evidencia pública. La integración de esta evidencia con el visor Streamlit todavía requiere verificación. |
| `demo/entradas_paso1.json` | AUDITADO + PROBADO al cargar la app: solo entradas sintéticas, resultados null. |
| Pruebas académicas | AUDITADO + PROBADO: 48 casos finales correctos, sin solver, incluida la carga aislada del worker. |
| Auditor de publicación y `.gitignore` | AUDITADO + PROBADO en política y escaneo; comprobación del índice e historial Git PENDIENTE. |
| `requirements.txt` y `compatibilidad_cloud.md` | REVISADO PARCIAL: metadatos oficiales; instalación Linux y selector cloud PENDIENTES. |
| README, arquitectura, investigación, presentación y plan del botón | REVISADO PARCIAL: documentación preparada; demo de ambas modalidades y despliegue real PENDIENTES. |
| `planificacion_comercial/trazabilidad_escenarios.py` y `__init__.py` | Reutilizados sin cambios; lector ejercitado por las nuevas pruebas académicas. |

SOLO REORGANIZADO: ninguno. Los módulos profesionales, bases e históricos no se
reescribieron ni eliminaron. La publicación sigue sin autorización y los runs
futuros no están incluidos automáticamente en la lista pública.

## Pendientes para la evidencia completa de Entrega 1

1. Verificar la ejecución del botón de optimización desde la
   interfaz Streamlit, utilizando el escenario sintético autorizado.
2. Comprobar la recuperación y consulta histórica del resultado
   real desde un proceso independiente.
3. Verificar la instalación, las dependencias y el funcionamiento
   de la aplicación en el entorno Linux de despliegue.
4. Revisar los archivos públicos, el índice y el historial Git
   antes de publicar el repositorio.
5. Publicar el repositorio en GitHub y desplegar la aplicación,
   registrando URL, commit, fecha y evidencia de funcionamiento.
6. Ensayar las modalidades de consulta y optimización desde la
   aplicación desplegada, respetando el mínimo de 2 GiB de memoria
   para ejecutar CP-SAT.
7. Preparar y verificar la presentación académica final.

No hay resultado individual recuperado de 896/966, no se ejecutaron los 966
trayectos y no se avanzó a tripulaciones. Esta preparación no certifica V5.2.
