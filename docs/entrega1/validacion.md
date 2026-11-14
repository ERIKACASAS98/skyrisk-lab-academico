# Validación del demostrador académico

Estado vigente de preparación: seis pruebas CP-SAT aprobadas en Colab y evidencia
inspeccionada; Ridge evaluado localmente. La interfaz pública ampliada y el botón
ML real siguen pendientes. Los registros preparatorios anteriores se conservan
como históricos y se contextualizan en la sección final de este documento.

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

## Cierre técnico del 13/11/2026: comprobaciones nuevas

Los registros de 48 pruebas anteriores se mantienen como evidencia histórica,
no como el recuento actual. En este cierre se ejecutó:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_*academic*.py' -q
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_ejecucion_academica.py -q
```

- Suite conjunta: 58 pruebas, OK, 3,923 s.
- Grupo del ejecutor tras añadir recuperación real de fixture: 17 pruebas,
  OK, 1,535 s. Tras la prueba adicional, quedaron 59 casos únicos cubiertos; no sumar ambas pasadas.
- AppTest de la suite conjunta: wall 1,989625 s, pico RSS muestreado
  149.663.744 bytes, `cp_sat_ejecutado=false`. Sin servidor ni navegador.
- La primera pasada dentro del sandbox quedó bloqueada por permisos sobre
  temporales (58 pruebas, errores de permisos); no se considera aprobada.
  La repetición acotada autorizada fuera del sandbox produjo el resultado OK.
- La primera versión de la prueba adicional comparaba un hash con el orden de
  claves anterior a la persistencia. Se corrigió la expectativa para comparar
  contenido y hash del JSON recuperado; la repetición final del grupo aprobó.

Se verificaron PID y argumentos del comando real, paquetes del entorno, .pth,
ausencia de importación del solver en las sondas, bloqueo entre procesos y
liberación, suma RSS de descendientes, cancelación cooperativa por deadline,
recuperador antes/después de consulta, limpieza tras error y rechazo de evidencia
Colab alterada. AppTest comprueba la separación histórica y errores de evidencia.
Las pruebas de supervisión usan sondas; la prueba adicional usa el worker real en
modo recuperador con `FIXTURE_TEST_NO_SOLVER`, sin llamar al productor CP-SAT.

La evidencia Colab se conserva sin cambios, SHA-256:
`7973ec39ac70e11f6cb8d778f4029e82f2121d731afdda58d536e8f8f6e7836c`.
Se comprobó su hash de escenario y su correspondencia con las entradas. Es un
resumen de ejecución previa; no contiene los archivos originales necesarios para
volver a validar toda la cadena de eventos. No se afirma autenticidad externa
solo por sus hashes. La ejecución local OPTIMAL permanece informada por el usuario,
sin reejecución ni certificación nueva en esta sesión.

Quedan pendientes instalación limpia y ejecución del código actual sobre Linux,
integración real desde Streamlit, revisión humana del historial Git, preparación
autorizada del índice, publicación, despliegue y demostración pública. No se
realizó optimización real, conexión SQLite, instalación o cambio profesional.

### Verificación final de paquete y finales de línea

Git conserva la evidencia con LF y Windows la representa con CRLF. Se verificó
que esa es la única diferencia entre la copia del índice y la de trabajo. La
huella de copia revisada normaliza exclusivamente CRLF a LF:
`088c2a6099402224170b23b36e695d457968e387a38c336338214b508b05460c`.
El hash original de bytes de Windows arriba indicado se conserva como registro;
no se reescribió la evidencia. El auditor registra ambas huellas y compara el
índice normalizando solo finales de línea, sin omitir cambios de contenido.

Tras esta corrección se ejecutaron únicamente los grupos afectados:

| Grupo final | Casos aprobados | Tiempo unittest |
| --- | ---: | ---: |
| Lector académico (suite conjunta previa) | 24 | Incluido en los 3,923 s |
| Ejecutor, incluida recuperación real sin solver | 17 | 1,535 s |
| Publicación, incluida diferencia real frente a CRLF/LF | 11 | 0,273 s |
| Interfaz AppTest, histórico Colab y error de integridad | 8 | 1,940 s |
| Total de casos únicos aprobados por grupos | 60 | No sumar repeticiones |

Última AppTest: 1,9397813 s, pico RSS muestreado 148.598.784 bytes,
`cp_sat_ejecutado=false`. Son mediciones del test sin solver, no del cloud.
`pip check` informó `No broken requirements found`; las cuatro versiones
instaladas coinciden con requirements.txt. AST de los Python permitidos válido.

La auditoría del paquete de trabajo permite exactamente 26 archivos, sin faltantes
ni hallazgos, con .gitignore coincidente. La simulación de inclusión usa
`git check-ignore --no-index -z --stdin` sobre la lista exacta: ninguno ignorado.
No se hizo git add ni se alteró el índice. El índice anterior conserva diferencias
de contenido respecto de las ediciones de trabajo y sigue no apto para publicar;
no confundir ese rechazo con un fallo del paquete propuesto. El escaneo limitado
no certifica ausencia absoluta de secretos ni revisa todo el historial Git.

`git diff --check` final aprobó. El índice no tiene cambios preparados por esta
sesión; sus 14 diferencias frente al trabajo incluyen la edición preexistente de
investigacion.md, que se conservó sin modificar durante este cierre.

## Ampliación v2 — resultados locales del 13/11/2026

Rama: desarrollo/ampliacion-academica, creada desde el estado académico 6421558.
Main local se conserva en a557b4e6dcc3128230017f201653ced8634c4338.
La ampliación no se ha publicado ni desplegado. Se mantienen los registros y bytes
de la evidencia histórica original. Entorno: Windows, Python 3.14.3,
Streamlit 1.66.1, OR-Tools 9.15.6755, pandas 3.0.0 y Scikit-learn 1.9.1.

La primera suite ampliada ejecutó 85 casos en 56,941 s: 79 correctos y seis
omitidos por RAM inferior a 2 GiB. La pasada inicial del nuevo grupo dentro del
sandbox encontró permisos insuficientes de temporales; se verificó con acceso
normal autorizado. No se interpretan errores de permisos ni omisiones como éxitos.

Tras reforzar la exclusión ML, la política JSON y la correlación de recuperación,
se repitieron únicamente los grupos afectados:

| Grupo | Casos comprobados sin CP-SAT | Tiempo de la última pasada |
| --- | ---: | ---: |
| Escenarios originales | 24 | Incluidos en la suite inicial de 56,941 s |
| Ejecutor original | 17 | 1,535 s |
| Interfaz, incluidas tres pruebas nuevas | 11 | 2,794 s |
| Publicación, incluida nueva entrada v2 | 12 | 0,336 s |
| Validadores y recuperación ampliada | 13 | 0,613 s |
| ML con entrenamiento real pequeño | 4 | 2,063 s |
| Total de casos únicos comprobados | 81 | No sumar repeticiones |

Durante la preparación local quedaron seis pruebas CP-SAT sin ejecutar por RAM.
Las seis aprobaron posteriormente en Colab; la evidencia inspeccionada figura al
final de este documento. Los casos que entonces quedaron pendientes eran:

1. Cobertura de 12 vuelos y cambio observable al bloquear HK-001.
2. Pendiente AMP-05 al bloquear HK-003 en CLO.
3. Plan vacío óptimo con todas las activas bloqueadas.
4. Óptimo de tres vuelos frente a enumeración independiente.
5. Productor y recuperador v2 completos mediante el supervisor real.
6. Ejecución real del caso original de dos trayectos tras la ampliación.

Se comprobó la admisión: aproximadamente 0,4–1,0 GiB disponibles durante el
trabajo, por debajo del mínimo. Ejecutar secuencialmente no elimina ese requisito.
No se forzó CP-SAT ni se simularon sus métricas. La evidencia OPTIMAL previa del
original no valida el nuevo solver ni sustituye estas seis pruebas.

La recuperación v2 sí se ejecutó realmente sobre una fixture marcada
FIXTURE_TEST_NO_SOLVER, en otro proceso. Se verificó su hash canónico y la
solicitud completa; una contingencia distinta y una comparación falsificada se
rechazan. Las fixtures no son resultados de optimización y no se publican como
asignaciones reales. Los validadores probaron frontera 59/60 minutos, ubicación,
disponibilidad, solapamientos, aeronaves bloqueadas/inactivas y planes vacíos.

Entrenamiento real ML: 1.000 registros, semilla 20261114, 100 días; 800 registros
para entrenamiento y 200 para prueba, sin días compartidos. Ridge MAE:
3,062833908100629 min; Dummy MAE: 6,210152021660345 min.
Datos SHA-256: 91860488e459ab7ab9273ee39761152569a2ca3b27476a556122202103cef7bd.
La primera importación fría y entrenamiento tardaron 49,217762 s; otra pasada
midió 2,012709 s y RSS final de 174.219.264 bytes. El RSS final no es un pico ni
una garantía de memoria. Las métricas reproducidas coinciden; evalúan el simulador,
no vuelos reales. No se conectaron predicciones con restricciones del solver.

Última AppTest: 2,793784 s y pico RSS muestreado 152.551.424 bytes,
cp_sat_ejecutado=false. Se probó navegación por las seis vistas sin entrenamiento,
botones explícitos, confirmación de contingencia y conservación de históricos
ante fallo. No equivale a un recorrido del navegador ni a despliegue Linux.

Las instrucciones de reproducción están en README. Posteriormente se recibieron
y verificaron las seis aprobaciones Colab, detalladas abajo. Sigue pendiente
verificar el stack completo Streamlit/Scikit-learn en Linux y la interfaz pública
ampliada, además de revisión y autorización antes de publicar.

Comprobaciones finales: auditoría del paquete de trabajo con 31 archivos,
sin faltantes ni hallazgos y .gitignore coincidente; AST de los Python permitidos
válido; pip check sin dependencias incompatibles; git diff --check correcto.
El JSON de entradas original y la huella de la evidencia Colab permanecen intactos.
No hay diferencias en módulos profesionales ni cambios en main. Los archivos
de la ampliación quedan sin commit ni preparación del índice para revisión.

## Preparación de validación Colab — sin ejecutar CP-SAT

Se añadieron preparar_colab.py, validar_cpsat_colab.py, validacion_colab.ipynb,
colab.md y test_colab_academico.py. En esa preparación se permitían 36 archivos;
la política de publicación actual admite 37, al incorporar explícitamente R2.
El paquete copia los bytes del trabajo sin commit y registra rama, revisión base,
SHA-256 por archivo y snapshot_id. No se cambia el optimizador ni los seis métodos
SolverAmpliadoRealTests; se mantienen todas sus comprobaciones.

Comprobaciones ligeras ejecutadas:

- Siete pruebas de preparación: OK, 1,025 s. Se verificaron copia exacta,
  reproducibilidad binaria, hashes, rechazo de traversal y cambios, preflight
  real desde un snapshot extraído sin ejecutar tests, bloqueo por RAM, rechazo
  de aprobaciones con skips y sintaxis de todas las celdas sin salidas guardadas.
- Doce pruebas de publicación afectadas por la lista: OK, 0,253 s.
- Las simulaciones de resultados de unittest pertenecen exclusivamente a pruebas
  de infraestructura y están marcadas FIXTURE_TEST_NO_SOLVER; no constituyen
  una ejecución ni aprobación de los seis tests pendientes.

El preflight de la copia extraída se invocó sin --ejecutar. Sus importaciones y
escritura de informe funcionan localmente. El cuaderno solo se compiló, sin
subirlo o ejecutarlo en Colab. No se instaló un entorno Linux en esta sesión.
En esa fase las seis pruebas reales aún estaban pendientes. Posteriormente se
recibió e inspeccionó el informe SEIS_APROBADAS, según el registro final siguiente.
No se suman estas siete pruebas de preparación a las seis aprobaciones CP-SAT. El informe identifica versiones del runtime; las transitivas no están
bloqueadas por un lock y se conservan mediante pip freeze en la evidencia.

Se conservan sin cambios las entradas originales y la evidencia Colab histórica.
El transporte excluye .git, .venv, SQLite y datos operacionales. No se realizó
commit, push, merge, publicación ni despliegue. Seguir la guía colab.md para cargar
el ZIP, pegar la huella externa, crear el venv y descargar evidencia real.


## Estado consolidado para publicación — evidencia Colab inspeccionada

Se inspeccionó evidencia_skyrisk_cpsat_colab.zip (4.116 bytes), sin modificarlo.
SHA-256 del archivo recibido:
`24b8f3547eb8e048e7b13acd9f496964360b29f9f04a7010daa9b63dc7a63171`.
Contiene resultado.json, unittest.log y MANIFIESTO_COLAB.json. Se comprobó:

- Estado SEIS_APROBADAS; seis_aprobadas=true y cp_sat_ejecutado=true.
- Seis pruebas con un caso ejecutado cada una, cero fallos, errores y omisiones.
- Log con los seis nombres correspondientes y seis cierres OK, sin FAILED/skips.
- pendientes vacío y snapshot_verificado_al_final=true.
- Manifiesto recibido idéntico byte a byte al manifiesto del ZIP original.
- snapshot_id recalculado a partir del manifiesto, coincidente con el informe.
- Admisión inicial y antes de cada prueba aprobadas. La inicial registró
  12.317.995.008 bytes disponibles, con cgroup SIN_LIMITE_FINITO. No se redujo
  el requisito de 2 GiB ni se desactivaron las comprobaciones operacionales.

Entorno registrado: Linux, Python 3.13.18, OR-Tools 9.15.6755, pandas 3.0.0,
psutil 7.2.2, NumPy 2.5.4 y protobuf 6.33.6. La fecha del informe es
2026-11-14T02:25:01.380789+00:00, equivalente al 13/11/2026 a las 21:25:01
(America/Bogota). Rama declarada: desarrollo/ampliacion-academica; commit base
642155818a82a2973ecd2afd1dbe1500e6486d3b, que no identifica por sí solo los
cambios entonces sin commit. La identidad exacta del código ensayado es:

`aca0c168268a2db1bb0c9b52fbd2735cf295b5a408a536bb27c64f6a6a48e456`.

| Prueba real | Resultado | Duración de la prueba (s) |
| --- | --- | ---: |
| test_12_atendidos_y_sustitucion_observable | APROBADA | 0,566087 |
| test_falta_aeronave_en_clo_produce_pendiente | APROBADA | 0,022358 |
| test_todas_bloqueadas_solucion_vacia_optima | APROBADA | 0,011693 |
| test_optimo_contra_enumeracion_independiente | APROBADA | 0,005012 |
| test_supervisor_productor_recuperador_v2_completo | APROBADA | 0,830416 |
| test_original_dos_trayectos_real_se_conserva | APROBADA | 0,828308 |

Los tiempos son duraciones de pruebas, no tiempos internos del solver ni una
medición nueva de rendimiento. No se volvieron a ejecutar las seis pruebas en
esta preparación. El informe no contiene todas las matrices de asignación ni el
almacén efímero; no se inventan esos resultados. El ZIP recibido queda en custodia
local separada, sin copiarlo al paquete público o alterar su contenido.

### Alcance separado de la evidencia

| Componente | Estado verificable |
| --- | --- |
| Modelo CP-SAT ampliado y contingencias | Seis pruebas reales aprobadas en Colab; informe, log y manifiesto inspeccionados |
| Caso original de dos trayectos | Prueba real de regresión incluida en esas seis; evidencia histórica conservada |
| Ridge sobre 1.000 filas sintéticas | Entrenamiento/evaluación locales reales: MAE 3,0628339081 min frente a Dummy 6,2101520217 min |
| Navegación y botón ML en AppTest | Pruebas locales aprobadas; el entrenamiento se sustituye por una respuesta simulada en la prueba de interfaz |
| Botón ML con entrenamiento real en la interfaz pública ampliada | Pendiente de verificación; no lo acredita el entrenamiento local ni Colab CP-SAT |
| Stack completo de dependencias web/ML en Linux de Community Cloud | Pendiente; el entorno Colab verificado instaló solo el subconjunto CP-SAT |
| Cuaderno externo R2 | Corrección de entorno comprobada localmente; no atribuirle una ejecución completa nueva por el informe original |

### Integridad y preparación de archivos

R2 se incorpora de forma explícita a PERMITIDOS y .gitignore: 37 rutas académicas
revisables. No se modifica el cuaderno original, el snapshot, su manifiesto ni el
ZIP. Incluir R2 en el repositorio no lo incorpora retroactivamente a aquel snapshot.
La guía y documentación actualizadas son revisiones externas; el código funcional
ensayado se conserva. No se regenera ningún paquete de fuentes.

El repositorio y main de Streamlit confirmados son
ERIKACASAS98/skyrisk-lab-academico y main, con app_academica.py como entrada
esperada y comprobada en el árbol local. Actualizar main puede activar despliegue;
esta preparación no hace fetch, merge, commit, push ni cambio de configuración.
La adición remota .devcontainer/devcontainer.json se concilia posteriormente
con autorización, según el registro de publicación controlada siguiente. Solo se reutilizan los dos archivos de
trazabilidad ya publicados, sin modificar módulos operacionales profesionales.


## Publicación controlada: conciliación de origin/main

Se creó el commit académico 929b24786304784188fa5ea949b5aee243d45f65 con las 37
rutas previamente auditadas. Después se obtuvo origin/main y se confirmó que su
único cambio nuevo era b09fb5ab0ac9354338a4af1458ee0ae5fb0fe1d9, que añadió
.devcontainer/devcontainer.json. Se integró sin conflictos en desarrollo mediante
18eb7a9d792d0aba97b823a467df9826e7af86ac, conservando ambos historiales.

La configuración original usaba Python 3.11, pip --user y flags que desactivaban
CORS/XSRF. Se corrige a Python 3.13 y se conserva explícitamente la protección de
ambos mecanismos. Imagen verificada por HEAD HTTP 200 en el registro oficial:

`mcr.microsoft.com/devcontainers/python:1-3.13-bookworm@sha256:0aa711e570b306c02946cdda67587ce8c65978dbb65691341cbcfd4854dfcfff`.

La instalación utiliza un venv local sin ensurepip, pip principal con --python y
los pins de requirements.txt; no usa apt upgrade ni agrega Streamlit sin pin.
La política añade únicamente .devcontainer/devcontainer.json y pasa de 37 a 38
rutas. Se agrega una prueba de seguridad de configuración sin eliminar pruebas
previas. No se ejecuta el contenedor ni se afirma validación pública del botón ML.
El snapshot original, su manifiesto, entradas y evidencia histórica no se alteran.

Comprobaciones posteriores a la conciliación: 72 pruebas de publicación,
integridad, recuperación e interfaz aprobadas en 7,583 s, sin errores, fallos ni
omisiones. Incluyen 13 de publicación (con nueva prueba de protección del Dev
Container), siete de transporte/runner sin solver, 17 del ejecutor, 24 del lector
y 11 de AppTest. No se repitió CP-SAT ni entrenamiento ML. AppTest observó
4,239763 s y pico RSS muestreado 152.608.768 bytes; no es rendimiento de Cloud.

pip check local aprobó. También aprobó la resolución cruzada --dry-run de las
cinco dependencias y transitivas para wheels Linux x86-64/Python 3.13, con informe
local excluido de Git en artifacts/publicacion/resolucion_linux_py313.json.
No se instalaron esos paquetes ni se ejecutó Linux: la resolución cruzada desde
Windows comprueba disponibilidad y compatibilidad del resolvedor para esos tags,
no todos los comportamientos de marcadores o del runtime real de Community Cloud.
El contenedor tampoco fue arrancado; la imagen se comprobó en el registro.
