"""Independent checks against the assignment before its example implementation.

The numbers used for test scenarios are synthetic, not the document's final
screenshots or its example coefficient table.  Each right-hand side below is
transcribed separately from table 2; it deliberately does not use EDGES.
"""
import math
import json
import os
import re
from contextlib import ExitStack
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from app.model import EDGES, MATRIX, MODEL, VARIABLES, derivative, perturbations
from app.services.calculation_service import build_configuration, integrate_model
from app.utils.constants import Constants


def parameters():
    return {
        "q1_a": 1.0, "q1_b": 0.0, "q1_c": 1.0, "q1_d": 0.0,
        "q2_a": 2.0, "q2_b": 0.0, "q2_c": 1.0, "q2_d": 0.0,
        "q5_a": 0.0, "q5_b": 5.0,
        "q4_steps": [{"time": 0.0, "value": 4.0}],
    }


def constant_coefficients():
    return {f"f{j}": {"A0": 1.0, "A1": 0.0, "A2": 0.0, "A3": 0.0}
            for j in range(1, 99)}


def complete_form(degree=0):
    form = {
        "t_start": "0", "t_end": "1", "polynomial_degree": str(degree),
        "q4_time_0": "0", "q4_value_0": "0.1",
        "q4_time_1": "0.45", "q4_value_1": "0.2",
    }
    for key, value in parameters().items():
        if key != "q4_steps":
            form[key] = str(value)
    for i in range(1, 16):
        form[f"L{i}"] = "0.5"
        form[f"L{i}_scale"] = "1"
        form[f"L{i}_minimum"] = "0.1"
    for j in range(1, 99):
        for k in range(degree + 1):
            form[f"f{j}_A{k}"] = "1" if k == 0 else "0.01"
    return form


