"""Almacén inmutable de ejecuciones comerciales, independiente de SQLite.

Cada evento se publica como directorio completo en el mismo volumen. Los
lectores nunca ejecutan código guardado ni invocan el optimizador. Un cierre
ausente significa SIN_CIERRE, no prueba que el escritor haya muerto.
"""
from base64 import b64decode, b64encode
from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import threading
from uuid import uuid4


VERSION_FORMATO = 1
_RUN_ID = re.compile(r'SRL-COM-\d{8}T\d{12}Z-[0-9a-f]{32}')
_EVENTO = re.compile(r'\d{8}')
_ETIQUETA = '__skyrisk_tipo__'


class PersistenciaError(RuntimeError):
    """No se puede asegurar que el nuevo resultado esté guardado íntegramente."""

    def __init__(self, mensaje, run_id=None):
        super().__init__(mensaje)
        self.run_id = run_id


class IntegridadError(PersistenciaError):
    """El registro no coincide con su manifiesto o su secuencia de eventos."""


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _nuevo_run_id():
    return 'SRL-COM-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid4().hex


def _canonico(datos):
    return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _hash(datos):
    return hashlib.sha256(datos).hexdigest()


def _codificar(valor):
    if valor is None or isinstance(valor, (str, bool, int)):
        return valor
    if isinstance(valor, float):
        if not math.isfinite(valor):
            raise ValueError('No se permiten números no finitos')
        return valor
    if isinstance(valor, datetime):
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError('La trazabilidad requiere datetime con zona horaria')
        return {_ETIQUETA: 'datetime', 'valor': valor.isoformat()}
    if isinstance(valor, date):
        return {_ETIQUETA: 'date', 'valor': valor.isoformat()}
    if isinstance(valor, bytes):
        return {_ETIQUETA: 'bytes', 'valor': b64encode(valor).decode('ascii')}
    if isinstance(valor, (set, frozenset, tuple)):
        items = [_codificar(v) for v in valor]
        if isinstance(valor, (set, frozenset)):
            items.sort(key=lambda v: _canonico(v))
        return {_ETIQUETA: type(valor).__name__, 'valor': items}
    if isinstance(valor, list):
        return [_codificar(v) for v in valor]
    if isinstance(valor, dict):
        if not all(isinstance(k, str) for k in valor):
            raise ValueError('Las claves de trazabilidad deben ser texto')
        if _ETIQUETA in valor:
            return {_ETIQUETA: 'dict', 'valor': [[k, _codificar(v)] for k, v in sorted(valor.items())]}
        return {k: _codificar(v) for k, v in valor.items()}
    raise ValueError(f'Tipo no serializable: {type(valor).__name__}')


def _decodificar(valor):
    if isinstance(valor, list):
        return [_decodificar(v) for v in valor]
    if not isinstance(valor, dict):
        return valor
    if _ETIQUETA not in valor:
        return {k: _decodificar(v) for k, v in valor.items()}
    if set(valor) != {_ETIQUETA, 'valor'}:
        raise IntegridadError('Marcador de tipo inválido')
    tipo, dato = valor[_ETIQUETA], valor['valor']
    if tipo == 'datetime':
        resultado = datetime.fromisoformat(dato)
        if resultado.tzinfo is None or resultado.utcoffset() is None:
            raise IntegridadError('Fecha guardada sin zona horaria')
        return resultado
    if tipo == 'date':
        return date.fromisoformat(dato)
    if tipo == 'bytes':
        return b64decode(dato, validate=True)
    if tipo in ('set', 'frozenset', 'tuple'):
        constructor = {'set': set, 'frozenset': frozenset, 'tuple': tuple}[tipo]
        return constructor(_decodificar(v) for v in dato)
    if tipo == 'dict':
        return {k: _decodificar(v) for k, v in dato}
    raise IntegridadError(f'Tipo guardado desconocido: {tipo}')


def _leer_json(datos):
    def sin_duplicados(pares):
        resultado = {}
        for k, v in pares:
            if k in resultado:
                raise IntegridadError(f'Clave JSON duplicada: {k}')
            resultado[k] = v
        return resultado

    def constante_invalida(_):
        raise IntegridadError('Constante JSON no finita')

    return json.loads(datos, object_pairs_hook=sin_duplicados, parse_constant=constante_invalida)


def _escribir_archivo(ruta, contenido):
    with ruta.open('xb') as archivo:
        if archivo.write(contenido) != len(contenido):
            raise OSError('Escritura incompleta del artefacto')
        archivo.flush()
        os.fsync(archivo.fileno())


def _sin_enlace(ruta):
    if ruta.is_symlink() or (hasattr(ruta, 'is_junction') and ruta.is_junction()):
        raise IntegridadError(f'No se permiten enlaces dentro del almacén: {ruta.name}')


