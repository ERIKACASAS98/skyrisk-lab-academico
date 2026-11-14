"""Preflight por defecto; --ejecutar realiza solo los seis tests CP-SAT existentes.

No modifica el solver, los tests, cgroups ni umbrales. Nunca parchea admisión.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from academico.ejecucion import evaluar_admision

METODOS = (
    'test_12_atendidos_y_sustitucion_observable',
    'test_falta_aeronave_en_clo_produce_pendiente',
    'test_todas_bloqueadas_solucion_vacia_optima',
    'test_optimo_contra_enumeracion_independiente',
    'test_supervisor_productor_recuperador_v2_completo',
    'test_original_dos_trayectos_real_se_conserva',
)


def verificar_snapshot(raiz=ROOT):
    raiz = Path(raiz)
    m = json.loads((raiz / 'MANIFIESTO_COLAB.json').read_text(encoding='utf-8'))
    identidad = hashlib.sha256(json.dumps(m['archivos'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if identidad != m['snapshot_id'] or m['rama'] != 'desarrollo/ampliacion-academica':
        raise ValueError('Identidad de snapshot inválida')
    for nombre, registro in m['archivos'].items():
        ruta = raiz / nombre
        if not ruta.resolve().is_relative_to(raiz.resolve()) or ruta.is_symlink():
            raise ValueError('Ruta de snapshot inválida')
        datos = ruta.read_bytes()
        if len(datos) != registro['bytes'] or hashlib.sha256(datos).hexdigest() != registro['sha256']:
            raise ValueError('El snapshot cambió: ' + nombre)
    return m


def ejecutar_seis():
    # Importar la clase no importa OR-Tools ni ejecuta el solver.
    sys.path.insert(0, str(ROOT / 'tests'))
    from test_ampliacion_academica import SolverAmpliadoRealTests
    registros, texto = [], io.StringIO()
    for metodo in METODOS:
        admision = evaluar_admision()
        registro = {'prueba': metodo, 'admision_antes': admision, 'estado': 'NO_EJECUTADA'}
        registros.append(registro)
        if not admision['admitido']:
            registro['estado'] = 'BLOQUEADA_POR_ADMISION'
            break  # No forzar ni continuar consumiendo recursos.
        inicio = time.perf_counter()
        resultado = unittest.TextTestRunner(stream=texto, verbosity=2).run(
            unittest.TestSuite([SolverAmpliadoRealTests(metodo)]))
        registro.update({'wall_s': time.perf_counter() - inicio,
                         'tests_ejecutados': resultado.testsRun,
                         'fallos': len(resultado.failures), 'errores': len(resultado.errors),
                         'omitidas': len(resultado.skipped),
                         'estado': 'APROBADA' if resultado.wasSuccessful() and not resultado.skipped else 'NO_APROBADA'})
        if not resultado.wasSuccessful() or resultado.skipped:
            break
    aprobadas = len(registros) == 6 and all(r['estado'] == 'APROBADA' for r in registros)
    return registros, texto.getvalue(), aprobadas


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.salida.exists():
        raise SystemExit('No sobrescribir informes: use otro directorio de salida')
    args.salida.mkdir(parents=True)
    informe = {'formato': 1, 'fecha_utc': datetime.now(timezone.utc).isoformat(),
               'python': platform.python_version(), 'sistema': platform.system(),
               'cp_sat_ejecutado': False, 'seis_aprobadas': False, 'estado': 'NO_EJECUTADO',
               'pruebas': [], 'pendientes': list(METODOS)}
    codigo = 2
    log = ''
    try:
        if sys.version_info < (3, 12):
            raise ValueError('Se necesita Python >=3.12 para las APIs de rutas del proyecto')
        m = verificar_snapshot()
        informe['snapshot_id'] = m['snapshot_id']
        informe['revision_base'] = m['revision_base']
        informe['rama'] = m['rama']
        informe['dependencias'] = {d.metadata['Name']: d.version for d in metadata.distributions()}
        for especificacion in m['dependencias_cpsat']:
            nombre, version = especificacion.split('==')
            if metadata.version(nombre) != version:
                raise ValueError('Versión distinta del snapshot: ' + nombre)
        informe['admision_inicial'] = evaluar_admision()
        if not informe['admision_inicial']['admitido']:
            informe['estado'] = 'BLOQUEADO_POR_ADMISION'
        elif not args.ejecutar:
            informe['estado'] = 'PREFLIGHT_LISTO_NO_EJECUTADO'
            codigo = 0
        else:
            informe['estado'] = 'EJECUCION_INICIADA_SIN_RESULTADO'
            registros, log, aprobadas = ejecutar_seis()
            informe['pruebas'] = registros
            # Un error puede ocurrir antes o dentro del solver: no inventar certeza.
            informe['cp_sat_ejecutado'] = (True if any(r['estado'] == 'APROBADA' for r in registros)
                else None if any(r.get('tests_ejecutados', 0) > r.get('omitidas', 0) for r in registros)
                else False)
            informe['seis_aprobadas'] = aprobadas
            informe['pendientes'] = [m for m in METODOS if not any(r['prueba'] == m and r['estado'] == 'APROBADA' for r in registros)]
            informe['estado'] = 'SEIS_APROBADAS' if aprobadas else 'VALIDACION_INCOMPLETA'
            codigo = 0 if aprobadas else 1
        verificar_snapshot()  # Detectar alteraciones durante el ensayo.
        informe['snapshot_verificado_al_final'] = True
    except KeyboardInterrupt:
        informe.update({'estado': 'INTERRUMPIDA_SIN_VALIDACION_COMPLETA', 'seis_aprobadas': False,
                        'cp_sat_ejecutado': None})
        codigo = 130
    except Exception as error:
        informe.update({'estado': 'ERROR_DE_VALIDACION', 'seis_aprobadas': False,
                        'pendientes': list(METODOS),
                        'error': type(error).__name__ + ': ' + str(error)})
        codigo = 1
    finally:
        (args.salida / 'resultado.json').write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding='utf-8')
        (args.salida / 'unittest.log').write_text(log, encoding='utf-8')
    print(json.dumps({'estado': informe['estado'], 'seis_aprobadas': informe['seis_aprobadas'],
                      'salida': str(args.salida)}, ensure_ascii=False))
    return codigo


if __name__ == '__main__':
    raise SystemExit(main())
