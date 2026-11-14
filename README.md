
# SkyRisk Lab ✈️

> Rama de desarrollo `desarrollo/ampliacion-academica`: la ampliación v2 y ML
> son cambios locales, sin publicar. La demostración pública enlazada más abajo
> corresponde a la versión original de dos trayectos. Estado y pruebas de la
> ampliación al final de este documento.
### Inteligencia operacional aplicada a la aviación

SkyRisk Lab es un proyecto de inteligencia operacional aeronáutica que busca integrar inteligencia artificial, analítica de datos y optimización matemática para apoyar la planificación y la toma de decisiones en las operaciones aéreas.

# Nuestra visión

Nuestro propósito es desarrollar una plataforma integral capaz de analizar escenarios operacionales, anticipar contingencias y evaluar alternativas que permitan tomar decisiones más eficientes, seguras y sostenibles.

No buscamos simplemente aumentar la cantidad de vuelos ni reducir costos. **Buscamos optimizar las decisiones**, equilibrando factores como:

- Seguridad operacional y cumplimiento de restricciones.
- Disponibilidad y utilización responsable de aeronaves.
- Planificación y bienestar de las tripulaciones.
- Continuidad del servicio y puntualidad.
- Costos operacionales y capacidad de respuesta ante contingencias.

SkyRisk Lab está concebido como una herramienta de apoyo a la toma de decisiones, no como un sustituto del criterio de los profesionales aeronáuticos.

# ¿Qué hemos desarrollado?

Como primera etapa, desarrollamos un demostrador académico para el curso **Introducción a la Inteligencia Artificial**, utilizando Python, Streamlit y OR-Tools CP-SAT.

El demostrador permite optimizar la asignación de aeronaves para un escenario sintético de dos trayectos nacionales, considerando 47 aeronaves regulares y tres de reserva excluidas de la programación rutinaria.

En esta implementación inicial, la función objetivo maximiza los trayectos asignados, con unicidad y continuidad de la cadena fija de dos vuelos. La ubicación y disponibilidad por aeronave se modelan explícitamente en la ampliación v2.

Este objetivo matemático específico no debe confundirse con la visión integral de SkyRisk Lab, que contempla múltiples criterios de optimización.

# Estado actual del proyecto

- Repositorio académico publicado en GitHub.
- Aplicación desplegada en Streamlit Community Cloud.
- Ejecución real de OR-Tools CP-SAT desde la interfaz.
- Resultado OPTIMAL: 2 de 2 trayectos asignados.
- Recuperación y validación del resultado desde un proceso independiente.
- Datos exclusivamente sintéticos.

**Alcance:** esta versión demuestra la optimización de dos trayectos. No representa todavía una plataforma operacional completa ni un sistema autorizado para uso real en una aerolínea.



# Problema que buscamos resolver

La planificación de operaciones aéreas implica coordinar múltiples recursos que dependen unos de otros. La disponibilidad de aeronaves, sus ubicaciones, los itinerarios, los tiempos de tránsito y las restricciones operacionales deben considerarse conjuntamente.

Una decisión que parece adecuada de manera individual puede generar dificultades en otras partes de la operación, como retrasos, conflictos de programación, utilización ineficiente de recursos o cancelaciones.

SkyRisk Lab busca abordar este problema mediante herramientas que permitan evaluar alternativas y apoyar decisiones operacionales de manera integral.

## Alcance de esta primera implementación

Para demostrar el funcionamiento de la solución, desarrollamos un escenario académico con las siguientes características:

- Dos trayectos nacionales sintéticos: Bogotá–Medellín y Medellín–Bogotá.
- Una flota simulada de 50 aeronaves Airbus A320.
- 47 aeronaves regulares elegibles para asignación.
- Tres aeronaves de reserva excluidas de la programación rutinaria.
- Tiempo mínimo de tránsito de 60 minutos.
- Restricciones de asignación y continuidad física de las aeronaves.

El demostrador utiliza un modelo de optimización con restricciones para encontrar una solución válida al escenario planteado.

Esta primera etapa no incluye la planificación de tripulaciones, la optimización semanal completa ni la gestión operacional real de una aerolínea.

Su propósito es comprobar, mediante un caso controlado y verificable, cómo la optimización matemática puede contribuir a resolver problemas de planificación aeronáutica.



# Inteligencia artificial y optimización

