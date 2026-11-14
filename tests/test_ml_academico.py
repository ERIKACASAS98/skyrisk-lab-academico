"""Entrenamiento real pequeño; sin solver ni archivos de modelos ejecutables."""
import math
import unittest

from academico.ml_retrasos import generar_datos, entrenar_evaluar, CARACTERISTICAS


class MLAcademicoTests(unittest.TestCase):
    def test_ml_no_compite_con_otro_ensayo(self):
        from academico.ejecucion import _exclusion_ensayo, EjecucionError
        with _exclusion_ensayo():
            with self.assertRaisesRegex(EjecucionError, 'EN_CURSO'):
                entrenar_evaluar()

    def test_generacion_reproducible_mil_registros(self):
        a, b = generar_datos(), generar_datos()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 1000)
        self.assertNotEqual(a, generar_datos(7))
        self.assertEqual(len({v['dia'] for v in a}), 100)

    def test_objetivo_y_dia_no_son_caracteristicas(self):
        self.assertNotIn('retraso_minutos', CARACTERISTICAS)
        self.assertNotIn('dia', CARACTERISTICAS)
        self.assertTrue(all(f['retraso_minutos'] >= 0 and f['origen'] != f['destino'] for f in generar_datos()))

    def test_entrenamiento_evaluacion_reales_sin_fuga(self):
        r = entrenar_evaluar()
        self.assertEqual((r['entrenamiento'], r['prueba']), (800, 200))
        self.assertFalse(set(r['dias_entrenamiento']) & set(r['dias_prueba']))
        self.assertTrue(math.isfinite(r['mae_ridge_minutos']))
        self.assertGreater(r['mae_ridge_minutos'], 0)
        self.assertLess(r['mae_ridge_minutos'], r['mae_dummy_minutos'])
        print('ML_RESULTADO_REAL', {k:r[k] for k in ('semilla', 'datos_sha256', 'mae_ridge_minutos', 'mae_dummy_minutos', 'wall_s', 'rss_final_bytes')})


if __name__ == '__main__':
    unittest.main()
