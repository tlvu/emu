import os
from pywps.app.Service import Service

from .processes import processes


def create_app(cfgfiles=None):
    config_files = [os.path.join(os.path.dirname(__file__), 'default.cfg')]
    if cfgfiles:
        config_files.extend(cfgfiles)
    service = Service(processes=processes, cfgfiles=config_files)
    return service


application = create_app()
