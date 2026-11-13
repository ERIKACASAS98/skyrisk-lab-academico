"""Controles del ejecutor académico con procesos simulados; cero CP-SAT."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

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
            [sys.executable, '-I', '-B', '-X', 'utf8', str(e.WORKER), '--help'],
            cwd=e.ROOT, capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('--modo {productor,recuperador}', resultado.stdout)
        self.assertNotIn('ortools', sys.modules)


if __name__ == '__main__':
    unittest.main()
