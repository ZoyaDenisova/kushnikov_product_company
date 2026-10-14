from flask import render_template, Blueprint, request, redirect, url_for
from app import injector
from app.form_defaults import form_values, Q_GROUPS
from app.utils.constants import Constants

main = Blueprint('main',__name__)


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
