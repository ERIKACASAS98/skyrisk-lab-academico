# Compatibilidad y condiciones de despliegue

Estado: comprobación de metadatos y preparación, sin instalación Linux ni
despliegue ejecutados. No hay una URL cloud verificada. El despliegue real es
obligatorio para la entrega y continúa pendiente de autorización.

El equipo auditado no tiene WSL instalado y no se autorizó instalarlo. Por ello,
la evidencia actual cubre rutas portables, carga aislada del worker, metadatos de
wheels Linux y pruebas locales sin solver; **no equivale a una instalación limpia
ejecutada sobre Linux**.

## Versiones preparadas

| Paquete directo | Versión | Evidencia Linux / Python 3.14 |
| --- | --- | --- |
| Streamlit | 1.66.1 | Requires-Python >=3.11, clasificador 3.14 y wheel universal |
| pandas | 3.0.0 | Wheel cp314 manylinux x86-64 |
| OR-Tools | 9.15.6755 | Wheel cp314 manylinux x86-64; aún no importado por la app |
| psutil | 7.2.2 | Wheel cp36-abi3 manylinux para CPython convencional |

Fuentes oficiales: [Streamlit](https://pypi.org/project/streamlit/1.66.1/),
[pandas](https://pypi.org/simple/pandas/),
[OR-Tools](https://pypi.org/project/ortools/9.15.6755/),
[psutil](https://pypi.org/simple/psutil/).

Los rangos de dependencias declarados se intersectan en NumPy >=2.3.3,<3,
protobuf >=6.33.1,<6.34 y typing-extensions >=4.12,<5 para Python 3.14.
El entorno Windows revisado usa Python 3.14.3, NumPy 2.4.2 y protobuf 6.33.6.
Fijar cuatro dependencias directas no equivale a un lock completo ni demuestra
que una instalación limpia vaya a resolver todas las transitivas.

## Community Cloud

La documentación ofrece selección de Python en Advanced settings y declara
soporte de versiones con actualizaciones de seguridad, pero no enumera aquí
Python 3.14 como opción comprobada. Verificar el selector antes de publicar el
despliegue; no sustituir silenciosamente la versión profesional. Si 3.14 no está
disponible, evaluar un proveedor cloud con contenedor Python 3.14.

Community Cloud utiliza Linux y un repositorio GitHub. Se preparará la entrada
`app_academica.py`; `st.navigation` registra exclusivamente la página académica
y evita la autodetección de `pages/` profesional.

Fuentes: [despliegue](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[dependencias](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
[navegación](https://docs.streamlit.io/develop/concepts/multipage-apps/pages-directory).

## Recursos para la futura optimización interactiva

La modalidad de consulta no utiliza CP-SAT. La modalidad interactiva ya está
integrada, pero su primer ensayo real requiere autorización expresa. **No se
reduce el mínimo de 2 GiB de RAM libre** ni se ejecuta el modelo al abrir la app.

Community Cloud publica recursos aproximados y variables; no garantiza 2 GiB
libres. Antes de habilitar CP deben comprobarse memoria disponible del sistema
y margen efectivo del contenedor (`memory.max - memory.current` en cgroup v2,
incluyendo ancestros), cuota CPU y ensayos activos. Si no puede verificarse el
margen, la modalidad de optimización permanece deshabilitada y la consulta sirve
de respaldo. El perfil ORIGINAL conserva cuatro trabajadores: no se ajusta
silenciosamente a la cuota de CPU.

Fuentes: [recursos Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app),
[cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).

## Git local

Git y el repositorio local ya están disponibles. La situación del 12 de noviembre
sin Git queda superada. Ejecutar el auditor con `--indice`: las diferencias
esperadas entre el índice y los archivos modificados se deben revisar antes de
preparar una versión. Esta sesión no modifica el índice ni inspecciona todo el
historial; no autoriza publicación.

## Evidencia pendiente antes de declarar cloud verificado

1. Revisión humana de archivos y comprobación del índice Git.
2. Autorización de publicación y despliegue; URL y commit reales.
3. Instalación Linux limpia con logs y versiones resueltas.
4. Prueba de arranque sin SQLite ni optimización automática.
5. Prueba de consulta con un escenario sintético validado cuando exista.
6. Para la modalidad interactiva: recursos efectivos suficientes,
   ejecución explícita pequeña y recuperación independiente con hashes.

## Estado del código actual — 13/11/2026

El lanzador ya no contiene una ruta fija `Lib/site-packages`. Usa purelib/platlib
del entorno mediante sysconfig y carga sus `.pth`. Las sondas reales comprobaron
PID directo, argumentos, paquetes y aislamiento en Windows/Python 3.14.3.
El recuperador real leyó una fixture persistida desde otro proceso, sin solver.
Las ramas Linux de bloqueo y cgroup no se ejecutaron en esta sesión; los tests
que simulan admisión Linux no sustituyen esa prueba. No se afirma instalación
Linux ni compatibilidad cloud validada para esta revisión.

`requirements.txt` mantiene streamlit 1.66.1, pandas 3.0.0, ortools 9.15.6755 y
psutil 7.2.2, sin dependencias nuevas. Las versiones instaladas y `pip check`
se revisan localmente; una instalación limpia sigue pendiente. El procedimiento
Linux exacto está en README, junto con publicación posterior, sin ejecutar Git add,
commit, push ni despliegue durante este cierre.

En producción de demostración, una plataforma con plazos estrictos o sin margen
verificable no es apta para habilitar esta optimización cooperativa. Conservar la
consulta histórica como respaldo y no reducir la admisión de 2 GiB. La exclusión
no cubre réplicas con temporales independientes. Los temporales y la sesión no
son almacenamiento durable; descargar el resultado y registrar la evidencia.
