from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from app.model import VARIABLES, PERTURBATIONS, perturbations
from app.utils.constants import Constants


class GraphService:
    def save_plot(self, calculation_id, y, x):
        fig, ax = plt.subplots(figsize=(13, 7))
        for i, variable in enumerate(VARIABLES):
            ax.plot(x, y[:, i], label=variable['symbol'] + ' — ' + variable['name'])
        ax.set(xlabel='Время t', ylabel='Нормированное значение', title='Показатели продуктовой компании')
        ax.grid(alpha=.3)
        ax.legend(fontsize=8, loc='center left', bbox_to_anchor=(1, .5))
        fig.savefig(Constants.PATH_SOLUTION_GRAPHS_IMAGE + calculation_id + '.png', bbox_inches='tight')
        plt.close(fig)

    def save_petal_plots(self, calculation_id, y, times, minima):
        directory = Path(Constants.PATH_PETAL_GRAPHS_IMAGE) / calculation_id
        directory.mkdir(parents=True, exist_ok=True)
        angles = np.linspace(0, 2 * np.pi, len(VARIABLES), endpoint=False)
        closed_angles = np.r_[angles, angles[0]]
        lower = min(0, float(np.min(y)), min(minima))
        upper = max(1, float(np.max(y)), max(minima))
        for i, (values, time) in enumerate(zip(y, times), 1):
            fig, ax = plt.subplots(figsize=(9, 8), subplot_kw={'projection': 'polar'})
            ax.plot(closed_angles, np.r_[values, values[0]], 'o-', label='Расчётные значения')
            ax.plot(closed_angles, np.r_[minima, minima[0]], 'r--', label='Минимальные значения')
            ax.set_thetagrids(np.degrees(angles), [v['symbol'] for v in VARIABLES])
            ax.set_title(f'Продуктовая компания: t={time:g}')
            # The same full range on every snapshot allows comparison over time.
            ax.set_ylim(lower, upper)
            ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.15))
            fig.savefig(directory / f'{i}.png', bbox_inches='tight')
            plt.close(fig)

    def save_perturbations(self, calculation_id, x, parameters):
        fig, ax = plt.subplots(figsize=(11, 6))
        jumps = [.6, .8] + [step['time'] for step in parameters['q4_steps'][1:]]
        extra = [np.nextafter(t, np.inf) for t in jumps if x[0] <= t < x[-1]]
        x = np.unique(np.r_[x, extra])
        values = np.array([perturbations(t, parameters) for t in x])
        for i, title in enumerate(PERTURBATIONS):
            ax.plot(x, values[:, i], label=f'q{i+1} — {title}')
        ax.set(xlabel='Время t', ylabel='Значение фактора', title='Внешние факторы продуктовой компании')
        ax.grid(alpha=.3)
        ax.legend()
        fig.savefig(Constants.PATH_SOLUTION_GRAPHS_IMAGE + calculation_id + '-q.png', bbox_inches='tight')
        plt.close(fig)
