"""Experimento de aprendizaje supervisado sobre simulaciones, nunca vuelos reales.

Importar este módulo no importa Scikit-learn, genera datos ni entrena modelos.
"""
from datetime import date, timedelta
import hashlib
import json
import random
import time

SEMILLA = 20261114
NUMERICAS = ['hora_programada', 'congestion_prevista', 'viento_previsto', 'lluvia_prevista']
CATEGORICAS = ['origen', 'destino']
CARACTERISTICAS = NUMERICAS + CATEGORICAS


def generar_datos(semilla=SEMILLA):
    rng = random.Random(semilla)
    aeropuertos = ['BOG', 'MDE', 'CLO', 'CTG']
    filas = []
    for dia in range(100):
        grupo = (date(2026, 1, 1) + timedelta(days=dia)).isoformat()
        for _ in range(10):
            origen, destino = rng.sample(aeropuertos, 2)
            hora = rng.randint(6, 20)
            congestion = rng.uniform(0, 10)
            viento = rng.uniform(0, 20)
            lluvia = rng.randint(0, 1)
            # Mecanismo sintético v1 con ruido irreducible, explícito y revisable.
            retraso = max(0, 3 + 1.7 * congestion + .6 * viento + 7 * lluvia
                          + (4 if hora in (7, 8, 17, 18) else 0)
                          + (2 if origen == 'BOG' else 0) + rng.gauss(0, 3))
            filas.append({'dia': grupo, 'origen': origen, 'destino': destino,
                          'hora_programada': hora, 'congestion_prevista': congestion,
                          'viento_previsto': viento, 'lluvia_prevista': lluvia,
                          'retraso_minutos': retraso})
    return filas


def entrenar_evaluar(semilla=SEMILLA):
    # Comparte la exclusión del servidor con CP-SAT; no compite con otro ensayo.
    from academico.ejecucion import _exclusion_ensayo
    with _exclusion_ensayo():
        return _entrenar_evaluar(semilla)


def _entrenar_evaluar(semilla):
    import psutil
    if psutil.virtual_memory().available < 256 * 1024 ** 2:
        raise RuntimeError('RAM insuficiente para el experimento ML sin CP-SAT (mínimo 256 MiB).')
    inicio = time.perf_counter()
    # Imports solo por acción explícita; ninguna conexión al optimizador.
    import pandas as pd
    import sklearn
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import Ridge
    from sklearn.dummy import DummyRegressor
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.metrics import mean_absolute_error
    from threadpoolctl import threadpool_limits
    filas = generar_datos(semilla)
    datos = pd.DataFrame(filas)
    x, y = datos[CARACTERISTICAS], datos['retraso_minutos']
    particion = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=semilla)
    entrenamiento, prueba = next(particion.split(x, y, groups=datos['dia']))
    dias_train = sorted(set(datos.iloc[entrenamiento]['dia']))
    dias_test = sorted(set(datos.iloc[prueba]['dia']))
    if set(dias_train) & set(dias_test):
        raise RuntimeError('Fuga de grupos entre entrenamiento y prueba')
    preprocesador = ColumnTransformer([
        ('numericas', StandardScaler(), NUMERICAS),
        ('categoricas', OneHotEncoder(handle_unknown='ignore'), CATEGORICAS)])
    modelo = Pipeline([('preprocesamiento', preprocesador), ('ridge', Ridge(alpha=1, solver='lsqr'))])
    referencia = DummyRegressor(strategy='mean')
    with threadpool_limits(limits=1):
        modelo.fit(x.iloc[entrenamiento], y.iloc[entrenamiento])
        referencia.fit(x.iloc[entrenamiento], y.iloc[entrenamiento])
        predicciones = modelo.predict(x.iloc[prueba]).clip(min=0)
        base = referencia.predict(x.iloc[prueba])
    resultado = {'tipo_datos': 'SINTETICO', 'generador': 'RETRASOS_V1',
        'advertencia': 'Aprende sobre datos simulados. No validado para vuelos reales. No modifica CP-SAT.',
        'semilla': semilla, 'sklearn': sklearn.__version__, 'registros': len(filas),
        'entrenamiento': len(entrenamiento), 'prueba': len(prueba),
        'dias_entrenamiento': dias_train, 'dias_prueba': dias_test,
        'caracteristicas': CARACTERISTICAS,
        'datos_sha256': hashlib.sha256(json.dumps(filas, sort_keys=True).encode()).hexdigest(),
        'mae_ridge_minutos': float(mean_absolute_error(y.iloc[prueba], predicciones)),
        'mae_dummy_minutos': float(mean_absolute_error(y.iloc[prueba], base)),
        'ejemplos_prueba': [{'real': float(real), 'predicho': float(predicho)}
                            for real, predicho in zip(y.iloc[prueba][:10], predicciones[:10])],
        'wall_s': time.perf_counter() - inicio,
        'rss_final_bytes': psutil.Process().memory_info().rss}
    return resultado
