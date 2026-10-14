import atexit
import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from .initial_settings import InitialSettings
from .services.scheduled_service import ScheduledService
from .utils.flask_inject import Inject

# Create Flask application object and
# set secret key for this object
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Dependency injection container
injector = Inject(app)

# Create scheduler with scheduled task which removes
# old calculation json files from static dir
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(ScheduledService.remove_old_sessions_task, 'interval', minutes=1150)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


def create_app() -> Flask:
    if app.extensions.get('product_company_initialized'):
        return app
    init_settings: InitialSettings = dependency_injection_container_initialize()
    # Create folders for store data
    init_settings.create_storage_folder()
    # Function for registration blueprints of routes in app
    init_settings.blueprint_registration()
    # Import error handlers
    init_settings.error_handlers()
    app.extensions['product_company_initialized'] = True

    return app


@app.context_processor
def product_company_context():
    from app.model import VARIABLES, MATRIX, EDGES, PERTURBATIONS, MODEL, equation_text
    return dict(variables=VARIABLES, matrix=MATRIX, model_edges=EDGES,
                perturbation_names=PERTURBATIONS,
                equations=[equation_text(i) for i in range(15)], model=MODEL)


def dependency_injection_container_initialize() -> InitialSettings:
    from app.services.container import container
    container()
    return injector.get('init_settings')
