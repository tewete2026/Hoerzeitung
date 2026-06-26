import mariadb, os
from flask import Blueprint
from flask import current_app, session
from flask import request
from flask import render_template
from flask import redirect, url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from ..db import Configure
from ..db import get_db, getLogin
from .. import version

bp = Blueprint("s_service", __name__, url_prefix="/S-Service")


@bp.route("/Neue-Codes", methods=['GET', 'POST'])
def confcreate():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] == 0:
        abort(403)
    
    ts = current_app.config["TS"]

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True

    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)

    if auth_code_valid:
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

    return render_template("service/confcreate.html", conf=conf)


@bp.route("/", methods=['GET', 'POST'])
def start():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] == 0:
        abort(403)
    
    ts = current_app.config["TS"]

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True

    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)

    if auth_code_valid:
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

    return render_template("service/confcreate.html", conf=conf)


