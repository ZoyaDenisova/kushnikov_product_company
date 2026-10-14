import time
from flask import Blueprint, render_template, request, redirect, url_for, make_response

from app import injector
from app.form_defaults import form_values, Q_GROUPS
from app.services.calculation_service import build_configuration
from app.utils.constants import Constants

calculation = Blueprint('calculation', __name__)


def current_id():
    value = request.cookies.get(Constants.CALCULATION_ID_COOKIE_NAME,'')
    if not value.isdigit():
        raise ValueError('Сначала заполните параметры и выполните расчёт.')
    return value


@calculation.route('/calculate',methods=['POST'])
def calculate():
    try:
        data = build_configuration(request.form)
        calculation_id = str(time.time_ns())
        injector.get('calculation_service').calculate(data,calculation_id)
    except ValueError as error:
        values, _ = form_values()
        values.update(request.form.to_dict())
        indexes = sorted({int(key.rsplit('_',1)[1]) for key in request.form if key.startswith('q4_time_') and key.rsplit('_',1)[1].isdigit()})
        steps = [{'time':request.form.get(f'q4_time_{i}',''),'value':request.form.get(f'q4_value_{i}','')} for i in indexes] or [{'time':0,'value':''}]
        return render_template('main/index.html',values=values,steps=steps,q_groups=Q_GROUPS,error=str(error)),400
    response = redirect(url_for('calculation.result_report'))
    response.set_cookie(Constants.CALCULATION_ID_COOKIE_NAME,calculation_id,httponly=True,samesite='Lax')
    return response


@calculation.route('/result')
def result_report():
    data = injector.get('calculation_service').read(current_id())
    return render_template('variables/result_report.html',data=data,plot_name=current_id())


@calculation.route('/get-pdf')
def get_generated_pdf():
    from app.services.report_service import create_pdf
    data = injector.get('calculation_service').read(current_id())
    response = make_response(create_pdf(data,current_id()))
    response.headers['Content-Type']='application/pdf'
    response.headers['Content-Disposition']='attachment; filename=product-company.pdf'
    return response


@calculation.route('/get-data')
def get_calculation_data():
    from flask import jsonify
    response = jsonify(injector.get('calculation_service').read(current_id()))
    response.headers['Content-Disposition']='attachment; filename=product-company.json'
    return response


@calculation.route('/initial-setup')
@calculation.route('/continue-setup')
@calculation.route('/final-setup')
@calculation.route('/decrease')
def legacy_setup():
    return redirect(url_for('main.index'))


@calculation.route('/cancel-calculation')
def legacy_result():
    return redirect(url_for('calculation.result_report'))
