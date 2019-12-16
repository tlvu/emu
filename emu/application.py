import os
from pywps.app.Service import Service

from .processes import processes


def make_app(cfgfiles=None):
    app = Service(processes=processes, cfgfiles=cfgfiles)
    return app
