import datetime, pytz, os
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from flask import Flask, url_for, send_from_directory
from flask import render_template, redirect
from flask import request
from logging.config import dictConfig
from .db import get_db, Configure
from . import version, credentials

class Http_Helper:
    def __init__(self, host:str):
        self.host = host
    def goTo(self, uri:str):
        return self.host + uri
    

class TimeSet:
    def __init__(self, tz:str):
        self.__tz = pytz.timezone(tz)
        self.__dt = datetime.datetime
    def today(self):
        # return self.__dt.fromtimestamp(timestamp=datetime.datetime.today().timestamp(), tz=self.__tz)
        return self.todaytime().today()
    def todaytime(self):
        return self.__dt.now(tz=self.__tz)
    def isocalendar(self, ts=None):
        if not ts: ts = self.todaytime()
        return self.__dt.isocalendar(ts)
    def fromtimestamp(self, ts:float):
        return self.__dt.fromtimestamp(timestamp=ts, tz=self.__tz)
    def addtimezone(self, datetime:datetime.datetime):
        timestamp_float = datetime.timestamp()
        return self.fromtimestamp(timestamp_float)
    def delta(self, days=None, years=None, months=None):
        if days is not None:
            delta = relativedelta(days=days)
        elif years is not None:
            delta = relativedelta(years=years)
        elif months is not None:
            delta = relativedelta(months=months)
        return self.__dt.now() + delta