def _publicar(run, destino, contenido, metadatos):
    """No borra staging tras fallos: puede conservar evidencia incompleta."""
    escenario_staging = run / '.staging'
    _sin_enlace(escenario_staging)
    temporal = escenario_staging / uuid4().hex
    temporal.mkdir()
    datos = _canonico(_codificar(contenido))
    manifiesto = dict(metadatos, formato=VERSION_FORMATO,
                      artefactos=[{'archivo': 'datos.json', 'sha256': _hash(datos), 'bytes': len(datos)}])
    envoltura = {'contenido': manifiesto, 'sha256': _hash(_canonico(manifiesto))}
    _escribir_archivo(temporal / 'datos.json', datos)
    manifiesto_bytes = _canonico(envoltura)
    _escribir_archivo(temporal / 'manifest.json', manifiesto_bytes)
    if ((temporal / 'datos.json').read_bytes() != datos
            or (temporal / 'manifest.json').read_bytes() != manifiesto_bytes):
        raise PersistenciaError('La verificación previa a publicación falló')
    if destino.exists():
        raise PersistenciaError(f'El histórico ya existe: {destino.name}')
    # Windows rechaza destinos existentes. Los destinos son directorios completos
    # no vacíos; tampoco se pueden sustituir mediante rename en POSIX.
    temporal.rename(destino)
    return envoltura['sha256']


def _leer_publicado(ruta):
    _sin_enlace(ruta)
    for nombre in ('datos.json', 'manifest.json'):
        _sin_enlace(ruta / nombre)
    envoltura = _leer_json((ruta / 'manifest.json').read_bytes())
    manifiesto = envoltura['contenido']
    if envoltura['sha256'] != _hash(_canonico(manifiesto)):
        raise IntegridadError(f'Manifiesto alterado: {ruta.name}')
    if manifiesto.get('formato') != VERSION_FORMATO:
        raise IntegridadError('Versión de formato no soportada')
    artefactos = manifiesto.get('artefactos', [])
    if len(artefactos) != 1 or artefactos[0].get('archivo') != 'datos.json':
        raise IntegridadError('Inventario de artefactos inválido')
    datos = (ruta / 'datos.json').read_bytes()
    esperado = artefactos[0]
    if esperado['sha256'] != _hash(datos) or esperado['bytes'] != len(datos):
        raise IntegridadError(f'Contenido alterado o incompleto: {ruta.name}')
    return manifiesto, _decodificar(_leer_json(datos)), envoltura['sha256']


def _clasificar(procedencia):
    permitidos = {'SINTETICO', 'OPERACIONAL', 'MIXTO', 'NO_DECLARADO'}
    if isinstance(procedencia, dict):
        declarado = procedencia.get('tipo_datos', 'NO_DECLARADO')
        return declarado if declarado in permitidos else 'NO_DECLARADO'
    texto = str(procedencia).upper()
    if 'SINTETIC' in texto or texto == 'SYN':
        return 'SINTETICO'
    return texto if texto in permitidos else 'NO_DECLARADO'


class RegistroEjecucion:
    """Un único escritor, creado exclusivamente por iniciar; no reabre históricos."""

    def __init__(self, ruta, run_id):
        self.ruta, self.run_id = ruta, run_id
        self._secuencia, self._anterior, self._cerrado = 0, None, False
        self._eventos = []
        self._lock = threading.RLock()

    def evento(self, tipo, datos):
        with self._lock:
            if self._cerrado:
                raise PersistenciaError('La ejecución ya está cerrada e inmutable')
            if not isinstance(tipo, str) or not tipo:
                raise PersistenciaError('Tipo de evento obligatorio')
            secuencia = self._secuencia + 1
            metadatos = {'run_id': self.run_id, 'secuencia': secuencia, 'tipo': tipo,
                         'creado_utc': _ahora(), 'anterior': self._anterior}
            try:
                _sin_enlace(self.ruta)
                _sin_enlace(self.ruta / 'eventos')
                sha = _publicar(self.ruta, self.ruta / 'eventos' / f'{secuencia:08d}', datos, metadatos)
            except (OSError, ValueError, TypeError, PersistenciaError) as error:
                raise PersistenciaError(f'No se pudo persistir {tipo}: {error}', self.run_id) from error
            self._secuencia, self._anterior = secuencia, sha
            acuse = {'run_id': self.run_id, 'secuencia': secuencia, 'tipo': tipo, 'hash': sha}
            self._eventos.append(acuse)
            return dict(acuse)

    def cerrar(self, estado, datos):
        with self._lock:
            if self._cerrado:
                raise PersistenciaError('La ejecución ya tiene cierre')
            if estado not in {'COMPLETA', 'FALLIDA'}:
                raise PersistenciaError('Estado terminal inválido')
            contenido = {'estado': estado, 'datos': datos, 'eventos': list(self._eventos)}
            try:
                sha = _publicar(self.ruta, self.ruta / 'cierre', contenido,
                                {'run_id': self.run_id, 'tipo': 'CIERRE', 'secuencia': self._secuencia,
                                 'creado_utc': _ahora(), 'anterior': self._anterior})
            except (OSError, ValueError, TypeError, PersistenciaError) as error:
                raise PersistenciaError(f'No se pudo cerrar {self.run_id}: {error}', self.run_id) from error
            self._cerrado = True
            return {'run_id': self.run_id, 'estado': estado, 'hash': sha}


