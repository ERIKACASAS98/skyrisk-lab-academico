"""Revisión de la lista pública con fixtures temporales; nunca publica."""
from contextlib import redirect_stdout
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from herramientas.validadores import auditar_paquete_academico as a


class PublicacionAcademicaTests(unittest.TestCase):
    def preparar(self, raiz):
        for nombre in a.PERMITIDOS:
            p = raiz / nombre
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('Contenido académico de prueba.\n', encoding='utf-8')
        (raiz / '.gitignore').write_text('\n'.join(a.reglas_gitignore()) + '\n', encoding='utf-8')
        (raiz / 'demo/entradas_paso1.json').write_text(json.dumps({
            'tipo_datos': 'SINTETICO', 'estado_ejecucion': 'SIN_EJECUCION', 'resultados': None}), encoding='utf-8')
        nombre = 'docs/evidencias/evidencia_cpsat_publica.json'
        (raiz / nombre).write_bytes((a.ROOT / nombre).read_bytes())

    def test_evidencia_revisada_pasa_y_alteracion_se_rechaza(self):
        nombre = 'docs/evidencias/evidencia_cpsat_publica.json'
        contenido = (a.ROOT / nombre).read_bytes()
        self.assertEqual(a.hallazgos_texto(nombre, contenido), [])
        self.assertEqual(a.hallazgos_texto(nombre, contenido.replace(b'\r\n', b'\n')), [])
        self.assertTrue(a.hallazgos_texto(nombre, contenido + b'\n'))
        self.assertIn('.streamlit/config.toml', a.PERMITIDOS)
        from academico.escenarios import cargar_evidencia_colab, ConsultaError
        evidencia = cargar_evidencia_colab()
        self.assertEqual(evidencia['resultado']['resultado']['diagnosticos'][0]['estado_solver'], 'OPTIMAL')
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'alterada.json'
            ruta.write_bytes(contenido + b'\n')
            with self.assertRaises(ConsultaError):
                cargar_evidencia_colab(ruta)
            ruta.write_bytes(contenido.replace(b'\r\n', b'\n'))
            self.assertEqual(cargar_evidencia_colab(ruta), evidencia)

    def test_lista_excluye_operacional_historial_respaldos_y_paginas(self):
        for nombre in ('app.py', 'data/skyrisk_operacion.db', 'pages/Planificacion_Comercial.py',
                       'backups/respaldo.db', '.streamlit/secrets.toml', 'docs/auditoria_continuidad_v52.md'):
            self.assertNotIn(nombre, a.PERMITIDOS)
        self.assertIn('app_academica.py', a.PERMITIDOS)
        self.assertFalse(any('/SRL-COM-' in n for n in a.PERMITIDOS))

    def test_directorios_no_habilitan_sus_archivos_arbitrariamente(self):
        reglas = a.reglas_gitignore()
        self.assertEqual(reglas[0], '/**')
        for i, regla in enumerate(reglas):
            if regla.startswith('!/') and regla.endswith('/'):
                self.assertEqual(reglas[i + 1], regla[1:] + '**')

    def test_tokens_detectados_sin_revelar_su_valor(self):
        token = 'ghp_' + 'z' * 36  # Token artificial construido solo para la prueba.
        resultado = a.hallazgos_texto('prueba.txt', token.encode())
        self.assertEqual(resultado[0]['tipo'], 'TOKEN_GITHUB')
        self.assertNotIn(token, str(resultado))

    def test_base_sqlite_no_es_contenido_publicable(self):
        resultado = a.hallazgos_texto('prueba', b'SQLite format 3\x00')
        self.assertIn('SQLITE_PROHIBIDA', {r['tipo'] for r in resultado})

    def test_json_solo_admite_entradas_sinteticas_sin_resultados(self):
        for tipo, resultados in (('OPERACIONAL', None), ('MIXTO', None), ('SINTETICO', {'inventado': True})):
            contenido = json.dumps({'tipo_datos': tipo, 'estado_ejecucion': 'SIN_EJECUCION',
                                    'resultados': resultados}).encode()
            self.assertTrue(a.hallazgos_texto('demo/entradas_paso1.json', contenido))

    def test_inventario_hace_hashes_sin_afirmar_autorizacion_o_indice(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self.preparar(raiz)
            antes = {str(p): p.read_bytes() for p in raiz.rglob('*') if p.is_file()}
            r = a.auditar(raiz)
            self.assertTrue(r['paquete_preparado_para_revision'], r)
            self.assertFalse(r['publicacion_autorizada'])
            self.assertEqual(r['indice']['estado'], 'NO_REVISADO')
            self.assertEqual(len(r['inventario']), len(a.PERMITIDOS))
            self.assertTrue(all(len(p['sha256']) == 64 for p in r['inventario']))
            self.assertEqual(antes, {str(p): p.read_bytes() for p in raiz.rglob('*') if p.is_file()})

    def test_politica_distinta_o_archivo_faltante_impiden_aceptar_paquete(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self.preparar(raiz)
            (raiz / '.gitignore').write_text('*.db\n', encoding='utf-8')
            self.assertFalse(a.auditar(raiz)['paquete_preparado_para_revision'])
            (raiz / 'README.md').unlink()
            self.assertIn('README.md', a.auditar(raiz)['faltantes'])

    def test_presupuesto_y_enlaces_se_rechazan(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self.preparar(raiz)
            with patch.object(a, 'MAX_ARCHIVO', 1):
                self.assertFalse(a.auditar(raiz)['paquete_preparado_para_revision'])
            with patch.object(Path, 'is_symlink', return_value=True):
                self.assertFalse(a.auditar(raiz)['paquete_preparado_para_revision'])

    def test_indice_sin_git_no_se_declara_verificado(self):
        with patch.object(a.shutil, 'which', return_value=None):
            r = a.auditar_indice(Path('.'), [])
        self.assertEqual(r['estado'], 'NO_VERIFICABLE_SIN_GIT')
        self.assertFalse(r['apto'])

    def test_indice_normaliza_solo_crlf_y_detecta_cambios_reales(self):
        raiz = a.ROOT
        inventario = [{'archivo': 'README.md',
                       'sha256_lf': hashlib.sha256(b'contenido\n').hexdigest()}]
        def git_simulado(git, ruta, argumentos):
            if argumentos[0] == 'rev-parse':
                return str(raiz).encode('utf-8')
            if argumentos[0] == 'ls-files':
                return b'100644 abc 0\tREADME.md\0'
            if argumentos[1] == '-s':
                return b'11'
            return b'contenido\r\n'
        with patch.object(a.shutil, 'which', return_value='git'), \
             patch.object(a, '_git', side_effect=git_simulado):
            self.assertEqual(a.auditar_indice(raiz, inventario)['hallazgos'], [])
            inventario[0]['sha256_lf'] = hashlib.sha256(b'cambio real\n').hexdigest()
            r = a.auditar_indice(raiz, inventario)
            self.assertIn('INDICE_DIFIERE_DEL_ARCHIVO_REVISADO', {h['tipo'] for h in r['hallazgos']})


if __name__ == '__main__':
    unittest.main()
