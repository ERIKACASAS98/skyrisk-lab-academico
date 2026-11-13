# Plan de integración del botón Optimizar

**PLAN APROBADO E IMPLEMENTADO; PRIMER ENSAYO REAL NO EJECUTADO.** La interfaz
contiene el botón y sus guardas. Las pruebas sustituyen los procesos y no invocan
CP-SAT. No se ha desplegado ni publicado la aplicación.

## Recorrido propuesto

1. Seleccionar únicamente el caso sintético PASO1-SINTETICO-20261109: dos
   trayectos, 50 filas de flota, 47 regulares elegibles y tres reservas excluidas.
2. Validar entradas, dependencias y recursos al mostrar la modalidad y nuevamente
   al pulsar Optimizar. Abrir la app, cambiar filtros o consultar no resolverá.
3. Adquirir una exclusión mutua de ensayo por instancia. Si hay otro trabajo,
   rechazar la segunda ejecución; los reruns de Streamlit no duplican trabajos.
4. Crear raíz temporal propia y SQLite sintética nueva. No copiar ni abrir bases
   operacionales, no usar rutas elegidas por visitantes ni SKYRISK_RUNS_DIR.
5. Lanzar un proceso Python propio que reutilice el planificador continuo y el
   CP-SAT existentes, con ORIGINAL, una ventana y como máximo 94 candidatos.
   No modificar restricciones, objetivo, perfil ni compromisos protegidos.
6. Validar independientemente las asignaciones y cerrar la trazabilidad antes de
   mostrar un resultado nuevo. Una falla conserva el último escenario válido.
7. Recuperar por run_id en un segundo proceso, sin cargar solver ni conectar
   SQLite; comparar IDs, matrícula, horarios, continuidad y hashes.
8. Mostrar estado CP-SAT, objetivo, cota, tiempo de construcción/resolución,
   motivo de terminación, asignaciones y diagnósticos. UNKNOWN o agotamiento de
   tiempo no se presentarán como inviabilidad demostrada.

## Recursos y cancelación

| Control | Propuesta conservada |
| --- | --- |
| RAM disponible mínima local | 2 GiB; no se reduce |
| RAM cloud | Exigir además al menos 2 GiB de margen efectivo de contenedor; si no se conoce, rechazar |
| Solver ORIGINAL | Cuatro trabajadores, 30 s de reloj, objetivo intacto |
| Productor | Presupuesto supervisado 60 s; RSS 512 MiB |
| Recuperador | 15 s; RSS 128 MiB |
| Ensayo completo | 90 s supervisados; almacenamiento 50 MiB |
| Escenario | Dos trayectos, una ventana, hasta 94 candidatos |
| Concurrencia | Un ensayo activo por instancia y ejecución identificada por sesión |

Contrastar los contadores de psutil con cgroup v2/v1 en Linux y sus límites
heredados; registrar la cuota CPU. Los límites de memoria supervisados son
umbrales observados, no cuotas duras del sistema operativo. No aceptar únicamente
la RAM del host como prueba de recursos de un servicio administrado.

Cancelar mediante bandera o archivo propio y `stop_search()` de la instancia del
ensayo, comprobando la cancelación antes de checkpoints y cierre. No usar
Stop-Process, kill, terminate ni actuar sobre procesos ajenos. Imports o fsync
pueden retrasar la cancelación: no prometer un deadline duro de 90 s.

## Aislamiento y persistencia

Separar dos almacenes académicos: runs incluidos en el paquete publicado,
inmutables y solo de lectura; y runs nuevos del ensayo, en temporal propio. Nunca
escribir en el almacén profesional. La consulta podrá incorporar el run de la
sesión después de validar su cierre; los checkpoints incompletos seguirán
identificados como evidencia no publicable.

El almacenamiento temporal cloud puede perderse en reinicios. Ofrecer descarga
de un paquete íntegro y documentar esa limitación; la retención durable externa
exige elegir y verificar un almacén independiente antes de prometer históricos
persistentes entre reinicios. No añadir credenciales ni almacenamiento remoto
sin revisar alcance y autorización.

## Archivos implementados

- `app_academica.py`: botón explícito, estado de trabajo y presentación de resultados.
- `academico/ejecucion.py`: admisión, procesos, supervisión y cancelación.
- `academico/worker.py`: modelo CP-SAT académico autónomo, persistencia y validación.
- `academico/escenarios.py`: lectura de los runs académicos de sesión ya validados.
- Pruebas nuevas de ejecución y UI; dependencias/documentación/política pública.
- Se reutiliza únicamente el formato de trazabilidad. El worker no importa SQLite,
  planificador continuo ni optimizador profesional.

El proceso académico registra los dos módulos realmente distribuidos y sus hashes,
sin depender de la captura profesional ni de páginas excluidas del paquete.

## Pruebas de aceptación anteriores a la habilitación

- Menos de 2 GiB, recursos desconocidos o exceso de candidatos: no se crea solver.
- Arranque, filtros, consulta y reruns: cero optimizaciones automáticas.
- Una pulsación válida: exactamente una ejecución; doble pulsación no duplica.
- Dos IDs confirmados, misma matrícula regular, tránsito 60 min, posición BOG y
  disponibilidad final 14:00 UTC; cero reservas, duplicados o cambios de horarios.
- Parámetros efectivos ORIGINAL y motivo de terminación registrados.
- Fallo, cancelación o persistencia incompleta: no sustituir el resultado válido.
- Recuperación independiente sin solver y con bytes íntegros.
- Hashes de SQLite operacional e históricos profesionales sin cambios en pruebas locales.

Las pruebas usarán exclusivamente datos sintéticos pequeños y temporales. No
ejecutar los 966 trayectos ni avanzar a tripulaciones. Presentar la configuración
efectiva y obtener autorización antes de cualquier optimización real del ensayo.
