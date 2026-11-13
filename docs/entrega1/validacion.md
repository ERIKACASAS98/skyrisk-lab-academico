# Validación del demostrador académico

Fecha de la preparación local: 12 de noviembre de 2026, America/Bogota.
Entorno: Windows, Python 3.14.3, Streamlit 1.66.1. No se ejecutó CP-SAT ni se
publicó el repositorio o la app. La modalidad interactiva está implementada,
pero el primer ensayo real continúa pendiente de autorización; véase
[el plan del botón](plan_optimizacion_interactiva.md).

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
| `app_academica.py` | AUDITADO + PROBADO: siete AppTest de navegación, entrada, filtros, botón explícito simulado, conservación histórica, consulta y errores. CP-SAT real PENDIENTE. |
| `academico/ejecucion.py`, `academico/worker.py` | AUDITADO + PROBADO SIN SOLVER: admisión, aislamiento, perfil ORIGINAL, supervisión, cancelación cooperativa, persistencia temporal y recuperación independiente. |
| `academico/escenarios.py` | AUDITADO + PROBADO: 24 pruebas de lectura, procedencia, límites e integridad; no valida un resultado real de CP-SAT aún inexistente. |
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

1. Autorizar expresamente el primer ensayo real del botón ya implementado.
2. Ejecutar el ensayo de dos trayectos solo con al menos 2 GiB disponibles; guardar
   asignaciones, estado, objetivo, cota, tiempos, parámetros y hashes reales.
3. Probar sobre el ensayo real la recuperación desde otro proceso y consulta histórica.
5. Confirmar Python 3.14, instalar y arrancar en Linux; verificar dependencias resueltas.
6. Revisar archivos e índice Git, obtener autorización para publicar y desplegar,
   y registrar URL, commit, logs, fecha y captura del servicio real.
7. Ensayar ambas modalidades y la presentación. Si el servicio cloud no admite
   recursos suficientes, conservar consulta y elegir infraestructura adecuada
   para CP-SAT; la consulta sola no completa el objetivo de ambas modalidades.

No hay resultado individual recuperado de 896/966, no se ejecutaron los 966
trayectos y no se avanzó a tripulaciones. Esta preparación no certifica V5.2.
