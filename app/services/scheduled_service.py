from pathlib import Path
import shutil
import time

from app.utils.constants import Constants


class ScheduledService:
    @staticmethod
    def remove_old_sessions_task():
        cutoff = time.time() - 86400
        for file in Path(Constants.PATH_TO_CALC_STORAGE_FILE).glob('*.json'):
            if file.stat().st_mtime < cutoff:
                calculation_id = file.stem
                file.unlink()
                for suffix in ('.png', '-q.png'):
                    (Path(Constants.PATH_SOLUTION_GRAPHS_IMAGE) / (calculation_id + suffix)).unlink(missing_ok=True)
                directory = Path(Constants.PATH_PETAL_GRAPHS_IMAGE) / calculation_id
                if directory.is_dir():
                    shutil.rmtree(directory)
