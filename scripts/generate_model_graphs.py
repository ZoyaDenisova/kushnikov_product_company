"""Regenerate all 15 subgraphs from the same signed matrix used by the solver."""
import math
from pathlib import Path
import sys
import textwrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from app.model import VARIABLES, MATRIX, EDGES, PERTURBATIONS


def generate(directory=None):
    directory = Path(directory or Path(__file__).resolve().parents[1] / 'app/static/images/graphs')
    directory.mkdir(parents=True, exist_ok=True)
    for i, (row, edges) in enumerate(zip(MATRIX, EDGES)):
        sources = [(f"L{e['variable']}", VARIABLES[e['variable']-1]['name'], e['sign'], f"f{e['function']}") for e in edges]
        sources += [(f'q{j+1}', PERTURBATIONS[j], sign, '') for j, sign in enumerate(row[15:]) if sign]
        fig, ax = plt.subplots(figsize=(13, 10))
        ax.set(xlim=(-5,5), ylim=(-4.1,4.1), aspect='equal')
        ax.axis('off')
        for j, (symbol, name, sign, function) in enumerate(sources):
            angle = 2 * math.pi * j / len(sources) + math.pi / 2
            x, y = 3.5 * math.cos(angle), 3.1 * math.sin(angle)
            color = '#167146' if sign == 1 else '#b63434'
            ax.annotate('', xy=(x*.28,y*.28), xytext=(x*.87,y*.87),
                        arrowprops=dict(arrowstyle='-|>', color=color, lw=1.7, mutation_scale=15))
            ax.text(x*.57,y*.57, ('+' if sign==1 else '−') + (' '+function if function else ''),
                    color=color, fontsize=10, ha='center', va='center', bbox=dict(facecolor='white',edgecolor='none',pad=1))
            ax.text(x,y,symbol+'\n'+'\n'.join(textwrap.wrap(name,23,break_long_words=False)),ha='center',va='center',fontsize=9,
                    bbox=dict(boxstyle='round,pad=.4',fc='#ffffff',ec=color))
        ax.text(0,0,VARIABLES[i]['symbol']+'\n'+'\n'.join(textwrap.wrap(VARIABLES[i]['name'],19)),
                ha='center',va='center',fontsize=12,fontweight='bold',bbox=dict(boxstyle='round,pad=.7',fc='#e7eefb',ec='#254d85'))
        ax.set_title(VARIABLES[i]['symbol']+' — '+VARIABLES[i]['name'],fontsize=15,pad=18)
        fig.text(.5,.03,'Зелёный: положительное влияние (+1). Красный: отрицательное влияние (−1).',ha='center',fontsize=10)
        fig.savefig(directory / f'L{i+1}-graph.png', dpi=120, bbox_inches='tight', metadata={'Software':'Product company model'})
        plt.close(fig)


if __name__ == '__main__':
    generate()
