"""Demostrador académico: optimización explícita y consulta sintética."""
from __future__ import annotations

import streamlit as st

from academico.escenarios import (
    ConsultaError, PersistenciaError, cargar_entradas, consultar_escenario,
    listar_escenarios, texto_json,
)
from academico.ejecucion import EjecucionError, evaluar_admision, ejecutar_interactivo


st.set_page_config(page_title='SkyRisk Lab | Entrega 1', page_icon=':material/flight:', layout='wide')


def mostrar_caso(datos, sha):
    st.subheader('Caso sintético de validación')
    st.info('Estas son entradas de prueba. Todavía no representan asignaciones obtenidas por CP-SAT.')
    origen = st.selectbox('Aeropuerto de origen', ['Todos', 'BOG', 'MDE'], key='origen_academico')
    operaciones = [v for v in datos['operaciones'] if origen == 'Todos' or v['origen'] == origen]
    st.dataframe(operaciones, hide_index=True, width='stretch')
    st.caption(f'{len(operaciones)} trayectos visibles. Todos los horarios incluyen zona UTC.')
    st.write('Perfil propuesto para el ensayo:', datos['perfil_propuesto'])
    st.json(datos['limites_ensayo'])
    st.caption('El tránsito del ejemplo es de 60 minutos. Las tres reservas están excluidas de la programación base.')
    with st.expander('Inventario sintético y evidencia de entrada'):
        st.write('Regulares:', ', '.join(datos['flota']['regulares']))
        st.write('Reservas excluidas:', ', '.join(datos['flota']['reservas']))
        st.code(sha, language=None)
    st.download_button('Descargar entradas sintéticas', texto_json(datos),
                       file_name='skyrisk_entradas_sinteticas.json', mime='application/json')


def mostrar_resultados():
    st.subheader('Resultados y trazabilidad')
    try:
        ids = listar_escenarios()
        if not ids:
            st.warning('SIN_EJECUCION: no hay escenarios comerciales sintéticos publicados en este demostrador.')
            st.write('El ensayo de dos trayectos está pendiente. Su ejecución requiere al menos 2 GiB de RAM libre y autorización.')
            st.caption('Aquí aparecerán los resultados íntegros cuando exista una ejecución aprobada. No se calcula cobertura sin resultados.')
            return
        elegido = st.selectbox('Ejecución sintética', ids, key='run_academico')
        with st.spinner('Verificando integridad del escenario...'):
            r = consultar_escenario(elegido)
        st.write('run_id:', r['run_id'])
        st.write('Estado archivado:', r['estado'], '| Fuente:', r['fuente'])
        st.caption('Integridad verificada mediante hashes. Esta comprobación no certifica una operación real.')
        if not r['publicable']:
            st.warning('Evidencia parcial: este checkpoint no equivale a una ejecución completa publicable.')
        st.write('Perfil archivado:', r['parametros']['perfil_solver'])
        st.json(r['parametros'].get('configuracion_solver', {}))
        if r['escenario'] is not None:
            for grupo, titulo in (('confirmados', 'Asignaciones confirmadas'),
                                  ('protegidos', 'Compromisos protegidos'),
                                  ('propuestas', 'Propuestas revisables')):
                st.write(titulo)
                st.dataframe(list(r['escenario'].get(grupo, {}).values()), hide_index=True, width='stretch')
        for grupo in ('pendientes', 'estado_inicial_incompleto'):
            st.write(grupo.replace('_', ' ').capitalize())
            st.dataframe(r['resultados_individuales'].get(grupo, []), hide_index=True, width='stretch')
        with st.expander('Diagnósticos, eventos y hashes'):
            st.dataframe(r['diagnosticos'], hide_index=True, width='stretch')
            st.dataframe(r['eventos'], hide_index=True, width='stretch')
            st.json(r['hashes'])
            st.caption(f"Tamaño verificado: {r['bytes']:,} bytes.")
        st.download_button('Descargar resumen consultado', texto_json(r),
                           file_name=f"{r['run_id']}-consulta.json", mime='application/json')
    except (ConsultaError, PersistenciaError, OSError, ValueError, KeyError, TypeError) as error:
        st.error('No se puede consultar este escenario de forma segura: ' + str(error))


def mostrar_resultado_interactivo(historico):
    r = historico['resultado']
    st.success('Resultado validado y recuperado desde un proceso independiente.')
    st.write('run_id:', historico['run_id'])
    st.caption('HISTÓRICO DE SESIÓN · se conserva si una ejecución posterior falla.')
    diagnosticos = r.get('diagnosticos', [])
    diagnostico = diagnosticos[-1] if diagnosticos else {}
    a, b, c, d = st.columns(4)
    a.metric('Asignaciones', len(r['escenario']['confirmados']))
    b.metric('Objetivo', diagnostico.get('objetivo', 'No disponible'))
    c.metric('Cota', diagnostico.get('cota', 'No disponible'))
    d.metric('Solver', diagnostico.get('estado_solver', 'No disponible'))
    st.dataframe(list(r['escenario']['confirmados'].values()), hide_index=True, width='stretch')
    st.write('Diagnóstico y parámetros efectivos')
    st.json(diagnostico)
    with st.expander('Recursos, recuperación e integridad'):
        st.json({'productor': historico['productor'], 'recuperador': historico['recuperador'],
                 'supervision_productor': historico['supervision_productor'],
                 'supervision_recuperador': historico['supervision_recuperador'],
                 'wall_total_s': historico['wall_total_s'],
                 'hash_escenario': historico['hash_escenario'],
                 'admision': historico['admision']})
    st.download_button('Descargar resultado validado', texto_json(historico),
                       file_name=f"{historico['run_id']}-resultado.json", mime='application/json')


