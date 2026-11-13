"""Lector académico puro: fixtures artificiales, disco temporal y ningún solver.

Los cierres construidos aquí se etiquetan FIXTURE_TEST_NO_SOLVER. Solo ejercitan
lectura, límites e integridad; no son resultados de optimización ni evidencia
de cobertura operacional. No se importan SQLite, Streamlit ni OR-Tools.
"""
from __future__ import annotations

import builtins
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from academico import escenarios as e
from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios, PersistenciaError


MARCA = 'FIXTURE_TEST_NO_SOLVER'
INICIO = datetime(2026, 11, 9, tzinfo=timezone.utc)


def entradas_fixture():
    return {
        'id_escenario': MARCA, 'tipo_datos': 'SINTETICO',
        'estado_ejecucion': 'SIN_EJECUCION', 'resultados': None,
        'flota': {'regulares': sorted(e.REGULARES), 'reservas': sorted(e.RESERVAS)},
        'operaciones': [
            {'id_vuelo': 'PASO1-SINT-N001', 'tipo': 'N', 'origen': 'BOG', 'destino': 'MDE',
             'salida_utc': '2026-11-09T10:00:00+00:00', 'llegada_utc': '2026-11-09T11:00:00+00:00',
             'operacion_origen': None, 'ruta_maestra': 'BOG-MDE'},
            {'id_vuelo': 'PASO1-SINT-N002', 'tipo': 'N', 'origen': 'MDE', 'destino': 'BOG',
             'salida_utc': '2026-11-09T12:00:00+00:00', 'llegada_utc': '2026-11-09T13:00:00+00:00',
             'operacion_origen': None, 'ruta_maestra': 'MDE-BOG'},
        ],
        'evidencia': MARCA,
    }


