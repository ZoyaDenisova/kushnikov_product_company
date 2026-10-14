import math

from app.model import EDGES, Q_FIELDS, VARIABLES

# Editable, synthetic example; these are not fitted company data or numbers
# copied from the rejected implementation in the assignment.
DEMO_PARAMETERS = {
    'q1_a': .4, 'q1_b': .1, 'q1_c': 2 * math.pi, 'q1_d': 0,
    'q2_a': .35, 'q2_b': .05, 'q2_c': 2 * math.pi, 'q2_d': 0,
    'q5_a': .1, 'q5_b': .4,
}

Q_GROUPS = [
    {'symbol':'q1','name':'Курс валюты','formula':'q₁(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q2','name':'Санкции','formula':'q₂(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q5','name':'Опыт специалистов','formula':'q₅(t) = a·√t + b', 'fields':[('a','Темп роста a'),('b','Начальное значение b')]},
]


def form_values(data=None):
    values = {'t_start':0, 't_end':1, 'polynomial_degree':2}
    for variable in VARIABLES:
        symbol = variable['symbol']
        values[symbol] = .6
        values[symbol+'_scale'] = 10
        values[symbol+'_minimum'] = variable['minimum']
    values.update(DEMO_PARAMETERS)
    # Each source/target pair gets a distinct synthetic quadratic. All demo
    # functions stay positive and increasing on [0, 1]; EDGES sets the sign.
    curvatures = (.08, -.06, .12, -.04)
    for target, edges in enumerate(EDGES):
        for edge in edges:
            source = edge['variable'] - 1
            coefficients = (round(.76 + .015 * source, 3),
                            round(.14 + .012 * target, 3),
                            curvatures[(source + target) % len(curvatures)], 0)
            for k, coefficient in enumerate(coefficients):
                values[f"f{edge['function']}_A{k}"] = coefficient
    steps = [{'time':0,'value':.05},{'time':.5,'value':.1},{'time':.8,'value':.15}]
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
