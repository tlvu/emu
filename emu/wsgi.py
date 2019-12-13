import os
from pywps.app.Service import Service

from .processes import processes


def create_app(cfgfiles=None):
    service = Service(processes=processes, cfgfiles=cfgfiles)
    return service


application = create_app()
