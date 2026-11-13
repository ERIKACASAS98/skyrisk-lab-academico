"""Controlador del ensayo académico, aislado de SQLite y módulos productivos.

El proceso solo se inicia por una llamada explícita. Los límites son supervisados:
la cancelación cooperativa no equivale a una terminación forzada del sistema.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

import psutil

from academico.escenarios import cargar_entradas


GIB = 1024 ** 3
MIB = 1024 ** 2
RAM_MINIMA = 2 * GIB
RSS_PRODUCTOR_MAX = 512 * MIB
RSS_RECUPERADOR_MAX = 128 * MIB
ALMACEN_MAX = 50 * MIB
PRODUCTOR_S = 60
RECUPERADOR_S = 15
ENSAYO_S = 90
MUESTREO_S = 0.1
ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).with_name('worker.py')


class EjecucionError(RuntimeError):
    pass


def _leer_entero(ruta):
    try:
        valor = Path(ruta).read_text(encoding='ascii').strip()
        return None if valor == 'max' else int(valor)
    except (OSError, ValueError):
        return None


def _cgroup_v2():
    base = Path('/sys/fs/cgroup')
    if os.name == 'nt':
        return {'estado': 'NO_APLICA_HOST_LOCAL', 'margen_bytes': None,
                'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}
    if not (base / 'cgroup.controllers').is_file():
        return {'estado': 'NO_VERIFICABLE', 'margen_bytes': None,
                'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}
    # El grupo actual puede estar anidado. Verificar el límite más restrictivo
    # entre él y sus ancestros hasta la raíz montada.
    try:
        linea = next(l for l in Path('/proc/self/cgroup').read_text().splitlines() if l.startswith('0::'))
        relativo = linea.split('::', 1)[1].lstrip('/')
    except (OSError, StopIteration):
        return {'estado': 'NO_VERIFICABLE', 'margen_bytes': None,
                'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}
    actual = (base / relativo).resolve()
    margenes, limites, usos, cpu = [], [], [], []
    while actual.is_relative_to(base.resolve()):
        limite, uso = _leer_entero(actual / 'memory.max'), _leer_entero(actual / 'memory.current')
        if limite is not None and uso is not None:
            margenes.append(max(0, limite - uso)); limites.append(limite); usos.append(uso)
        try:
            cpu.append((actual / 'cpu.max').read_text(encoding='ascii').strip())
        except OSError:
            pass
        if actual == base.resolve():
            break
        actual = actual.parent
    if not margenes:
        return {'estado': 'SIN_LIMITE_FINITO', 'margen_bytes': None,
                'limite_bytes': None, 'uso_bytes': None, 'cpu_max': cpu[0] if cpu else None}
    i = min(range(len(margenes)), key=margenes.__getitem__)
    return {'estado': 'VERIFICADO', 'margen_bytes': margenes[i],
            'limite_bytes': limites[i], 'uso_bytes': usos[i],
            'cpu_max': cpu[0] if cpu else None}


def evaluar_admision():
    memoria = psutil.virtual_memory()
    contenedor = _cgroup_v2()
    motivos = []
    if memoria.available < RAM_MINIMA:
        motivos.append('RAM_HOST_MENOR_2_GIB')
    if os.name != 'nt':
        if contenedor['estado'] not in ('VERIFICADO', 'SIN_LIMITE_FINITO'):
            motivos.append('LIMITE_CONTENEDOR_NO_VERIFICABLE')
        elif contenedor['margen_bytes'] is not None and contenedor['margen_bytes'] < RAM_MINIMA:
            motivos.append('RAM_CONTENEDOR_MENOR_2_GIB')
    datos, sha = cargar_entradas()
    if len(datos['operaciones']) != 2 or datos['limites_ensayo']['candidatos_maximos'] != 94:
        motivos.append('ESCENARIO_FUERA_DE_ALCANCE')
    return {'admitido': not motivos, 'motivos': motivos,
            'ram_host_disponible_bytes': memoria.available,
            'ram_host_total_bytes': memoria.total, 'contenedor': contenedor,
            'cpu_logicos': psutil.cpu_count(), 'entrada_sha256': sha,
            'perfil': 'ORIGINAL', 'trabajadores': 4, 'solver_segundos': 30,
            'cancelacion': 'COOPERATIVA_NO_FORZADA'}


def _tamano(raiz):
    total, archivos = 0, 0
    for actual, directorios, nombres in os.walk(raiz):
        if len(directorios) + len(nombres) > 256:
            raise EjecucionError('Demasiadas entradas en el ensayo')
        for nombre in nombres:
            p = Path(actual) / nombre
            if p.is_symlink() or p.is_junction():
                raise EjecucionError('Enlace no permitido en el ensayo')
            total += p.stat().st_size; archivos += 1
            if total > ALMACEN_MAX:
                raise EjecucionError('PRESUPUESTO_ALMACENAMIENTO')
    return total, archivos


def _leer_salida(ruta, pid):
    if not ruta.is_file() or ruta.stat().st_size > MIB:
        raise EjecucionError('Salida del proceso ausente o excesiva')
    try:
        datos = json.loads(ruta.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise EjecucionError('Salida del proceso inválida') from error
    if datos.get('pid') != pid:
        raise EjecucionError('PID de salida inconsistente')
    return datos


def _proceso(fase, raiz, token, *, run_id=None, deadline=None):
    admision = evaluar_admision()
    if not admision['admitido']:
        raise EjecucionError('Admisión rechazada antes de ' + fase + ': ' + ', '.join(admision['motivos']))
    control = raiz / 'control'
    salida, error = control / f'{fase}.json', control / f'{fase}.stderr'
    cancelar = control / 'CANCELAR'
    args = [sys.executable, '-I', '-B', '-X', 'utf8', str(WORKER),
            '--modo', fase, '--raiz', str(raiz), '--token', token]
    if run_id:
        args += ['--run-id', run_id]
    inicio = time.perf_counter()
    presupuesto = PRODUCTOR_S if fase == 'productor' else RECUPERADOR_S
    rss_max = RSS_PRODUCTOR_MAX if fase == 'productor' else RSS_RECUPERADOR_MAX
    motivo_cancelacion = None
    with salida.open('xb') as out, error.open('xb') as err:
        proceso = subprocess.Popen(args, stdout=out, stderr=err, cwd=raiz,
                                   env=dict(os.environ, SKYRISK_MODO_ACADEMICO='1'),
                                   shell=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        observado = psutil.Process(proceso.pid)
        pico = 0
        while proceso.poll() is None:
            try:
                pico = max(pico, observado.memory_info().rss)
                # Los 2 GiB se exigen justo antes de lanzar cada hijo. Durante
                # el trabajo se vigila el RSS propio y una reserva crítica del
                # host; no se vuelve imposible el ensayo por su consumo normal.
                if psutil.virtual_memory().available < 256 * MIB:
                    motivo_cancelacion = 'RESERVA_CRITICA_HOST'
                elif pico > rss_max:
                    motivo_cancelacion = 'RSS_SUPERADO'
                elif time.perf_counter() - inicio > presupuesto or (deadline and time.perf_counter() > deadline):
                    motivo_cancelacion = 'TIEMPO_SUPERADO'
                _tamano(raiz)
            except (OSError, psutil.Error, EjecucionError):
                motivo_cancelacion = 'ERROR_SUPERVISION'
            if motivo_cancelacion and not cancelar.exists():
                cancelar.touch(exist_ok=False)
            time.sleep(MUESTREO_S)
    datos = _leer_salida(salida, proceso.pid)
    datos['supervision'] = {'wall_s': time.perf_counter() - inicio,
                            'pico_rss_bytes': pico,
                            'cancelacion_solicitada': motivo_cancelacion}
    if proceso.returncode != 0 or not datos.get('correcto') or motivo_cancelacion:
        raise EjecucionError(datos.get('error') or motivo_cancelacion or 'Proceso académico fallido')
    return datos


def ejecutar_interactivo():
    """Ejecutar solo desde el botón explícito de Streamlit."""
    admision = evaluar_admision()
    if not admision['admitido']:
        raise EjecucionError('Optimización deshabilitada: ' + ', '.join(admision['motivos']))
    raiz = Path(tempfile.mkdtemp(prefix='SkyRiskLab-academico-')).resolve()
    control = raiz / 'control'; control.mkdir()
    token = uuid4().hex
    configuracion = {'token_sha256': hashlib.sha256(token.encode()).hexdigest(),
                     'entrada_sha256': admision['entrada_sha256'], 'admision': admision,
                     'perfil': {'nombre': 'ORIGINAL', 'num_search_workers': 4,
                                'max_time_in_seconds': 30, 'cp_model_presolve': False},
                     'limites': {'productor_s': PRODUCTOR_S, 'recuperador_s': RECUPERADOR_S,
                                 'ensayo_s': ENSAYO_S, 'almacen_bytes': ALMACEN_MAX}}
    (control / 'configuracion.json').write_text(json.dumps(configuracion, sort_keys=True), encoding='utf-8')
    inicio = time.perf_counter(); deadline = inicio + ENSAYO_S
    productor = _proceso('productor', raiz, token, deadline=deadline)
    recuperador = _proceso('recuperador', raiz, token, run_id=productor['run_id'], deadline=deadline)
    if productor['pid'] == recuperador['pid']:
        raise EjecucionError('La recuperación no ocurrió en un proceso independiente')
    if productor['hash_escenario'] != recuperador['hash_escenario']:
        raise EjecucionError('La recuperación no coincide con el resultado persistido')
    return {'correcto': True, 'historico': True, 'run_id': productor['run_id'],
            'raiz': str(raiz), 'resultado': recuperador['resultado'],
            'productor': productor['metricas'], 'recuperador': recuperador['metricas'],
            'supervision_productor': productor['supervision'],
            'supervision_recuperador': recuperador['supervision'],
            'wall_total_s': time.perf_counter() - inicio,
            'admision': admision, 'hash_escenario': productor['hash_escenario']}
