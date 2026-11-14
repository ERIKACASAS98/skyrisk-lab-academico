# Reproducción externa R2 de las seis pruebas CP-SAT en Colab

## Identidad y evidencia conservadas

Use docs/entrega1/validacion_colab_entorno_r2.ipynb como cuaderno externo. No está
incluido en el snapshot original ni en su manifiesto. Conserva una referencia
SHA-256 al cuaderno original en sus metadatos, pero no modifica aquel archivo.
La guía de trabajo actual también es externa: no la copie dentro del snapshot.

El usuario informó que, en Colab/Python 3.13, ensurepip falló al crear el venv,
pero venv --without-pip y el pip principal con --python funcionaron. Informó
además PREFLIGHT_LISTO_NO_EJECUTADO y SEIS_APROBADAS con integridad final válida,
con evidencia guardada por separado en evidencia_skyrisk_cpsat_colab.zip. Esa
evidencia no se modifica ni se reemplaza; el cuaderno R2 no contiene resultados
nuevos y su ejecución completa en Colab debe verificarse de forma independiente.

**No regenerar el snapshot ni el manifiesto.** No ejecutar preparar_colab.py para
esta corrección. No reemplazar el cuaderno ni esta guía dentro del ZIP o de la
carpeta extraída. El runner sigue verificando los archivos originales registrados.
La corrección se ejecuta desde fuera de esa carpeta para mantener sus hashes.

La rama contiene cambios sin commit: clonar GitHub o usar únicamente HEAD no
sustituye al ZIP original. Seleccione exactamente el paquete que produjo su
evidencia y su huella externa de confianza, no un paquete regenerado. La identidad
se describe por snapshot_id y hashes por archivo; el commit base solo aporta contexto.
Conserve el ZIP, su identidad y evidencia originales sin sobrescribirlos.

## Dependencias y alcance de la corrección

El manifiesto original fija ortools==9.15.6755, pandas==3.0.0 y psutil==7.2.2.
R2 toma esos pins directamente de MANIFIESTO_COLAB.json y exige su coincidencia
con requirements.txt del snapshot. No cambia versiones ni instala software global.
Las transitivas se resuelven y quedan registradas mediante pip freeze; no se
promete un entorno transitivo idéntico sin comparar ese registro. No se necesitan
Streamlit, Scikit-learn, entrenamiento ML, GPU ni acceso a SQLite.

La celda de entorno aplica este mecanismo:

```python
subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(VENV)], check=True)
PIP_VENV = [sys.executable, '-m', 'pip', '--python', str(PYTHON)]
subprocess.run([*PIP_VENV, 'install', '--only-binary=:all:', *pins], check=True)
subprocess.run([*PIP_VENV, 'check'], check=True)
freeze = subprocess.check_output([*PIP_VENV, 'freeze'])
```

El pip principal dirige las operaciones al intérprete del venv, aunque este no
tenga pip propio. La celda comprueba también, ejecutando el Python aislado, que
cada versión coincide y que su distribución se encuentra bajo sys.prefix del
venv. Los comandos de preflight y ejecución siguen usando ese intérprete aislado.
Si el pip principal no soporta --python, detenerse: no actualizarlo globalmente,
no usar get-pip, no activar --system-site-packages ni relajar versiones.

## Pasos para el docente

1. Abra un runtime **alojado nuevo de Colab, CPU**, con Python >=3.12. No conecte
   un runtime local ni reutilice carpetas de una ejecución anterior. No requiere
   pagar ni activar GPU; los recursos disponibles no están garantizados.
2. En Archivo → Subir cuaderno, seleccione validacion_colab_entorno_r2.ipynb.
   El cuaderno original validacion_colab.ipynb permanece intacto dentro del ZIP.
3. Pegue el SHA-256 externo correspondiente al ZIP original en la primera celda
   de código. No use el hash del cuaderno R2 como hash del ZIP.
4. Cargue solamente el ZIP original. La celda conserva las verificaciones de
   huella, rutas, tamaños, identidad del manifiesto y contenido antes de extraer.
   Si ya existe la carpeta de extracción, detenerse y usar un runtime nuevo.
5. Ejecute la celda de entorno R2: crea venv_skyrisk_r2_<id> sin ensurepip y usa
   el pip principal con --python. Rechaza por anticipado cualquier venv o carpeta
   evidencia_skyrisk_r2_<id> existente, incluidos enlaces. Nunca borra ni repara
   entornos anteriores. Si la instalación queda incompleta, no eliminarla para
   forzar la repetición: utilice un runtime nuevo.
6. Revise pip check y las versiones/ubicaciones impresas. El manifiesto original
   se copia sin cambios a la nueva carpeta de evidencia; freeze registra paquetes
   del venv, no del kernel global.
7. Ejecute preflight: se mantiene la admisión original de 2 GiB y cgroup v2.
   Un rechazo bloquea el paso siguiente; no parchear evaluadores ni /sys.
8. Con preflight aprobado, ejecute la celda --ejecutar. El runner original
   selecciona los mismos seis métodos SolverAmpliadoRealTests secuencialmente,
   comprueba admisión antes de cada uno y se detiene ante fallo, omisión o rechazo.
9. Descargue la evidencia mediante la última celda antes de desconectar. No
   sobrescriba evidencia_skyrisk_cpsat_colab.zip: guarde la nueva descarga con
   otro nombre, por ejemplo evidencia_skyrisk_cpsat_colab_entorno_r2.zip.
   Si el ZIP de salida ya existe en el runtime, la celda se detiene; recupere
   los informes desde el panel de archivos sin sobrescribir nada.

## Verificación e interpretación

La copia original se verifica mediante SHA-256 antes de extraer. El runner
comprueba nuevamente el snapshot antes y después del preflight y de las pruebas.
R2 no elimina ninguna entrada del manifiesto ni incorpora excepciones para el
cuaderno antiguo o esta guía. No cambia el optimizador, los seis tests, límites,
trabajadores, presolve, tránsito, escenarios ni validadores.

Los tests del supervisor conservan sus límites RSS y cancelación; los tests
directos conservan su comportamiento, sin una contención dura adicional. La
cancelación sigue siendo cooperativa y no garantiza un plazo máximo estricto.

El ZIP nuevo contiene JSON/logs de preflight y ejecución, MANIFIESTO_COLAB.json
original y requirements_instalados.txt del venv. Solo aceptar SEIS_APROBADAS con
seis registros APROBADA, cero fallos/errores/omisiones, seis_aprobadas=true,
pendientes vacío y snapshot_verificado_al_final=true. Compare snapshot_id con el
original y revise logs y versiones. Un preflight listo o unittest OK con skips
no demuestra aprobación. Conserve fallos e interrupciones sin editar informes.

El runner no añade corridas ni exporta el almacén efímero completo: los tests
limpian sus temporales. Conserve las evidencias fuera del runtime antes de cerrarlo.
La revisión R2 está identificada por nombre y metadatos, sin incorporarla a la
lista PERMITIDOS, al manifiesto ni a Git. Cualquier inclusión pública posterior
requiere una revisión separada de la política, fuera de esta corrección.

Fuentes oficiales: [carga y descarga](https://colab.research.google.com/notebooks/io.ipynb)
y [recursos de runtimes](https://research.google.com/colaboratory/faq.html).
