"""Lectura acotada de entradas y escenarios exclusivamente sintéticos.

No abre SQLite, no genera demanda, no resuelve ni escribe. Los hashes verifican
integridad, no certifican por sí mismos procedencia o cumplimiento operacional.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios, PersistenciaError


ROOT = Path(__file__).resolve().parents[1]
ENTRADAS = ROOT / 'demo' / 'entradas_paso1.json'
ESCENARIOS = ROOT / 'demo' / 'escenarios'
EVIDENCIA_COLAB = ROOT / 'docs' / 'evidencias' / 'evidencia_cpsat_publica.json'
RESERVAS = frozenset({'HK-020', 'HK-021', 'HK-022'})
REGULARES = frozenset(f'HK-{i:03}' for i in range(1, 51)) - RESERVAS
IDS = frozenset({'PASO1-SINT-N001', 'PASO1-SINT-N002'})
MAX_BYTES = 8 * 1024 ** 2
MAX_ARCHIVOS = 128
MAX_ENTRADAS = 256
MAX_RUNS = 20


class ConsultaError(ValueError):
    """Entrada no permitida o escenario no adecuado para el demostrador."""


def exigir(condicion, mensaje):
    if not condicion:
        raise ConsultaError(mensaje)


def sin_enlace(ruta):
    ruta = Path(ruta)
    exigir(not ruta.is_symlink() and not ruta.is_junction(), 'No se admiten enlaces en la demostración.')


def fecha(valor):
    resultado = datetime.fromisoformat(valor) if isinstance(valor, str) else valor
    exigir(isinstance(resultado, datetime) and resultado.tzinfo is not None and resultado.utcoffset() is not None,
           'Los horarios requieren zona horaria explícita.')
    return resultado


def validar_operaciones(operaciones):
    exigir(isinstance(operaciones, list) and len(operaciones) == 2, 'El caso académico contiene exactamente dos trayectos.')
    exigir({v.get('id_vuelo') for v in operaciones} == IDS, 'IDs ajenos al caso sintético aprobado.')
    for v in operaciones:
        exigir(v.get('tipo') == 'N' and v.get('operacion_origen') is None, 'Solo se admiten los dos trayectos nacionales sintéticos.')
        exigir(fecha(v['llegada_utc']) > fecha(v['salida_utc']), 'Horario de llegada inválido.')
    por_id = {v['id_vuelo']: v for v in operaciones}
    a, b = por_id['PASO1-SINT-N001'], por_id['PASO1-SINT-N002']
    exigir((a['origen'], a['destino'], b['origen'], b['destino']) == ('BOG', 'MDE', 'MDE', 'BOG'), 'Ruta sintética incorrecta.')
    exigir(fecha(b['salida_utc']) - fecha(a['llegada_utc']) == timedelta(minutes=60), 'El ejemplo debe conservar el tránsito de 60 minutos.')


def cargar_entradas(ruta=ENTRADAS):
    ruta = Path(ruta)
    sin_enlace(ruta)
    exigir(ruta.stat().st_size <= 64 * 1024, 'Entrada académica demasiado grande.')
    bruto = ruta.read_bytes()
    datos = json.loads(bruto)
    exigir(datos.get('tipo_datos') == 'SINTETICO', 'La demostración solo admite datos sintéticos.')
    exigir(datos.get('estado_ejecucion') == 'SIN_EJECUCION' and datos.get('resultados') is None,
           'Las entradas no pueden presentar resultados no ejecutados.')
    flota = datos['flota']
    exigir(len(flota['regulares']) == 47 and set(flota['regulares']) == REGULARES, 'Inventario regular incorrecto.')
    exigir(len(flota['reservas']) == 3 and set(flota['reservas']) == RESERVAS, 'Inventario de reserva incorrecto.')
    validar_operaciones(datos['operaciones'])
    return datos, hashlib.sha256(bruto).hexdigest()


def inventario_acotado(raiz):
    raiz = Path(raiz)
    sin_enlace(raiz)
    pendientes, inventario, total, entradas = [raiz], {}, 0, 0
    while pendientes:
        actual = pendientes.pop()
        for p in actual.iterdir():
            entradas += 1
            exigir(entradas <= MAX_ENTRADAS, 'El escenario supera el límite de entradas del visor.')
            sin_enlace(p)
            exigir(p.resolve().is_relative_to(raiz.resolve()), 'Archivo fuera del escenario.')
            if p.is_dir():
                pendientes.append(p)
            elif p.is_file():
                exigir(len(inventario) < MAX_ARCHIVOS, 'Demasiados archivos en el escenario.')
                total += p.stat().st_size
                exigir(total <= MAX_BYTES, 'El escenario supera los 8 MiB admitidos.')
                inventario[p.relative_to(raiz).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return inventario, total


def listar_escenarios(raiz=ESCENARIOS):
    raiz = Path(raiz)
    sin_enlace(raiz)
    if not raiz.exists():
        return []
    almacen, ids, revisadas = AlmacenEscenarios(raiz), [], 0
    for p in raiz.iterdir():
        revisadas += 1
        exigir(revisadas <= MAX_ENTRADAS, 'Demasiadas entradas en el almacén académico.')
        sin_enlace(p)
        if not p.is_dir():
            continue
        almacen._ruta(p.name)  # Valida el formato de run_id sin leer ni escribir.
        ids.append(p.name)
        exigir(len(ids) <= MAX_RUNS, 'El visor admite como máximo veinte ejecuciones pequeñas.')
    return sorted(ids, reverse=True)


def consultar_escenario(run_id, raiz=ESCENARIOS):
    raiz = Path(raiz)
    sin_enlace(raiz)
    almacen = AlmacenEscenarios(raiz)
    ruta = almacen._ruta(run_id)
    antes, cantidad_bytes = inventario_acotado(ruta)
    registro = almacen.consultar(run_id)
    inicio = registro['inicio']
    exigir(inicio.get('tipo_datos') == 'SINTETICO', 'Escenario rechazado: su procedencia no es SINTETICO.')
    exigir(inicio.get('es_programacion_operacional_aprobada') is False, 'El visor no admite programación operacional aprobada.')
    validar_operaciones(inicio['entradas']['operaciones'])
    parametros = inicio.get('parametros', {})
    exigir(parametros.get('perfil_solver') in ('ORIGINAL', 'EXPERIMENTAL_REPRODUCIBLE'), 'Perfil histórico no verificable.')
    cierre = registro['cierre']
    datos = cierre['datos'] if cierre else {}
    escenario = datos.get('escenario')
    fuente = ('CIERRE_VALIDADO' if cierre and registro['estado'] == 'COMPLETA'
              and datos.get('publicable') and escenario is not None else 'SIN_CIERRE_PUBLICABLE')
    if fuente != 'CIERRE_VALIDADO':
        escenario = None
        for evento in reversed(registro['eventos']):
            if evento['tipo'] == 'VENTANA_VALIDADA':
                escenario = evento['datos'].get('escenario')
                fuente = 'CHECKPOINT_VALIDADO'
                break
    if escenario is not None:
        exigir(set(escenario.get('flota', {})) == REGULARES, 'El escenario no conserva las 47 regulares.')
        for estado in escenario['flota'].values():
            exigir(estado.get('categoria') == 'REGULAR', 'Categoría ajena a la flota regular.')
        for grupo in ('confirmados', 'protegidos', 'propuestas'):
            vuelos = escenario.get(grupo, {})
            exigir(set(vuelos) <= IDS, 'El resultado contiene trayectos ajenos al caso académico.')
            for identificador, v in vuelos.items():
                exigir(v.get('id_vuelo') == identificador, 'ID interno distinto de su clave de asignación.')
                exigir(v.get('aeronave') in REGULARES, 'Asignación a una reserva o matrícula desconocida.')
    individuales = datos.get('resultados_individuales', {})
    exigir(isinstance(individuales, dict), 'Resultados individuales inválidos.')
    exigir(set(individuales) <= {'confirmados', 'protegidos', 'propuestas', 'pendientes', 'estado_inicial_incompleto'},
           'Grupo de resultados individuales desconocido.')
    por_grupo = {}
    for grupo, vuelos in individuales.items():
        exigir(isinstance(vuelos, list), 'Los resultados individuales requieren listas.')
        ids = [v.get('id_vuelo') for v in vuelos]
        exigir(len(ids) == len(set(ids)) and set(ids) <= IDS, 'IDs individuales duplicados o ajenos al caso.')
        por_grupo[grupo] = {v['id_vuelo']: v for v in vuelos}
        if grupo in ('confirmados', 'protegidos', 'propuestas'):
            for v in vuelos:
                exigir(v.get('aeronave') in REGULARES, 'Reserva en los resultados individuales.')
            if fuente == 'CIERRE_VALIDADO':
                exigir(por_grupo[grupo] == escenario.get(grupo, {}), 'Resultados individuales contradictorios con el escenario.')
    if fuente == 'CIERRE_VALIDADO':
        exigir(por_grupo.get('confirmados', {}) == escenario.get('confirmados', {}), 'Faltan asignaciones individuales confirmadas.')
        clasificados = [i for grupo in ('confirmados', 'pendientes', 'estado_inicial_incompleto')
                        for i in por_grupo.get(grupo, {})]
        exigir(set(clasificados) == IDS and len(clasificados) == len(IDS), 'Clasificación individual incompleta o duplicada.')
    despues, _ = inventario_acotado(ruta)
    exigir(antes == despues, 'El escenario cambió durante la consulta; vuelva a intentarlo.')
    return {'run_id': run_id, 'estado': registro['estado'], 'fuente': fuente,
            'publicable': fuente == 'CIERRE_VALIDADO', 'escenario': escenario,
            'parametros': parametros, 'resultados_individuales': individuales,
            'diagnosticos': datos.get('diagnosticos', []),
            'ventanas': datos.get('ventanas', []),
            'eventos': [{k: e[k] for k in ('secuencia', 'tipo', 'hash', 'creado_utc')} for e in registro['eventos']],
            'hashes': antes, 'bytes': cantidad_bytes}


def texto_json(valor):
    def convertir(v):
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, (set, frozenset)):
            return sorted(v)
        raise TypeError(type(v).__name__)
    return json.dumps(valor, ensure_ascii=False, indent=2, default=convertir, allow_nan=False)


def cargar_evidencia_colab(ruta=EVIDENCIA_COLAB):
    """Lee el resumen histórico revisado; no reconstruye la cadena de eventos."""
    ruta = Path(ruta)
    sin_enlace(ruta)
    exigir(ruta.stat().st_size <= 128 * 1024, 'Resumen Colab excesivo.')
    bruto = ruta.read_bytes()
    exigir(hashlib.sha256(bruto.replace(b'\r\n', b'\n')).hexdigest() ==
           '088c2a6099402224170b23b36e695d457968e387a38c336338214b508b05460c',
           'La evidencia Colab difiere de la copia revisada.')
    evidencia = json.loads(bruto)
    r = evidencia['resultado']; consulta = r['resultado']
    exigir(r['correcto'] and r['historico'] and r['run_id'] == consulta['run_id'],
           'Identidad histórica Colab inconsistente.')
    exigir(hashlib.sha256(texto_json(consulta['escenario']).encode('utf-8')).hexdigest()
           == r['hash_escenario'], 'Hash del escenario Colab inconsistente.')
    _, sha = cargar_entradas()
    exigir(r['admision']['entrada_sha256'] == sha, 'Las entradas no coinciden con Colab.')
    validar_operaciones(list(consulta['escenario']['confirmados'].values()))
    return evidencia
