"""Shared line identities for the interactive chart and exported reports."""

SERIES_STYLES = [
    {'color': '#0072B2', 'dash': []},
    {'color': '#D55E00', 'dash': []},
    {'color': '#009E73', 'dash': []},
    {'color': '#CC3377', 'dash': []},
    {'color': '#B88600', 'dash': []},
    {'color': '#6F42C1', 'dash': []},
    {'color': '#00A6B2', 'dash': []},
    {'color': '#A51C30', 'dash': [7, 3]},
    {'color': '#637400', 'dash': [7, 3]},
    {'color': '#3F51B5', 'dash': [7, 3]},
    {'color': '#8C564B', 'dash': [7, 3]},
    {'color': '#E7298A', 'dash': [2, 3]},
    {'color': '#008B8B', 'dash': [2, 3]},
    {'color': '#333333', 'dash': [9, 3, 2, 3]},
    {'color': '#A65E00', 'dash': [9, 3, 2, 3]},
]


def spread_labels(targets, lower, upper, gap):
    """Place labels in sorted vertical order without overlap or clipping."""
    if not targets:
        return []
    gap = min(gap, (upper - lower) / max(1, len(targets) - 1))
    order = sorted(range(len(targets)), key=targets.__getitem__)
    positions = []
    for i in order:
        positions.append(max(targets[i], positions[-1] + gap if positions else lower))
    positions[-1] = min(positions[-1], upper)
    for i in range(len(positions) - 2, -1, -1):
        positions[i] = min(positions[i], positions[i+1] - gap)
    result = [0] * len(targets)
    for i, position in zip(order, positions):
        result[i] = max(lower, min(upper, position))
    return result
