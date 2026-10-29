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
            for k in range(4):
                values[f'{function}_A{k}'] = coefficients.get(f'A{k}', 0) if k <= data['polynomial_degree'] else 0
        steps = data['perturbation_parameters']['q4_steps']
    return values, steps


def random_form_values(start, end, degree, step_count, rng=None):
    """Draw one set of parameters; integration belongs to the Calculate action."""
    rng = rng or random.Random()
    number = lambda low, high: rng.randint(round(low * 10), round(high * 10)) / 10
    last_tick = math.ceil(end * 10) - 1
    if step_count - 1 > last_tick:
        raise ValueError('Для такого количества ступеней q₄ недостаточно разных времён с шагом 0,1. Уменьшите количество ступеней или увеличьте конец интервала.')
    values = dict(t_start=start, t_end=end, polynomial_degree=degree)
    for variable in VARIABLES:
        symbol = variable['symbol']
        values[symbol] = number(0, 1)
        values[symbol+'_scale'] = number(.1, 1)
        values[symbol+'_minimum'] = number(.1, .3)
    for factor, offset, amplitude, phase in [
        ('q1', (.4, .6), (.1, .3), (-.3, .3)),
        ('q2', (.4, .5), (.1, .2), (.8, 1.4)),
    ]:
        values[factor+'_a'] = number(*offset)
        values[factor+'_b'] = number(*amplitude)
        values[factor+'_c'] = number(5, 7.5)
        values[factor+'_d'] = number(*phase)
    values['q5_a'] = number(.1, .2)
    values['q5_b'] = number(.2, .3)
    times = [0] + [tick / 10 for tick in sorted(rng.sample(range(1, last_tick + 1), step_count - 1))]
    steps = [{'time': time, 'value': number(.1, .2)} for time in times]
    for edges in EDGES:
        for edge in edges:
            for k, bounds in enumerate(((.1, 1), (.5, .8), (-.2, .2), (-.1, .1))):
                values[f"f{edge['function']}_A{k}"] = number(*bounds)
    return values, steps
