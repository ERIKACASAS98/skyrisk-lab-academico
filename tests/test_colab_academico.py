"""Prueba el transporte y el runner. Nunca ejecuta las seis pruebas CP-SAT."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile

from herramientas.validadores import preparar_colab as paquete
from herramientas.validadores import validar_cpsat_colab as runner


class ColabAcademicoTests(unittest.TestCase):
    def test_paquete_contiene_bytes_exactos_y_detecta_corrupcion(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / 'fuentes.zip'
            m, sha = paquete.crear_paquete(paquete.ROOT, destino, 'FIXTURE_TEST_NO_SOLVER')
            self.assertEqual(paquete.verificar_paquete(destino, sha), m)
            self.assertEqual(set(m['archivos']), paquete.PERMITIDOS)
            _, repetido = paquete.crear_paquete(paquete.ROOT, Path(d) / 'segunda_copia.zip', 'FIXTURE_TEST_NO_SOLVER')
            self.assertEqual(sha, repetido)
            with zipfile.ZipFile(destino) as z:
                for nombre in m['archivos']:
                    self.assertEqual(z.read(nombre), (paquete.ROOT / nombre).read_bytes())
                self.assertFalse(any('.git/' in n or n.endswith('.db') for n in z.namelist()))
            with self.assertRaises(ValueError):
                paquete.verificar_paquete(destino, '0' * 64)
            with self.assertRaises(FileExistsError):
                paquete.crear_paquete(paquete.ROOT, destino, 'FIXTURE_TEST_NO_SOLVER')

    def test_preflight_real_desde_snapshot_extraido_sin_solver(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            destino = raiz / 'fuentes.zip'
            paquete.crear_paquete(paquete.ROOT, destino, 'FIXTURE_TEST_NO_SOLVER')
            fuente = raiz / 'snapshot'; fuente.mkdir()
            # ZIP creado y verificado por el propio empaquetador, no de un tercero.
            paquete.verificar_paquete(destino, hashlib.sha256(destino.read_bytes()).hexdigest())
            with zipfile.ZipFile(destino) as z:
                z.extractall(fuente)
            proceso = subprocess.run([sys.executable, '-I', '-B',
                str(fuente / 'herramientas/validadores/validar_cpsat_colab.py'),
                '--salida', str(raiz / 'preflight')], capture_output=True, text=True, timeout=20)
            r = json.loads((raiz / 'preflight/resultado.json').read_text(encoding='utf-8'))
            self.assertIn(proceso.returncode, (0, 2), proceso.stderr)
            self.assertIn(r['estado'], ('PREFLIGHT_LISTO_NO_EJECUTADO', 'BLOQUEADO_POR_ADMISION'))
            self.assertFalse(r['cp_sat_ejecutado'])
            self.assertFalse(r['seis_aprobadas'])
            self.assertEqual(r['pruebas'], [])
            self.assertEqual(len(r['pendientes']), 6)
            self.assertTrue(r['snapshot_verificado_al_final'])

    def test_zip_traversal_no_se_acepta(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'inseguro.zip'
            with zipfile.ZipFile(ruta, 'w') as z:
                z.writestr('../fuera.txt', 'fixture')
            with self.assertRaisesRegex(ValueError, 'Ruta ZIP'):
                paquete.verificar_paquete(ruta, hashlib.sha256(ruta.read_bytes()).hexdigest())

    def test_snapshot_modificado_se_rechaza(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / 'ejemplo.py').write_bytes(b'print(1)\n')
            archivos = {'ejemplo.py': {'sha256': hashlib.sha256(b'print(1)\n').hexdigest(), 'bytes': 9}}
            m = {'rama': paquete.RAMA, 'archivos': archivos, 'snapshot_id': paquete.snapshot_id(archivos)}
            (raiz / paquete.MANIFIESTO).write_text(json.dumps(m), encoding='utf-8')
            self.assertEqual(runner.verificar_snapshot(raiz), m)
            (raiz / 'ejemplo.py').write_bytes(b'print(2)\n')
            with self.assertRaisesRegex(ValueError, 'snapshot cambió'):
                runner.verificar_snapshot(raiz)

    def test_preflight_con_ram_insuficiente_no_lanza_pruebas(self):
        m = {'snapshot_id': 'FIXTURE_TEST_NO_SOLVER', 'revision_base': 'fixture',
             'rama': paquete.RAMA, 'dependencias_cpsat': []}
        with tempfile.TemporaryDirectory() as d, \
             patch.object(runner, 'verificar_snapshot', return_value=m), \
             patch.object(runner, 'evaluar_admision', return_value={'admitido': False, 'motivos': ['RAM_HOST_MENOR_2_GIB']}), \
             patch.object(runner, 'ejecutar_seis', side_effect=AssertionError('No lanzar CP-SAT')) as ejecutar:
            salida = Path(d) / 'informe'
            codigo = runner.main(['--ejecutar', '--salida', str(salida)])
            r = json.loads((salida / 'resultado.json').read_text(encoding='utf-8'))
            self.assertEqual(codigo, 2)
            self.assertFalse(r['seis_aprobadas'])
            self.assertFalse(r['cp_sat_ejecutado'])
            self.assertEqual(len(r['pendientes']), 6)
            ejecutar.assert_not_called()

    def test_omision_de_unittest_no_es_aprobacion(self):
        # Simula solo el resultado de unittest, no parchea ni ejecuta el optimizador.
        omitido = unittest.TestResult()
        omitido.testsRun = 1
        omitido.skipped = [('FIXTURE_TEST_NO_SOLVER', 'RAM insuficiente')]
        with patch.object(runner, 'evaluar_admision', return_value={'admitido': True}), \
             patch.object(unittest.TextTestRunner, 'run', return_value=omitido) as ejecutar:
            registros, _, aprobadas = runner.ejecutar_seis()
            self.assertEqual(ejecutar.call_count, 1)
            self.assertFalse(aprobadas)
            self.assertEqual(registros[0]['estado'], 'NO_APROBADA')

    def test_seleccion_exacta_seis_y_notebook_sin_resultados(self):
        import sys
        sys.path.insert(0, str(paquete.ROOT / 'tests'))
        from test_ampliacion_academica import SolverAmpliadoRealTests
        self.assertEqual(set(runner.METODOS), set(unittest.defaultTestLoader.getTestCaseNames(SolverAmpliadoRealTests)))
        notebook = json.loads((paquete.ROOT / 'docs/entrega1/validacion_colab.ipynb').read_text(encoding='utf-8'))
        for i, celda in enumerate(notebook['cells']):
            if celda['cell_type'] == 'code':
                self.assertEqual(celda['outputs'], [])
                self.assertIsNone(celda['execution_count'])
                compile(''.join(celda['source']), f'celda_{i}', 'exec')


if __name__ == '__main__':
    unittest.main()
