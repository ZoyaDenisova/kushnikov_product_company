from flask import render_template, Blueprint, request, redirect, url_for, jsonify
from app import injector
from app.form_defaults import form_values, random_form_values, Q_GROUPS
from app.services.calculation_service import finite_number
from app.utils.constants import Constants

main = Blueprint('main',__name__)


@main.route('/random-scenario', methods=['POST'])
def random_scenario():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(error='Передайте настройки сценария.'), 400
    try:
        start = finite_number(payload.get('t_start'), 'Начало интервала')
        end = finite_number(payload.get('t_end'), 'Конец интервала')
        degree = finite_number(payload.get('polynomial_degree'), 'Степень полиномов')
        count = finite_number(payload.get('step_count'), 'Количество ступеней q₄')
        if not 0 <= start < end:
            raise ValueError('Укажите интервал 0 ≤ начало < конец.')
        if degree not in (0, 1, 2, 3):
            raise ValueError('Выберите степень полиномов от 0 до 3.')
        if not count.is_integer() or not 1 <= count <= 100:
            raise ValueError('Для генерации задайте от 1 до 100 ступеней q₄.')
        values, steps = random_form_values(start, end, int(degree), int(count))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(values=values, steps=steps)


@main.route('/')
def index():
    data = None
    calculation_id = request.cookies.get(Constants.CALCULATION_ID_COOKIE_NAME,'')
    if calculation_id.isdigit():
        try:
            data = injector.get('calculation_service').read(calculation_id)
        except (ValueError,FileNotFoundError):
            pass
    values,steps = form_values(data)
    return render_template('main/index.html',values=values,steps=steps,q_groups=Q_GROUPS,has_result=bool(data))


@main.route('/about')
def about():
    return render_template('main/about.html')


@main.route('/documents')
def documents():
    return render_template('main/documents.html')


@main.route('/clear-session')
def clear_session():
    response = redirect(url_for('main.index'))
    response.delete_cookie(Constants.CALCULATION_ID_COOKIE_NAME)
    return response
