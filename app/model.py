"""Product-company model transcribed from the supplied assignment.

Rows are affected L variables; columns are influencing L1..L15, q1..q5.
Polynomial numbering follows table 2: positive L edges, then negative L edges.
"""
import json
import math
from pathlib import Path

MODEL = json.loads(Path(__file__).with_name('product_company.json').read_text(encoding='utf-8'))
VARIABLES = MODEL['variables']
MATRIX = MODEL['matrix']
PERTURBATIONS = ['Курс валюты', 'Санкции', 'Эпидемия COVID', 'Штрафы на CO₂',
                 'Опыт задействованных специалистов']
Q_FIELDS = ['q1_a', 'q1_b', 'q1_c', 'q1_d',
            'q2_a', 'q2_b', 'q2_c', 'q2_d', 'q5_a', 'q5_b']
EDGES = []
next_function = 1
for row in MATRIX:
    edges = []
    for sign in (1, -1):
        for j, value in enumerate(row[:15]):
            if value == sign:
                edges.append({'function': next_function, 'variable': j + 1, 'sign': sign})
                next_function += 1
    EDGES.append(edges)
assert next_function == 99


def perturbations(t, parameters):
    p = parameters
    sine = lambda k: p[k + '_a'] + p[k + '_b'] * math.sin(p[k + '_c'] * t + p[k + '_d'])
    q4 = p['q4_steps'][0]['value']
    for step in p['q4_steps'][1:]:
        if t < step['time']:
            break
        q4 = step['value']
    return [sine('q1'), sine('q2'), 0 if t <= .6 else .3 if t <= .8 else .4,
            q4,
            p['q5_a'] * math.sqrt(t) + p['q5_b']]


def equation_text(index):
    row, edges = MATRIX[index], EDGES[index]
    positive = ' · '.join(f"f{e['function']}(L{e['variable']}(t))" for e in edges if e['sign'] == 1) or '1'
    negative = ' · '.join(f"f{e['function']}(L{e['variable']}(t))" for e in edges if e['sign'] == -1)
    q_plus = ' + '.join(f'q{j+1}(t)' for j, sign in enumerate(row[15:]) if sign == 1)
    q_minus = ' + '.join(f'q{j+1}(t)' for j, sign in enumerate(row[15:]) if sign == -1)
    terms = positive + (f' · ({q_plus})' if q_plus else '')
    if negative:
        terms += f' − ({negative})'
    if q_minus:
        terms += f' − ({q_minus})'
    return f'dL{index+1}/dt = (1/L{index+1}*) · [{terms}]'


def derivative(t, y, coefficients, scales, parameters):
    q = perturbations(t, parameters)
    output = []
    for i, (row, edges) in enumerate(zip(MATRIX, EDGES)):
        plus, minus = [], []
        for edge in edges:
            c = coefficients['f' + str(edge['function'])]
            x = y[edge['variable'] - 1]
            value = float(c.get('A3', 0))
            for k in (2, 1, 0):
                value = value * x + float(c.get('A' + str(k), 0))
            (plus if edge['sign'] == 1 else minus).append(value)
        growth = math.prod(plus)
        positive_q = [q[j] for j, sign in enumerate(row[15:]) if sign == 1]
        if positive_q:
            growth *= sum(positive_q)
        decline = (math.prod(minus) if minus else 0) + sum(q[j] for j, sign in enumerate(row[15:]) if sign == -1)
        output.append((growth - decline) / scales[i])
    return output
