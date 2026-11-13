"""Auditoría de solo lectura de la lista pública académica.

No inicializa Git, no añade archivos, no publica, no escribe manifiestos y no
accede a SQLite. --indice requiere Git y un repositorio ya existente. La revisión
automática es una barrera adicional: no sustituye revisión humana ni autorización.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
PERMITIDOS = frozenset({
    '.streamlit/config.toml', 'docs/evidencias/evidencia_cpsat_publica.json',
    '.gitignore', 'README.md', 'app_academica.py', 'requirements.txt',
    'academico/__init__.py', 'academico/escenarios.py',
    'academico/ejecucion.py', 'academico/worker.py',
    'demo/README.md', 'demo/entradas_paso1.json', 'demo/escenarios/.gitkeep',
    'docs/entrega1/arquitectura.md', 'docs/entrega1/compatibilidad_cloud.md',
    'docs/entrega1/investigacion.md', 'docs/entrega1/presentacion.md',
    'docs/entrega1/validacion.md',
    'docs/entrega1/plan_optimizacion_interactiva.md',
    'herramientas/validadores/auditar_paquete_academico.py',
    'planificacion_comercial/__init__.py',
    'planificacion_comercial/trazabilidad_escenarios.py',
    'tests/test_app_academica.py', 'tests/test_escenarios_academicos.py',
    'tests/test_ejecucion_academica.py',
    'tests/test_publicacion_academica.py',
})
MAX_ARCHIVO = 5 * 1024 * 1024
MAX_PAQUETE = 20 * 1024 * 1024
PATRONES = (
    ('CLAVE_PRIVADA', re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----')),
    ('TOKEN_GITHUB', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b')),
    ('CLAVE_ACCESO_AWS', re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('TOKEN_SLACK', re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b')),
    ('CREDENCIAL_LITERAL', re.compile(
        r'''(?im)\b(?:password|passwd|api_key|secret_key|access_token|client_secret)\b\s*[:=]\s*["']([^"'\r\n]{12,})["']''')),
    ('RUTA_PERSONAL_WINDOWS', re.compile(r'(?i)[A-Z]:[\\/]+Users[\\/]+(?!<|usuario\b|user\b)[^\\/\s"\']+')),
)


def reglas_gitignore():
    """La lista de archivos es exacta; no habilita nuevos runs ni carpetas completas."""
    directorios = set()
    for nombre in PERMITIDOS:
        padre = Path(nombre).parent
        while padre != Path('.'):
            directorios.add(padre.as_posix())
            padre = padre.parent
    ordenados = sorted(directorios, key=lambda s: (s.count('/'), s))
    # Al permitir un directorio, volver a denegar su contenido antes de admitir
    # nombres exactos; no depender de la herencia de patrones de Git.
    reglas_directorios = [regla for d in ordenados for regla in ('!/' + d + '/', '/' + d + '/**')]
    return ['/**', *reglas_directorios,
            *['!/' + n for n in sorted(PERMITIDOS)]]


def hallazgos_texto(nombre, contenido):
    """Nunca devuelve credenciales, fragmentos ni valores detectados."""
    hallazgos = []
    try:
        texto = contenido.decode('utf-8-sig')
    except UnicodeDecodeError:
        return [{'archivo': nombre, 'tipo': 'CONTENIDO_NO_UTF8'}]
    for tipo, patron in PATRONES:
        for coincidencia in patron.finditer(texto):
            # Los marcadores de documentación no son credenciales reales.
            if tipo == 'CREDENCIAL_LITERAL':
                valor = coincidencia.group(1)
                if any(p in valor.lower() for p in ('<', 'placeholder', 'ejemplo', 'example', 'reemplazar')):
                    continue
            hallazgos.append({'archivo': nombre, 'tipo': tipo,
                             'linea': texto.count('\n', 0, coincidencia.start()) + 1})
    if contenido.startswith(b'SQLite format 3\x00'):
        hallazgos.append({'archivo': nombre, 'tipo': 'SQLITE_PROHIBIDA'})
    if nombre == 'docs/evidencias/evidencia_cpsat_publica.json':
        # Copia revisada, normalizando solo CRLF/LF para Git Windows/Linux.
        # Cambiar esta huella requiere revisar de nuevo la evidencia completa.
        if hashlib.sha256(contenido.replace(b'\r\n', b'\n')).hexdigest() != '088c2a6099402224170b23b36e695d457968e387a38c336338214b508b05460c':
            hallazgos.append({'archivo': nombre, 'tipo': 'EVIDENCIA_DIFIERE_DE_COPIA_REVISADA'})
    if nombre == 'demo/entradas_paso1.json':
        try:
            datos = json.loads(texto)
            if (not isinstance(datos, dict) or datos.get('tipo_datos') != 'SINTETICO'
                    or datos.get('estado_ejecucion') != 'SIN_EJECUCION'
                    or 'resultados' not in datos or datos['resultados'] is not None):
                hallazgos.append({'archivo': nombre, 'tipo': 'DEMO_NO_DECLARADA_COMO_ENTRADA_SINTETICA_SIN_RESULTADOS'})
        except (ValueError, TypeError):
            hallazgos.append({'archivo': nombre, 'tipo': 'JSON_DEMO_INVALIDO'})
    return hallazgos


def _ruta_segura(raiz, nombre):
    raiz = Path(raiz).absolute()
    partes = Path(nombre).parts
    if nombre not in PERMITIDOS or Path(nombre).is_absolute() or '..' in partes:
        raise ValueError('Ruta fuera de la lista pública')
    ruta = raiz
    for parte in ('', *partes):
        if parte:
            ruta = ruta / parte
        if ruta.is_symlink() or ruta.is_junction():
            raise ValueError('Enlace o junction en una ruta pública')
    if not ruta.resolve().is_relative_to(raiz.resolve()):
        raise ValueError('Ruta fuera de la raíz del paquete')
    return ruta


def _git(git, raiz, argumentos):
    entorno = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    resultado = subprocess.run([git, '-C', str(raiz), *argumentos],
                               capture_output=True, timeout=10, check=False,
                               env=entorno, shell=False)
    if resultado.returncode != 0:
        # No divulgar stderr ni configuraciones del usuario.
        raise ValueError('Git no pudo completar la consulta de solo lectura')
    return resultado.stdout


def auditar_indice(raiz, inventario):
    git = shutil.which('git')
    if not git:
        return {'estado': 'NO_VERIFICABLE_SIN_GIT', 'hallazgos': [], 'apto': False}
    try:
        raiz_git = Path(_git(git, raiz, ['rev-parse', '--show-toplevel']).decode('utf-8').strip()).resolve()
        if raiz_git != Path(raiz).resolve():
            raise ValueError('La raíz Git no coincide con la del paquete')
        entradas = _git(git, raiz, ['ls-files', '--stage', '-z']).split(b'\x00')
        hallazgos, seguidos, total = [], [], 0
        por_nombre = {p['archivo']: p for p in inventario}
        for entrada in entradas:
            if not entrada:
                continue
            cabecera, nombre_bruto = entrada.split(b'\t', 1)
            modo, objeto, etapa = cabecera.decode('ascii').split()
            nombre = nombre_bruto.decode('utf-8')
            seguidos.append(nombre)
            if nombre not in PERMITIDOS:
                hallazgos.append({'archivo': nombre, 'tipo': 'ARCHIVO_SEGUIDO_NO_PERMITIDO'})
                continue
            if modo not in {'100644', '100755'} or etapa != '0':
                hallazgos.append({'archivo': nombre, 'tipo': 'MODO_O_ETAPA_GIT_NO_PERMITIDOS'})
                continue
            longitud = int(_git(git, raiz, ['cat-file', '-s', objeto]).decode('ascii'))
            total += longitud
            if longitud > MAX_ARCHIVO or total > MAX_PAQUETE:
                hallazgos.append({'archivo': nombre, 'tipo': 'INDICE_EXCEDE_PRESUPUESTO'})
                break
            contenido = _git(git, raiz, ['cat-file', 'blob', objeto])
            hallazgos.extend(hallazgos_texto(nombre, contenido))
            esperado = por_nombre.get(nombre, {}).get('sha256_lf')
            if hashlib.sha256(contenido.replace(b'\r\n', b'\n')).hexdigest() != esperado:
                hallazgos.append({'archivo': nombre, 'tipo': 'INDICE_DIFIERE_DEL_ARCHIVO_REVISADO'})
        faltantes = sorted(PERMITIDOS - set(seguidos))
        return {'estado': 'REVISADO', 'seguidos': sorted(seguidos), 'faltantes': faltantes,
                'hallazgos': hallazgos, 'apto': not hallazgos and not faltantes}
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return {'estado': 'NO_VERIFICABLE_INDICE', 'hallazgos': [], 'apto': False}


def auditar(raiz=ROOT, *, revisar_indice=False):
    raiz = Path(raiz)
    inventario, faltantes, hallazgos, total = [], [], [], 0
    politica = 'FALTA'
    for nombre in sorted(PERMITIDOS):
        try:
            ruta = _ruta_segura(raiz, nombre)
            if not ruta.is_file():
                faltantes.append(nombre)
                continue
            longitud = ruta.stat().st_size
            total += longitud
            if longitud > MAX_ARCHIVO or total > MAX_PAQUETE:
                hallazgos.append({'archivo': nombre, 'tipo': 'PAQUETE_EXCEDE_PRESUPUESTO'})
                continue
            contenido = ruta.read_bytes()
            inventario.append({'archivo': nombre, 'bytes': len(contenido),
                               'sha256': hashlib.sha256(contenido).hexdigest(),
                               'sha256_lf': hashlib.sha256(contenido.replace(b'\r\n', b'\n')).hexdigest()})
            hallazgos.extend(hallazgos_texto(nombre, contenido))
            if nombre == '.gitignore':
                reglas = [l.strip() for l in contenido.decode('utf-8-sig').splitlines()
                          if l.strip() and not l.lstrip().startswith('#')]
                politica = 'COINCIDE_LISTA_EXPLICITA' if reglas == reglas_gitignore() else 'DIFIERE'
                if politica == 'DIFIERE':
                    hallazgos.append({'archivo': nombre, 'tipo': 'POLITICA_GITIGNORE_DISTINTA'})
        except (OSError, ValueError, UnicodeError):
            hallazgos.append({'archivo': nombre, 'tipo': 'RUTA_NO_SEGURA_O_NO_LEGIBLE'})
    indice = auditar_indice(raiz, inventario) if revisar_indice else {
        'estado': 'NO_REVISADO', 'apto': False,
        'nota': 'Solicitar --indice cuando exista un repositorio Git; .gitignore no retira archivos ya seguidos.'}
    return {
        'modo': 'PREPARACION_SOLO_LECTURA', 'publicacion_autorizada': False,
        'inventario': inventario, 'bytes_totales_leidos': total,
        'faltantes': faltantes, 'hallazgos': hallazgos, 'politica_gitignore': politica,
        'paquete_preparado_para_revision': not faltantes and not hallazgos,
        'indice': indice,
        'limites': {'archivo_bytes': MAX_ARCHIVO, 'paquete_bytes': MAX_PAQUETE},
        'limitacion': 'El escaneo no demuestra ausencia total de secretos ni verifica GitHub, historial Git o despliegue.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz', type=Path, default=ROOT)
    parser.add_argument('--indice', action='store_true', help='Revisar el índice real con Git existente; no lo modifica')
    args = parser.parse_args(argv)
    resultado = auditar(args.raiz, revisar_indice=args.indice)
    print(json.dumps(resultado, ensure_ascii=False, sort_keys=True, indent=2))
    correcto = resultado['paquete_preparado_para_revision'] and (
        not args.indice or resultado['indice']['apto'])
    return 0 if correcto else 1


if __name__ == '__main__':
    raise SystemExit(main())
