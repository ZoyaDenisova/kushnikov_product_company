import json
import math
from pathlib import Path
import re

import numpy as np
from scipy.integrate import solve_ivp

from app.model import MODEL, VARIABLES, Q_FIELDS, derivative
from app.utils.constants import Constants


def finite_number(value, label):
    try:
        result = float(str(value).strip().replace(',', '.'))
    except (TypeError, ValueError):
        raise ValueError(f'{label}: введите число.')
    if not math.isfinite(result):
        raise ValueError(f'{label}: требуется конечное число.')
    return result


def build_configuration(form):
    degree = finite_number(form.get('polynomial_degree'), 'Выберите степень полиномов')
    if degree not in (0, 1, 2, 3):
        raise ValueError('Степень полиномов должна быть целой: от 0 до 3.')
    degree = int(degree)
    initial, scales, minima = {}, [], []
    for variable in VARIABLES:
        symbol = variable['symbol']
        initial[symbol] = finite_number(form.get(symbol), f'{symbol}: начальное значение')
        scales.append(finite_number(form.get(symbol + '_scale'), f'{symbol}*: нормировка'))
        minima.append(finite_number(form.get(symbol + '_minimum'), f'{symbol}: минимальный порог'))
    if any(value <= 0 for value in scales):
        raise ValueError('Все L* должны быть положительными.')
    if any(not 0 <= value <= 1 for value in minima):
        raise ValueError('Нормированные минимальные пороги должны быть от 0 до 1.')
    start = finite_number(form.get('t_start'), 'Начало интервала')
    end = finite_number(form.get('t_end'), 'Конец интервала')
    if not 0 <= start < end:
        raise ValueError('Укажите интервал 0 ≤ начало < конец. Время не может быть отрицательным из-за √t в q₅.')
    parameters = {key: finite_number(form.get(key), key) for key in Q_FIELDS}
    indexes = sorted({int(match.group(1)) for key in form for match in [re.fullmatch(r'q4_time_(\d+)', key)] if match})
    value_indexes = sorted({int(match.group(1)) for key in form for match in [re.fullmatch(r'q4_value_(\d+)', key)] if match})
    if not indexes or indexes != list(range(len(indexes))) or indexes != value_indexes:
        raise ValueError('Задайте последовательный список ступеней q₄.')
    steps = [{'time': finite_number(form.get(f'q4_time_{i}'), f'q₄: время ступени {i+1}'),
              'value': finite_number(form.get(f'q4_value_{i}'), f'q₄: уровень ступени {i+1}')} for i in indexes]
    if steps[0]['time'] != 0 or any(right['time'] <= left['time'] for left, right in zip(steps, steps[1:])):
        raise ValueError('Первая ступень q₄ начинается при t=0; времена следующих ступеней должны строго возрастать.')
    parameters['q4_steps'] = steps
    coefficients = {}
    for i in range(1, 99):
        coefficients[f'f{i}'] = {f'A{k}': finite_number(form.get(f'f{i}_A{k}'), f'f{i}: a{k}') if k <= degree else 0 for k in range(4)}
    return {'model_version': MODEL['version'], 'polynomial_degree': degree,
            'polynomial_coefficients': coefficients, 'initial_variable_values': initial,
            'scales': scales, 'minima': minima, 'interval': [start, end], 'perturbation_parameters': parameters}


