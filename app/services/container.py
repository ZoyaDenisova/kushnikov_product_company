from app import injector, InitialSettings, app
from app.services.calculation_service import CalculationService
from app.services.graph_service import GraphService
from app.utils.utils import Utils


def container():
    injector.map(init_settings=InitialSettings(app=app))
    injector.map(utils=Utils())
    injector.map(graph_service=GraphService())
    injector.map(calculation_service=CalculationService(utils=injector.get('utils'),graph_service=injector.get('graph_service')))
