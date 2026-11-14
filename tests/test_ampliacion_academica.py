"""Validadores sin solver y ensayos reales CP-SAT sujetos a admisión de 2 GiB."""
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from academico import simulacion as s
from academico import ejecucion as e
from academico.escenarios import ConsultaError
from planificacion_comercial.trazabilidad_escenarios import AlmacenEscenarios


def plan_fixture(datos, sustituta='HK-001'):
    asignaciones = {}
    for v in datos['operaciones']:
        numero = int(v['id_vuelo'].split('-')[1])
        m = sustituta if numero <= 4 else ('HK-003' if numero <= 8 else 'HK-004')
        asignaciones[v['id_vuelo']] = dict(v, aeronave=m)
    return {'asignaciones': asignaciones, 'pendientes': [],
            'diagnostico': {'estado_solver': 'FIXTURE_TEST_NO_SOLVER'}}


def guardar_fixture(raiz, datos, alterar=False):
    base, recuperada = plan_fixture(datos), plan_fixture(datos, 'HK-002')
    r = {'version': 2, 'entrada': datos, 'entrada_sha256': s.huella(datos),
         'afectada': 'HK-001', 'original': base, 'recuperada': recuperada,
         'comparacion': s.comparar(datos, base, recuperada, 'HK-001')}
    if alterar:
        r['comparacion'][0]['sustituta'] = 'HK-050'
    registro = AlmacenEscenarios(raiz / 'ejecuciones').iniciar(
        entradas={'simulacion': datos}, parametros={'perfil_solver': 'AMPLIADO_V2', 'afectada': 'HK-001'},
        procedencia={'tipo_datos': 'SINTETICO', 'origen': 'FIXTURE_TEST_NO_SOLVER'})
    registro.cerrar('COMPLETA', {'publicable': True, 'simulacion': r})
    return registro.run_id, r


