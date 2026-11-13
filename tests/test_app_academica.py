"""AppTest del demostrador: cero solver, cero SQLite, fixtures temporales.

Los registros artificiales de estos tests comprueban el visor. No constituyen
resultados obtenidos por CP-SAT y no se incorporan a demo/escenarios.
"""
from copy import deepcopy
from pathlib import Path
import builtins
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from academico import escenarios as e
from academico.ejecucion import EjecucionError
from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios


APP = Path(__file__).resolve().parents[1] / 'app_academica.py'


class AppAcademicaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psutil
        cls.proceso = psutil.Process()
        cls.psutil = psutil
        cls.inicio = time.perf_counter()
        cls.pico_rss = cls.proceso.memory_info().rss
        cls.fin = threading.Event()

        def muestrear():
            while not cls.fin.wait(0.1):
                cls.pico_rss = max(cls.pico_rss, cls.proceso.memory_info().rss)

        cls.monitor = threading.Thread(target=muestrear, daemon=True)
        cls.monitor.start()

    @classmethod
    def tearDownClass(cls):
        cls.fin.set()
        cls.monitor.join()
        print('UI_METRICAS ' + json.dumps({'wall_s': time.perf_counter() - cls.inicio,
              'pico_rss_muestreado_bytes': cls.pico_rss, 'cp_sat_ejecutado': False}))

    def comprobar_recursos(self):
        # Este umbral es solo para el visor sin solver. El ensayo CP-SAT mantiene
        # invariable su admisión de 2 GiB y no está invocado por estos tests.
        self.assertGreaterEqual(self.psutil.virtual_memory().available, 256 * 1024 ** 2,
                                'Margen insuficiente para continuar AppTest sin solver')
        self.assertLessEqual(self.proceso.memory_info().rss, 384 * 1024 ** 2,
                             'Presupuesto RSS de pruebas UI superado')
        self.assertLess(time.perf_counter() - self.inicio, 45, 'Presupuesto supervisado de AppTest agotado')

    def setUp(self):
        self.comprobar_recursos()
        self.importar = builtins.__import__
        admision = patch('academico.ejecucion.evaluar_admision', return_value={
            'admitido': False, 'motivos': ['RAM_HOST_MENOR_2_GIB'],
            'contenedor': {'estado': 'NO_APLICA_HOST_LOCAL'}})
        admision.start()
        self.addCleanup(admision.stop)

        def sin_motores(nombre, *args, **kwargs):
            prohibidos = ('ortools', 'app', 'planificacion_comercial.planificador_continuo',
                           'planificacion_comercial.optimizador_horarios',
                           'planificacion_comercial.rutas_maestras', 'planificacion_tripulaciones')
            if any(nombre == p or nombre.startswith(p + '.') for p in prohibidos):
                raise AssertionError('Importación del motor prohibida en el visor: ' + nombre)
            return self.importar(nombre, *args, **kwargs)

        guardia = patch.object(builtins, '__import__', side_effect=sin_motores)
        guardia.start()
        self.addCleanup(guardia.stop)
        conexion = patch.object(sqlite3, 'connect', side_effect=AssertionError('SQLite prohibido en la app académica'))
        conexion.start()
        self.addCleanup(conexion.stop)

    def abrir(self):
        self.comprobar_recursos()
        app = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertEqual(len(app.exception), 0, app.exception)
        self.assertEqual(len(app.error), 0, app.error)
        return app

    def cambiar(self, app, vista):
        self.comprobar_recursos()
        app.segmented_control(key='vista_academica').set_value(vista).run(timeout=15)
        self.assertEqual(len(app.exception), 0, app.exception)
        return app

    def test_arranque_no_resuelve_no_conecta_sqlite_y_muestra_entradas(self):
        with patch.object(AlmacenEscenarios, 'iniciar', side_effect=AssertionError('No escribir escenarios')), \
             patch('academico.ejecucion.ejecutar_interactivo',
                   side_effect=AssertionError('No ejecutar sin clic')) as ejecutar:
            app = self.abrir()
            self.assertEqual([m.value for m in app.metric], ['2', '47', '3'])
            self.assertTrue(any('Cada nuevo ensayo CP-SAT' in w.value for w in app.warning))
            self.cambiar(app, 'Caso sintético')
            app.selectbox(key='origen_academico').select('MDE').run(timeout=15)
            self.cambiar(app, 'Optimización')
            boton = next(b for b in app.button if b.label == 'Optimizar')
            self.assertTrue(boton.disabled)
            ejecutar.assert_not_called()

    def test_filtro_sintetico_y_modalidad_interactiva_no_conectada(self):
        app = self.cambiar(self.abrir(), 'Caso sintético')
        self.assertEqual(len(app.dataframe[0].value), 2)
        app.selectbox(key='origen_academico').select('MDE').run(timeout=15)
        self.assertEqual(len(app.dataframe[0].value), 1)
        self.assertEqual(app.dataframe[0].value.iloc[0]['id_vuelo'], 'PASO1-SINT-N002')
        self.cambiar(app, 'Optimización')
        self.assertTrue(any('Optimización deshabilitada' in w.value for w in app.warning))
        self.assertTrue(next(b for b in app.button if b.label == 'Optimizar').disabled)

    def test_boton_explicito_ejecuta_una_vez_y_conserva_historico_ante_fallo(self):
        admision = {'admitido': True, 'motivos': [], 'ram_host_disponible_bytes': 3 * 1024**3,
                    'contenedor': {'estado': 'NO_APLICA_HOST_LOCAL'}}
        diagnostico = {'estado_solver': 'OPTIMAL', 'objetivo': 2, 'cota': 2}
        historico = {'run_id': 'RUN-SINTETICO', 'resultado': {'escenario': {'confirmados': {
            'PASO1-SINT-N001': {'id_vuelo': 'PASO1-SINT-N001', 'aeronave': 'HK-001'},
            'PASO1-SINT-N002': {'id_vuelo': 'PASO1-SINT-N002', 'aeronave': 'HK-001'}}},
            'diagnosticos': [diagnostico]}, 'productor': {}, 'recuperador': {},
            'supervision_productor': {}, 'supervision_recuperador': {},
            'wall_total_s': 1.0, 'hash_escenario': 'a' * 64, 'admision': admision}
        with patch('academico.ejecucion.evaluar_admision', return_value=admision), \
             patch('academico.ejecucion.ejecutar_interactivo', return_value=historico) as ejecutar:
            app = self.cambiar(self.abrir(), 'Optimización')
            app.checkbox(key='confirmar_optimizacion_academica').check()
            next(b for b in app.button if b.label == 'Optimizar').click().run(timeout=15)
            self.assertEqual(ejecutar.call_count, 1)
            self.assertEqual(app.session_state['ultimo_resultado_academico_valido']['run_id'], 'RUN-SINTETICO')
            self.assertTrue(any('HISTÓRICO DE SESIÓN' in c.value for c in app.caption))
        with patch('academico.ejecucion.evaluar_admision', return_value=admision), \
             patch('academico.ejecucion.ejecutar_interactivo', side_effect=EjecucionError('fallo simulado')):
            next(b for b in app.button if b.label == 'Optimizar').click().run(timeout=15)
        self.assertEqual(app.session_state['ultimo_resultado_academico_valido']['run_id'], 'RUN-SINTETICO')
        self.assertTrue(any('último histórico válido' in i.value for i in app.info))

    def test_consulta_sin_runs_no_inventa_cobertura(self):
        with patch.object(e, 'listar_escenarios', return_value=[]):
            app = self.cambiar(self.abrir(), 'Consulta histórica')
        self.assertTrue(any('SIN_EJECUCION' in w.value for w in app.warning))
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(any('HISTÓRICO COLAB' in i.value for i in app.info))
        self.assertTrue(any('no contiene los archivos originales' in c.value for c in app.caption))

    def test_evidencia_colab_alterada_muestra_error_sin_ejecutar(self):
        with patch.object(e, 'listar_escenarios', return_value=[]), \
             patch.object(e, 'cargar_evidencia_colab', side_effect=e.ConsultaError('copia alterada')), \
             patch('academico.ejecucion.ejecutar_interactivo', side_effect=AssertionError('No resolver')):
            app = self.cambiar(self.abrir(), 'Consulta histórica')
        self.assertTrue(any('copia alterada' in error.value for error in app.error))

    def test_error_integridad_se_muestra_sin_publicar_resultados(self):
        with patch.object(e, 'listar_escenarios', side_effect=e.ConsultaError('Integridad no verificable')):
            app = self.cambiar(self.abrir(), 'Consulta histórica')
        self.assertEqual(len(app.error), 1)
        self.assertIn('Integridad no verificable', app.error[0].value)

    def test_consulta_real_fixture_no_solver_conserva_bytes(self):
        datos, _ = e.cargar_entradas()
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            almacen = AlmacenEscenarios(raiz)
            registro = almacen.iniciar(
                entradas={'operaciones': datos['operaciones'], 'origen': 'FIXTURE_TEST_NO_SOLVER'},
                parametros={'perfil_solver': 'ORIGINAL', 'configuracion_solver': {}, 'origen': 'FIXTURE_TEST_NO_SOLVER'},
                procedencia={'tipo_datos': 'SINTETICO', 'origen': 'FIXTURE_TEST_NO_SOLVER'})
            a, b = [dict(v, aeronave='HK-001') for v in datos['operaciones']]
            escenario = {'flota': {m: {'categoria': 'REGULAR'} for m in e.REGULARES},
                         'confirmados': {a['id_vuelo']: a, b['id_vuelo']: b},
                         'protegidos': {}, 'propuestas': {}, 'origen': 'FIXTURE_TEST_NO_SOLVER'}
            registro.cerrar('COMPLETA', {'publicable': True, 'escenario': escenario,
                'resultados_individuales': {'confirmados': [a, b], 'pendientes': [], 'estado_inicial_incompleto': []},
                'diagnosticos': [{'codigo': 'FIXTURE_TEST_NO_SOLVER'}]})
            antes, _ = e.inventario_acotado(raiz / registro.run_id)
            listar_real, consultar_real = e.listar_escenarios, e.consultar_escenario
            with patch.object(e, 'listar_escenarios', side_effect=lambda: listar_real(raiz)), \
                 patch.object(e, 'consultar_escenario', side_effect=lambda run: consultar_real(run, raiz)), \
                 patch.object(AlmacenEscenarios, 'iniciar', side_effect=AssertionError('No escribir al consultar')):
                app = self.cambiar(self.abrir(), 'Consulta histórica')
                self.assertEqual(len(app.error), 0, app.error)
                self.assertEqual(len(app.dataframe[0].value), 2)
            despues, _ = e.inventario_acotado(raiz / registro.run_id)
            self.assertEqual(antes, despues)

    def test_paginas_profesionales_no_estan_registradas(self):
        app = self.abrir()
        with self.assertRaises(ValueError):
            app.switch_page('pages/Control_de_aeronaves.py')


if __name__ == '__main__':
    unittest.main()
