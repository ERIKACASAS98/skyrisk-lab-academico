# SkyRisk Lab Académico

Demostrador de planificación de aeronaves, recuperación ante contingencias y
predicción de retrasos, desarrollado para Introducción a la Inteligencia Artificial
de la Fundación Universitaria Católica del Norte.

La versión publicada presenta **12 trayectos sintéticos, cuatro aeronaves activas
y cuatro aeropuertos**. Combina OR-Tools CP-SAT y Ridge Regression. Sus resultados
no están validados para operaciones reales de una aerolínea.

**Actualización:** 14 de noviembre de 2026. Entrega académica: 16 de noviembre de
2026. Interfaz publicada y comprobada a partir del commit
[`853868e`](https://github.com/ERIKACASAS98/skyrisk-lab-academico/commit/853868e2f28189a58d6d46cbbc75a8ad58a8d2dc).

- [Aplicación pública en Streamlit](https://erikacasas98-jeerw6vvkvzvbt2s5yjnyr.streamlit.app/)
- [Repositorio en GitHub](https://github.com/ERIKACASAS98/skyrisk-lab-academico)

Desarrollado por Erika Liliana Casas Toro y Viana Maria Ruiz Ruiz.

## Objetivos

- Explorar asignaciones respetando ubicaciones, horarios y continuidad física.
- Comparar el plan inicial con la recuperación ante una aeronave indisponible.
- Evaluar una predicción de retrasos frente a una referencia simple.
- Distinguir entradas, resultados de sesión y evidencias históricas.

## Escenario principal y funcionalidades

Las [entradas ampliadas](demo/entradas_ampliadas.json) contienen **AMP-01 a AMP-12**,
sin duplicaciones ni omisiones, entre Bogotá (BOG), Medellín (MDE), Cali (CLO) y
Cartagena (CTG). Los horarios corresponden a una jornada en UTC.

Participan HK-001 y HK-002 inicialmente en BOG, HK-003 en CLO y HK-004 en CTG,
con disponibilidad explícita. El inventario conserva 47 regulares y tres reservas;
solo las cuatro activas intervienen en la ampliación. Las demás aeronaves no se
habilitan automáticamente.

La aplicación permite consultar trayectos, filtrar por origen, bloquear una
aeronave toda la jornada y solicitar el cálculo del plan base y su recuperación.
Cuando existe un resultado validado, muestra asignaciones, cambios y pendientes.
Las descargas conservan parámetros y diagnósticos retirados de pantalla.

### Las cinco secciones actuales

| Sección | Contenido |
| --- | --- |
| **Resumen** | 12 trayectos, cuatro aeropuertos, cuatro aeronaves activas, disponibilidad de recursos y único aviso general de datos sintéticos. |
| **Trayectos** | Los doce trayectos, filtro por aeropuerto de origen y horarios UTC. |
| **Planificación y contingencias** | Aeronave afectada, confirmación explícita, ejecución y comparación de planes. |
| **Validación técnica** | Caso original de dos trayectos, ejecución opcional y consulta histórica, incluida evidencia Colab. |
| **Predicción de retrasos** | Entrenamiento y evaluación de Ridge por botón, comparación del error y ejemplos. |

Navegar no ejecuta CP-SAT ni entrena Ridge automáticamente. Un estado de recursos
disponibles no acredita un resultado calculado. Si una ejecución posterior falla,
se conserva el último resultado válido de sesión, identificado como histórico.

## Optimización CP-SAT

El [modelo ampliado](academico/simulacion.py) construye secuencias temporales por
aeronave y aplica:

- Como máximo una aeronave por trayecto.
- Inicio alcanzable desde la ubicación y disponibilidad de cada aeronave activa.
- Continuidad entre destino y origen de trayectos consecutivos.
- Tránsito mínimo de 60 minutos y ausencia de solapamientos.
- Exclusión de la aeronave bloqueada durante toda la jornada.
- Clasificación completa de cada trayecto como asignado o pendiente, sin duplicados.

El objetivo prioriza cobertura, luego conservar asignaciones del plan inicial
durante la recuperación y finalmente una preferencia de matrícula. Admite planes
parciales o vacíos; un pendiente no prueba imposibilidad en cualquier otro escenario.

Utiliza cuatro trabajadores y hasta 15 segundos por plan, en dos resoluciones.
Solo admite resultados `OPTIMAL` o `FEASIBLE`, con validación independiente.
`FEASIBLE` no demuestra optimalidad; `UNKNOWN` no se convierte en solución vacía válida.

### Ejecución supervisada y validación

La [ejecución](academico/ejecucion.py) mantiene admisión mínima de 2 GiB de memoria
libre para CP-SAT, comprobación del contenedor cuando aplica, exclusión entre
ejecuciones y confirmación del usuario. La admisión común también verifica la
integridad del caso original; sus metadatos `ORIGINAL` no describen el perfil
ampliado `AMPLIADO_V2`.

Productor y recuperador trabajan en procesos independientes. Se supervisan memoria,
tiempo y almacenamiento; la cancelación es cooperativa, sin garantizar terminación
forzada. El recuperador verifica hashes, correspondencia con la solicitud, planes
y comparación. Los temporales se eliminan al finalizar: los resultados de sesión
no alimentan automáticamente el catálogo histórico y deben descargarse para
conservarlos.

## Machine Learning: Ridge Regression

El [experimento](academico/ml_retrasos.py) genera 1.000 registros en 100 días
sintéticos, con semilla `20261114`. Predice minutos de retraso usando origen,
destino, hora programada, congestión, viento y lluvia previstos.

`GroupShuffleSplit` separa días completos: 800 registros de entrenamiento y 200
de prueba. El pipeline ajusta `StandardScaler` y `OneHotEncoder` solo con
entrenamiento y utiliza `Ridge(alpha=1, solver='lsqr')`. La referencia es
`DummyRegressor`, que predice la media de entrenamiento. Las predicciones se
limitan inferiormente a cero; no se ajustan hiperparámetros usando la prueba.

| Resultado verificado | Valor |
| --- | ---: |
| MAE Ridge | **3,063 minutos** |
| MAE de referencia | **6,210 minutos** |
| Reducción aproximada del error | **50,7 %** |

MAE significa error absoluto medio. La reducción se calcula como
`(MAE de referencia − MAE Ridge) / MAE de referencia`, con los valores sin
redondear: 3,0628339081 y 6,2101520217 minutos.

El entrenamiento y evaluación se comprobaron localmente y, el 14/11/2026,
mediante el botón de la aplicación pública en Streamlit: 3,063 y 6,210 minutos,
sin excepción visible. Esto acredita el modelo predictivo, no una ejecución
del optimizador ampliado en producción.

El objetivo predictivo procede de una fórmula sintética con ruido. Las métricas
miden aprendizaje del generador, no capacidad demostrada sobre vuelos reales.
Ridge no modifica CP-SAT; usa un hilo de cómputo, comprueba 256 MiB disponibles
y comparte la exclusión de ejecución con el optimizador.

## Arquitectura

| Tecnología o componente | Función |
| --- | --- |
| **Python** | Coordinación, validaciones y procesos independientes. |
| **Streamlit** | Interfaz de cinco secciones y acciones explícitas. |
| **OR-Tools CP-SAT** | Asignación y recuperación bajo restricciones. |
| **scikit-learn** | Preprocesamiento, Ridge, referencia y evaluación. |
| **Pandas** | Preparación y manejo tabular de datos. |
| **psutil** | Admisión y supervisión de recursos. |
| **Validadores y hashes** | Integridad, correspondencia con la solicitud y verificación independiente de planes. |
| **GitHub y Streamlit Community Cloud** | Código público y alojamiento del demostrador. |

El flujo de optimización es: entradas → admisión y confirmación → productor →
recuperador independiente → resultado validado. La predicción se entrena y evalúa
por su propio botón. No se requiere una base de datos operacional.

| Ruta | Contenido |
| --- | --- |
| `app_academica.py` | Interfaz publicada. |
| `academico/simulacion.py` | Ampliación, contingencias y validación de planes. |
| `academico/ejecucion.py` y `academico/worker.py` | Admisión, supervisión y procesos aislados. |
| `academico/escenarios.py` | Entradas originales, consulta e integridad histórica. |
| `academico/ml_retrasos.py` | Generador sintético y evaluación Ridge. |
| `planificacion_comercial/trazabilidad_escenarios.py` | Almacén de trazabilidad utilizado por el demostrador. |
| `demo/`, `tests/`, `docs/`, `herramientas/validadores/` | Escenarios, pruebas, documentos y auditoría. |

## Resultados, pruebas y evidencia histórica

| Componente | Estado y alcance |
| --- | --- |
| Interfaz publicada, 14/11/2026 | Cinco secciones recorridas; 12 de 12 trayectos; dos originales en Validación técnica y aviso general único. |
| Ridge en Streamlit, 14/11/2026 | Entrenamiento y evaluación reales por botón; MAE 3,063 frente a 6,210 minutos. |
| CP-SAT ampliado en producción | Interfaz y controles disponibles; **no se acredita una ejecución nueva exitosa de los 12 trayectos en Streamlit**. |
| CP-SAT ampliado en Colab | Informe histórico de seis pruebas reales aprobadas, incluida la regresión original; log y manifiesto inspeccionados. |
| Caso original en Colab | Evidencia pública: `OPTIMAL`, dos trayectos con HK-049, objetivo y cota 2, 94 variables y 49 restricciones. |
| Caso original en Streamlit, 13/11/2026 | Registro documental de `OPTIMAL`, dos de dos trayectos con HK-003 y recuperación independiente. No corresponde al caso ampliado. |

El caso original Bogotá–Medellín–Bogotá, con tránsito de 60 minutos, 47 regulares
elegibles y tres reservas excluidas, queda como validación secundaria. Las
matrículas históricas distintas son compatibles con múltiples soluciones óptimas.

La [evidencia pública de Colab](docs/evidencias/evidencia_cpsat_publica.json)
conserva el resumen original, pero no todos los archivos para revalidar la cadena
completa de eventos. El informe ampliado está descrito en
[Validación técnica](docs/entrega1/validacion.md); el ZIP inspeccionado permanece
en custodia local, fuera del repositorio público. No se inventan matrices de
asignación ni tiempos ausentes del informe.

### Suite automatizada vigente

La última repetición local documentada del 14/11/2026 descubrió **98 pruebas**:

| Estado | Cantidad |
| --- | ---: |
| Aprobadas | **92** |
| Omitidas por restricciones de memoria | **6** |
| Fallos | **0** |
| Errores | **0** |

Las seis omisiones son de `SolverAmpliadoRealTests`: cobertura y sustitución,
pendiente al bloquear HK-003, comparación con enumeración, regresión original,
supervisión ampliada y solución vacía con todas las aeronaves bloqueadas.
La admisión rechazó CP-SAT por memoria libre inferior a 2 GiB
(`RAM_HOST_MENOR_2_GIB`). **Una omisión no equivale a ejecución ni aprobación.**

Las 92 aprobaciones incluyen 14 pruebas de interfaz, validadores y evaluación
real de Ridge. Las fixtures no son resultados reales del solver. Las seis
aprobaciones históricas de Colab pertenecen a otra ejecución y no se suman a
las 92 locales para afirmar una suite completa ejecutada en Cloud.

## Instrucciones de uso

### Aplicación pública

1. Abrir la [aplicación](https://erikacasas98-jeerw6vvkvzvbt2s5yjnyr.streamlit.app/).
2. Consultar Resumen y explorar los doce Trayectos.
3. En Planificación y contingencias, elegir una aeronave, confirmar el alcance
   y ejecutar si la admisión lo permite. Si faltan recursos, conservar el bloqueo.
4. Revisar el caso original y sus evidencias en Validación técnica.
5. Pulsar Evaluar predicción de retrasos para entrenar y comparar Ridge.
6. Descargar los resultados que se deseen conservar antes de cerrar la sesión.

### Instalación local

Se ha trabajado con Python 3.14.3 en Windows; Colab CP-SAT usó Python 3.13.18.
El Dev Container está configurado con Python 3.13. Community Cloud configura su
intérprete por separado; no se deduce su versión de estos entornos.

Las versiones están fijadas en [requirements.txt](requirements.txt):

| Dependencia | Versión |
| --- | --- |
| Streamlit | 1.66.1 |
| Pandas | 3.0.0 |
| OR-Tools | 9.15.6755 |
| psutil | 7.2.2 |
| scikit-learn | 1.9.1 |

```bash
git clone https://github.com/ERIKACASAS98/skyrisk-lab-academico.git
cd skyrisk-lab-academico
```

Windows (PowerShell):

```powershell
py -3.14 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app_academica.py
```

Linux, con un intérprete compatible y las dependencias disponibles:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app_academica.py
```

### Repetir comprobaciones

Windows:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m herramientas.validadores.auditar_paquete_academico --indice
```

En Linux, sustituir `.venv/Scripts/python.exe` por `.venv/bin/python`.
Si los recursos satisfacen la admisión, la suite puede ejecutar CP-SAT; de lo
contrario omite sus seis pruebas. El recuento documentado no garantiza el resultado
de otra ejecución. La auditoría revisa archivos e índice, sin publicar ni autorizar
un despliegue.

Para reproducir las comprobaciones históricas consultar la
[guía Colab](docs/entrega1/colab.md) y el
[cuaderno externo R2](docs/entrega1/validacion_colab_entorno_r2.ipynb).
El informe inspeccionado acredita el snapshot histórico, no una ejecución nueva
del cuaderno R2. No se regeneran silenciosamente manifiestos ni evidencias.

## Limitaciones y alcance académico

- Datos sintéticos: sin validación de decisiones operacionales o predicciones
  sobre vuelos reales.
- Planificación de una jornada y hasta doce trayectos, sin reposicionamiento,
  cambios de horarios, mantenimiento detallado, tripulaciones ni planificación semanal.
- Viento y lluvia son predictores simulados de Ridge; no son restricciones
  meteorológicas de CP-SAT.
- La validación ampliada en Colab y el recorrido público de la interfaz no prueban
  una nueva optimización ampliada exitosa en producción.
- Los presupuestos supervisados y la cancelación cooperativa no garantizan
  terminación forzada ni límites duros de consumo.
- Los resultados de sesión son temporales y no actualizan automáticamente el catálogo.

El desarrollo profesional futuro de SkyRisk Lab contempla mayor alcance de
planificación y apoyo a decisiones. Esa visión no constituye funcionalidad
implementada ni certificación de seguridad de esta entrega. El paquete académico
mantiene una lista explícita de archivos, separada del entorno profesional y sus datos.

## Documentación y trazabilidad

| Documento | Uso |
| --- | --- |
| [Validación técnica](docs/entrega1/validacion.md) | Pruebas, evidencias y registros de preparación. |
| [Arquitectura](docs/entrega1/arquitectura.md) | Diseño y fundamentos técnicos. |
| [Investigación](docs/entrega1/investigacion.md) | Problema y selección tecnológica. |
| [Compatibilidad cloud](docs/entrega1/compatibilidad_cloud.md) | Estudios y condiciones de entorno. |
| [Presentación](docs/entrega1/presentacion.md) | Guion y recorrido de la interfaz. |
| [Colab](docs/entrega1/colab.md) | Reproducción de comprobaciones históricas. |

Las guías técnicas conservan registros de etapas anteriores, algunos con tareas
entonces pendientes. Este README actualiza el estado publicado al 14/11/2026,
incluida la verificación pública de navegación y Ridge posterior al commit
`853868e`. Esa comprobación se registró en el informe de publicación de la sesión;
no se añadió un artefacto público independiente de navegador. Los resultados
históricos se conservan y no se atribuyen a ejecuciones nuevas.
