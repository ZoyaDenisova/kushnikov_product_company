import random
import json
from functools import lru_cache
from pathlib import Path

from app.model import EDGES, Q_POLYNOMIAL_FIELDS, VARIABLES, PERTURBATIONS, MODEL

# Editable, synthetic example; these are not fitted company data or numbers
# copied from the rejected implementation in the assignment.
DEMO_PARAMETERS = {f'q{i}_A{k}': coefficient
                   for i, coefficients in enumerate(((.5,.2,-.2,0), (.5,-.2,.1,.1),
                                                      (0,0,.1,.3), (.1,.1,0,0), (.3,.1,0,0)), 1)
                   for k, coefficient in enumerate(coefficients)}
DEMO_INITIAL = (.48, .50, .70, .82, .75, .78, .74, .86, .46, .72, .80, .58, .50, .72, .46)
DEMO_SCALES = (1.4, 1.8, 1.5, 1.7, 1.4, 1.4, 1.7, 1.7, 1.5, 1.6, 1.6, 1.8, 1.5, 1.6, 1.8)

Q_GROUPS = [{'symbol': f'q{i}', 'name': name} for i, name in enumerate(PERTURBATIONS, 1)]


def form_values(data=None):
    values = {'t_start':0, 't_end':1, 'polynomial_degree':2}
    for i, variable in enumerate(VARIABLES):
        symbol = variable['symbol']
        values[symbol] = DEMO_INITIAL[i]
        values[symbol+'_scale'] = DEMO_SCALES[i]
        values[symbol+'_minimum'] = variable['minimum']
    values.update(DEMO_PARAMETERS)
    # Centre each polynomial at its source's initial state. Stronger slopes
    # expose feedback without starting with large products of influence terms.
    curvatures = (-.18, -.08, .10, .18)
    for edges in EDGES:
        for edge in edges:
            j = edge['function']
            x = values[f"L{edge['variable']}"]
            a1, a2 = .52 + .025 * (j % 6), curvatures[j % 4]
            gain = .88 + .0006 * j
            coefficients = (round(gain - a1*x - a2*x*x, 6), a1, a2, 0)
            for k, coefficient in enumerate(coefficients):
                values[f"f{edge['function']}_A{k}"] = coefficient
    steps = []
    if data:
        values.update(data['initial_variable_values'])
        parameters = data['perturbation_parameters']
        if 'q1_A0' in parameters:
            values.update({key: parameters[key] for key in Q_POLYNOMIAL_FIELDS})
        else:
            values['legacy_external_factors'] = True
        values.update(t_start=data['interval'][0],t_end=data['interval'][1],polynomial_degree=data['polynomial_degree'])
        for i, variable in enumerate(VARIABLES):
            values[variable['symbol']+'_scale'] = data['scales'][i]
            values[variable['symbol']+'_minimum'] = data['minima'][i]
        for function, coefficients in data['polynomial_coefficients'].items():
            for k in range(4):
                values[f'{function}_A{k}'] = coefficients.get(f'A{k}', 0) if k <= data['polynomial_degree'] else 0
        steps = data['perturbation_parameters'].get('q4_steps', [])
    return values, steps


@lru_cache(maxsize=1)
def _scenario_bank():
    bank = json.loads(Path(__file__).with_name('data').joinpath('tested_scenarios.json').read_text(encoding='utf-8'))
    if bank['model_version'] != MODEL['version'] or len(bank['scenarios']) != 200:
        raise ValueError('Библиотека сценариев не соответствует модели. Обновите проверенные наборы.')
    return bank


def random_form_values(start, end, degree, step_count=None, rng=None):
    """Choose a precomputed, tested scenario without running the solver."""
    bank = _scenario_bank()
    if [start, end] != bank['interval']:
        raise ValueError('Готовые наборы проверены на интервале 0–1. Для другого интервала задайте параметры вручную.')
    if degree not in bank['validated_degrees']:
        raise ValueError('Для этой степени полиномов нет проверенных наборов.')
    selected = (rng or random.Random()).choice(bank['scenarios'])
    values = dict(selected['values'], polynomial_degree=degree)
    return values, []