def create_app(test_config="DEV"):
    """Create and configure an instance of the Flask application.
       First config the logger"""
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }, 'mail': {
            'format': '[%(asctime)s] in %(module)s: %(message)s',
        }},
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
            },
            "file1": {
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 1048576,
                "backupCount": 10,
                "filename": f"/var/log/python/{version.Configs.APP_NAME}.log",
                "formatter": "default"
            },
            "file2": {
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 1048576,
                "backupCount": 10,
                "filename": f"/var/log/python/{version.Configs.APP_NAME}_ERR.log",
                "formatter": "default",
                'level': 'ERROR'
            },
            "smtp": {
                "class": "logging.handlers.SMTPHandler",
                "mailhost": ("localhost",825),
                "fromaddr": f"{version.Configs.APP_NAME}-noreply@drk-nhz.de",
                "toaddrs": credentials.EMails.SMTPHandler,
                "subject": "Flask-Mail-Handler",
                "formatter": "mail",
                'level': 'ERROR'
            },
        },
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi', 'file1', 'file2', 'smtp']
        }
    })
    inst_path = {}
    inst_path.update({"DEV":"/home/thomas/Dokumente/Cloudstation/Development/Python/DRK_NHZ/src/instance"})
    inst_path.update({"PROD":"/home/python/PyApps/webapps/nhz_instance"})
    app = Flask(version.Configs.APP_NAME, instance_relative_config=False, instance_path=inst_path[test_config], static_url_path=f"/src")
    app.logger.debug("Line Statement Prefix=%s:",app.jinja_env.line_statement_prefix)
    if test_config == "DEV":
        modname = "/"
        ownhost = "http://localhost:5000"
    else:
        modname = f"/{version.Configs.APP_NAME}"
        ownhost = "https://hoerzeitung.drk-norderstedt.ipv64.net/nhz"
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY=credentials.Passwords.SECRET_KEY,
        OWN_URL=Http_Helper(ownhost),
        SESSION_COOKIE_NAME="drk-nhz-session",
        SESSION_COOKIE_PATH=modname,
        PERMANENT_SESSION_LIFETIME=timedelta(days=360),
        TS=TimeSet("Europe/Berlin"),
        HOSTNAME = os.uname().nodename,
        MAX_CONTENT_LENGTH = 150 * 1000 * 1000,
        VERSION = version.Configs.APP_VERSION,
        CREATED = version.Configs.APP_CREATED,
        TEST_RUN=False,
        DB_POOL=None,
        NO_POOL_AVAILABLE=False,
        FREE_CODE=credentials.Passwords.FREE_CODE,
        SEND_TO=credentials.EMails.SMTPHandler, SEND_FROM=f"{version.Configs.APP_NAME}@drk-nhz.de",
        SMTP_HOST="localhost", SMTP_PORT=25, SMTP_USER=None, SMTP_PWD=None
    )


    @app.after_request
    def add_several_headers(response):
        response.headers['Cache-Control']='no-cache'
        response.headers['Pragma']='no-cache'
        return response

    @app.route("/")
    def default():
        return redirect(url_for("bx_start.start"))

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        conf = Configure(title="Norderstedter Hörzeitung - Seite nicht gefunden", app='notFound', link='link-main', request=request, current_app=app)
        return render_template('pageNotFound.html', conf=conf, javascript=conf.javascript.getOut()), 404

    @app.errorhandler(413)
    def requestEntityTooLarge(e):
        conf = Configure(title="Norderstedter Hörzeitung - Datei zum Hochladen zu groß", app='entityTooLarge', link='link-main', request=request, current_app=app)
        return render_template('requestEntityTooLarge.html', conf=conf, javascript=conf.javascript.getOut()), 413

    @app.errorhandler(422)
    def requestUnprocessable(e):
        conf = Configure(title="Norderstedter Hörzeitung - Wichtige Prozesse können nicht ausgeführt werden", app='Unprocessable', link='link-main', request=request, current_app=app)
        return render_template('requestUnprocessable.html', conf=conf, javascript=conf.javascript.getOut()), 422

    @app.errorhandler(500)
    def internal_server_error(e):
        conf = Configure(title="Norderstedter Hörzeitung - Interner Fehler", app='notFound', link='link-main', request=request, current_app=app)
        return render_template('internalError.html', conf=conf, javascript=conf.javascript.getOut()), 500

    @app.errorhandler(403)
    def access_not_allowed(e):
        conf = Configure(title="Norderstedter Hörzeitung - Keine Berechtigung", app='notFound', link='link-main', request=request, current_app=app)
        return render_template('notAllowed.html', conf=conf, javascript=conf.javascript.getOut()), 403

    @app.errorhandler(405)
    def method_not_valid(e):
        conf = Configure(title="Norderstedter Hörzeitung - Methode nicht erlaubt", app='notFound', link='link-main', request=request, current_app=app)
        return render_template('methodNotAllowed.html', conf=conf, javascript=conf.javascript.getOut()), 405
                
    @app.route("/favicon.ico")
    def favicon():
        path = app.root_path + '/static'
        return send_from_directory(path, 'Logo_Title.png')

    app.logger.info("Name=%s; Version detected=%s; Created=%s", app.name, app.config["VERSION"], app.config["CREATED"])

    if test_config == "DEV":
        app.config.from_mapping(TEST_RUN=True, SEND_TO='Thomas@twtdiskstation.local', SMTP_HOST='192.168.168.200', SMTP_PORT=25, SMTP_USER='Thomas', SMTP_PWD='Tomgret')
        app.logger.info("Test-Dev active; Logger=%s; Parent-Logger=%s", app.logger.name, app.logger.parent.name)
        for hdlr in app.logger.parent.handlers:
            if hdlr.get_name() == "smtp":
                app.logger.parent.removeHandler(hdlr)
                app.logger.debug("Handler %s aus %s entfernt.", hdlr.get_name(), app.logger.parent.name)
    else:
        app.logger.info("Production active")

    # register the database commands
    from . import db
    if db.init_app(app) == "ERR":
        app.config.from_mapping(NO_POOL_AVAILABLE=True)

    # apply the blueprints to the app
    from . import main, bx_start
    from .service import service, ax_member, ax_default, srv_tool, ax_episode
    app.register_blueprint(main.bp)
    app.register_blueprint(bx_start.bp)
    app.register_blueprint(service.bp)
    app.register_blueprint(ax_default.bp)
    app.register_blueprint(ax_member.bp)
    app.register_blueprint(ax_episode.bp)
    app.register_blueprint(srv_tool.bp)
    app.logger.debug(f"Registered Blueprint Count: {len(app.blueprints.items())}")
    for bp_name, blpr in app.blueprints.items():
        app.logger.debug(f"Registered Blueprint: {bp_name}, {blpr.import_name}, {blpr.url_prefix}, {blpr.root_path}")
    for rul in app.url_map.iter_rules():
        app.logger.debug(f"Registered Rules: Endpoint={rul.endpoint}, Rule={rul.rule}")
    for hdlr in app.logger.parent.handlers:
        app.logger.debug("Registered Handler in %s: %s", app.logger.parent.name, hdlr.get_name())

    app.add_url_rule(f"/{version.Configs.APP_NAME}/", view_func=main.index)

    return app
