"""Build the tested scenario bank offline; never called by the web endpoint."""
import json
import random
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.model import EDGES, MODEL, VARIABLES
from app.services.calculation_service import build_configuration, integrate_model, solve_ivp


def candidate(rng):
    number = lambda lo, hi: rng.randint(lo, hi) / 10
    values = dict(t_start=0, t_end=1, polynomial_degree=3)
    for v in VARIABLES:
        symbol = v['symbol']
        values[symbol] = number(5, 9)
        values[symbol+'_scale'] = number(7, 10)
        values[symbol+'_minimum'] = number(1, 3)
    for i in range(1, 6):
        for k, bounds in enumerate(((0,2),(-1,1),(-1,1),(-1,1))):
            values[f'q{i}_A{k}'] = number(*bounds)
    for edges in EDGES:
        for edge in edges:
            bounds = ((5,7) if edge['sign'] == 1 else (2,4), (1,2), (-1,1), (-1,1))
            for k, interval in enumerate(bounds):
                values[f"f{edge['function']}_A{k}"] = number(*interval)
    return values


def limited_solver(fun, *args, **kwargs):
    calls = 0
    def bounded(t, y):
        nonlocal calls
        calls += 1
        if calls > 5000:
            raise ValueError('Offline candidate exceeded evaluation budget')
        return fun(t, y)
    return solve_ivp(bounded, *args, **kwargs)


def verify(values):
    summaries = {}
    for degree in range(4):
        fields = dict(values, polynomial_degree=degree)
        with patch('app.services.calculation_service.solve_ivp', limited_solver):
            result = integrate_model(build_configuration(fields))
        trajectory = np.array(result['trajectory'])
        if not np.isfinite(trajectory).all() or trajectory.min() < 0 or trajectory.max() > 1:
            raise ValueError('Trajectory outside [0,1]')
        times = np.array(result['times'])
        chord = trajectory[0] + times[:,None] * (trajectory[-1]-trajectory[0])
        summaries[str(degree)] = dict(final=result['solution'], minimum=float(trajectory.min()),
                                     maximum=float(trajectory.max()),
                                     chord_deviation=float(np.max(np.abs(trajectory-chord))))
    return summaries


def main():
    rng = random.Random(20261029)
    scenarios = []
    for attempt in range(1, 5001):
        values = candidate(rng)
        try:
            validation = verify(values)
        except ValueError:
            continue
        scenarios.append(dict(id=len(scenarios)+1, values=values, validation=validation))
        if len(scenarios) % 20 == 0:
            print(f'Accepted {len(scenarios)}/200; attempts {attempt}', flush=True)
        if len(scenarios) == 200:
            break
    if len(scenarios) != 200:
        raise RuntimeError(f'Only {len(scenarios)} valid scenarios; existing bank was not changed')
    output = Path(__file__).resolve().parents[1] / 'app/data/tested_scenarios.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    bank = dict(model_version=MODEL['version'], interval=[0,1], validated_degrees=[0,1,2,3],
                seed=20261029, attempts=attempt, count=len(scenarios), scenarios=scenarios)
    output.write_text(json.dumps(bank, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(f'Saved {len(scenarios)} scenarios, {len(scenarios)*4} successful calculations: {output}', flush=True)


if __name__ == '__main__':
    main()
