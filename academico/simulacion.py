"""Red nacional sintética v2. Sin solver ni escrituras al importar el módulo."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta, timezone
import hashlib
import json
from pathlib import Path
import threading

from academico.escenarios import (ROOT, REGULARES, RESERVAS, exigir, fecha,
                                 cargar_entradas, sin_enlace, inventario_acotado)
from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios

ENTRADAS = ROOT / 'demo' / 'entradas_ampliadas.json'
AEROPUERTOS = frozenset(('BOG', 'MDE', 'CLO', 'CTG'))
TRANSITO = timedelta(minutes=60)


def huella(datos):
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def cargar_simulacion(ruta=ENTRADAS):
    ruta = Path(ruta); sin_enlace(ruta)
    exigir(ruta.stat().st_size <= 64 * 1024, 'Entrada ampliada excesiva.')
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    original, _ = cargar_entradas()
    # Solo inventario: la ubicación global del caso original NO habilita aeronaves.
    datos['inventario'] = {k: original['flota'][k] for k in ('regulares', 'reservas')}
    validar_entrada(datos)
    return datos


def validar_entrada(datos):
    exigir(datos.get('version') == 2 and datos.get('tipo_datos') == 'SINTETICO', 'Solo escenario sintético v2.')
    exigir(isinstance(datos.get('id_escenario'), str) and bool(datos['id_escenario']), 'Falta identidad del caso.')
    dia = date.fromisoformat(datos['jornada'])
    exigir(set(datos['aeropuertos']) == AEROPUERTOS and len(datos['aeropuertos']) == 4, 'Cuatro aeropuertos nacionales.')
    inventario = datos['inventario']
    exigir(len(inventario['regulares']) == 47 and set(inventario['regulares']) == REGULARES,
           'Debe conservarse el inventario de 47 regulares.')
    exigir(len(inventario['reservas']) == 3 and set(inventario['reservas']) == RESERVAS, 'Tres reservas excluidas.')
    activas = datos['activas']
    exigir(isinstance(activas, dict) and 1 <= len(activas) <= 6 and set(activas) <= REGULARES, 'Entre una y seis regulares activas.')
    for estado in activas.values():
        exigir(estado['ubicacion'] in AEROPUERTOS, 'Ubicación inicial desconocida.')
        instante = fecha(estado['disponible_desde']).astimezone(timezone.utc)
        exigir(instante.date() == dia, 'Disponibilidad fuera de la jornada UTC.')
    vuelos = datos['operaciones']
    exigir(isinstance(vuelos, list) and 1 <= len(vuelos) <= 12, 'Entre uno y doce trayectos.')
    exigir(all(isinstance(v.get('id_vuelo'), str) and v['id_vuelo'] for v in vuelos), 'ID requerido.')
    exigir(len({v['id_vuelo'] for v in vuelos}) == len(vuelos), 'IDs duplicados.')
    for v in vuelos:
        exigir(v['origen'] in AEROPUERTOS and v['destino'] in AEROPUERTOS and v['origen'] != v['destino'], 'Ruta inválida.')
        salida, llegada = fecha(v['salida_utc']), fecha(v['llegada_utc'])
        exigir(salida < llegada and salida.astimezone(timezone.utc).date() == dia
               and llegada.astimezone(timezone.utc).date() == dia, 'Horario fuera de jornada o duración inválida.')
    return datos


def conectar(a, b):
    return (a['destino'] == b['origen']
            and fecha(b['salida_utc']) - fecha(a['llegada_utc']) >= TRANSITO)


def validar_plan(datos, plan, bloqueadas=()):
    """Verificador independiente del modelo: recorre cada rotación física."""
    validar_entrada(datos)
    exigir(set(bloqueadas) <= set(datos['activas']), 'Contingencia sobre aeronave no activa.')
    entrada = {v['id_vuelo']: v for v in datos['operaciones']}
    asignados, pendientes = plan['asignaciones'], plan['pendientes']
    exigir(isinstance(asignados, dict) and isinstance(pendientes, list), 'Resultado inválido.')
    exigir(len(set(pendientes)) == len(pendientes) and not set(asignados) & set(pendientes)
           and set(asignados) | set(pendientes) == set(entrada), 'Clasificación incompleta o duplicada.')
    rotaciones = {m: [] for m in datos['activas']}
    for identificador, v in asignados.items():
        m = v['aeronave']
        exigir(m in rotaciones and m not in bloqueadas, 'Aeronave no disponible.')
        exigir({k: valor for k, valor in v.items() if k != 'aeronave'} == entrada[identificador], 'Vuelo modificado respecto de las entradas.')
        rotaciones[m].append(v)
    for m, vuelos in rotaciones.items():
        vuelos.sort(key=lambda v: fecha(v['salida_utc']))
        if vuelos:
            estado = datos['activas'][m]
            exigir(vuelos[0]['origen'] == estado['ubicacion']
                   and fecha(vuelos[0]['salida_utc']) >= fecha(estado['disponible_desde']), 'Primer vuelo inalcanzable.')
            exigir(all(conectar(a, b) for a, b in zip(vuelos, vuelos[1:])), 'Continuidad, solapamiento o tránsito inválidos.')
    return True


def resolver(datos, bloqueadas=(), referencia=None, cancelar=None):
    validar_entrada(datos)
    exigir(set(bloqueadas) <= set(datos['activas']), 'Aeronave afectada desconocida.')
    # También se exige admisión cuando esta API se utiliza fuera del supervisor.
    from academico.ejecucion import evaluar_admision, EjecucionError
    admision = evaluar_admision()
    if not admision['admitido']:
        raise EjecucionError('Admisión CP-SAT: ' + ', '.join(admision['motivos']))
    from ortools.sat.python import cp_model
    if cancelar is not None and cancelar.exists():
        raise EjecucionError('ENSAYO_CANCELADO_COOPERATIVAMENTE')
    vuelos = sorted(datos['operaciones'], key=lambda v: (fecha(v['salida_utc']), v['id_vuelo']))
    matriculas = sorted(datos['activas'])
    modelo = cp_model.CpModel()
    x = {(m, i): modelo.NewBoolVar(f'x_{m}_{i}') for m in matriculas for i in range(len(vuelos))}
    for i in range(len(vuelos)):
        modelo.Add(sum(x[m, i] for m in matriculas) <= 1)
    for m in matriculas:
        inicio, finales, arcos = {}, {}, {}
        estado = datos['activas'][m]
        for i, v in enumerate(vuelos):
            finales[i] = modelo.NewBoolVar(f'fin_{m}_{i}')
            if v['origen'] == estado['ubicacion'] and fecha(v['salida_utc']) >= fecha(estado['disponible_desde']):
                inicio[i] = modelo.NewBoolVar(f'inicio_{m}_{i}')
            for j in range(i + 1, len(vuelos)):
                if conectar(v, vuelos[j]):
                    arcos[i, j] = modelo.NewBoolVar(f'arco_{m}_{i}_{j}')
            if m in bloqueadas:
                modelo.Add(x[m, i] == 0)
        modelo.Add(sum(inicio.values()) <= 1)
        modelo.Add(sum(inicio.values()) == sum(finales.values()))
        for i in range(len(vuelos)):
            modelo.Add(x[m, i] == inicio.get(i, 0) + sum(a for (u, v), a in arcos.items() if v == i))
            modelo.Add(x[m, i] == finales[i] + sum(a for (u, v), a in arcos.items() if u == i))
    # Objetivo lexicográfico acotado: cobertura > estabilidad > preferencia de matrícula.
    n, k = len(vuelos), len(matriculas)
    peso_estable = n * k + 1
    peso_cobertura = n * peso_estable + n * k + 1
    conservar = sum(x[m, i] for (m, i) in x if referencia and
                    referencia['asignaciones'].get(vuelos[i]['id_vuelo'], {}).get('aeronave') == m)
    modelo.Maximize(peso_cobertura * sum(x.values()) + peso_estable * conservar
                    - sum((matriculas.index(m) + 1) * var for (m, i), var in x.items()))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 4
    solver.parameters.max_time_in_seconds = 15  # Dos resoluciones dentro de los 30 s configurados.
    solver.parameters.cp_model_presolve = False
    fin = threading.Event()
    def vigilar():
        while not fin.wait(0.1):
            if cancelar is not None and cancelar.exists():
                solver.stop_search()
                return
    hilo = threading.Thread(target=vigilar, daemon=True); hilo.start()
    try:
        estado_solver = solver.Solve(modelo)
    finally:
        fin.set(); hilo.join()
    if cancelar is not None and cancelar.exists():
        raise EjecucionError('ENSAYO_CANCELADO_COOPERATIVAMENTE')
    # UNKNOWN no se transforma en una supuesta solución vacía.
    if estado_solver not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise EjecucionError('Sin solución verificable: ' + solver.StatusName(estado_solver))
    asignaciones = {v['id_vuelo']: dict(v, aeronave=m) for i, v in enumerate(vuelos)
                    for m in matriculas if solver.Value(x[m, i])}
    plan = {'asignaciones': asignaciones,
            'pendientes': sorted({v['id_vuelo'] for v in vuelos} - set(asignaciones)),
            'diagnostico': {'estado_solver': solver.StatusName(estado_solver),
                'atendidos': len(asignaciones), 'total': n,
                'objetivo_ponderado': solver.ObjectiveValue(), 'cota_ponderada': solver.BestObjectiveBound(),
                'solver_s': solver.WallTime(), 'variables': len(modelo.Proto().variables),
                'trabajadores': 4, 'limite_solver_s': 15}}
    validar_plan(datos, plan, bloqueadas)
    return plan


def comparar(datos, original, recuperada, afectada):
    validar_plan(datos, original)
    validar_plan(datos, recuperada, [afectada])
    filas = []
    for v in datos['operaciones']:
        i = v['id_vuelo']
        antes = original['asignaciones'].get(i, {}).get('aeronave')
        despues = recuperada['asignaciones'].get(i, {}).get('aeronave')
        filas.append({'id_vuelo': i, 'afectado_directo': antes == afectada,
                      'original': antes, 'recuperada': despues,
                      'sustituta': despues if antes == afectada and despues else None,
                      'cambio': antes != despues,
                      'estado': 'ATENDIDO' if despues else 'PENDIENTE'})
    return filas


def producir_simulacion(raiz, solicitud):
    datos = deepcopy(solicitud['entrada']); validar_entrada(datos)
    afectada = solicitud['afectada']
    exigir(afectada in datos['activas'], 'Aeronave afectada no activa.')
    cancelar = raiz / 'control' / 'CANCELAR'
    original = resolver(datos, cancelar=cancelar)
    recuperada = resolver(datos, [afectada], referencia=original, cancelar=cancelar)
    resultado = {'version': 2, 'entrada': datos, 'entrada_sha256': huella(datos),
                 'afectada': afectada, 'original': original, 'recuperada': recuperada,
                 'comparacion': comparar(datos, original, recuperada, afectada)}
    registro = AlmacenEscenarios(raiz / 'ejecuciones').iniciar(
        entradas={'simulacion': datos}, parametros={'perfil_solver': 'AMPLIADO_V2', 'afectada': afectada},
        procedencia={'tipo_datos': 'SINTETICO', 'declaracion': 'DEMOSTRADOR_ACADEMICO'},
        codigo={'academico/simulacion.py': Path(__file__).read_bytes()})
    registro.evento('PLANES_VALIDADOS', {'entrada_sha256': huella(datos)})
    registro.cerrar('COMPLETA', {'publicable': True, 'simulacion': resultado})
    recuperado = consultar_simulacion(registro.run_id, raiz / 'ejecuciones')
    return {'run_id': registro.run_id, 'hash_escenario': huella(recuperado)}


def consultar_simulacion(run_id, raiz):
    almacen = AlmacenEscenarios(raiz)
    ruta = almacen._ruta(run_id)
    antes, _ = inventario_acotado(ruta)
    registro = almacen.consultar(run_id)
    exigir(registro['inicio']['tipo_datos'] == 'SINTETICO'
           and registro['inicio']['es_programacion_operacional_aprobada'] is False, 'Procedencia no académica.')
    cierre = registro['cierre']
    exigir(registro['estado'] == 'COMPLETA' and cierre and cierre['datos'].get('publicable'), 'Falta cierre completo.')
    resultado = cierre['datos']['simulacion']
    exigir(resultado.get('version') == 2, 'Versión de resultado desconocida.')
    datos = resultado['entrada']; validar_entrada(datos)
    exigir(registro['inicio']['entradas']['simulacion'] == datos, 'Entradas archivadas divergentes.')
    parametros = registro['inicio']['parametros']
    exigir(parametros.get('perfil_solver') == 'AMPLIADO_V2'
           and parametros.get('afectada') == resultado['afectada'], 'Contingencia archivada divergente.')
    exigir(resultado['entrada_sha256'] == huella(datos), 'Hash de entrada inconsistente.')
    comparacion = comparar(datos, resultado['original'], resultado['recuperada'], resultado['afectada'])
    exigir(comparacion == resultado['comparacion'], 'Comparación inconsistente.')
    despues, _ = inventario_acotado(ruta)
    exigir(antes == despues, 'El escenario cambió durante la recuperación.')
    return resultado
