"""Render configuration for sequential calculations on a small instance."""

import os

bind = '0.0.0.0:' + os.environ.get('PORT', '10000')
# Matplotlib uses shared state. Keep requests in a single process and thread.
workers = 1
worker_class = 'sync'
threads = 1
# Generating all plots and a PDF can take longer on the free CPU.
timeout = 180
graceful_timeout = 30
accesslog = '-'
errorlog = '-'
capture_output = True
# Set these before importing NumPy/SciPy, including for manual deployments.
raw_env = ['OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=1', 'MPLBACKEND=Agg']
