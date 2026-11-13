# Datos del demostrador

`entradas_paso1.json` contiene exclusivamente entradas sintéticas diseñadas para
dos trayectos. `resultados: null` y `SIN_EJECUCION` son estados deliberados: no hay
una corrida CP-SAT ejecutada que pueda publicarse todavía.

`escenarios/` está vacío salvo `.gitkeep`. No copiar aquí SQLite operacional,
históricos publicados ni la corrida histórica 896/966. El visor no busca el
almacén de `%LOCALAPPDATA%` ni utiliza `SKYRISK_RUNS_DIR`.

Cuando el ensayo autorizado pueda ejecutarse con al menos 2 GiB libres, revisar
su procedencia SINTETICO, integridad, contenido y metadatos antes de incorporar
un run. La política de publicación actual **no permite subir runs nuevos**;
requieren una revisión explícita de la lista de archivos. Conservar los bytes y
hashes originales: editar una ejecución invalida su integridad.

El visor admite hasta veinte runs, con un máximo de 128 archivos y 8 MiB cada
uno; no ejecuta código archivado. La integridad criptográfica no prueba por sí
sola autenticidad ni validez operacional.
