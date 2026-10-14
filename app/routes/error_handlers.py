from flask import render_template, redirect, url_for, flash
from werkzeug.exceptions import HTTPException
from app import app


@app.errorhandler(ValueError)
def invalid_input(error):
    return render_template('errors/invalid_input.html', message=str(error)), 400


@app.errorhandler(FileNotFoundError)
def missing_session(error):
    flash('Сессия не найдена. Начните новый расчёт.')
    return redirect(url_for('main.index'))


@app.errorhandler(Exception)
def unexpected_error(error):
    if isinstance(error, HTTPException):
        return error
    app.logger.exception('Calculation request failed')
    return render_template('errors/invalid_input.html', message='Не удалось выполнить расчёт. Проверьте введённые параметры.'), 500
