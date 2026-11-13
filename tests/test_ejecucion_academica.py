"""Controles académicos con simulaciones y sondas de procesos reales; cero CP-SAT."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

from academico import ejecucion as e


class EjecucionAcademicaTests(unittest.TestCase):
    def recursos(self, disponibles=e.RAM_MINIMA):
        return type('Memoria', (), {'available': disponibles, 'total': 8 * e.GIB})()

    def entradas(self):
        return ({'operaciones': [{}, {}],
                 'limites_ensayo': {'candidatos_maximos': 94}}, 'a' * 64)

    def test_menos_de_dos_gib_rechaza_antes_de_crear_proceso(self):
        with patch.object(e.psutil, 'virtual_memory', return_value=self.recursos(e.RAM_MINIMA - 1)), \
             patch.object(e, '_cgroup_v2', return_value={'estado': 'NO_APLICA_HOST_LOCAL', 'margen_bytes': None,
                 'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}), \
             patch.object(e, 'cargar_entradas', return_value=self.entradas()), \
             patch.object(e.tempfile, 'mkdtemp', side_effect=AssertionError('No crear temporal')), \
             patch.object(e.subprocess, 'Popen', side_effect=AssertionError('No crear proceso')):
            with self.assertRaisesRegex(e.EjecucionError, 'RAM_HOST_MENOR_2_GIB'):
                e.ejecutar_interactivo()

    def test_linux_rechaza_cgroup_desconocido_o_sin_margen(self):
        base = {'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}
        for cgroup, codigo in ((dict(base, estado='NO_VERIFICABLE', margen_bytes=None),
                                'LIMITE_CONTENEDOR_NO_VERIFICABLE'),
                               (dict(base, estado='VERIFICADO', margen_bytes=e.RAM_MINIMA - 1),
                                'RAM_CONTENEDOR_MENOR_2_GIB')):
            with self.subTest(codigo=codigo), \
                 patch.object(e.os, 'name', 'posix'), \
                 patch.object(e.psutil, 'virtual_memory', return_value=self.recursos()), \
                 patch.object(e, '_cgroup_v2', return_value=cgroup), \
                 patch.object(e, 'cargar_entradas', return_value=self.entradas()):
                self.assertIn(codigo, e.evaluar_admision()['motivos'])

    def test_escenario_fuera_de_dos_por_cuarenta_y_siete_se_rechaza(self):
        datos, sha = self.entradas(); datos['operaciones'].append({})
        with patch.object(e.psutil, 'virtual_memory', return_value=self.recursos()), \
             patch.object(e, '_cgroup_v2', return_value={'estado': 'NO_APLICA_HOST_LOCAL', 'margen_bytes': None,
                 'limite_bytes': None, 'uso_bytes': None, 'cpu_max': None}), \
             patch.object(e, 'cargar_entradas', return_value=(datos, sha)):
            self.assertIn('ESCENARIO_FUERA_DE_ALCANCE', e.evaluar_admision()['motivos'])

    def test_dos_procesos_independientes_y_hash_coincidente(self):
        admitido = {'admitido': True, 'motivos': [], 'entrada_sha256': 'b' * 64}
        llamadas = []
        def proceso(fase, raiz, token, **kwargs):
            llamadas.append(fase)
            comun = {'correcto': True, 'run_id': 'SRL-COM-20261109T000000000000Z-' + 'a' * 32,
                     'hash_escenario': 'c' * 64, 'metricas': {'fase': fase},
                     'supervision': {'cancelacion_solicitada': None}}
            if fase == 'productor':
                return dict(comun, pid=101)
            return dict(comun, pid=202, resultado={'escenario': {'confirmados': {}}, 'diagnosticos': []})
        with tempfile.TemporaryDirectory() as temporal, \
             patch.object(e, 'evaluar_admision', return_value=admitido), \
             patch.object(e.tempfile, 'mkdtemp', return_value=temporal), \
             patch.object(e, '_proceso', side_effect=proceso):
            resultado = e.ejecutar_interactivo()
        self.assertEqual(llamadas, ['productor', 'recuperador'])
        self.assertTrue(resultado['historico'])
        self.assertEqual(resultado['hash_escenario'], 'c' * 64)

    def test_recuperacion_inconsistente_impide_devolver_resultado(self):
        admitido = {'admitido': True, 'motivos': [], 'entrada_sha256': 'b' * 64}
        respuestas = [
            {'pid': 1, 'run_id': 'RUN', 'hash_escenario': 'a', 'metricas': {}, 'supervision': {}},
            {'pid': 2, 'run_id': 'RUN', 'hash_escenario': 'b', 'resultado': {}, 'metricas': {}, 'supervision': {}},
        ]
        with tempfile.TemporaryDirectory() as temporal, \
             patch.object(e, 'evaluar_admision', return_value=admitido), \
             patch.object(e.tempfile, 'mkdtemp', return_value=temporal), \
             patch.object(e, '_proceso', side_effect=respuestas):
            with self.assertRaisesRegex(e.EjecucionError, 'no coincide'):
                e.ejecutar_interactivo()

    def test_worker_declara_original_y_no_importa_productivo_o_sqlite(self):
        fuente = e.WORKER.read_text(encoding='utf-8')
        self.assertIn('num_search_workers = 4', fuente)
        self.assertIn('max_time_in_seconds = 30', fuente)
        self.assertIn('cp_model_presolve = False', fuente)
        for prohibido in ('import sqlite3', 'planificador_continuo', 'optimizador_horarios', 'app.py'):
            self.assertNotIn(prohibido, fuente)

    def test_cancelacion_es_cooperativa_y_no_fuerza_el_proceso(self):
        controlador = Path(e.__file__).read_text(encoding='utf-8')
        worker = e.WORKER.read_text(encoding='utf-8')
        self.assertIn("cancelar.touch(exist_ok=False)", controlador)
        self.assertIn('solver.stop_search()', worker)
        for operacion_forzada in ('.terminate(', '.kill(', 'taskkill', 'Stop-Process'):
            self.assertNotIn(operacion_forzada, controlador)
            self.assertNotIn(operacion_forzada, worker)

    def test_worker_arranca_aislado_sin_resolver(self):
        resultado = subprocess.run(
            e._comando_trabajador_directo(['--help']),
            cwd=e.ROOT, capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('--modo {productor,recuperador}', resultado.stdout)
        self.assertNotIn('ortools', sys.modules)


    def test_comando_real_pid_argumentos_dependencias_y_aislamiento(self):
        with tempfile.TemporaryDirectory(prefix='worker con espacios ') as temporal:
            raiz = Path(temporal)
            worker = raiz / 'sonda académica.py'
            worker.write_text(
                'import sys, os, json, importlib.util, psutil\n'
                'print(json.dumps(dict(pid=os.getpid(), argv=sys.argv[1:], '
                'aislado=sys.flags.isolated, bytecode=sys.dont_write_bytecode, '
                'utf8=sys.flags.utf8_mode, psutil=psutil.__file__, '
                'intruso=importlib.util.find_spec("intruso_sonda") is not None, '
                'solver="ortools" in sys.modules)))\n', encoding='utf-8')
            (raiz / 'intruso_sonda.py').write_text('raise AssertionError()', encoding='utf-8')
            for fase in ('productor', 'recuperador'):
                args = ['--modo', fase, '--raiz', temporal, '--token', "a ' ñ \\",
                        '--run-id', 'RUN con espacios']
                with self.subTest(fase=fase), patch.object(e, 'WORKER', worker):
                    comando = e._comando_trabajador_directo(args)
                    with subprocess.Popen(comando, cwd=raiz,
                                          env=dict(os.environ, PYTHONPATH=temporal),
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True, encoding='utf-8') as proceso:
                        salida, error = proceso.communicate(timeout=10)
                        self.assertEqual(proceso.returncode, 0, error)
                        datos = json.loads(salida)
                        self.assertEqual(datos['pid'], proceso.pid)
                self.assertEqual(datos['argv'], args)
                self.assertEqual(datos['aislado'], 1)
                self.assertTrue(datos['bytecode'])
                self.assertEqual(datos['utf8'], 1)
                self.assertEqual(Path(datos['psutil']).resolve(), Path(e.psutil.__file__).resolve())
                self.assertFalse(datos['intruso'])
                self.assertFalse(datos['solver'])

    def test_comando_real_procesa_pth_y_rutas_distintas(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            puro, nativo, extra = (raiz / n for n in ('pure', 'plat', 'extra'))
            for p in (puro, nativo, extra):
                p.mkdir()
            (puro / 'extra.pth').write_text(str(extra) + '\n', encoding='utf-8')
            (extra / 'desde_pth.py').write_text('valor = 17', encoding='utf-8')
            (nativo / 'desde_plat.py').write_text('valor = 25', encoding='utf-8')
            worker = raiz / 'sonda.py'
            worker.write_text('import desde_pth, desde_plat; '
                              'print(desde_pth.valor + desde_plat.valor)', encoding='utf-8')
            with patch.object(e, 'WORKER', worker), patch.object(
                    e.sysconfig, 'get_paths', return_value={'purelib': str(puro), 'platlib': str(nativo)}):
                resultado = subprocess.run(e._comando_trabajador_directo([]), cwd=raiz,
                                           capture_output=True, text=True, timeout=10)
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
            self.assertEqual(resultado.stdout.strip(), '42')

    def test_supervisor_lanza_sonda_real_en_ambas_fases(self):
        # Sustituye solo la carga útil y la admisión: Popen, comando y lectura PID son reales.
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            (raiz / 'control').mkdir()
            worker = raiz / 'sonda.py'
            worker.write_text(
                'import os, sys, json, time\n'
                'time.sleep(0.2)\n'
                'print(json.dumps(dict(correcto=True, pid=os.getpid(), argv=sys.argv[1:])))\n',
                encoding='utf-8')
            with patch.object(e, 'WORKER', worker), \
                 patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
                 patch.object(e.psutil, 'virtual_memory', return_value=self.recursos()):
                for fase in ('productor', 'recuperador'):
                    datos = e._proceso(fase, raiz, 'token con espacios', run_id='RUN')
                    self.assertEqual(datos['argv'], ['--modo', fase, '--raiz', str(raiz),
                                                     '--token', 'token con espacios', '--run-id', 'RUN'])
                    self.assertIsNone(datos['supervision']['cancelacion_solicitada'])

    def test_exclusion_entre_hilos_y_procesos_y_liberacion(self):
        with tempfile.TemporaryDirectory() as temporal, \
             patch.object(e.tempfile, 'gettempdir', return_value=temporal):
            with e._exclusion_ensayo():
                with self.assertRaisesRegex(e.EjecucionError, 'EN_CURSO'):
                    with e._exclusion_ensayo():
                        self.fail('No debe admitir un segundo ensayo')
                codigo = (
                    f'import sys; sys.path.insert(0, {str(e.ROOT)!r}); '
                    'from academico import ejecucion as e; '
                    f'e.tempfile.gettempdir = lambda: {temporal!r}; '
                    'ctx=e._exclusion_ensayo(); ctx.__enter__()')
                resultado = subprocess.run([str(Path(sys._base_executable).resolve()),
                    '-I', '-B', '-c',
                    f'import site; [site.addsitedir(p) for p in {list(dict.fromkeys(e.sysconfig.get_paths()[k] for k in ("purelib", "platlib")))!r}]; '
                    + codigo], capture_output=True, text=True, timeout=10)
                self.assertNotEqual(resultado.returncode, 0)
                self.assertIn('EN_CURSO_O_BLOQUEO', resultado.stderr)
            with e._exclusion_ensayo():
                pass  # Se puede volver a adquirir al finalizar el ensayo anterior.

    def test_rss_incluye_descendientes_que_siguen_vivos(self):
        padre, hijo, terminado = Mock(), Mock(), Mock()
        padre.memory_info.return_value.rss = 100
        hijo.memory_info.return_value.rss = 200
        terminado.memory_info.side_effect = e.psutil.NoSuchProcess(123)
        padre.children.return_value = [hijo, terminado]
        self.assertEqual(e._rss_arbol(padre), 300)
        padre.children.assert_called_once_with(recursive=True)

    def test_recuperador_respeta_cancelacion_antes_y_despues_de_consultar(self):
        from academico import worker
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal); (raiz / 'control').mkdir()
            marcador = raiz / 'control' / 'CANCELAR'
            marcador.touch()
            with patch.object(worker, 'consultar_escenario') as consultar:
                with self.assertRaisesRegex(RuntimeError, 'CANCELADO'):
                    worker.recuperar(raiz, 'RUN')
                consultar.assert_not_called()
            marcador.unlink()
            def consulta(*args):
                marcador.touch()
                return {'publicable': True}
            with patch.object(worker, 'consultar_escenario', side_effect=consulta):
                with self.assertRaisesRegex(RuntimeError, 'CANCELADO'):
                    worker.recuperar(raiz, 'RUN')

    def test_temporal_se_limpia_y_exclusion_se_libera_tras_error(self):
        rutas = []
        def fallo(raiz, admision):
            rutas.append(raiz)
            (raiz / 'prueba.txt').write_text('fixture sin solver', encoding='utf-8')
            raise e.EjecucionError('fallo simulado')
        with patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
             patch.object(e, '_ejecutar_en_temporal', side_effect=fallo):
            with self.assertRaisesRegex(e.EjecucionError, 'fallo simulado'):
                e.ejecutar_interactivo()
        self.assertFalse(rutas[0].exists())
        self.assertFalse(e._ENSAYO_ACTIVO.locked())

    def test_deadline_solicita_cancelacion_a_sonda_real_sin_forzar(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal); (raiz / 'control').mkdir()
            worker = raiz / 'sonda.py'
            worker.write_text(
                'import os, json, time\nfrom pathlib import Path\n'
                'fin=time.monotonic()+3\n'
                'while not Path("control/CANCELAR").exists() and time.monotonic()<fin:\n'
                '    time.sleep(0.01)\n'
                'print(json.dumps(dict(correcto=True, pid=os.getpid())))\n', encoding='utf-8')
            with patch.object(e, 'WORKER', worker), \
                 patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
                 patch.object(e.psutil, 'virtual_memory', return_value=self.recursos()):
                with self.assertRaisesRegex(e.EjecucionError, 'TIEMPO_SUPERADO'):
                    e._proceso('recuperador', raiz, 'token', deadline=e.time.perf_counter() - 1)
            self.assertTrue((raiz / 'control' / 'CANCELAR').exists())

    def test_recuperador_real_lee_fixture_por_lanzador_y_supervisor(self):
        # Fixture explícita; ningún solver produce estas asignaciones.
        from academico.escenarios import cargar_entradas, REGULARES, texto_json
        from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios
        import hashlib
        with tempfile.TemporaryDirectory(prefix='SkyRiskLab-academico-') as temporal:
            raiz = Path(temporal); (raiz / 'control').mkdir()
            (raiz / 'control' / 'configuracion.json').write_text(json.dumps({
                'token_sha256': hashlib.sha256(b'fixture').hexdigest()}), encoding='utf-8')
            datos, _ = cargar_entradas()
            vuelos = [dict(v, aeronave='HK-001') for v in datos['operaciones']]
            escenario = {'flota': {m: {'categoria': 'REGULAR'} for m in REGULARES},
                         'confirmados': {v['id_vuelo']: v for v in vuelos},
                         'protegidos': {}, 'propuestas': {}}
            registro = AlmacenEscenarios(raiz / 'ejecuciones').iniciar(
                entradas={'operaciones': datos['operaciones'], 'origen': 'FIXTURE_TEST_NO_SOLVER'},
                parametros={'perfil_solver': 'ORIGINAL', 'configuracion_solver': {}},
                procedencia={'tipo_datos': 'SINTETICO', 'origen': 'FIXTURE_TEST_NO_SOLVER'})
            registro.cerrar('COMPLETA', {'publicable': True, 'escenario': escenario,
                'resultados_individuales': {'confirmados': vuelos, 'pendientes': [],
                                           'estado_inicial_incompleto': []},
                'diagnosticos': [{'codigo': 'FIXTURE_TEST_NO_SOLVER'}]})
            with patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
                 patch.object(e.psutil, 'virtual_memory', return_value=self.recursos()):
                recuperado = e._proceso('recuperador', raiz, 'fixture', run_id=registro.run_id)
            self.assertTrue(recuperado['resultado']['publicable'])
            self.assertEqual(recuperado['run_id'], registro.run_id)
            self.assertEqual(recuperado['resultado']['escenario'], escenario)
            self.assertEqual(recuperado['hash_escenario'],
                             hashlib.sha256(texto_json(recuperado['resultado']['escenario']).encode('utf-8')).hexdigest())
            self.assertEqual(recuperado['resultado']['diagnosticos'][0]['codigo'], 'FIXTURE_TEST_NO_SOLVER')


if __name__ == '__main__':
    unittest.main()
