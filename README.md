# software_quality_determinant

## Overview
A web application for determining the quality of designed information systems.

## Local Development
* Use Python 3.13. Create a fresh environment when changing Python versions.
* Install environment
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

* Run server `python manage.py runserver`
* Point your web browser to http://localhost:5000/

## PyCharm
Open the project and select the shared **Application** run configuration, then press
Run (Shift+F10). It uses `.venv/Scripts/python.exe`, runs `manage.py runserver`
from the project root, and serves http://127.0.0.1:5000/.
The environment must be created and dependencies installed as described above.

PDF report export additionally requires the external `wkhtmltopdf` executable
installed and available on `PATH`. Calculation and graph generation work without it.

## Documentation
The /documents page contains instructions for using the application.
