"""Demostrador académico: optimización explícita y consulta sintética."""
from __future__ import annotations

import streamlit as st

from academico.escenarios import (
    ConsultaError, PersistenciaError, cargar_entradas, consultar_escenario,
    listar_escenarios, texto_json, cargar_evidencia_colab,
)
from academico.ejecucion import EjecucionError, evaluar_admision, ejecutar_interactivo, ejecutar_simulacion
from academico.simulacion import cargar_simulacion


st.set_page_config(page_title='SkyRisk Lab | Entrega 1', page_icon=':material/flight:', layout='wide')


def mostrar_caso(datos, sha):
    st.subheader('Caso sintético de validación')
    st.caption('Caso original de dos trayectos conservado para validación.')
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

    st.download_button('Descargar entradas sintéticas', texto_json(datos),
                       file_name='skyrisk_entradas_sinteticas.json', mime='application/json')


def mostrar_resultados():
    st.subheader('Resultados y trazabilidad')
    try:
        ids = listar_escenarios()
        if not ids:
            st.warning('SIN_EJECUCION: no hay ejecuciones completas archivadas en este catálogo.')
            st.caption('La evidencia de Colab se conserva por separado como histórico.')
            mostrar_evidencia_colab()
            return
        elegido = st.selectbox('Ejecución sintética', ids, key='run_academico')
        with st.spinner('Verificando integridad del escenario...'):
            r = consultar_escenario(elegido)
        st.write('run_id:', r['run_id'])
        st.write('Estado archivado:', r['estado'], '| Fuente:', r['fuente'])
        st.caption('Integridad verificada mediante hashes. Esta comprobación no certifica una operación real.')
        if not r['publicable']:
            st.warning('Evidencia parcial: este checkpoint no equivale a una ejecución completa publicable.')
        if r['escenario'] is not None:
            for grupo, titulo in (('confirmados', 'Asignaciones confirmadas'),
                                  ('protegidos', 'Compromisos protegidos'),
                                  ('propuestas', 'Propuestas revisables')):
                st.write(titulo)
                st.dataframe(list(r['escenario'].get(grupo, {}).values()), hide_index=True, width='stretch')
        for grupo in ('pendientes', 'estado_inicial_incompleto'):
            st.write(grupo.replace('_', ' ').capitalize())
            st.dataframe(r['resultados_individuales'].get(grupo, []), hide_index=True, width='stretch')
        st.download_button('Descargar resumen consultado', texto_json(r),
                           file_name=f"{r['run_id']}-consulta.json", mime='application/json')
        mostrar_evidencia_colab()
    except (ConsultaError, PersistenciaError, OSError, ValueError, KeyError, TypeError) as error:
        st.error('No se puede consultar este escenario de forma segura: ' + str(error))


def mostrar_evidencia_colab():
    with st.expander('Evidencia histórica de Google Colab · 13/11/2026'):
        try:
            evidencia = cargar_evidencia_colab()
            r = evidencia['resultado']
            st.info('HISTÓRICO COLAB · no es una ejecución nueva desde Streamlit.')
            st.write('run_id:', r['run_id'])
            st.dataframe(list(r['resultado']['escenario']['confirmados'].values()),
                         hide_index=True, width='stretch')
            st.caption('Huella de la copia revisada y hash del escenario comprobados. '
                       'El resumen no contiene los archivos originales para revalidar toda la cadena de eventos.')
            st.download_button('Descargar evidencia histórica Colab', texto_json(evidencia),
                               file_name='evidencia_colab_historica.json', mime='application/json')
        except (OSError, ValueError, KeyError, TypeError) as error:
            st.error('Evidencia histórica no verificable: ' + str(error))


def mostrar_resultado_interactivo(historico):
    r = historico['resultado']
    st.success('Resultado validado y recuperado desde un proceso independiente.')
    st.write('run_id:', historico['run_id'])
    st.caption('HISTÓRICO DE SESIÓN · se conserva si una ejecución posterior falla.')
    st.caption('El almacén temporal se elimina al finalizar. Descargue el resultado; '
               'la sesión no es almacenamiento durable y no alimenta el catálogo de runs.')
    diagnosticos = r.get('diagnosticos', [])
    diagnostico = diagnosticos[-1] if diagnosticos else {}
    a, b, c, d = st.columns(4)
    a.metric('Asignaciones', len(r['escenario']['confirmados']))
    b.metric('Objetivo', diagnostico.get('objetivo', 'No disponible'))
    c.metric('Cota', diagnostico.get('cota', 'No disponible'))
    d.metric('Solver', diagnostico.get('estado_solver', 'No disponible'))
    st.dataframe(list(r['escenario']['confirmados'].values()), hide_index=True, width='stretch')
    st.download_button('Descargar resultado validado', texto_json(historico),
                       file_name=f"{historico['run_id']}-resultado.json", mime='application/json')