SkyRisk Lab utiliza técnicas de optimización matemática para evaluar alternativas de planificación y encontrar soluciones que respeten las restricciones operacionales establecidas.

Para esta primera implementación seleccionamos **OR-Tools CP-SAT**, un solucionador de programación por restricciones desarrollado por Google, que combina técnicas de búsqueda, programación por restricciones y optimización.

## ¿Por qué CP-SAT?

La asignación de aeronaves es un problema de decisiones interdependientes. No basta con encontrar una aeronave disponible: también debemos comprobar que pueda realizar el trayecto, encontrarse en la ubicación adecuada y cumplir los tiempos mínimos entre operaciones.

CP-SAT permite representar estas condiciones mediante variables de decisión, restricciones y una función objetivo.

## ¿Cómo funciona nuestro modelo?

El demostrador académico utiliza:

- **94 variables binarias:** representan posibles asignaciones entre 47 aeronaves regulares y dos trayectos.
- **49 restricciones:** limitan las combinaciones permitidas según las reglas del escenario.
- **Función objetivo:** maximizar el número de trayectos asignados sin incumplir las restricciones del modelo.
- **Solucionador CP-SAT:** busca una combinación válida y determina si puede demostrar su optimalidad.

## Optimización frente a maximización

La optimización consiste en encontrar la mejor solución de acuerdo con los objetivos y las restricciones definidos. Dependiendo del problema, puede implicar maximizar, minimizar o equilibrar varios criterios.

En este demostrador, maximizar los trayectos asignados es una función objetivo específica y simplificada.

La visión futura de SkyRisk Lab es desarrollar una optimización integral que considere simultáneamente seguridad, continuidad operacional, costos, disponibilidad de recursos y bienestar de las tripulaciones.

## Interpretación de resultados

El solucionador puede devolver estados como:

- **OPTIMAL:** encontró una solución y demostró que es óptima para el modelo.
- **FEASIBLE:** encontró una solución válida, sin demostrar necesariamente que sea óptima.
- **INFEASIBLE:** demostró que no existe una solución que cumpla todas las restricciones.
- **UNKNOWN:** no pudo determinar un resultado concluyente dentro de los límites establecidos.

Un resultado óptimo para dos trayectos no significa que se haya optimizado toda la operación de una aerolínea.

Esta implementación corresponde a optimización y búsqueda con restricciones; no utiliza un modelo predictivo entrenado con datos históricos.


# Arquitectura tecnológica

SkyRisk Lab Académico utiliza una arquitectura modular desarrollada en Python y desplegada en Streamlit Community Cloud.

La solución separa la interfaz, la validación de entradas, la ejecución del optimizador y la recuperación de resultados. Esta separación permite mantener un flujo de ejecución controlado y facilita las pruebas y el mantenimiento del código.

## Componentes principales

| Componente | Tecnología | Función |
|---|---|---|
| Interfaz web | Streamlit | Permite explorar el escenario, ejecutar la optimización y consultar resultados. |
| Lógica de aplicación | Python | Gestiona las entradas, validaciones y flujo de ejecución. |
| Motor de optimización | Google OR-Tools CP-SAT | Resuelve el problema de asignación de aeronaves bajo restricciones. |
| Ejecución independiente | Procesos de Python | Aísla el cálculo del proceso principal de la interfaz. |
| Recuperación y validación | Python | Recupera y comprueba los resultados generados por el optimizador. |
| Alojamiento en la nube | Streamlit Community Cloud | Permite acceder al demostrador desde un navegador. |
| Control de versiones | Git y GitHub | Mantiene el código, la documentación y el historial del proyecto. |

## Flujo de funcionamiento

1. El usuario accede a la aplicación desplegada en la nube.
2. Streamlit presenta el escenario sintético y sus restricciones.
3. La aplicación valida las condiciones necesarias para iniciar la ejecución.
4. Un proceso independiente ejecuta el modelo de optimización CP-SAT.
5. El sistema recupera y valida el resultado del proceso.
6. Streamlit presenta el estado del solucionador, las asignaciones y las métricas disponibles.

## Consideraciones técnicas

La aplicación incorpora controles de recursos y límites de ejecución para reducir el riesgo de sobrecarga del entorno.

El motor CP-SAT se ejecuta en un proceso independiente, con mecanismos de recuperación y validación de resultados.

