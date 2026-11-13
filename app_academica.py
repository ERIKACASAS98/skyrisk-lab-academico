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

    st.markdown("#### ✈ Programación de trayectos")

    st.dataframe(
        operaciones,
        hide_index=True,
        width="stretch",
        column_config={
            "id_vuelo": st.column_config.TextColumn("Identificador"),
            "tipo": st.column_config.TextColumn("Tipo"),
            "origen": st.column_config.TextColumn("Origen"),
            "destino": st.column_config.TextColumn("Destino"),
            "salida_utc": st.column_config.TextColumn("Salida (UTC)"),
            "llegada_utc": st.column_config.TextColumn("Llegada (UTC)"),
            "ruta_maestra": st.column_config.TextColumn("Ruta"),
            "operacion_origen": st.column_config.TextColumn("Operación de origen"),
        },
    )

    st.caption(f'{len(operaciones)} trayectos visibles. Todos los horarios incluyen zona UTC.')

    st.markdown("#### Parámetros del escenario")

    limites = datos['limites_ensayo']

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Trayectos", limites["trayectos"])
    col2.metric("Candidatos máximos", limites["candidatos_maximos"])
    col3.metric("Tránsito mínimo", f'{limites["transito_minutos"]} min')
    col4.metric("Tiempo de optimización", f'{limites["solver_segundos"]} s')

    st.caption(f"Perfil del ensayo: {datos['perfil_propuesto']}")

    with st.expander("Configuración técnica completa"):
        st.json(limites)

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

    st.caption('Perfil de optimización: ORIGINAL · 4 trabajadores')

    limites = datos['limites_ensayo']

    col1, col2, col3, col4 = st.columns(4, gap='medium')

    col1.metric('✈ Trayectos', limites['trayectos'])
    col2.metric('◈ Candidatos máximos', limites['candidatos_maximos'])
    col3.metric('◷ Tránsito mínimo', f"{limites['transito_minutos']} min")
    col4.metric('◴ Tiempo del solver', f"{limites['solver_segundos']} s")

    with st.expander('Ver configuración técnica completa'):
        st.json(limites)


    st.markdown("#### Motor de optimización CP-SAT")

    if admision["admitido"]:
        st.success(
            "🟢 SISTEMA DISPONIBLE · Recursos suficientes. "
            "La optimización comenzará únicamente cuando autorices la ejecución."
        )
    else:
        st.warning(
            "🟡 SISTEMA EN ESPERA · Optimización deshabilitada: "
            + ", ".join(admision["motivos"])
        )

        with st.expander("Consultar motivos de la restricción"):
            for motivo in admision["motivos"]:
                st.write(f"• {motivo}")

    st.caption(
        "El sistema verifica los recursos antes de ejecutar CP-SAT. "
        "No se generan resultados simulados para reemplazar una ejecución real."
    )

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

    st.markdown(
        """
<div style="background: linear-gradient(110deg, #14263B, #0B1C30); border: 1px solid #24445D; border-radius: 16px; padding: 30px 34px; margin-bottom: 24px;">
    <div style="color: #38BDF8; font-size: 12px; letter-spacing: 3px; font-weight: 700;">
        ✈ AVIATION INTELLIGENCE PLATFORM
    </div>
    <h1 style="color: #F1F5F9; font-size: 38px; margin: 12px 0 8px 0;">
        SkyRisk Lab
    </h1>
    <p style="color: #A8BED3; font-size: 16px; margin: 0;">
        Centro de inteligencia y optimización de operaciones aéreas
    </p>
    <div style="margin-top: 22px; color: #7F9BB5; font-size: 12px;">
        DEMOSTRADOR ACADÉMICO · ENTREGA 1 · NOVIEMBRE 2026
<br>
<span style="color: #CBD5E1; font-size: 13px;">
    Desarrollado por: Erika Liliana Casas Toro · Viana Maria Ruiz Ruiz
</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

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
            
        st.markdown("### Centro de control operacional")
        st.caption(
            "Visión general del escenario académico de planificación aérea."
        )

        col1, col2, col3 = st.columns(3, gap="medium")

        col1.metric(
            "✈ Trayectos programados",
            len(datos["operaciones"])
        )
        col2.metric(
            "◈ Aeronaves regulares",
            len(datos["flota"]["regulares"])
        )
        col3.metric(
            "◇ Reservas excluidas",
            len(datos["flota"]["reservas"])
        )

        st.divider()

        izquierda, derecha = st.columns([3, 2], gap="large")

        with izquierda:
            st.markdown("#### Inteligencia operacional")
            st.write(
                "SkyRisk Lab utiliza optimización matemática mediante "
                "OR-Tools CP-SAT para evaluar asignaciones de aeronaves "
                "respetando restricciones operacionales."
            )

            st.markdown("**Restricciones consideradas**")
            st.write(
                "Continuidad física, tiempos mínimos de tránsito, "
                "mantenimiento y compromisos protegidos."
            )

            st.info(
                "El demostrador utiliza datos sintéticos. "
                "No representa operaciones reales de una aerolínea."
            )

        with derecha:
            st.markdown("#### Estado del demostrador")

            admision_resumen = evaluar_admision()

            if admision_resumen["admitido"]:
                st.success("Motor CP-SAT disponible para ejecución autorizada.")
            else:
                st.warning(
    "Motor CP-SAT en espera de recursos suficientes. "
    "El primer ensayo CP-SAT requiere autorización expresa "
    "y al menos 2 GiB de memoria libre."
)

            st.caption(
                "La optimización requiere confirmación explícita. "
                "No se presentan resultados inventados."
            )

        with st.expander("Alcance y evidencia técnica"):
            st.write(
                "La auditoría profesional previa fue aceptada con 112 pruebas. "
                "Los 12 casos de seguridad del paso 1 se prepararon "
                "sin ejecutarse por falta de RAM."
            )
            st.write(
                "La validación del visor se documenta en "
                "docs/entrega1/validacion.md."
            )
            st.write(
                "GitHub público, compatibilidad Linux y despliegue "
                "cloud pendientes de verificación."
            )
            st.caption(
                "El demostrador académico no declara terminada "
                "la plataforma profesional SkyRisk Lab V5.2."
            )


# Lista explícita: Streamlit ignora el directorio pages/ profesional.
pagina = st.navigation([st.Page(mostrar_demostrador, title='Demostrador académico', default=True)])
pagina.run()