def mostrar_optimizacion(datos):
    st.subheader('Optimización interactiva')
    st.selectbox('Escenario sintético', [datos['id_escenario']], key='escenario_optimizar_academico')
    admision = evaluar_admision()

    mostrar_disponibilidad(admision)
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


def mostrar_simulacion(datos):
    st.subheader('Planificar los 12 trayectos y resolver una contingencia')
    st.dataframe(datos['operaciones'], hide_index=True, width='stretch')
    st.write('Ubicaciones y disponibilidad de las aeronaves activas')
    st.dataframe([dict(aeronave=m, **estado) for m, estado in datos['activas'].items()], hide_index=True, width='stretch')
    admision = evaluar_admision()
    mostrar_disponibilidad(admision)
    with st.form('contingencia_ampliada'):
        afectada = st.selectbox('Aeronave indisponible durante toda la jornada', sorted(datos['activas']), key='afectada_ampliada')
        confirmado = st.checkbox('Confirmo la simulación sintética y la contingencia de jornada completa.', key='confirmar_ampliada')
        ejecutar = st.form_submit_button('Planificar y recuperar', disabled=not admision['admitido'])
    if ejecutar:
        if not confirmado:
            st.error('Confirme el alcance de la simulación antes de ejecutar.')
        else:
            try:
                with st.spinner('Resolviendo planificación base y contingencia...'):
                    nuevo = ejecutar_simulacion(datos, afectada)
                st.session_state['simulacion_ampliada_valida'] = nuevo
                st.session_state.pop('error_ampliada', None)
            except (OSError, ValueError, RuntimeError, PersistenciaError) as error:
                st.session_state['error_ampliada'] = str(error)
    if st.session_state.get('error_ampliada'):
        st.error('Nueva simulación fallida: ' + st.session_state['error_ampliada'])
        if st.session_state.get('simulacion_ampliada_valida'):
            st.info('Se conserva el último resultado válido de esta sesión.')
    historico = st.session_state.get('simulacion_ampliada_valida')
    if historico:
        r = historico['resultado']
        st.caption('HISTÓRICO DE SESIÓN · cambiar la selección no vuelve a ejecutar el solver. '
                   'El temporal se elimina al finalizar; descargue el resultado para conservarlo.')
        st.write('run_id:', historico['run_id'], '| Aeronave afectada en este resultado:', r['afectada'])
        if r['afectada'] != afectada:
            st.info('El resultado mostrado corresponde a otra aeronave. Ejecute de nuevo para actualizarlo.')
        a, b, c = st.columns(3)
        a.metric('Atendidos originales', len(r['original']['asignaciones']))
        b.metric('Atendidos recuperados', len(r['recuperada']['asignaciones']))
        c.metric('Pendientes recuperados', len(r['recuperada']['pendientes']))
        st.dataframe(r['comparacion'], hide_index=True, width='stretch')
        st.write('Pendientes:', r['recuperada']['pendientes'])
        st.download_button('Descargar simulación validada', texto_json(historico),
                           file_name=f"{historico['run_id']}-ampliada.json", mime='application/json')
    else:
        st.caption('Aún no hay un resultado validado de los 12 trayectos en esta sesión.')


def mostrar_ml():
    st.subheader('Predicción académica de minutos de retraso')
    st.caption('Estime minutos de retraso. La predicción no cambia la planificación de aeronaves.')
    if st.button('Evaluar predicción de retrasos', key='entrenar_ml'):
        try:
            from academico.ml_retrasos import entrenar_evaluar
            with st.spinner('Entrenando y evaluando sobre días separados...'):
                st.session_state['ml_academico_valido'] = entrenar_evaluar()
            st.session_state.pop('error_ml', None)
        except (ImportError, OSError, ValueError, RuntimeError) as error:
            st.session_state['error_ml'] = str(error)
    if st.session_state.get('error_ml'):
        st.error('Experimento ML no completado: ' + st.session_state['error_ml'])
    r = st.session_state.get('ml_academico_valido')
    if r:
        st.caption('Resultado del último entrenamiento explícito de esta sesión.')
        a, b = st.columns(2)
        a.metric('Error medio de predicción (min)', f"{r['mae_ridge_minutos']:.3f}")
        b.metric('Error medio de referencia (min)', f"{r['mae_dummy_minutos']:.3f}")
        st.dataframe(r['ejemplos_prueba'], hide_index=True, width='stretch')
        st.download_button('Descargar evaluación ML', texto_json(r), file_name='evaluacion_ml_sintetica.json', mime='application/json')


