import os

workers = 2
bind = '0.0.0.0:8000'

# allow to override settings by setting e.g. GUNICORN_WORKERS=1
for k,v in os.environ.items():
    if k.startswith("GUNICORN_"):
        key = k.split('_', 1)[1].lower()
        locals()[key] = v