def mostrar_optimizacion(datos):
    st.subheader('Optimización interactiva')
    st.selectbox('Escenario sintético', [datos['id_escenario']], key='escenario_optimizar_academico')
    admision = evaluar_admision()
    st.write('Perfil:', 'ORIGINAL · 4 trabajadores · 30 s de solver')
    st.json(datos['limites_ensayo'])
    if admision['admitido']:
        st.success('Recursos admitidos. La optimización solo comenzará al pulsar el botón.')
    else:
        st.warning('Optimización deshabilitada: ' + ', '.join(admision['motivos']))
    with st.expander('Comprobación de recursos'):
        st.json(admision)
        st.caption('Los límites son supervisados. La cancelación cooperativa no garantiza una terminación forzada.')
    with st.form('formulario_optimizacion_academica', border=False):
        confirmado = st.checkbox('Confirmo que ejecutaré únicamente el caso sintético de dos trayectos.',
                                  key='confirmar_optimizacion_academica')
        ejecutar = st.form_submit_button('Optimizar', icon=':material/play_arrow:', type='primary',
                                         disabled=not admision['admitido'])
    if ejecutar and not confirmado:
        st.session_state['ultimo_error_optimizacion_academica'] = 'Debe confirmar el alcance sintético antes de ejecutar.'
    elif ejecutar:
        try:
            with st.spinner('Ejecutando CP-SAT, validando y recuperando el escenario...'):
                nuevo = ejecutar_interactivo()
            st.session_state['ultimo_resultado_academico_valido'] = nuevo
            st.session_state.pop('ultimo_error_optimizacion_academica', None)
        except (EjecucionError, OSError, ValueError, RuntimeError) as error:
            st.session_state['ultimo_error_optimizacion_academica'] = str(error)
    error = st.session_state.get('ultimo_error_optimizacion_academica')
    if error:
        st.error('La ejecución nueva no se publicó: ' + error)
        if st.session_state.get('ultimo_resultado_academico_valido'):
            st.info('Se conserva y muestra el último histórico válido de esta sesión.')
    historico = st.session_state.get('ultimo_resultado_academico_valido')
    if historico:
        mostrar_resultado_interactivo(historico)
    else:
        st.caption('Aún no existe un resultado CP-SAT válido en esta sesión.')


def mostrar_demostrador():
    st.title('SkyRisk Lab')
    st.caption('Entrega 1 · Taller ABP de Introducción a la Inteligencia Artificial · 16 de noviembre de 2026')
    st.write('Planificación comercial de aeronaves mediante optimización con restricciones y resultados trazables.')
    try:
        datos, sha = cargar_entradas()
    except (ConsultaError, OSError, ValueError, KeyError, TypeError) as error:
        st.error('No se pudo cargar el caso sintético: ' + str(error))
        return
    vista = st.segmented_control('Vista académica', ['Resumen', 'Caso sintético', 'Optimización', 'Consulta histórica'],
                                default='Resumen', key='vista_academica')
    if vista == 'Caso sintético':
        mostrar_caso(datos, sha)
    elif vista == 'Consulta histórica':
        mostrar_resultados()
    elif vista == 'Optimización':
        mostrar_optimizacion(datos)
    else:
        a, b, c = st.columns(3)
        a.metric('Trayectos del caso', len(datos['operaciones']))
        b.metric('Aeronaves regulares', len(datos['flota']['regulares']))
        c.metric('Reservas excluidas', len(datos['flota']['reservas']))
        st.info('La optimización solo se inicia desde el botón explícito y después de superar la admisión de recursos.')
        st.write('El componente de IA existente utiliza OR-Tools CP-SAT para seleccionar trayectos compatibles con continuidad física, tránsito, mantenimiento y compromisos protegidos.')
        st.write('Las cuatro rutas especiales BOG–MIA, MDE–MIA, MDE–PTY y MDE–SDQ conservan 60–120 minutos totales en tierra y no permiten pernocta comercial programada.')
        st.warning('El primer ensayo CP-SAT aún requiere autorización expresa. No se presentan asignaciones ni porcentajes de cobertura inventados.')
        with st.expander('Alcance y evidencia disponible'):
            st.write('La auditoría profesional previa fue aceptada con 112 pruebas. Los 12 casos de seguridad del paso 1 se prepararon sin ejecutarse por falta de RAM.')
            st.write('La validación de este visor se documenta por separado en docs/entrega1/validacion.md.')
            st.write('Publicación GitHub, instalación Linux y despliegue cloud real pendientes de verificación y autorización.')
            st.caption('El demostrador académico no declara terminada SkyRisk Lab V5.2.')


# Lista explícita: Streamlit ignora el directorio pages/ profesional.
pagina = st.navigation([st.Page(mostrar_demostrador, title='Demostrador académico', default=True)])
pagina.run()