def mostrar_disponibilidad(admision):
    if admision['admitido']:
        st.success('Recursos disponibles. Confirme la ejecución para obtener un resultado.')
    else:
        mensajes = {
            'RAM_HOST_MENOR_2_GIB': 'Se requieren al menos 2 GiB de memoria libre.',
            'RAM_CONTENEDOR_MENOR_2_GIB': 'La memoria disponible del servidor es insuficiente.',
            'ENSAYO_ACADEMICO_EN_CURSO': 'Hay otra ejecución en curso.',
            'LIMITE_CONTENEDOR_NO_VERIFICABLE': 'No se pudo verificar la memoria del servidor.',
            'ESCENARIO_FUERA_DE_ALCANCE': 'El caso original no cumple los controles de integridad.',
        }
        st.warning('Optimización deshabilitada. ' + ' '.join(
            mensajes.get(m, m) for m in admision['motivos']))


def mostrar_trayectos(datos):
    st.subheader('Los 12 trayectos de la jornada')
    origen = st.selectbox('Aeropuerto de origen', ['Todos', *sorted(datos['aeropuertos'])],
                          key='origen_ampliado')
    filas = [v for v in datos['operaciones'] if origen == 'Todos' or v['origen'] == origen]
    st.dataframe(filas, hide_index=True, width='stretch', column_config={
        'id_vuelo': 'Trayecto', 'origen': 'Origen', 'destino': 'Destino',
        'salida_utc': 'Salida (UTC)', 'llegada_utc': 'Llegada (UTC)'})
    st.caption(f"{len(filas)} de {len(datos['operaciones'])} trayectos visibles. Horarios en UTC.")


def mostrar_validacion():
    st.subheader('Validación técnica · caso original de 2 trayectos')
    seccion = st.selectbox('Consultar', ['Caso original', 'Ejecutar caso original', 'Consulta histórica'],
                           key='seccion_validacion')
    if seccion == 'Consulta histórica':
        mostrar_resultados()
    else:
        datos, sha = cargar_entradas()
        if seccion == 'Caso original':
            mostrar_caso(datos, sha)
        else:
            mostrar_optimizacion(datos)
    st.caption('Los parámetros, diagnósticos y comprobaciones de integridad se conservan en las descargas y la documentación del repositorio.')


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

    vista = st.segmented_control('Vista académica',
        ['Resumen', 'Trayectos', 'Planificación y contingencias', 'Validación técnica', 'Predicción de retrasos'],
        default='Resumen', key='vista_academica')
    try:
        if vista == 'Validación técnica':
            mostrar_validacion()
        elif vista == 'Predicción de retrasos':
            mostrar_ml()
        else:
            datos = cargar_simulacion()
            if vista == 'Trayectos':
                mostrar_trayectos(datos)
            elif vista == 'Planificación y contingencias':
                mostrar_simulacion(datos)
            else:
                st.subheader('Planificación de 12 trayectos nacionales')
                st.warning('El demostrador utiliza datos sintéticos. No representa operaciones reales de una aerolínea.')
                a, b, c = st.columns(3)
                a.metric('Trayectos programados', len(datos['operaciones']))
                b.metric('Aeropuertos', len(datos['aeropuertos']))
                c.metric('Aeronaves activas', len(datos['activas']))
                st.write('Consulte los trayectos y compare el plan antes y después de la indisponibilidad de una aeronave.')
                st.caption('Se respeta la continuidad de las rutas y un tránsito mínimo de 60 minutos. Las reservas están excluidas.')
                mostrar_disponibilidad(evaluar_admision())
                st.caption('Los trayectos programados son entradas. Los resultados se muestran después de ejecutar y validar el plan.')
                st.caption('El caso original de dos trayectos y su evidencia histórica están en Validación técnica.')
    except (ConsultaError, PersistenciaError, OSError, ValueError, KeyError, TypeError) as error:
        st.error('No se pudo cargar la vista de forma segura: ' + str(error))


# Lista explícita: Streamlit ignora el directorio pages/ profesional.
pagina = st.navigation([st.Page(mostrar_demostrador, title='Demostrador académico', default=True)])
pagina.run()
