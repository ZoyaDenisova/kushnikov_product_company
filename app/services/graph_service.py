from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import numpy as np

from app.model import VARIABLES, PERTURBATIONS, perturbations
from app.chart_style import SERIES_STYLES, spread_labels
from app.utils.constants import Constants


class GraphService:
    def save_plot(self, calculation_id, y, x):
        fig, ax = plt.subplots(figsize=(9.5, 9), dpi=140)
        for i, variable in enumerate(VARIABLES):
            style = SERIES_STYLES[i]
            ax.plot(x, y[:, i], color=style['color'], linewidth=1.9,
                    linestyle=(0, tuple(style['dash'])) if style['dash'] else '-',
                    label=variable['symbol'] + ' — ' + variable['name'])
        span = max(float(np.ptp(y)), max(float(np.max(np.abs(y))), 1) * .02)
        lower, upper = float(np.min(y)) - span*.06, float(np.max(y)) + span*.06
        ax.set_ylim(lower, upper)
        # Put label spacing in data units so export resolution cannot cause
        # neighbouring labels to collide. Never modify the plotted data.
        positions = spread_labels(y[-1].tolist(), lower+span*.015, upper-span*.015, span*.035)
        duration = x[-1] - x[0]
        ax.set_xlim(x[0], x[-1]+duration*.12)
        for i, (variable, label_y) in enumerate(zip(VARIABLES, positions)):
            color = SERIES_STYLES[i]['color']
            ax.plot([x[-1], x[-1]+duration*.012, x[-1]+duration*.035],
                    [y[-1,i], y[-1,i], label_y], color=color, linewidth=.8)
            ax.plot(x[-1], y[-1,i], 'o', color=color, markersize=3)
            label = ax.text(x[-1]+duration*.043, label_y, variable['symbol'],
                            color=color, fontsize=9, fontweight='bold', va='center')
            label.set_path_effects([path_effects.withStroke(linewidth=3, foreground='white')])
        ax.set(xlabel='Время t', ylabel='Нормированное значение', title='Показатели продуктовой компании')
        ax.grid(alpha=.3)
        ax.legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(.5, -.11), ncol=3,
                  frameon=False, columnspacing=1.2, handlelength=2.7)
        fig.subplots_adjust(left=.09, right=.96, top=.94, bottom=.23)
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
