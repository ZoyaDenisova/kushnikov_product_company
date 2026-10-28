import math
import random

from app.model import EDGES, Q_FIELDS, VARIABLES

# Editable, synthetic example; these are not fitted company data or numbers
# copied from the rejected implementation in the assignment.
DEMO_PARAMETERS = {
    'q1_a': .5, 'q1_b': .22, 'q1_c': 2 * math.pi, 'q1_d': .15,
    'q2_a': .45, 'q2_b': .18, 'q2_c': 2 * math.pi, 'q2_d': 1.1,
    'q5_a': .15, 'q5_b': .25,
}
DEMO_INITIAL = (.48, .50, .70, .82, .75, .78, .74, .86, .46, .72, .80, .58, .50, .72, .46)
DEMO_SCALES = (1.4, 1.8, 1.5, 1.7, 1.4, 1.4, 1.7, 1.7, 1.5, 1.6, 1.6, 1.8, 1.5, 1.6, 1.8)

Q_GROUPS = [
    {'symbol':'q1','name':'Курс валюты','formula':'q₁(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q2','name':'Санкции','formula':'q₂(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q5','name':'Опыт специалистов','formula':'q₅(t) = a·√t + b', 'fields':[('a','Темп роста a'),('b','Начальное значение b')]},
]


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
    steps = [{'time':0,'value':.08},{'time':.35,'value':.22},{'time':.75,'value':.12}]
    if data:
        values.update(data['initial_variable_values'])
        values.update({key:data['perturbation_parameters'][key] for key in Q_FIELDS})
        values.update(t_start=data['interval'][0],t_end=data['interval'][1],polynomial_degree=data['polynomial_degree'])
        for i, variable in enumerate(VARIABLES):
            values[variable['symbol']+'_scale'] = data['scales'][i]
            values[variable['symbol']+'_minimum'] = data['minima'][i]
        for function, coefficients in data['polynomial_coefficients'].items():
            for k in range(data['polynomial_degree']+1):
                values[f'{function}_A{k}'] = coefficients[f'A{k}']
        steps = data['perturbation_parameters']['q4_steps']
    return values, steps


def random_form_values(start, end, degree, step_count, rng=None):
    """Return a synthetic scenario only after solving it on the chosen interval."""
    from app.services.calculation_service import build_configuration, integrate_model

    rng = rng or random.Random()
    number = lambda low, high: round(rng.uniform(low, high), 6)
    for _ in range(16):
        values, _ = form_values()
        values.update(t_start=start, t_end=end, polynomial_degree=degree)
        for i, variable in enumerate(VARIABLES):
            symbol = variable['symbol']
            values[symbol] = number(DEMO_INITIAL[i] - .05, DEMO_INITIAL[i] + .05)
            values[symbol+'_scale'] = number(DEMO_SCALES[i] * .85, DEMO_SCALES[i] * 1.15)
            values[symbol+'_minimum'] = number(.10, .35)
        for factor, offset, amplitude, phase in [
            ('q1', (.45, .55), (.18, .25), (-.3, .3)),
            ('q2', (.40, .50), (.14, .20), (.8, 1.4)),
        ]:
            values[factor+'_a'] = number(*offset)
            values[factor+'_b'] = number(*amplitude)
            values[factor+'_c'] = number(1.6 * math.pi, 2.4 * math.pi)
            values[factor+'_d'] = number(*phase)
        values['q5_a'] = number(.10, .20)
        values['q5_b'] = number(.20, .30)
        steps = [{'time': 0 if i == 0 else float(f'{end * ((i + rng.uniform(-.2, .2)) / step_count):.12g}'),
                  'value': number(.06, .24)} for i in range(step_count)]
        for edges in EDGES:
            for edge in edges:
                x = values[f"L{edge['variable']}"]
                coefficients = [0, number(.55, .75), number(-.18, .18), number(-.06, .06)]
                # Preserve the initial gain for every selected polynomial order.
                coefficients[0] = round(number(.87, .95) - sum(
                    coefficients[k] * x**k for k in range(1, degree + 1)), 6)
                for k, coefficient in enumerate(coefficients):
                    values[f"f{edge['function']}_A{k}"] = coefficient
        fields = dict(values)
        for i, step in enumerate(steps):
            fields[f'q4_time_{i}'] = step['time']
            fields[f'q4_value_{i}'] = step['value']
        try:
            result = integrate_model(build_configuration(fields))
        except ValueError:
            continue
        # Reject rather than clip trajectories. This condition only selects
        # generated examples; the actual equations and solver remain unchanged.
        if all(0 <= value <= 1 for row in result['trajectory'] for value in row):
            return values, steps
    raise ValueError('Не удалось подобрать устойчивый случайный сценарий на выбранном интервале. Попробуйте ещё раз.')