class AssignmentModelTests(unittest.TestCase):
    def test_matrix_matches_all_fifteen_assignment_rows(self):
        rows = [
            "0 0 0 0 1 1 1 0 0 1 0 0 1 1 0 1 1 -1 0 0",
            "0 0 1 0 0 0 0 0 0 0 0 1 1 1 1 0 1 0 -1 1",
            "0 0 0 0 1 1 1 0 0 1 0 0 1 1 1 0 1 0 0 -1",
            "1 0 0 0 1 1 1 1 -1 1 1 0 0 1 1 0 1 0 0 0",
            "1 0 0 0 0 1 1 1 -1 1 1 0 1 0 0 1 1 1 0 0",
            "1 0 1 1 0 0 1 1 -1 0 0 0 0 0 0 1 0 1 0 0",
            "0 0 0 1 0 1 0 0 -1 0 0 0 1 1 0 0 0 1 1 0",
            "0 0 0 1 -1 1 1 0 -1 0 1 0 1 0 1 0 0 1 0 0",
            "0 0 1 -1 -1 1 -1 -1 0 -1 0 0 0 0 0 1 0 1 1 0",
            "1 0 0 0 0 1 0 0 -1 0 1 1 1 1 0 0 1 0 0 1",
            "0 0 0 1 -1 1 -1 1 0 1 0 0 1 0 0 1 0 1 0 0",
            "0 1 1 1 0 0 0 0 -1 0 0 0 0 0 0 1 1 0 0 1",
            "1 0 1 1 1 1 0 0 0 1 0 0 0 1 0 1 1 0 -1 0",
            "1 0 0 0 0 0 1 0 0 1 0 0 1 0 0 0 1 1 0 -1",
            "0 1 1 1 0 1 0 1 1 0 1 0 0 0 0 1 1 -1 0 1",
        ]
        self.assertEqual(MATRIX, [[int(v) for v in row.split()] for row in rows])
        self.assertEqual(len(VARIABLES), 15)
        self.assertEqual([edge["function"] for row in EDGES for edge in row],
                         list(range(1, 99)))
        self.assertEqual(next(e for e in EDGES[1] if e["function"] == 9)["variable"], 13)
        self.assertEqual(MATRIX[4][16], 1)  # q2 omitted in the source's L5 drawing.

    def test_fifteen_equations_with_distinct_function_arguments(self):
        y = np.arange(1, 16, dtype=float) / 20
        coefficients = {
            f"f{j}": {"A0": 1 + j / 100, "A1": 0.1, "A2": 0.03, "A3": 0.01}
            for j in range(1, 99)
        }
        p = parameters()
        p.update(q1_b=0.13, q1_c=2.3, q1_d=0.2, q2_b=0.07, q5_a=0.15)
        t = 0.73
        q1 = 1 + 0.13 * math.sin(2.3 * t + 0.2)
        q2 = 2 + 0.07 * math.sin(t)
        q3, q4, q5 = 0.3, 4, 0.15 * math.sqrt(t) + 5

        def f(j, variable):
            x = y[variable - 1]
            return 1 + j / 100 + 0.1 * x + 0.03 * x ** 2 + 0.01 * x ** 3

        expected = [
            f(1, 5)*f(2, 6)*f(3, 7)*f(4, 10)*f(5, 13)*f(6, 14)*(q1+q2)-q3,
            f(7, 3)*f(8, 12)*f(9, 13)*f(10, 14)*f(11, 15)*(q2+q5)-q4,
            f(12, 5)*f(13, 6)*f(14, 7)*f(15, 10)*f(16, 13)*f(17, 14)*f(18, 15)*q2-q5,
            f(19, 1)*f(20, 5)*f(21, 6)*f(22, 7)*f(23, 8)*f(24, 10)*f(25, 11)*f(26, 14)*f(27, 15)*q2-f(28, 9),
            f(29, 1)*f(30, 6)*f(31, 7)*f(32, 8)*f(33, 10)*f(34, 11)*f(35, 13)*(q1+q2+q3)-f(36, 9),
            f(37, 1)*f(38, 3)*f(39, 4)*f(40, 7)*f(41, 8)*(q1+q3)-f(42, 9),
            f(43, 4)*f(44, 6)*f(45, 13)*f(46, 14)*(q3+q4)-f(47, 9),
            f(48, 4)*f(49, 6)*f(50, 7)*f(51, 11)*f(52, 13)*f(53, 15)*q3-f(54, 5)*f(55, 9),
            f(56, 3)*f(57, 6)*(q1+q3+q4)-f(58, 4)*f(59, 5)*f(60, 7)*f(61, 8)*f(62, 10),
            f(63, 1)*f(64, 6)*f(65, 11)*f(66, 12)*f(67, 13)*f(68, 14)*(q2+q5)-f(69, 9),
            f(70, 4)*f(71, 6)*f(72, 8)*f(73, 10)*f(74, 13)*(q1+q3)-f(75, 5)*f(76, 7),
            f(77, 2)*f(78, 3)*f(79, 4)*(q1+q2+q5)-f(80, 9),
            f(81, 1)*f(82, 3)*f(83, 4)*f(84, 5)*f(85, 6)*f(86, 10)*f(87, 14)*(q1+q2)-q4,
            f(88, 1)*f(89, 7)*f(90, 10)*f(91, 13)*(q2+q3)-q5,
            f(92, 2)*f(93, 3)*f(94, 4)*f(95, 6)*f(96, 8)*f(97, 9)*f(98, 11)*(q1+q2+q5)-q3,
        ]
        scales = np.arange(2, 17, dtype=float)
        actual = derivative(t, y, coefficients, scales, p)
        np.testing.assert_allclose(actual, np.array(expected) / scales, rtol=1e-12)

    def test_simple_hand_calculated_derivative_and_scaling(self):
        expected = np.array([3, 3, -3, 1, 2, 0, 3, -1, 4, 6, 0, 7, -1, -3, 8], dtype=float)
        cf, p = constant_coefficients(), parameters()
        np.testing.assert_allclose(derivative(0.5, [0.5]*15, cf, [1]*15, p), expected)
        for i in range(15):
            with self.subTest(variable=i+1):
                scales = [1.0]*15
                scales[i] = 2.0
                adjusted = expected.copy()
                adjusted[i] /= 2
                np.testing.assert_allclose(derivative(0.5, [0.5]*15, cf, scales, p), adjusted)

    def test_external_function_types_and_exact_q3_steps(self):
        p = parameters()
        p.update(q1_a=0.2, q1_b=0.7, q1_c=1.3, q1_d=0.4,
                 q2_a=0.8, q2_b=0.3, q2_c=0.9, q2_d=-0.2,
                 q5_a=0.6, q5_b=0.15,
                 q4_steps=[{"time": 0, "value": 0.1}, {"time": 0.4, "value": 0.7}])
        for t, expected_q3 in [(0, 0), (0.6, 0), (0.600001, 0.3),
                               (0.8, 0.3), (0.800001, 0.4), (1.2, 0.4)]:
            with self.subTest(time=t):
                expected = [0.2+0.7*math.sin(1.3*t+0.4),
                            0.8+0.3*math.sin(0.9*t-0.2), expected_q3,
                            0.1 if t < 0.4 else 0.7, 0.6*math.sqrt(t)+0.15]
                np.testing.assert_allclose(perturbations(t, p), expected)