Los datos utilizados son sintéticos y el demostrador no se conecta a sistemas operacionales reales de aerolíneas.

La documentación detallada de la arquitectura se encuentra en [Arquitectura técnica](docs/entrega1/arquitectura.md).



## Demostración pública

SkyRisk Lab Académico está desplegado en Streamlit Community Cloud y puede utilizarse directamente desde un navegador.

**Aplicación web:** [Acceder a SkyRisk Lab](https://erikacasas98-jeerw6vvkvzvbt2s5yjnyr.streamlit.app/)

**Repositorio público:** [GitHub - SkyRisk Lab Académico](https://github.com/ERIKACAS98/skyrisk-lab-academico)

## ¿Cómo explorar la aplicación?

La interfaz está organizada en cuatro secciones:

1. **Resumen:** presenta el propósito y las características del demostrador académico.
2. **Caso sintético:** permite consultar los dos trayectos, las aeronaves elegibles y las restricciones del escenario.
3. **Optimización:** permite ejecutar el modelo CP-SAT y consultar las asignaciones y métricas obtenidas.
4. **Consulta histórica:** muestra las evidencias disponibles y diferencia los registros históricos de los resultados temporales de sesión.

## Ejecución validada en la nube

El 13 de noviembre de 2026 se ejecutó el modelo CP-SAT desde la aplicación desplegada en Streamlit Community Cloud.

El resultado obtenido fue:

- **Estado:** OPTIMAL.
- **Trayectos asignados:** 2 de 2.
- **Valor de la función objetivo:** 2.
- **Aeronave asignada:** HK-003.
- **Variables:** 94.
- **Restricciones:** 49.
- **Tiempo mínimo de tránsito:** 60 minutos.

El resultado fue recuperado y validado desde un proceso independiente.

Esta ejecución demuestra el funcionamiento del modelo en el escenario académico definido. No representa una optimización integral de la operación de una aerolínea.

**Nota:** los resultados generados durante la sesión no se almacenan automáticamente en un catálogo permanente.


# Resultados y evidencias

SkyRisk Lab Académico cuenta con ejecuciones reales del modelo OR-Tools CP-SAT y pruebas automatizadas que respaldan el funcionamiento del demostrador.
## Ejecución en Streamlit Community Cloud

El 13 de noviembre de 2026 se ejecutó el modelo desde la aplicación pública.

| Indicador | Resultado |
|---|---|
| Estado del solucionador | OPTIMAL |
| Trayectos asignados | 2 de 2 |
| Valor objetivo | 2 |
| Cota superior | 2 |
| Aeronave asignada | HK-003 |
| Variables | 94 |
| Restricciones | 49 |
| Tránsito entre trayectos | 60 minutos |

El resultado fue recuperado y validado desde un proceso independiente.

El estado OPTIMAL indica que el solucionador demostró la optimalidad de la solución respecto de la función objetivo y las restricciones del escenario académico.

## Ejecución en Google Colab

También se realizó una ejecución independiente en Google Colab el 13 de noviembre de 2026.

| Indicador | Resultado |
|---|---|
| Estado del solucionador | OPTIMAL |
| Trayectos asignados | 2 de 2 |
| Valor objetivo | 2 |
| Cota superior | 2 |
| Aeronave asignada | HK-049 |
| Variables | 94 |
| Restricciones | 49 |
| Tiempo de resolución | 0.012 segundos |

Ambas ejecuciones alcanzaron el mismo valor objetivo, aunque seleccionaron aeronaves diferentes.

Esto no representa una contradicción: un problema de optimización puede tener varias soluciones igualmente óptimas.

La evidencia histórica de Colab está disponible en:

`docs/evidencias/evidencia_cpsat_publica.json`

## Pruebas automatizadas

Se aprobaron 60 pruebas académicas únicas, distribuidas en:

| Componente | Pruebas aprobadas |
|---|---:|
| Lectura y validación | 24 |
| Ejecución y recuperación | 17 |
| Auditoría de publicación | 11 |
| Interfaz académica | 8 |
| **Total** | **60** |

Estas pruebas verifican componentes del demostrador, pero no sustituyen las ejecuciones reales del solucionador.

## Alcance de los resultados

Las evidencias corresponden a un escenario sintético controlado de dos trayectos.

No demuestran todavía escalabilidad a una programación semanal completa ni validan el uso operacional de SkyRisk Lab en una aerolínea.

Los resultados de Streamlit Cloud se conservan temporalmente durante la sesión, mientras que la evidencia histórica de Colab está documentada en el repositorio.



# Estructura del repositorio

El repositorio de SkyRisk Lab Académico organiza el código fuente, los escenarios sintéticos, las pruebas y la documentación técnica de la solución.

Su estructura principal es:

```text
skyrisk-lab-academico/
│
├── app_academica.py
├── academico/
├── demo/
├── docs/
│   ├── entrega1/
│   └── evidencias/
├── tests/
├── herramientas/
│   └── validadores/
├── requirements.txt
└── README.md
```

## Descripción de los componentes

| Archivo o carpeta | Función |
|---|---|
| `app_academica.py` | Punto de entrada de la aplicación Streamlit. |
| `academico/` | Componentes del demostrador, validaciones y ejecución controlada. |
| `demo/` | Entradas y escenarios sintéticos utilizados en la demostración. |
| `docs/entrega1/` | Documentación de arquitectura, investigación y validación. |
| `docs/evidencias/` | Evidencias técnicas de ejecuciones documentadas. |
| `tests/` | Pruebas automatizadas del proyecto académico. |
| `herramientas/validadores/` | Utilidades de revisión y auditoría del paquete. |
| `requirements.txt` | Dependencias necesarias para ejecutar la aplicación. |
| `README.md` | Presentación, instrucciones y documentación general del proyecto. |

## Organización académica

El repositorio público contiene una versión delimitada de SkyRisk Lab, desarrollada para demostrar un componente inicial de optimización aeronáutica.

El proyecto académico se mantiene separado del entorno profesional y utiliza exclusivamente información sintética.

La documentación complementaria permite consultar los fundamentos técnicos, las decisiones de arquitectura y las evidencias de validación.

## Instalación y ejecución local

SkyRisk Lab Académico puede ejecutarse localmente utilizando Python y un entorno virtual independiente.

## Requisitos

- Python 3.14.
- Git, para clonar el repositorio.
- Conexión a Internet para instalar las dependencias.
- Recursos suficientes para ejecutar el optimizador.

Las principales bibliotecas utilizadas son:

| Biblioteca | Versión | Propósito |
|---|---|---|
| Streamlit | 1.66.1 | Interfaz web |
| pandas | 3.0.0 | Manejo de datos |
| OR-Tools | 9.15.6755 | Motor de optimización CP-SAT |
| psutil | 7.2.2 | Supervisión de recursos |

## 1. Clonar el repositorio

```bash
git clone https://github.com/ERIKACAS98/skyrisk-lab-academico.git
cd skyrisk-lab-academico
```

## 2. Crear el entorno virtual

**Windows (PowerShell):**

```powershell
py -3.14 -m venv .venv
```

**Linux:**

```bash
python3.14 -m venv .venv
```

## 3. Instalar las dependencias

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux:**

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## 4. Iniciar la aplicación

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_academica.py
```

**Linux:**

```bash
.venv/bin/python -m streamlit run app_academica.py
```

Streamlit mostrará una dirección local que podrá abrirse desde el navegador.

## Consideraciones de ejecución

La interfaz puede explorarse sin iniciar el optimizador.

Para ejecutar CP-SAT, el sistema comprueba previamente las condiciones de admisión, incluida la disponibilidad mínima de 2 GiB de memoria, según los controles implementados.

Si el entorno no cumple los requisitos, la ejecución puede ser rechazada sin modificar las restricciones de seguridad.

La instalación local no requiere bases de datos operacionales ni información real de aerolíneas.








# Seguridad, ética y limitaciones

SkyRisk Lab reconoce que las decisiones aeronáuticas pueden afectar la seguridad operacional, el bienestar de las tripulaciones, los recursos de una organización y la continuidad del servicio.

Por esta razón, el desarrollo de la plataforma debe incorporar principios de seguridad, transparencia, responsabilidad y supervisión humana.

## Protección de datos

El demostrador académico utiliza exclusivamente información sintética.

No requiere datos personales de tripulaciones, pasajeros ni empleados, y no se conecta a bases de datos operacionales de aerolíneas.

El repositorio público se prepara mediante una lista explícita de archivos autorizados y un proceso de auditoría para reducir el riesgo de publicar información privada, credenciales o archivos del proyecto profesional.

## Transparencia y explicabilidad

El modelo utiliza variables, restricciones y una función objetivo definidas explícitamente.

Los resultados permiten identificar las asignaciones realizadas y consultar información sobre el estado del solucionador.

El estado OPTIMAL significa que se demostró la optimalidad de una solución respecto del modelo implementado; no garantiza que esa solución sea la mejor para una operación aeronáutica real.

## Seguridad de ejecución

La aplicación incorpora controles para limitar el consumo de recursos y supervisar la ejecución del optimizador.

Entre ellos se encuentran:

- Verificación previa de recursos, incluida la disponibilidad mínima de 2 GiB de memoria.
- Ejecución del optimizador en un proceso independiente.
- Límites supervisados de ejecución.
- Recuperación y validación de resultados.
- Mecanismos de cancelación cooperativa.

Estos mecanismos reducen riesgos técnicos, pero no garantizan la terminación inmediata de todos los procesos ante cualquier fallo.

## Supervisión humana y responsabilidad

SkyRisk Lab está concebido como una herramienta de apoyo a la toma de decisiones.

En una aplicación operacional futura, las recomendaciones deberán ser evaluadas por personal competente y cumplir la normativa aeronáutica aplicable.

La plataforma no debe sustituir el criterio profesional ni priorizar objetivos económicos por encima de la seguridad.

## Limitaciones actuales

Esta primera implementación:

- Trabaja con dos trayectos sintéticos.
- No representa una programación semanal completa.
- No incorpora todavía planificación de tripulaciones, mantenimiento o meteorología en el modelo académico.
- No utiliza modelos predictivos entrenados con datos históricos.
- No está validada para operar en una aerolínea real.
- No almacena automáticamente las ejecuciones de sesión en un catálogo permanente.

Los resultados obtenidos permiten validar el funcionamiento del demostrador dentro de su alcance, pero no deben extrapolarse a operaciones comerciales reales.

La documentación detallada de las pruebas y limitaciones se encuentra en [Validación técnica](docs/entrega1/validacion.md).



# Documentación y referencias

SkyRisk Lab Académico fue desarrollado como parte del Taller ABP – Entrega 1 del curso Introducción a la Inteligencia Artificial, de la Fundación Universitaria Católica del Norte.

La entrega reúne una solución tecnológica desplegada en la nube, su código fuente, documentación técnica y evidencias de funcionamiento.

## Documentación del proyecto

| Documento | Contenido |
|---|---|
| [Arquitectura tecnológica](docs/entrega1/arquitectura.md) | Componentes, diseño de la solución y flujo de ejecución. |
| [Investigación y fundamentos](docs/entrega1/investigacion.md) | Justificación del problema y fundamentos tecnológicos. |
| [Validación técnica](docs/entrega1/validacion.md) | Pruebas, resultados, evidencias y limitaciones. |
| [Compatibilidad con la nube](docs/entrega1/compatibilidad_cloud.md) | Dependencias y consideraciones del entorno de despliegue. |
| [Presentación académica](docs/entrega1/presentacion.md) | Estructura y contenido de la presentación del proyecto. |

## Relación con los objetivos de la actividad

El proyecto aborda los componentes solicitados en la entrega:

- **Análisis del problema:** identificación de las dificultades de planificación y asignación de recursos aeronáuticos.
- **Arquitectura tecnológica:** desarrollo de una aplicación modular desplegada en la nube.
- **Ingeniería de software:** organización del código, control de versiones, pruebas y validaciones.
- **Aplicación de inteligencia artificial:** utilización de optimización matemática mediante OR-Tools CP-SAT.
- **Ética y responsabilidad:** protección de datos, transparencia, limitaciones y supervisión humana.
- **Comunicación de resultados:** repositorio público, demostración funcional y presentación académica.

## Recursos tecnológicos

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Google OR-Tools](https://developers.google.com/optimization)
- [GitHub](https://github.com/)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)

## Acceso al proyecto

**Repositorio:** https://github.com/ERIKACAS98/skyrisk-lab-academico

**Aplicación:** https://erikacasas98-jeerw6vvkvzvbt2s5yjnyr.streamlit.app/

---

**SkyRisk Lab — Inteligencia operacional para decisiones aeronáuticas más seguras, eficientes y responsables.**

## Ampliación académica v2 en desarrollo — 13/11/2026

Esta rama conserva el caso original, el inventario de 47 regulares y tres
reservas, y los bytes de la evidencia Colab. No se ha publicado esta ampliación.
No modifica SQLite ni módulos profesionales.

La vista **Simulación ampliada** presenta 12 vuelos nacionales entre BOG, MDE,
CLO y CTG. Solo cuatro aeronaves están activas: HK-001 y HK-002 en BOG, HK-003
en CLO y HK-004 en CTG, con disponibilidad explícita. Las demás aeronaves del
inventario no se habilitan automáticamente. No hay reposicionamiento, cambios
de horarios, mantenimiento detallado ni tripulaciones.

El modelo CP-SAT v2 construye caminos temporales por aeronave, con inicio factible,
conservación de flujo y conexiones aeropuerto/horario con tránsito mínimo de
60 minutos. Admite planes parciales y vacíos; cada vuelo queda asignado o pendiente.
El objetivo prioriza cobertura, luego conservar asignaciones de la planificación
base y finalmente una preferencia de matrícula. No se interpreta una solución
FEASIBLE como prueba de optimalidad ni un pendiente como prueba de imposibilidad.

Se puede seleccionar una aeronave activa y bloquearla toda la jornada. Una acción
explícita calcula la base y la recuperación, valida ambas y muestra afectados,
sustitutas reales, cambios y pendientes. Las pruebas reales de Colab verificaron
12 vuelos atendidos antes y después de bloquear HK-001, con un cambio observable,
y AMP-05 pendiente al bloquear HK-003 en CLO. El informe conserva resultados de
pruebas, no todas las matrices de asignación: no se inventan matrículas sustitutas
ni tiempos internos del solver ausentes de la evidencia. Los validadores también
se comprobaron con fixtures explícitas sin solver.

La solicitud completa se copia al temporal y se guarda con inventario, ubicaciones,
incidente y hash canónico. El recuperador separado valida manifiestos, planes,
comparación y correspondencia exacta con la solicitud. El resultado de sesión se
puede descargar; el almacén temporal se elimina tras la salida de los procesos.
No se incorpora automáticamente al catálogo histórico ni es persistencia durable.

Se mantienen 2 GiB de admisión CP-SAT, 512/128 MiB de RSS productor/recuperador y
los presupuestos de 60/15/90 s. Cada uno de los dos planes v2 tiene un presupuesto
de solver de 15 s, dentro de los 30 s originales totales. Estos presupuestos son
supervisados: la cancelación sigue siendo cooperativa, sin terminación forzada.

### Predicción de retrasos: entrenamiento real, datos simulados

La vista **Predicción de retrasos** solo entrena por botón. Genera 1.000 registros
con semilla 20261114, en 100 días sintéticos. Predictores: origen, destino, hora
programada, congestión, viento y lluvia previstos. El objetivo se genera mediante
una fórmula explícita con ruido; no procede de vuelos reales ni de CP-SAT.

GroupShuffleSplit separa días completos: 800 registros de entrenamiento y 200 de
prueba. StandardScaler y OneHotEncoder se ajustan dentro de un Pipeline solo con
entrenamiento. Se compara Ridge(alpha=1, solver=lsqr) con DummyRegressor(media).
La predicción mostrada se limita inferiormente a cero. No se realiza selección de
hiperparámetros usando la prueba ni se conectan predicciones a las restricciones.

Resultados reales del experimento local:

| Medida | Valor |
| --- | --- |
| MAE Ridge | 3,0628339081 minutos |
| MAE referencia Dummy | 6,2101520217 minutos |
| Datos SHA-256 | 91860488e459ab7ab9273ee39761152569a2ca3b27476a556122202103cef7bd |
| Registros entrenamiento / prueba | 800 / 200 |

Estos resultados evalúan aprendizaje del generador sintético, no capacidad de
predecir retrasos reales. ML utiliza un hilo de cómputo y comparte exclusión con
CP-SAT. Exige 256 MiB disponibles antes de comenzar; esto no cambia el requisito
de 2 GiB del optimizador. No guarda ni carga modelos pickle de fuentes externas.

### Verificación y pendiente de aceptación

Se comprobaron 81 pruebas únicas locales sin CP-SAT y las seis pruebas reales
CP-SAT aprobaron en Google Colab/Linux/Python 3.13.18. El informe y su log fueron
inspeccionados, con seis registros APROBADA, sin fallos, errores ni omisiones,
y con snapshot verificado al finalizar. No se redujo la admisión de 2 GiB.
Las 60 pruebas originales están incluidas en los 81 casos locales; no se suman
repeticiones ni se presenta todo como una única suite ejecutada en Cloud.
La evaluación Ridge es local; el entrenamiento real desde la interfaz pública
ampliada todavía requiere validación. Ver `docs/entrega1/validacion.md`.

Para repetir solo las comprobaciones sin solver:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_ampliacion_academica.py -k AmpliacionAcademicaTests -q
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_ml_academico.py -q
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_app_academica.py -q
```

Con al menos 2 GiB libres y admisión válida, ejecutar los seis ensayos de forma
secuencial; si la admisión falla, unittest los marca omitidos, no aprobados:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_ampliacion_academica.py -k SolverAmpliadoRealTests -v
```

Para ejecutar la suite completa:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_*academic*.py' -v
.venv/Scripts/python.exe -B -m pip check
.venv/Scripts/python.exe -B -m streamlit run app_academica.py
```

Arrancar el servidor no ejecuta entrenamiento ni CP-SAT. AppTest comprobó la
navegación y acciones, sin navegador ni servidor público. La validación Colab
acredita CP-SAT y sus dependencias mínimas; no sustituye la instalación Linux del
stack completo de Streamlit/Scikit-learn ni el recorrido público real del botón ML.
Faltan esas comprobaciones y autorización para publicar. La política actual admite
37 rutas exactas, incluido el cuaderno externo R2; no añade artefactos ni resultados
automáticamente. No hacer commit, push, merge o despliegue sin autorización.

## Reproducción de las seis pruebas aprobadas en Colab

La guía está en [docs/entrega1/colab.md](docs/entrega1/colab.md). Para reproducir
el entorno use el [cuaderno externo R2](docs/entrega1/validacion_colab_entorno_r2.ipynb),
que evita ensurepip usando venv --without-pip y el pip principal con --python.
El [cuaderno original](docs/entrega1/validacion_colab.ipynb) y los 36 archivos de
su snapshot permanecen intactos dentro del ZIP original. Se conservan sus hashes.
No basta clonar el commit base para obtener aquel árbol de trabajo sin commit.
R2 se incluye ahora en la política del repositorio, no en el manifiesto original.

El venv de Colab instala solo OR-Tools 9.15.6755, pandas 3.0.0 y psutil 7.2.2,
con sus transitivas registradas. No necesita Streamlit, ML ni GPU. Un preflight
aplica la admisión original de 2 GiB y cgroup; cada prueba vuelve a comprobarla.
El runner ejecuta exclusivamente los seis métodos existentes, secuencialmente,
y no considera una omisión como aprobación. Los tests directos mantienen sus
controles actuales: el procedimiento no añade una contención dura ni promete
plazos estrictos donde la cancelación es cooperativa.

El resultado real se conserva en evidencia_skyrisk_cpsat_colab.zip, con
resultado.json, unittest.log y MANIFIESTO_COLAB.json. Su huella SHA-256 es:
`24b8f3547eb8e048e7b13acd9f496964360b29f9f04a7010daa9b63dc7a63171`.
El manifiesto coincide byte a byte con el del snapshot original. La ejecución
registró 2026-11-14T02:25:01.380789+00:00 (13/11/2026, 21:25:01, America/Bogota).
El archivo de evidencia se mantiene en custodia local separada; no se añade el
ZIP de Descargas ni se exponen rutas personales en el paquete público.

El snapshot original mantiene SHA-256
`34b5bffd805aaff0ef04b22d27b00aaf4ecd2a979d067e6ec671faa880c0bb13`
y snapshot_id
`aca0c168268a2db1bb0c9b52fbd2735cf295b5a408a536bb27c64f6a6a48e456`.
No regenerarlo ni actualizar silenciosamente su manifiesto. artifacts/ permanece
excluido de Git. Publicar documentación nueva o R2 no convierte el commit nuevo
en aquel snapshot: son revisiones externas y trazables, sin cambiar el optimizador.
La instalación y ejecución completa del cuaderno externo R2 no se acredita solo
por el informe del snapshot: debe distinguirse de la corrección manual del entorno
con la que se obtuvieron las seis aprobaciones.
