"""Empaqueta bytes del árbol académico actual sin Git add, commit ni publicación."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from herramientas.validadores.auditar_paquete_academico import ROOT, PERMITIDOS, _ruta_segura, auditar

MANIFIESTO = 'MANIFIESTO_COLAB.json'
RAMA = 'desarrollo/ampliacion-academica'


def sha(datos):
    return hashlib.sha256(datos).hexdigest()


def snapshot_id(archivos):
    return sha(json.dumps(archivos, sort_keys=True, separators=(',', ':')).encode())


def crear_paquete(raiz, destino, revision):
    raiz, destino = Path(raiz), Path(destino)
    informe = auditar(raiz)
    if not informe['paquete_preparado_para_revision']:
        raise ValueError('El paquete de trabajo no supera la revisión de inclusión/contenido')
    contenido = {n: _ruta_segura(raiz, n).read_bytes() for n in sorted(PERMITIDOS)}
    archivos = {n: {'sha256': sha(b), 'bytes': len(b)} for n, b in contenido.items()}
    manifiesto = {'formato': 1, 'rama': RAMA, 'revision_base': revision,
                  'fuente': 'ARBOL_DE_TRABAJO_NO_ES_UN_COMMIT_DE_LA_AMPLIACION',
                  'snapshot_id': snapshot_id(archivos), 'archivos': archivos,
                  'dependencias_cpsat': ['ortools==9.15.6755', 'pandas==3.0.0', 'psutil==7.2.2']}
    requisitos = contenido['requirements.txt'].decode('utf-8-sig').splitlines()
    if any(pin not in requisitos for pin in manifiesto['dependencias_cpsat']):
        raise ValueError('Los pins mínimos no coinciden con requirements.txt')
    # No sobrescribir evidencia ni archivos de otros paquetes.
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        miembros = dict(contenido)
        miembros[MANIFIESTO] = json.dumps(manifiesto, ensure_ascii=False, sort_keys=True, indent=2).encode()
        for nombre, datos in miembros.items():
            info = zipfile.ZipInfo(nombre, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, datos)
    return manifiesto, sha(destino.read_bytes())


def verificar_paquete(ruta, esperado):
    """Verifica antes de extraer; nunca ejecuta código del ZIP."""
    ruta = Path(ruta)
    if ruta.stat().st_size > 20 * 1024 ** 2 or sha(ruta.read_bytes()) != esperado:
        raise ValueError('SHA-256 de ZIP incorrecto o tamaño excesivo')
    with zipfile.ZipFile(ruta) as z:
        infos = z.infolist()
        nombres = [i.filename for i in infos]
        if len(nombres) != len(set(nombres)) or len(nombres) > 128:
            raise ValueError('Miembros duplicados o excesivos')
        if sum(i.file_size for i in infos) > 20 * 1024 ** 2:
            raise ValueError('Paquete descomprimido excesivo')
        for nombre in nombres:
            p = PurePosixPath(nombre)
            if p.is_absolute() or '..' in p.parts or '\\' in nombre or ':' in nombre:
                raise ValueError('Ruta ZIP no permitida')
        if any(i.is_dir() or (i.external_attr >> 16) & 0o170000 == 0o120000 for i in infos):
            raise ValueError('Directorios o enlaces ZIP no permitidos')
        m = json.loads(z.read(MANIFIESTO))
        if (m['formato'] != 1 or m['rama'] != RAMA or m['snapshot_id'] != snapshot_id(m['archivos'])
                or set(nombres) != set(m['archivos']) | {MANIFIESTO}):
            raise ValueError('Manifiesto inconsistente')
        for nombre, registro in m['archivos'].items():
            bruto = z.read(nombre)
            if len(bruto) != registro['bytes'] or sha(bruto) != registro['sha256']:
                raise ValueError('Contenido distinto del snapshot: ' + nombre)
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    rama = subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current']).decode().strip()
    if rama != RAMA:
        raise SystemExit('Preparar únicamente desde ' + RAMA)
    revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip()
    m, huella = crear_paquete(ROOT, args.salida, revision)
    verificar_paquete(args.salida, huella)
    print(json.dumps({'zip': str(args.salida), 'sha256_zip': huella,
                      'snapshot_id': m['snapshot_id'], 'archivos': len(m['archivos']),
                      'revision_base': revision, 'rama': rama}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
