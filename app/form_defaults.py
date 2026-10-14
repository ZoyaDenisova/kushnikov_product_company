from app.model import VARIABLES, Q_FIELDS

Q_GROUPS = [
    {'symbol':'q1','name':'Курс валюты','formula':'q₁(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q2','name':'Санкции','formula':'q₂(t) = a + b·sin(c·t + d)', 'fields':[('a','Смещение a'),('b','Амплитуда b'),('c','Частота c'),('d','Фаза d')]},
    {'symbol':'q5','name':'Опыт специалистов','formula':'q₅(t) = a·√t + b', 'fields':[('a','Темп роста a'),('b','Начальное значение b')]},
]


def form_values(data=None):
    values = {'t_start':0, 't_end':'', 'polynomial_degree':''}
    for variable in VARIABLES:
        symbol = variable['symbol']
        values[symbol] = ''
        values[symbol+'_scale'] = ''
        values[symbol+'_minimum'] = variable['minimum']
    values.update({key:'' for key in Q_FIELDS})
    for i in range(1,99):
        for k in range(4):
            values[f'f{i}_A{k}'] = ''
    steps = [{'time':0,'value':''},{'time':'','value':''}]
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
