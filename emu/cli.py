###########################################################
# Demo WPS service for testing and debugging.
#
# See the werkzeug documentation on how to use the debugger:
# http://werkzeug.pocoo.org/docs/0.12/debug/
###########################################################

import os
import psutil
import click
from pywps.app.Service import Service
from pywps import configuration
from pywps.watchdog import WatchDog

from .wsgi import create_app
from urllib.parse import urlparse

PID_FILE = os.path.abspath(os.path.join(os.path.curdir, "pywps.pid"))

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def get_host():
    url = configuration.get_config_value('server', 'url')
    url = url or 'http://localhost:5000/wps'

    click.echo("starting WPS service on {}".format(url))

    parsed_url = urlparse(url)
    if ':' in parsed_url.netloc:
        host, port = parsed_url.netloc.split(':')
        port = int(port)
    else:
        host = parsed_url.netloc
        port = 80
    return host, port


def run_process_action(action=None):
    """Run an action with psutil on current process
    and return a status message."""
    action = action or 'status'
    try:
        with open(PID_FILE, 'r') as fp:
            pid = int(fp.read())
            p = psutil.Process(pid)
            if action == 'stop':
                p.terminate()
                msg = "pid={}, status=terminated".format(p.pid)
            else:
                from psutil import _pprint_secs
                msg = "pid={}, status={}, created={}".format(
                    p.pid, p.status(), _pprint_secs(p.create_time()))
        if action == 'stop':
            os.remove(PID_FILE)
    except IOError:
        msg = 'No PID file found. Service not running? Try "netstat -nlp | grep :5000".'
    except psutil.NoSuchProcess as e:
        msg = e.msg
    click.echo(msg)


def _run(application, bind_host=None, daemon=False):
    from werkzeug.serving import run_simple
    # call this *after* app is initialized ... needs pywps config.
    host, port = get_host()
    bind_host = bind_host or host
    # need to serve the wps outputs
    static_files = {
        '/outputs': configuration.get_config_value('server', 'outputpath')
    }
    run_simple(
        hostname=bind_host,
        port=port,
        application=application,
        use_debugger=False,
        use_reloader=False,
        threaded=True,
        # processes=2,
        use_evalex=not daemon,
        static_files=static_files)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def cli():
    """Command line to start/stop a PyWPS service.

    Do not use this service in a production environment.
    It's intended to be running in a test environment only!
    For more documentation, visit http://pywps.org/doc
    """
    pass


@cli.command()
def status():
    """Show status of PyWPS service"""
    run_process_action(action='status')


@cli.command()
def stop():
    """Stop PyWPS service"""
    run_process_action(action='stop')


@cli.command()
@click.option('--config', '-c', metavar='PATH', help='path to pywps configuration file.')
@click.option('--bind-host', '-b', metavar='IP-ADDRESS', default='127.0.0.1',
              help='IP address used to bind service.')
@click.option('--daemon', '-d', is_flag=True, help='run in daemon mode.')
def start(config, bind_host, daemon):
    """Start PyWPS service.
    This service is by default available at http://localhost:5000/wps
    """
    if os.path.exists(PID_FILE):
        click.echo('PID file exists: "{}". Service still running?'.format(PID_FILE))
        os._exit(0)
    cfgfiles = []
    if config:
        cfgfiles.append(config)
    app = create_app(cfgfiles=cfgfiles)
    # let's start the service ...
    # See:
    # * https://github.com/geopython/pywps-flask/blob/master/demo.py
    # * http://werkzeug.pocoo.org/docs/0.14/serving/
    if daemon:
        # daemon (fork) mode
        pid = None
        try:
            pid = os.fork()
            if pid:
                click.echo('forked process id: {}'.format(pid))
                with open(PID_FILE, 'w') as fp:
                    fp.write("{}".format(pid))
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if pid == 0:
            os.setsid()
            _run(app, bind_host=bind_host, daemon=True)
        else:
            os._exit(0)
    else:
        # no daemon
        # _run(app, bind_host=bind_host)
        import signal
        import threading
        watchdog = WatchDog(cfgfiles)
        signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
        try:
            t = threading.Thread(target=_run, args=(app, bind_host))
            t.setDaemon(True)
            t.start()
            watchdog.run()
        except KeyboardInterrupt:
            pass