class RequiredInputTests(unittest.TestCase):
    def test_all_polynomial_orders_parse_and_inactive_terms_are_zero(self):
        for degree in range(4):
            with self.subTest(degree=degree):
                data = build_configuration(complete_form(degree))
                self.assertEqual(data["polynomial_degree"], degree)
                self.assertEqual(len(data["polynomial_coefficients"]), 98)
                for j in range(1, 99):
                    for k in range(4):
                        expected = 1 if k == 0 else 0.01 if k <= degree else 0
                        self.assertEqual(float(data["polynomial_coefficients"][f"f{j}"][f"A{k}"]), expected)

    def test_missing_required_values_are_not_silently_defaulted(self):
        required = ["t_start", "t_end", "polynomial_degree", "L1", "L15",
                    "L1_scale", "L15_scale", "L1_minimum", "L15_minimum",
                    "q1_a", "q1_b", "q1_c", "q1_d", "q2_a", "q2_b",
                    "q2_c", "q2_d", "q5_a", "q5_b", "q4_time_0",
                    "q4_value_0", "f1_A0", "f98_A0"]
        for key in required:
            for replacement in (None, "", "   "):
                with self.subTest(field=key, value=replacement):
                    form = complete_form()
                    if replacement is None:
                        form.pop(key)
                    else:
                        form[key] = replacement
                    with self.assertRaises(ValueError):
                        build_configuration(form)
        for degree in (1, 2, 3):
            with self.subTest(active_order=degree):
                form = complete_form(degree)
                form.pop(f"f98_A{degree}")
                with self.assertRaises(ValueError):
                    build_configuration(form)

    def test_finite_domain_and_interval_validation(self):
        invalid = {
            "t_start": ["-0.1", "nan", "inf"],
            "t_end": ["0", "-1", "nan", "inf"],
            "polynomial_degree": ["-1", "4", "1.5", "nan"],
            "L2_scale": ["0", "-1", "nan", "inf"],
            "L4_minimum": ["-0.1", "1.1", "nan", "inf"],
            "L5": ["nan", "inf", "-inf"],
            "q1_b": ["nan", "inf"], "f67_A0": ["nan", "inf"],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    form = complete_form()
                    form[field] = value
                    with self.assertRaises(ValueError):
                        build_configuration(form)
        form = complete_form()
        form.update(t_start="2", t_end="1")
        with self.assertRaises(ValueError):
            build_configuration(form)

    def test_initial_states_are_not_arbitrarily_clamped(self):
        form = complete_form()
        form.update(L1="-0.25", L2="2.75", q1_a="0,15")
        data = build_configuration(form)
        self.assertEqual(float(data["initial_variable_values"]["L1"]), -0.25)
        self.assertEqual(float(data["initial_variable_values"]["L2"]), 2.75)
        self.assertEqual(data["perturbation_parameters"]["q1_a"], 0.15)

    def test_q4_requires_sorted_unique_times_and_complete_rows(self):
        for changes in [
            {"q4_time_0": "0.1"}, {"q4_time_1": "0"},
            {"q4_time_1": "-0.1"}, {"q4_time_1": "nan"},
            {"q4_value_1": "nan"}, {"q4_time_1": "0.5", "q4_time_2": "0.4", "q4_value_2": "1"},
            {"q4_time_1": "0.5", "q4_time_2": "0.5", "q4_value_2": "1"},
        ]:
            with self.subTest(changes=changes):
                form = complete_form()
                form.update(changes)
                with self.assertRaises(ValueError):
                    build_configuration(form)
        for missing in ("q4_time_1", "q4_value_1"):
            with self.subTest(missing=missing):
                form = complete_form()
                form.pop(missing)
                with self.assertRaises(ValueError):
                    build_configuration(form)
        form = complete_form()
        form.pop("q4_time_1")
        form.pop("q4_value_1")
        data = build_configuration(form)
        self.assertEqual(data["perturbation_parameters"]["q4_steps"],
                         [{"time": 0.0, "value": 0.1}])


class IntegrationTests(unittest.TestCase):
    def test_nonconstant_polynomials_drive_coupled_state_evolution(self):
        form = complete_form(1)
        form.update(t_end="0.5", q1_a="1", q2_a="0", q5_b="0",
                    q4_value_0="0", q4_value_1="0", L1="0.2", L5="0.4")
        for j in range(1, 99):
            form[f"f{j}_A1"] = "0"
        for j in (1, 29):
            form[f"f{j}_A0"] = "0"
            form[f"f{j}_A1"] = "1"
        form["f36_A0"] = "0"
        # q3=0 on this interval, leaving L1'=L5 and L5'=L1.
        result = integrate_model(build_configuration(form))
        for t, row in zip(result["times"], result["trajectory"]):
            self.assertAlmostEqual(row[0], 0.2*math.cosh(t)+0.4*math.sinh(t), places=7)
            self.assertAlmostEqual(row[4], 0.4*math.cosh(t)+0.2*math.sinh(t), places=7)

    def test_piecewise_analytic_solution_with_sqrt_and_nonzero_start(self):
        form = complete_form()
        form.update(t_start="0.2", t_end="1.2", q5_a="0.8", q5_b="0.4",
                    q4_time_1="0.25", q4_value_1="0.2",
                    q4_time_2="0.9", q4_value_2="0.6")
        for i in range(1, 16):
            form[f"L{i}_scale"] = str(1 + i / 10)
        form["L8_scale"] = "1"
        data = build_configuration(form)
        result = integrate_model(data)
        scales = np.array(data["scales"])

        def exact(t):
            start = 0.2
            dt = t-start
            i1, i2 = dt, 2*dt
            i3 = 0.3*max(0, min(t, 0.8)-0.6) + 0.4*max(0, t-0.8)
            i4 = 0.1*max(0, min(t, 0.25)-start) + 0.2*max(0, min(t, 0.9)-0.25) + 0.6*max(0, t-0.9)
            i5 = 0.8*(2/3)*(t**1.5-start**1.5) + 0.4*dt
            increments = np.array([
                i1+i2-i3, i2+i5-i4, i2-i5, i2-dt, i1+i2+i3-dt,
                i1+i3-dt, i3+i4-dt, i3-dt, i1+i3+i4-dt, i2+i5-dt,
                i1+i3-dt, i1+i2+i5-dt, i1+i2-i4, i2+i3-i5, i1+i2+i5-i3,
            ])
            return 0.5 + increments/scales

        np.testing.assert_allclose(result["solution"], exact(1.2), rtol=2e-7, atol=2e-7)
        times = np.array(result["times"])
        values = np.array(result["trajectory"])
        self.assertEqual(values.shape, (len(times), 15))
        self.assertAlmostEqual(times[0], 0.2)
        self.assertAlmostEqual(times[-1], 1.2)
        np.testing.assert_allclose(values[0], [0.5]*15)
        for t, row in zip(times, values):
            np.testing.assert_allclose(row, exact(t), rtol=3e-7, atol=3e-7)
        for discontinuity in (0.25, 0.6, 0.8, 0.9):
            self.assertTrue(np.any(np.isclose(times, discontinuity, rtol=0, atol=1e-12)))
        snapshots = [0.2, 0.45, 0.7, 0.95, 1.2]
        np.testing.assert_allclose(result["snapshot_times"], snapshots)
        np.testing.assert_allclose(result["snapshot_values"], [exact(t) for t in snapshots],
                                   rtol=3e-7, atol=3e-7)
        self.assertGreater(np.max(values), 1)
        self.assertLess(np.min(values), 0)

    def test_first_breach_is_a_continuous_event(self):
        form = complete_form()
        form.update(t_start="0.1", t_end="0.5", q1_a="0", q2_a="0",
                    q5_b="0", q4_value_0="0", q4_value_1="0",
                    L8_minimum="0.34567")
        for i in range(1, 16):
            form[f"L{i}"] = "0.7"
            if i != 8:
                form[f"L{i}_minimum"] = "0"
        result = integrate_model(build_configuration(form))
        # Here q3=0 and all f=1: L8(t)=0.7-(t-0.1).
        self.assertAlmostEqual(result["first_breach"][7], 0.45433, places=7)
        self.assertTrue(result["below_minimum"][7])
        self.assertTrue(result["ever_below_minimum"][7])

    def test_initial_breach_survives_later_recovery(self):
        form = complete_form()
        form.update(t_start="0.2", t_end="0.4", L1="0", L1_minimum="0.2")
        result = integrate_model(build_configuration(form))
        self.assertFalse(result["below_minimum"][0])
        self.assertTrue(result["ever_below_minimum"][0])
        self.assertAlmostEqual(result["first_breach"][0], 0.2)
        self.assertAlmostEqual(result["minimum_values"][0], 0.0)


class FormFields(HTMLParser):
    """Read actual form values without depending on template whitespace."""
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.select_name = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and "name" in attrs:
            self.values[attrs["name"]] = attrs.get("value", "")
        elif tag == "select":
            self.select_name = attrs.get("name")
        elif tag == "option" and self.select_name and "selected" in attrs:
            self.values[self.select_name] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag == "select":
            self.select_name = None


class FlaskWorkflowTests(unittest.TestCase):
    def setUp(self):
        from app import create_app

        self.files = TemporaryDirectory(prefix="product-company-test-")
        self.addCleanup(self.files.cleanup)
        self.paths = {}
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        for attribute, directory in [
            ("PATH_TO_CALC_STORAGE_FILE", "calculations"),
            ("PATH_SOLUTION_GRAPHS_IMAGE", "solutions"),
            ("PATH_PETAL_GRAPHS_IMAGE", "radars"),
        ]:
            path = Path(self.files.name) / directory
            path.mkdir()
            self.paths[attribute] = path
            self.patches.enter_context(patch.object(Constants, attribute, str(path) + os.sep))
        self.app = create_app()
        self.assertIs(self.app, create_app())
        self.patches.enter_context(patch.dict(self.app.config, {"TESTING": True}))
        self.client = self.app.test_client()

    def test_demo_form_is_complete_bounded_and_errors_preserve_input(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        fields = FormFields(page.get_data(as_text=True)).values
        for key in ("L1", "L15", "L1_scale", "L15_scale", "q1_a",
                    "q2_d", "q5_b", "polynomial_degree", "f1_A0", "f98_A3"):
            self.assertNotEqual(fields[key], "", key)
        for variable in VARIABLES:
            self.assertEqual(float(fields[variable["symbol"]+"_minimum"]), variable["minimum"])
        self.assertNotIn("coefficient_example", MODEL)
        self.assertEqual(int(fields['polynomial_degree']), 2)
        demo = integrate_model(build_configuration(fields))
        trajectory = np.array(demo['trajectory'])
        self.assertGreater(trajectory.min(), .3)
        self.assertLess(trajectory.max(), .9)
        response = self.client.post('/calculate', data=fields)
        self.assertEqual(response.status_code, 302)
        saved_files = list(self.paths["PATH_TO_CALC_STORAGE_FILE"].iterdir())

        form = complete_form()
        form.update(L1="0.12345", q1_a="0.45678", f98_A0="0.76543",
                    q4_time_2="0.7", q4_value_2="0.8")
        form.pop("L5_scale")
        failure = self.client.post("/calculate", data=form)
        self.assertEqual(failure.status_code, 400)
        failed_fields = FormFields(failure.get_data(as_text=True)).values
        for key in ("L1", "q1_a", "f98_A0", "q4_time_2", "q4_value_2"):
            self.assertEqual(failed_fields[key], form[key])
        self.assertEqual(failed_fields["L5_scale"], "")
        self.assertEqual(list(self.paths["PATH_TO_CALC_STORAGE_FILE"].iterdir()), saved_files)

    def test_real_calculation_generates_unclipped_json_plots_and_pdf(self):
        form = complete_form()
        form.update(t_start="0.2", t_end="1.2", q5_a="0.8", q5_b="0.4",
                    L8="0.15", q4_time_1="0.25", q4_value_1="0.2",
                    q4_time_2="0.7", q4_value_2="0.4",
                    q4_time_3="0.9", q4_value_3="0.6")
        response = self.client.post("/calculate", data=form)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/result"))
        cookie = self.client.get_cookie(Constants.CALCULATION_ID_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        calculation_id = cookie.value
        self.assertTrue(calculation_id.isdigit())
        report = self.client.get("/result")
        self.assertEqual(report.status_code, 200)

        data_response = self.client.get("/get-data")
        self.assertEqual(data_response.status_code, 200)
        self.assertEqual(data_response.mimetype, "application/json")
        data = data_response.get_json()
        self.assertEqual(data["interval"], [0.2, 1.2])
        self.assertEqual(len(data["perturbation_parameters"]["q4_steps"]), 4)
        self.assertEqual(len(data["polynomial_coefficients"]), 98)
        trajectory = np.array(data["result"]["trajectory"])
        chart_source = re.search(
            r'<script type="application/json" id="chart-data">(.*?)</script>',
            report.get_data(as_text=True), re.S)
        self.assertIsNotNone(chart_source)
        chart = json.loads(chart_source.group(1))
        self.assertEqual(chart['times'], data['result']['times'])
        np.testing.assert_array_equal(chart['trajectory'], trajectory)
        self.assertEqual([v['symbol'] for v in chart['variables']],
                         [v['symbol'] for v in VARIABLES])
        self.assertGreater(trajectory.max(), 1)
        self.assertLess(trajectory.min(), 0)
        self.assertLess(data["result"]["solution"][7], 0)
        np.testing.assert_allclose(trajectory[-1], data["result"]["solution"])
        stored = self.paths["PATH_TO_CALC_STORAGE_FILE"] / f"{calculation_id}.json"
        self.assertTrue(stored.is_file())

        images = [self.paths["PATH_SOLUTION_GRAPHS_IMAGE"] / f"{calculation_id}.png",
                  self.paths["PATH_SOLUTION_GRAPHS_IMAGE"] / f"{calculation_id}-q.png"]
        images += [self.paths["PATH_PETAL_GRAPHS_IMAGE"] / calculation_id / f"{i}.png"
                   for i in range(1, 6)]
        for path in images:
            with self.subTest(image=path.name):
                self.assertTrue(path.is_file())
                self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertGreater(path.stat().st_size, 1000)
        pdf = self.client.get("/get-pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf.mimetype, "application/pdf")
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", pdf.data[-1024:])
        self.assertGreater(len(pdf.data), 10000)

        restored = FormFields(self.client.get("/").get_data(as_text=True)).values
        for key, value in form.items():
            self.assertAlmostEqual(float(restored[key]), float(value), msg=key)

    def test_recalculation_uses_changed_parameters_and_keeps_separate_results(self):
        form = complete_form()
        form.update(t_start="0.2", t_end="0.4", q5_b="0")
        self.assertEqual(self.client.post("/calculate", data=form).status_code, 302)
        previous_id = self.client.get_cookie(Constants.CALCULATION_ID_COOKIE_NAME).value
        previous = self.client.get("/get-data").get_json()
        self.assertAlmostEqual(previous["result"]["solution"][0], 1.1)

        changed = dict(form)
        changed.update(t_end="0.5", L1="0.25", q1_a="2")
        response = self.client.post("/calculate", data=changed)
        self.assertEqual(response.status_code, 302)
        new_id = self.client.get_cookie(Constants.CALCULATION_ID_COOKIE_NAME).value
        self.assertNotEqual(previous_id, new_id)
        current = self.client.get("/get-data").get_json()
        self.assertEqual(current["interval"], [0.2, 0.5])
        # q3=0 throughout; all f=1, so L1'=q1+q2=4.
        self.assertAlmostEqual(current["result"]["solution"][0], 1.45, places=7)
        for identity in (previous_id, new_id):
            self.assertTrue((self.paths["PATH_TO_CALC_STORAGE_FILE"] / f"{identity}.json").exists())
        fields = FormFields(self.client.get("/").get_data(as_text=True)).values
        for key in ("t_end", "L1", "q1_a"):
            self.assertAlmostEqual(float(fields[key]), float(changed[key]))


if __name__ == "__main__":
    unittest.main()