class AmpliacionAcademicaTests(unittest.TestCase):
    def setUp(self):
        self.datos = s.cargar_simulacion()

    def test_inventario_completo_solo_cuatro_activas(self):
        self.assertEqual(len(self.datos['operaciones']), 12)
        self.assertEqual(len(self.datos['inventario']['regulares']), 47)
        self.assertEqual(len(self.datos['inventario']['reservas']), 3)
        self.assertEqual(len(self.datos['activas']), 4)
        self.assertTrue(s.validar_plan(self.datos, plan_fixture(self.datos)))

    def test_entrada_rechaza_fuera_de_alcance(self):
        for campo, valor in [('version', 1), ('tipo_datos', 'OPERACIONAL'),
                             ('aeropuertos', ['BOG', 'MDE', 'CLO', 'CTG', 'MIA']),
                             ('operaciones', self.datos['operaciones'] + [self.datos['operaciones'][0]])]:
            with self.subTest(campo=campo):
                datos = deepcopy(self.datos); datos[campo] = valor
                with self.assertRaises(ConsultaError):
                    s.validar_entrada(datos)

    def test_reserva_no_puede_activarse(self):
        self.datos['activas']['HK-020'] = self.datos['activas']['HK-001']
        with self.assertRaises(ConsultaError):
            s.validar_entrada(self.datos)

    def test_sin_zona_y_fuera_jornada_se_rechazan(self):
        for horario in ('2026-11-14T08:00:00', '2026-11-15T08:00:00+00:00'):
            datos = deepcopy(self.datos); datos['operaciones'][0]['salida_utc'] = horario
            with self.assertRaises(ConsultaError):
                s.validar_entrada(datos)

    def test_bloqueada_y_regular_inactiva_se_rechazan(self):
        plan = plan_fixture(self.datos)
        with self.assertRaises(ConsultaError):
            s.validar_plan(self.datos, plan, ['HK-001'])
        plan['asignaciones']['AMP-01']['aeronave'] = 'HK-050'
        with self.assertRaises(ConsultaError):
            s.validar_plan(self.datos, plan)

    def test_ubicacion_inicial_y_disponibilidad_son_efectivas(self):
        for campo, valor in [('ubicacion', 'CTG'), ('disponible_desde', '2026-11-14T08:01:00+00:00')]:
            datos = deepcopy(self.datos); datos['activas']['HK-001'][campo] = valor
            with self.assertRaises(ConsultaError):
                s.validar_plan(datos, plan_fixture(datos))

    def test_transito_59_rechaza_y_60_acepta(self):
        self.assertTrue(s.validar_plan(self.datos, plan_fixture(self.datos)))
        self.datos['operaciones'][1]['salida_utc'] = '2026-11-14T09:59:00+00:00'
        with self.assertRaises(ConsultaError):
            s.validar_plan(self.datos, plan_fixture(self.datos))

    def test_solapamiento_y_teletransporte_se_rechazan(self):
        for i in ('AMP-05', 'AMP-06'):
            plan = plan_fixture(self.datos)
            plan['asignaciones'][i]['aeronave'] = 'HK-001'
            with self.assertRaises(ConsultaError):
                s.validar_plan(self.datos, plan)

    def test_solucion_parcial_y_vacia_validas_sin_inventar_asignaciones(self):
        ids = sorted(v['id_vuelo'] for v in self.datos['operaciones'])
        self.assertTrue(s.validar_plan(self.datos, {'asignaciones': {}, 'pendientes': ids}))
        with self.assertRaises(ConsultaError):
            s.validar_plan(self.datos, {'asignaciones': {}, 'pendientes': ids[:-1]})
        with self.assertRaises(ConsultaError):
            s.validar_plan(self.datos, {'asignaciones': {}, 'pendientes': ids + ids[:1]})

    def test_comparacion_identifica_sustitucion_real_y_cancelacion(self):
        base, recuperada = plan_fixture(self.datos), plan_fixture(self.datos, 'HK-002')
        filas = s.comparar(self.datos, base, recuperada, 'HK-001')
        self.assertEqual(sum(f['cambio'] for f in filas), 4)
        self.assertEqual({f['sustituta'] for f in filas if f['afectado_directo']}, {'HK-002'})
        recuperada = {'asignaciones': {}, 'pendientes': sorted(base['asignaciones'])}
        filas = s.comparar(self.datos, base, recuperada, 'HK-001')
        self.assertTrue(all(f['sustituta'] is None for f in filas))

    def test_huella_independiente_del_orden_de_claves(self):
        self.assertEqual(s.huella(self.datos), s.huella(dict(reversed(list(self.datos.items())))))

    def test_recuperacion_real_fixture_y_comparacion_falsificada(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            run_id, esperado = guardar_fixture(raiz, self.datos)
            self.assertEqual(s.consultar_simulacion(run_id, raiz / 'ejecuciones'), esperado)
            alterado, _ = guardar_fixture(raiz, self.datos, alterar=True)
            with self.assertRaises(ConsultaError):
                s.consultar_simulacion(alterado, raiz / 'ejecuciones')

    def test_worker_recuperador_v2_real_sin_solver(self):
        with tempfile.TemporaryDirectory(prefix='SkyRiskLab-academico-') as temporal:
            raiz = Path(temporal); (raiz / 'control').mkdir()
            run_id, esperado = guardar_fixture(raiz, self.datos)
            config = {'token_sha256': hashlib.sha256(b'fixture').hexdigest(),
                      'entrada_sha256': s.huella(self.datos),
                      'solicitud': {'entrada': self.datos, 'afectada': 'HK-001'}}
            (raiz / 'control' / 'configuracion.json').write_text(json.dumps(config), encoding='utf-8')
            memoria = type('Memoria', (), {'available': 512 * e.MIB})()
            with patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
                 patch.object(e.psutil, 'virtual_memory', return_value=memoria):
                r = e._proceso('recuperador', raiz, 'fixture', run_id=run_id)
            self.assertEqual(r['resultado'], esperado)
            self.assertEqual(r['hash_escenario'], s.huella(esperado))
            # Una salida íntegra de otro incidente tampoco satisface la solicitud.
            for extension in ('json', 'stderr'):
                archivo = raiz / 'control' / f'recuperador.{extension}'
                archivo.rename(archivo.with_name(f'primera-recuperacion.{extension}'))
            config['solicitud']['afectada'] = 'HK-003'
            (raiz / 'control' / 'configuracion.json').write_text(json.dumps(config), encoding='utf-8')
            with patch.object(e, 'evaluar_admision', return_value={'admitido': True}), \
                 patch.object(e.psutil, 'virtual_memory', return_value=memoria):
                with self.assertRaisesRegex(e.EjecucionError, 'solicitud ampliada'):
                    e._proceso('recuperador', raiz, 'fixture', run_id=run_id)


class SolverAmpliadoRealTests(unittest.TestCase):
    def setUp(self):
        admision = e.evaluar_admision()
        if not admision['admitido']:
            self.skipTest('CP-SAT real bloqueado por admisión: ' + ', '.join(admision['motivos']))
        self.datos = s.cargar_simulacion()

    def test_12_atendidos_y_sustitucion_observable(self):
        base = s.resolver(self.datos)
        recuperada = s.resolver(self.datos, ['HK-001'], referencia=base)
        self.assertEqual(len(base['asignaciones']), 12)
        self.assertEqual(len(recuperada['asignaciones']), 12)
        self.assertEqual(base['diagnostico']['estado_solver'], 'OPTIMAL')
        filas = s.comparar(self.datos, base, recuperada, 'HK-001')
        self.assertTrue(any(f['afectado_directo'] and f['cambio'] for f in filas))
        self.assertNotIn('HK-001', {v['aeronave'] for v in recuperada['asignaciones'].values()})

    def test_falta_aeronave_en_clo_produce_pendiente(self):
        r = s.resolver(self.datos, ['HK-003'])
        self.assertIn('AMP-05', r['pendientes'])
        self.assertTrue(s.validar_plan(self.datos, r, ['HK-003']))

    def test_todas_bloqueadas_solucion_vacia_optima(self):
        r = s.resolver(self.datos, list(self.datos['activas']))
        self.assertEqual(r['asignaciones'], {})
        self.assertEqual(len(r['pendientes']), 12)
        self.assertEqual(r['diagnostico']['estado_solver'], 'OPTIMAL')

    def test_optimo_contra_enumeracion_independiente(self):
        datos = deepcopy(self.datos)
        datos['operaciones'] = datos['operaciones'][:3]
        datos['activas'] = {'HK-001': datos['activas']['HK-001']}
        posibles = []
        for seleccion in itertools.product((False, True), repeat=3):
            asignados = {v['id_vuelo']: dict(v, aeronave='HK-001')
                         for v, elegido in zip(datos['operaciones'], seleccion) if elegido}
            plan = {'asignaciones': asignados, 'pendientes': [v['id_vuelo'] for v in datos['operaciones'] if v['id_vuelo'] not in asignados]}
            try:
                s.validar_plan(datos, plan)
            except ConsultaError:
                continue
            posibles.append(len(asignados))
        self.assertEqual(len(s.resolver(datos)['asignaciones']), max(posibles))

    def test_supervisor_productor_recuperador_v2_completo(self):
        r = e.ejecutar_simulacion(self.datos, 'HK-001')
        self.assertEqual(len(r['resultado']['recuperada']['asignaciones']), 12)
        self.assertEqual(r['hash_escenario'], s.huella(r['resultado']))
        self.assertEqual(r['almacen'], 'TEMPORAL_ELIMINADO_AL_FINALIZAR')

    def test_original_dos_trayectos_real_se_conserva(self):
        r = e.ejecutar_interactivo()
        self.assertEqual(len(r['resultado']['escenario']['confirmados']), 2)
        self.assertEqual(r['resultado']['diagnosticos'][0]['estado_solver'], 'OPTIMAL')


if __name__ == '__main__':
    unittest.main()
