from pywps.app.Service import Service


def make_app(cfgfiles=None):
    app = Service(cfgfiles=cfgfiles)
    return app
