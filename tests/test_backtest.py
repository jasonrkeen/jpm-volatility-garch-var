import contextlib
import io
import math
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

import garch_var_model as model


class BacktestTests(unittest.TestCase):
    def setUp(self):
        self.returns = pd.Series(
            np.random.default_rng(173).normal(0.0004, 0.015, 255),
            index=pd.bdate_range('2020-01-01', periods=255),
        )

    def run_quietly(self, function, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return function(*args, **kwargs)

    def test_historical_threshold_uses_only_preceding_window(self):
        r = pd.Series([-.04, -.02, 0, .02, .04, -.99])
        threshold = self.run_quietly(model.run_historical_var, r, 'test', window=5)[0]
        self.assertAlmostEqual(threshold.iloc[0], -3.6)
        self.assertEqual(threshold.index.tolist(), [5])

    def test_target_and_future_changes_cannot_change_current_forecasts(self):
        changed = self.returns.copy()
        changed.iloc[253:] = [.07, -.09]
        for function, position in [(model.run_garch_var, 1), (model.run_historical_var, 0)]:
            before = self.run_quietly(function, self.returns, 'before')[position]
            after = self.run_quietly(function, changed, 'after')[position]
            pd.testing.assert_series_equal(before.iloc[:4], after.iloc[:4])

    def test_models_share_evaluation_dates_and_realized_returns(self):
        g = self.run_quietly(model.run_garch_var, self.returns, 'garch')
        h = self.run_quietly(model.run_historical_var, self.returns, 'historical')
        pd.testing.assert_series_equal(g[2], h[1])
        self.assertEqual(len(g[2]), 5)
        self.assertEqual(g[1].index[0], self.returns.index[250])
        self.assertTrue(np.isfinite(g[1]).all())

    def test_garch_forecast_matches_independent_single_training_fit(self):
        from arch import arch_model
        from statistics import NormalDist
        r = self.returns.iloc[:251]
        fit = arch_model(r.iloc[:250] * 100, mean='Constant', vol='Garch',
                         p=1, q=1, dist='normal', rescale=False).fit(disp='off')
        forecast = fit.forecast(horizon=1, reindex=False)
        expected = forecast.mean.iloc[-1, 0] + NormalDist().inv_cdf(.05) * math.sqrt(forecast.variance.iloc[-1, 0])
        actual = self.run_quietly(model.run_garch_var, r, 'test')[1].iloc[0]
        self.assertAlmostEqual(actual, expected)

    def test_kupiec_finite_boundary_likelihoods(self):
        self.assertAlmostEqual(model.kupiec_lr(0, 10), -20 * math.log(.95))
        self.assertAlmostEqual(model.kupiec_lr(10, 10), -20 * math.log(.05))
        self.assertAlmostEqual(model.kupiec_lr(5, 100), 0)
        with self.assertRaises(ValueError):
            model.kupiec_lr(0, 0)

    def test_invalid_inputs_fail_before_fitting(self):
        for r in [self.returns.iloc[:250], self.returns.iloc[::-1],
                  pd.concat([self.returns, self.returns.iloc[-1:]])]:
            with self.assertRaises(ValueError):
                model.run_garch_var(r, 'invalid')
        r = self.returns.copy()
        r.iloc[-1] = np.nan
        with self.assertRaises(ValueError):
            model.run_historical_var(r, 'missing')
        with self.assertRaises(ValueError):
            model.run_historical_var(self.returns, 'window', window=0)

    def test_failed_optimizer_is_not_counted_as_valid_forecast(self):
        fake = MagicMock()
        fake.fit.return_value.convergence_flag = 1
        with patch.object(model, 'arch_model', return_value=fake):
            with self.assertRaisesRegex(RuntimeError, 'did not converge'):
                model.run_garch_var(self.returns, 'failure')


if __name__ == '__main__':
    unittest.main()
