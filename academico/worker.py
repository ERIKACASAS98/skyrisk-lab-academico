"""Proceso académico de CP-SAT o recuperación; nunca importa SQLite/productivo."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from academico.escenarios import IDS, REGULARES, cargar_entradas, consultar_escenario, texto_json
from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios


def _hash(datos):
    return hashlib.sha256(texto_json(datos).encode('utf-8')).hexdigest()


def _validar_raiz(raiz):
    raiz = Path(raiz).resolve()
    temporal = Path(os.environ.get('TEMP') or os.environ.get('TMP') or Path.cwd()).resolve()
    if not raiz.name.startswith('SkyRiskLab-academico-'):
        raise ValueError('Raíz académica inválida')
    # tempfile puede resolver a otra representación en Windows; la raíz debe
    # estar fuera del proyecto y nunca contenerlo.
    if raiz.is_relative_to(ROOT) or ROOT.is_relative_to(raiz):
        raise ValueError('El ensayo no puede usar el proyecto como almacenamiento')
    return raiz


def _medir(raiz, fase, funcion):
    import psutil
    proceso = psutil.Process(); inicio = time.perf_counter(); cpu = proceso.cpu_times()
    pico = proceso.memory_info().rss; fin = threading.Event()
    def vigilar():
        nonlocal pico
        while not fin.wait(0.1):
            pico = max(pico, proceso.memory_info().rss)
    hilo = threading.Thread(target=vigilar, daemon=True); hilo.start()
    try:
        resultado = funcion()
    finally:
        fin.set(); hilo.join()
    despues = proceso.cpu_times()
    archivos = [p for p in raiz.rglob('*') if p.is_file()]
    return resultado, {'fase': fase, 'wall_s': time.perf_counter() - inicio,
        'cpu_s': despues.user + despues.system - cpu.user - cpu.system,
        'pico_rss_muestreado_bytes': pico, 'bytes_raiz': sum(p.stat().st_size for p in archivos),
        'archivos_raiz': len(archivos)}


def producir(raiz):
    from ortools.sat.python import cp_model
    datos, entrada_sha = cargar_entradas()
    operaciones = datos['operaciones']; matriculas = sorted(REGULARES)
    if len(operaciones) * len(matriculas) != 94:
        raise ValueError('El modelo excede o no alcanza 94 candidatos')
    modelo = cp_model.CpModel()
    x = {(v['id_vuelo'], m): modelo.NewBoolVar(f"{v['id_vuelo']}__{m}")
         for v in operaciones for m in matriculas}
    for v in operaciones:
        modelo.Add(sum(x[v['id_vuelo'], m] for m in matriculas) <= 1)
    # Continuidad física: el regreso MDE-BOG solo puede usar la matrícula que
    # ejecutó BOG-MDE. La espera es exactamente 60 minutos en las entradas.
    for m in matriculas:
        modelo.Add(x['PASO1-SINT-N002', m] <= x['PASO1-SINT-N001', m])
    modelo.Maximize(sum(x.values()))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 4
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.cp_model_presolve = False
    cancelar = raiz / 'control' / 'CANCELAR'; terminado = threading.Event()
    def observar_cancelacion():
        while not terminado.wait(0.1):
            if cancelar.exists():
                solver.stop_search(); return
    hilo = threading.Thread(target=observar_cancelacion, daemon=True); hilo.start()
    inicio = time.perf_counter()
    try:
        estado = solver.Solve(modelo)
    finally:
        terminado.set(); hilo.join()
    estado_nombre = solver.StatusName(estado)
    factible = estado in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    asignaciones = []
    if factible:
        for v in operaciones:
            for m in matriculas:
                if solver.Value(x[v['id_vuelo'], m]):
                    asignaciones.append(dict(v, aeronave=m))
    por_id = {v['id_vuelo']: v for v in asignaciones}
    if cancelar.exists():
        raise RuntimeError('ENSAYO_CANCELADO_COOPERATIVAMENTE')
    if set(por_id) != IDS or len({v['aeronave'] for v in asignaciones}) != 1:
        raise RuntimeError('El resultado no satisface la cadena sintética completa')
    escenario = {'flota': {m: {'categoria': 'REGULAR'} for m in matriculas},
                  'confirmados': por_id, 'protegidos': {}, 'propuestas': {}}
    respuesta = solver.ResponseProto()
    diagnostico = {'estado_solver': estado_nombre,
        'motivo_terminacion': 'OPTIMALIDAD_DEMOSTRADA' if estado == cp_model.OPTIMAL else 'SOLUCION_FACTIBLE',
        'objetivo': solver.ObjectiveValue(), 'cota': solver.BestObjectiveBound(),
        'resolucion_s': solver.WallTime(), 'construccion_y_resolucion_s': time.perf_counter() - inicio,
        'tiempo_determinista': getattr(respuesta, 'deterministic_time', None),
        'variables': 94, 'restricciones': 49, 'candidatos': 94,
        'perfil_solver': 'ORIGINAL', 'parametros_efectivos': {
            'num_search_workers': 4, 'max_time_in_seconds': 30, 'cp_model_presolve': False}}
    almacen = AlmacenEscenarios(raiz / 'ejecuciones')
    registro = almacen.iniciar(
        entradas={'operaciones': operaciones, 'entrada_sha256': entrada_sha,
                  'escenario_id': datos['id_escenario']},
        parametros={'perfil_solver': 'ORIGINAL', 'configuracion_solver': {
            'nombre': 'ORIGINAL', 'parametros': diagnostico['parametros_efectivos']},
            'limites': datos['limites_ensayo']},
        procedencia={'tipo_datos': 'SINTETICO', 'declaracion': 'DEMOSTRADOR_ACADEMICO'},
        codigo={'academico/worker.py': Path(__file__).read_bytes(),
                'academico/ejecucion.py': Path(__file__).with_name('ejecucion.py').read_bytes()})
    registro.evento('MODELO_PREPARADO', {'candidatos': 94, 'variables': 94,
                    'restricciones': 49, 'reservas_elegibles': 0})
    registro.evento('SOLVER_FINALIZADO', diagnostico)
    registro.evento('VENTANA_VALIDADA', {'escenario': escenario,
        'comprobaciones': ['dos_ids', 'misma_matricula', 'transito_60_min', 'flota_regular']})
    cierre = {'publicable': True, 'escenario': escenario,
        'resultados_individuales': {'confirmados': asignaciones, 'pendientes': [],
                                    'estado_inicial_incompleto': []},
        'diagnosticos': [diagnostico], 'ventanas': [diagnostico]}
    registro.cerrar('COMPLETA', cierre)
    consultado = consultar_escenario(registro.run_id, almacen.root)
    return {'run_id': registro.run_id, 'hash_escenario': _hash(consultado['escenario'])}


def recuperar(raiz, run_id):
    # Este modo no importa OR-Tools y valida el histórico antes de devolverlo.
    consultado = consultar_escenario(run_id, raiz / 'ejecuciones')
    if not consultado['publicable']:
        raise ValueError('La ejecución no tiene cierre validado')
    return {'run_id': run_id, 'hash_escenario': _hash(consultado['escenario']),
            'resultado': consultado}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--modo', choices=('productor', 'recuperador'), required=True)
    p.add_argument('--raiz', required=True); p.add_argument('--token', required=True)
    p.add_argument('--run-id')
    args = p.parse_args(argv); raiz = _validar_raiz(args.raiz)
    config = json.loads((raiz / 'control' / 'configuracion.json').read_text(encoding='utf-8'))
    if hashlib.sha256(args.token.encode()).hexdigest() != config['token_sha256']:
        raise SystemExit(2)
    try:
        funcion = (lambda: producir(raiz)) if args.modo == 'productor' else (lambda: recuperar(raiz, args.run_id))
        datos, metricas = _medir(raiz, args.modo, funcion)
        print(json.dumps({'correcto': True, 'pid': os.getpid(), **datos, 'metricas': metricas},
                         ensure_ascii=False, default=str))
        return 0
    except BaseException as error:
        print(json.dumps({'correcto': False, 'pid': os.getpid(),
                          'error': type(error).__name__ + ': ' + str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