class EscenariosAcademicosTests(unittest.TestCase):
    def setUp(self):
        temporal = tempfile.TemporaryDirectory(prefix='skyrisk-fixture-lector-')
        self.addCleanup(temporal.cleanup)
        self.raiz = Path(temporal.name)
        self.almacen = AlmacenEscenarios(self.raiz / 'escenarios')

    def escribir_entrada(self, datos=None):
        ruta = self.raiz / 'entrada.json'
        ruta.write_text(json.dumps(entradas_fixture() if datos is None else datos), encoding='utf-8')
        return ruta

    def fixture_run(self, *, tipo='SINTETICO', modificar=None, cierre=True):
        """Registro artificial exclusivamente en el temporal propiedad del test."""
        datos = entradas_fixture()
        registro = self.almacen.iniciar(
            entradas={'operaciones': datos['operaciones'], 'evidencia': MARCA},
            parametros={'perfil_solver': 'ORIGINAL', 'evidencia': MARCA},
            procedencia={'tipo_datos': tipo, 'evidencia': MARCA})
        vuelos = {v['id_vuelo']: {**deepcopy(v), 'aeronave': 'HK-001', 'evidencia': MARCA}
                  for v in datos['operaciones']}
        escenario = {'flota': {m: {'categoria': 'REGULAR'} for m in sorted(e.REGULARES)},
                     'confirmados': vuelos, 'protegidos': {}, 'propuestas': {}, 'evidencia': MARCA}
        if modificar is not None:
            modificar(escenario)
        registro.evento('VENTANA_VALIDADA', {'escenario': escenario, 'evidencia': MARCA})
        if cierre:
            registro.cerrar('COMPLETA', {
                'publicable': True, 'escenario': escenario, 'evidencia': MARCA,
                'resultados_individuales': {'confirmados': list(vuelos.values()),
                                          'pendientes': [], 'estado_inicial_incompleto': []},
                'diagnosticos': [{'codigo': MARCA}], 'ventanas': []})
        return registro.run_id, escenario

    def test_entradas_dos_trayectos_cincuenta_categorias_y_hash_real(self):
        ruta = self.escribir_entrada()
        datos, sha = e.cargar_entradas(ruta)
        self.assertEqual(sha, hashlib.sha256(ruta.read_bytes()).hexdigest())
        self.assertEqual(len(datos['operaciones']), 2)
        self.assertEqual(len(datos['flota']['regulares']), 47)
        self.assertEqual(len(datos['flota']['reservas']), 3)
        self.assertFalse(set(datos['flota']['regulares']) & set(datos['flota']['reservas']))
        a, b = datos['operaciones']
        self.assertEqual(e.fecha(b['salida_utc']) - e.fecha(a['llegada_utc']), timedelta(minutes=60))
        self.assertIsNone(datos['resultados'])

    def test_entradas_mixtas_y_operacionales_se_rechazan(self):
        for tipo in ('MIXTO', 'OPERACIONAL'):
            with self.subTest(tipo=tipo):
                datos = entradas_fixture()
                datos['tipo_datos'] = tipo
                with self.assertRaises(e.ConsultaError):
                    e.cargar_entradas(self.escribir_entrada(datos))

    def test_entradas_no_pueden_incluir_resultados_no_ejecutados(self):
        datos = entradas_fixture()
        datos['resultados'] = {'asignados': 2, 'evidencia': MARCA}
        with self.assertRaises(e.ConsultaError):
            e.cargar_entradas(self.escribir_entrada(datos))

    def test_entradas_no_pueden_cambiar_categorias_o_duplicar_matriculas(self):
        datos = entradas_fixture()
        datos['flota']['regulares'][0] = 'HK-020'
        with self.assertRaises(e.ConsultaError):
            e.cargar_entradas(self.escribir_entrada(datos))
        datos = entradas_fixture()
        datos['flota']['reservas'] = ['HK-020', 'HK-020', 'HK-022']
        with self.assertRaises(e.ConsultaError):
            e.cargar_entradas(self.escribir_entrada(datos))

    def test_entrada_demasiado_grande_se_rechaza_antes_de_decodificar(self):
        ruta = self.raiz / 'grande.json'
        ruta.write_bytes(b' ' * (64 * 1024 + 1))
        with self.assertRaises(e.ConsultaError):
            e.cargar_entradas(ruta)

    def test_transito_distinto_de_sesenta_se_rechaza(self):
        for minutos in (59, 61):
            with self.subTest(minutos=minutos):
                datos = entradas_fixture()
                datos['operaciones'][1]['salida_utc'] = (INICIO + timedelta(hours=11, minutes=minutos)).isoformat()
                with self.assertRaises(e.ConsultaError):
                    e.validar_operaciones(datos['operaciones'])

    def test_horarios_sin_zona_horaria_se_rechazan(self):
        datos = entradas_fixture()
        datos['operaciones'][0]['salida_utc'] = '2026-11-09T10:00:00'
        with self.assertRaises(e.ConsultaError):
            e.validar_operaciones(datos['operaciones'])

    def test_ids_duplicados_o_ajenos_se_rechazan(self):
        for identificador in ('PASO1-SINT-N001', 'OTRO-VUELO'):
            with self.subTest(id=identificador):
                datos = entradas_fixture()
                datos['operaciones'][1]['id_vuelo'] = identificador
                with self.assertRaises(e.ConsultaError):
                    e.validar_operaciones(datos['operaciones'])

    def test_almacen_ausente_no_se_crea_al_listar(self):
        inexistente = self.raiz / 'no-existe'
        self.assertEqual(e.listar_escenarios(inexistente), [])
        self.assertFalse(inexistente.exists())

    def test_run_id_traversal_rechazado(self):
        for run_id in ('..', '../data/skyrisk_operacion.db', '/tmp/otro', 'RUN/../OTRO', '', None):
            with self.subTest(run_id=run_id), self.assertRaises(PersistenciaError):
                e.consultar_escenario(run_id, self.almacen.root)

    def test_lista_y_cierre_real_con_fixture_explicita_sin_solver(self):
        run_id, escenario = self.fixture_run()
        self.assertEqual(e.listar_escenarios(self.almacen.root), [run_id])
        leido = e.consultar_escenario(run_id, self.almacen.root)
        self.assertEqual(leido['escenario'], escenario)
        self.assertEqual(leido['escenario']['evidencia'], MARCA)
        self.assertEqual(leido['estado'], 'COMPLETA')
        self.assertEqual(leido['fuente'], 'CIERRE_VALIDADO')
        self.assertTrue(leido['publicable'])  # Publicable como estructura íntegra, no como evidencia de optimización.
        self.assertEqual(set(leido['escenario']['confirmados']), e.IDS)
        self.assertTrue(leido['hashes'])
        self.assertGreater(leido['bytes'], 0)
        self.assertNotIn('estado_solver', leido['parametros'])

    def test_checkpoint_sin_cierre_se_recupera_sin_publicar(self):
        run_id, escenario = self.fixture_run(cierre=False)
        leido = e.consultar_escenario(run_id, self.almacen.root)
        self.assertEqual(leido['fuente'], 'CHECKPOINT_VALIDADO')
        self.assertFalse(leido['publicable'])
        self.assertEqual(leido['escenario'], escenario)

    def test_run_mixto_u_operacional_se_rechaza_aunque_hashes_sean_correctos(self):
        for tipo in ('MIXTO', 'OPERACIONAL'):
            with self.subTest(tipo=tipo):
                run_id, _ = self.fixture_run(tipo=tipo)
                with self.assertRaises(e.ConsultaError):
                    e.consultar_escenario(run_id, self.almacen.root)

    def test_asignacion_a_reserva_no_es_admisible_en_el_visor(self):
        def asignar_reserva(escenario):
            escenario['confirmados']['PASO1-SINT-N001']['aeronave'] = 'HK-020'
        run_id, _ = self.fixture_run(modificar=asignar_reserva)
        with self.assertRaises(e.ConsultaError):
            e.consultar_escenario(run_id, self.almacen.root)

    def test_id_interno_de_asignacion_debe_coincidir_con_su_clave(self):
        def cambiar_id(escenario):
            escenario['confirmados']['PASO1-SINT-N001']['id_vuelo'] = 'OTRO'
        run_id, _ = self.fixture_run(modificar=cambiar_id)
        with self.assertRaises(e.ConsultaError):
            e.consultar_escenario(run_id, self.almacen.root)

    def test_cierre_sin_escenario_no_se_presenta_como_publicable(self):
        registro = self.almacen.iniciar(
            entradas={'operaciones': entradas_fixture()['operaciones'], 'evidencia': MARCA},
            parametros={'perfil_solver': 'ORIGINAL'}, procedencia={'tipo_datos': 'SINTETICO'})
        registro.cerrar('COMPLETA', {'publicable': True, 'escenario': None})
        leido = e.consultar_escenario(registro.run_id, self.almacen.root)
        self.assertFalse(leido['publicable'])
        self.assertIsNone(leido['escenario'])

    def test_resultados_individuales_contradictorios_se_rechazan(self):
        datos = entradas_fixture()
        registro = self.almacen.iniciar(
            entradas={'operaciones': datos['operaciones'], 'evidencia': MARCA},
            parametros={'perfil_solver': 'ORIGINAL'}, procedencia={'tipo_datos': 'SINTETICO'})
        vuelos = {v['id_vuelo']: dict(v, aeronave='HK-001') for v in datos['operaciones']}
        escenario = {'flota': {m: {'categoria': 'REGULAR'} for m in e.REGULARES},
                     'confirmados': vuelos, 'propuestas': {}, 'protegidos': {}}
        distintos = deepcopy(list(vuelos.values()))
        distintos[0]['aeronave'] = 'HK-002'
        registro.cerrar('COMPLETA', {'publicable': True, 'escenario': escenario,
            'resultados_individuales': {'confirmados': distintos, 'pendientes': [], 'estado_inicial_incompleto': []}})
        with self.assertRaises(e.ConsultaError):
            e.consultar_escenario(registro.run_id, self.almacen.root)

    def test_escenario_sin_las_cuarenta_y_siete_regulares_se_rechaza(self):
        def quitar_regular(escenario):
            escenario['flota'].pop('HK-001')
        run_id, _ = self.fixture_run(modificar=quitar_regular)
        with self.assertRaises(e.ConsultaError):
            e.consultar_escenario(run_id, self.almacen.root)

    def test_alteracion_de_bytes_con_json_equivalente_se_detecta_por_hash(self):
        run_id, _ = self.fixture_run()
        archivo = self.almacen.root / run_id / 'eventos' / '00000001' / 'datos.json'
        archivo.write_bytes(archivo.read_bytes() + b' ')
        with self.assertRaises(PersistenciaError):
            e.consultar_escenario(run_id, self.almacen.root)

    def test_limite_de_bytes_del_inventario(self):
        carpeta = self.raiz / 'bytes'
        carpeta.mkdir()
        (carpeta / 'a').write_bytes(b'ab')
        with patch.object(e, 'MAX_BYTES', 1), self.assertRaises(e.ConsultaError):
            e.inventario_acotado(carpeta)

    def test_limite_de_archivos_del_inventario(self):
        carpeta = self.raiz / 'archivos'
        carpeta.mkdir()
        for nombre in ('a', 'b'):
            (carpeta / nombre).write_bytes(b'x')
        with patch.object(e, 'MAX_ARCHIVOS', 1), self.assertRaises(e.ConsultaError):
            e.inventario_acotado(carpeta)

    def test_limite_de_entradas_incluye_directorios(self):
        carpeta = self.raiz / 'directorios'
        carpeta.mkdir()
        (carpeta / 'a').mkdir()
        (carpeta / 'b').mkdir()
        with patch.object(e, 'MAX_ENTRADAS', 1), self.assertRaises(e.ConsultaError):
            e.inventario_acotado(carpeta)

    def test_limite_de_runs_pequenos(self):
        self.fixture_run()
        self.fixture_run()
        with patch.object(e, 'MAX_RUNS', 1), self.assertRaises(e.ConsultaError):
            e.listar_escenarios(self.almacen.root)

    def test_consulta_no_escribe_ni_importa_sqlite_o_motor(self):
        run_id, _ = self.fixture_run()
        ruta = self.almacen.root / run_id
        antes, _ = e.inventario_acotado(ruta)
        importar_real, abrir_real = builtins.__import__, io.open

        def importar_guardado(nombre, *args, **kwargs):
            prohibidos = ('sqlite3', 'ortools', 'streamlit',
                          'planificacion_comercial.planificador_continuo',
                          'planificacion_comercial.optimizador_horarios')
            if any(nombre == p or nombre.startswith(p + '.') for p in prohibidos):
                raise AssertionError('La consulta importó un módulo prohibido')
            return importar_real(nombre, *args, **kwargs)

        def abrir_guardado(archivo, mode='r', *args, **kwargs):
            if any(c in mode for c in 'wax+'):
                raise AssertionError('La consulta intentó escribir')
            return abrir_real(archivo, mode, *args, **kwargs)

        with patch('builtins.__import__', side_effect=importar_guardado), \
             patch('io.open', side_effect=abrir_guardado), \
             patch.object(AlmacenEscenarios, 'iniciar', side_effect=AssertionError('No iniciar al consultar')):
            leido = e.consultar_escenario(run_id, self.almacen.root)
        despues, _ = e.inventario_acotado(ruta)
        self.assertEqual(antes, despues)
        self.assertEqual(leido['hashes'], antes)


if __name__ == '__main__':
    unittest.main()