class AlmacenEscenarios:
    """Crear esta instancia no escribe; la ruta es inyectable para pruebas."""

    def __init__(self, root=None):
        if root is None:
            root = os.environ.get('SKYRISK_RUNS_DIR')
        if root is None:
            local = os.environ.get('LOCALAPPDATA')
            root = (Path(local) if local else Path.home() / '.local' / 'share') / 'SkyRiskLab' / 'ejecuciones_comerciales'
        self.root = Path(root).expanduser().resolve()

    def _ruta(self, run_id):
        if not isinstance(run_id, str) or _RUN_ID.fullmatch(run_id) is None:
            raise IntegridadError('run_id inválido')
        ruta = self.root / run_id
        _sin_enlace(ruta)
        if ruta.resolve().parent != self.root:
            raise IntegridadError('La ejecución sale del almacén')
        return ruta

    def iniciar(self, entradas, parametros, procedencia, parent_run_id=None, codigo=None):
        if parent_run_id is not None:
            self._ruta(parent_run_id)
        run_id = _nuevo_run_id()
        ruta = self._ruta(run_id)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            ruta.mkdir(exist_ok=False)
            (ruta / 'eventos').mkdir()
            (ruta / '.staging').mkdir()
            fuentes = {}
            for nombre, contenido in (codigo or {}).items():
                if not isinstance(contenido, (str, bytes)):
                    raise ValueError('La copia del código debe ser texto o bytes')
                bruto = contenido.encode('utf-8') if isinstance(contenido, str) else contenido
                fuentes[nombre] = {'contenido': contenido, 'sha256': _hash(bruto)}
            registro = RegistroEjecucion(ruta, run_id)
            registro.evento('EJECUCION_INICIADA', {
                'entradas': entradas, 'parametros': parametros, 'procedencia': procedencia,
                'tipo_datos': _clasificar(procedencia), 'parent_run_id': parent_run_id,
                'codigo': fuentes, 'es_programacion_operacional_aprobada': False,
                'escritor': {'pid': os.getpid(), 'inicio_utc': _ahora()},
            })
            return registro
        except (OSError, ValueError, TypeError, PersistenciaError) as error:
            raise PersistenciaError(f'No se pudo iniciar {run_id}: {error}', run_id) from error

    def consultar(self, run_id):
        ruta = self._ruta(run_id)
        try:
            # Si el cierre aparece durante esta lectura, el prefijo sigue siendo
            # una vista válida SIN_CIERRE. No mezclarlo con un cierre más nuevo.
            cierre_visible = (ruta / 'cierre').exists()
            _sin_enlace(ruta / 'eventos')
            directorios = sorted((ruta / 'eventos').iterdir(), key=lambda p: p.name)
            eventos, anterior = [], None
            for secuencia, directorio in enumerate(directorios, 1):
                if not directorio.is_dir() or _EVENTO.fullmatch(directorio.name) is None or directorio.name != f'{secuencia:08d}':
                    raise IntegridadError('Secuencia de eventos inválida')
                manifiesto, datos, sha = _leer_publicado(directorio)
                if (manifiesto.get('run_id') != run_id or manifiesto.get('secuencia') != secuencia
                        or manifiesto.get('anterior') != anterior):
                    raise IntegridadError('Cadena de eventos inválida')
                eventos.append({'run_id': run_id, 'secuencia': secuencia, 'tipo': manifiesto['tipo'],
                                'datos': datos, 'hash': sha, 'creado_utc': manifiesto['creado_utc']})
                anterior = sha
            if not eventos or eventos[0]['tipo'] != 'EJECUCION_INICIADA':
                raise IntegridadError('No existe un inicio íntegro')
            cierre = None
            if cierre_visible:
                manifiesto, cierre, sha = _leer_publicado(ruta / 'cierre')
                referencias = [{k: e[k] for k in ('run_id', 'secuencia', 'tipo', 'hash')} for e in eventos]
                if (manifiesto.get('run_id') != run_id or manifiesto.get('tipo') != 'CIERRE'
                        or manifiesto.get('anterior') != anterior
                        or manifiesto.get('secuencia') != len(eventos) or cierre['eventos'] != referencias
                        or cierre['estado'] not in {'COMPLETA', 'FALLIDA'}):
                    raise IntegridadError('El cierre no corresponde a sus eventos')
                cierre = dict(cierre, hash=sha)
            return {'run_id': run_id, 'estado': cierre['estado'] if cierre else 'SIN_CIERRE',
                    'eventos': eventos, 'inicio': eventos[0]['datos'], 'cierre': cierre,
                    'staging_presente': any((ruta / '.staging').iterdir())}
        except IntegridadError:
            raise
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            raise IntegridadError(f'No se pudo verificar {run_id}: {error}') from error

    def listar(self):
        if not self.root.exists():
            return []
        resultados = []
        for ruta in sorted(self.root.iterdir(), key=lambda p: p.name, reverse=True):
            if _RUN_ID.fullmatch(ruta.name) is None:
                continue
            try:
                registro = self.consultar(ruta.name)
                resultados.append({'run_id': ruta.name, 'estado': registro['estado'],
                                   'tipo_datos': registro['inicio'].get('tipo_datos', 'NO_DECLARADO')})
            except PersistenciaError as error:
                resultados.append({'run_id': ruta.name, 'estado': 'INTEGRIDAD_FALLIDA', 'error': str(error)})
        return resultados

    def recuperar(self, run_id):
        registro = self.consultar(run_id)
        cierre = registro['cierre']
        datos = cierre['datos'] if cierre else {}
        if cierre and registro['estado'] == 'COMPLETA' and datos.get('publicable') and datos.get('escenario') is not None:
            return {'run_id': run_id, 'estado': registro['estado'], 'escenario': datos['escenario'],
                    'fuente': 'CIERRE_VALIDADO', 'publicable': True}
        for evento in reversed(registro['eventos']):
            if evento['tipo'] == 'VENTANA_VALIDADA' and evento['datos'].get('escenario') is not None:
                return {'run_id': run_id, 'estado': registro['estado'], 'escenario': evento['datos']['escenario'],
                        'fuente': 'CHECKPOINT_VALIDADO', 'publicable': False}
        return {'run_id': run_id, 'estado': registro['estado'], 'escenario': None,
                'fuente': 'SIN_CHECKPOINT_VALIDADO', 'publicable': False}

    def comparar(self, run_id_a, run_id_b):
        registros = [self.consultar(r) for r in (run_id_a, run_id_b)]
        recuperados = [self.recuperar(r) for r in (run_id_a, run_id_b)]
        comparacion = {'run_id_a': run_id_a, 'run_id_b': run_id_b,
                       'estados': [r['estado'] for r in registros]}
        for campo in ('entradas', 'parametros', 'codigo', 'procedencia'):
            comparacion[f'{campo}_iguales'] = (_canonico(_codificar(registros[0]['inicio'].get(campo)))
                                               == _canonico(_codificar(registros[1]['inicio'].get(campo))))
        for grupo in ('confirmados', 'protegidos', 'propuestas'):
            a, b = [(r['escenario'] or {}).get(grupo, {}) for r in recuperados]
            comparacion[grupo] = {
                'solo_a': sorted(set(a) - set(b)), 'solo_b': sorted(set(b) - set(a)),
                'modificados': sorted(i for i in set(a) & set(b)
                                      if _canonico(_codificar(a[i])) != _canonico(_codificar(b[i]))),
            }
        for grupo in ('pendientes', 'estado_inicial_incompleto'):
            individuales, disponibles = [], []
            for registro, recuperado in zip(registros, recuperados):
                cierre = (registro['cierre'] or {}).get('datos', {})
                clasificados = cierre.get('resultados_individuales', {})
                checkpoint = recuperado['escenario'] or {}
                disponible = grupo in clasificados or grupo in cierre or grupo in checkpoint
                disponibles.append(disponible)
                datos = clasificados.get(grupo, cierre.get(grupo, checkpoint.get(grupo, [])))
                if isinstance(datos, dict):
                    individuales.append(datos)
                else:
                    individuales.append({v if isinstance(v, str) else v['id_vuelo']: v for v in datos})
            a, b = individuales
            completa = all(disponibles)
            comparacion[grupo] = {
                'disponible_a': disponibles[0], 'disponible_b': disponibles[1],
                'comparacion_completa': completa,
                'solo_a': sorted(set(a) - set(b)) if completa else None,
                'solo_b': sorted(set(b) - set(a)) if completa else None,
                'modificados': (sorted(i for i in set(a) & set(b)
                                      if _canonico(_codificar(a[i])) != _canonico(_codificar(b[i])))
                                if completa else None),
            }
        return comparacion