def integrate_model(data):
    start, end = data['interval']
    parameters, minima = data['perturbation_parameters'], data['minima']
    y0 = np.array([data['initial_variable_values'][v['symbol']] for v in VARIABLES], dtype=float)
    jumps = [.6, .8] + [step['time'] for step in parameters['q4_steps'][1:]]
    boundaries = sorted({start, end, *[t for t in jumps if start < t < end]})
    snapshots = np.linspace(start, end, 5)
    points = set(np.linspace(start, end, 201)) | set(boundaries) | set(snapshots)
    first_breach = [start if y0[i] < minima[i] else None for i in range(15)]
    segments = []
    evaluations = 0
    for left, right in zip(boundaries, boundaries[1:]):
        def rhs(t, values):
            nonlocal evaluations
            evaluations += 1
            if evaluations > 200000:
                raise ValueError('Расчёт не сходится за разумное число шагов. Проверьте коэффициенты или уменьшите интервал.')
            t = min(max(t, np.nextafter(left, right)), np.nextafter(right, left))
            with np.errstate(over='raise', invalid='raise'):
                return derivative(t, values, data['polynomial_coefficients'], data['scales'], parameters)
        events = []
        for i, minimum in enumerate(minima):
            def crossing(t, values, i=i, minimum=minimum):
                return values[i] - minimum
            crossing.direction = -1
            events.append(crossing)
        try:
            solution = solve_ivp(rhs, (left, right), y0, dense_output=True, events=events, rtol=1e-9, atol=1e-11)
        except (FloatingPointError, OverflowError):
            raise ValueError('Решение расходится до бесконечности. Проверьте коэффициенты или сократите интервал.')
        if not solution.success:
            raise ValueError('Численное решение не сошлось: ' + solution.message)
        for i, times in enumerate(solution.t_events):
            for time in times:
                # A stationary value equal to the threshold is not a breach.
                if rhs(time, solution.sol(time))[i] < 0:
                    if first_breach[i] is None:
                        first_breach[i] = float(time)
                    points.add(float(time))
        segments.append((left, right, solution.sol))
        y0 = solution.y[:, -1]
    x = np.array(sorted(points))
    y = np.empty((len(x), 15))
    snapshot_values = np.empty((5, 15))
    for left, right, dense in segments:
        mask = (x >= left) & (x <= right)
        y[mask] = dense(x[mask]).T
        mask_snapshots = (snapshots >= left) & (snapshots <= right)
        if np.any(mask_snapshots):
            snapshot_values[mask_snapshots] = dense(snapshots[mask_snapshots]).T
    if not np.all(np.isfinite(y)):
        raise ValueError('Получены неконечные значения решения.')
    below = [bool(value < minimum) for value, minimum in zip(y[-1], minima)]
    ever = [bool(first_breach[i] is not None or np.any(y[:, i] < minima[i])) for i in range(15)]
    return {'solution': y[-1].tolist(), 'times': x.tolist(), 'trajectory': y.tolist(),
            'snapshot_times': snapshots.tolist(), 'snapshot_values': snapshot_values.tolist(),
            'below_minimum': below, 'ever_below_minimum': ever, 'first_breach': first_breach,
            'minimum_values': y.min(axis=0).tolist(),
            'outside_unit_interval': [bool(np.any((y[:, i] < 0) | (y[:, i] > 1))) for i in range(15)]}


class CalculationService:
    def __init__(self, utils, graph_service):
        self.graph_service = graph_service

    def path(self, calculation_id):
        if not calculation_id or not calculation_id.isdigit():
            raise ValueError('Сначала выполните расчёт.')
        return Path(Constants.PATH_TO_CALC_STORAGE_FILE) / (calculation_id + '.json')

    def read(self, calculation_id):
        data = json.loads(self.path(calculation_id).read_text(encoding='utf-8'))
        if data.get('model_version') != MODEL['version']:
            raise ValueError('Этот расчёт относится к прежней модели. Начните новый.')
        return data

    def calculate(self, configuration, calculation_id):
        result = integrate_model(configuration)
        self.graph_service.save_plot(calculation_id, np.array(result['trajectory']), np.array(result['times']))
        self.graph_service.save_petal_plots(calculation_id, np.array(result['snapshot_values']), np.array(result['snapshot_times']), configuration['minima'])
        self.graph_service.save_perturbations(calculation_id, np.array(result['times']), configuration['perturbation_parameters'])
        configuration['result'] = result
        self.path(calculation_id).write_text(json.dumps(configuration, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        return configuration
