
# SkyRisk Lab ✈️
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

En esta implementación inicial, la función objetivo maximiza los trayectos asignados, respetando las restricciones de disponibilidad, continuidad física y tránsito mínimo.

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
