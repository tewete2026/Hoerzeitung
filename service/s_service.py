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
from .srv_tool import generateCode

bp = Blueprint("s_service", __name__, url_prefix="/S-Service")


@bp.route("/Neue-Codes", methods=['GET', 'POST'])
def confcreate():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] == 0:
        abort(403)
    
    ts = current_app.config["TS"]
    error = False
    post_request = False
    quantity = ""
    level = "-1"

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True

    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    
    if auth_code_valid and post_request:
        if len(form_data['quantity']) == 0:
            conf.error['quantity'] = "Die Anzahl darf nicht leer sein!"
            error = True
        else:
            quantity = form_data['quantity']
            if not form_data['quantity'].isnumeric():
                conf.error['quantity'] = "Die Anzahl muss numerisch sein!"
                error = True
            else:
                quantity = int(form_data['quantity'])
        if len(form_data['level']) == 0 or form_data['level'] == '-1':
            conf.error['level'] = "Die Berechtigungsebene muss ausgewählt werden!"
            error = True
        else:
            level = form_data['level']
        if not error:
            if quantity > 10:
                conf.error['quantity'] = "Die Anzahl darf z.Zt. nicht größer 10 sein!"
                error = True
            if session['dbdata']['seclevel'] == 1 and level > 0:
                conf.error['level'] = "Die Berechtigungsebene darf nicht größer 0 sein!"
                error = True
            elif session['dbdata']['seclevel'] == 2 and level > 1:
                conf.error['level'] = "Die Berechtigungsebene darf nicht größer 1 sein!"
                error = True
            if not error:
                try:
                    db = get_db()
                    if not db:
                        raise mariadb.PoolError("Kein Databasepool vorhanden.")
                    db.begin()
                    cur = db.cursor(dictionary=True)
                    cur.execute("SELECT current_timestamp as tmst")
                    tmst = cur.fetchone()['tmst']
                    cur.execute("SELECT MAX(pnr)+1 as max_pnr from tUser FOR UPDATE")
                    max_pnr = cur.fetchone()['max_pnr']
                    cur.execute("INSERT INTO tHistory(quantity,seclevel,pnrcreate,createDate) values(?,?,?,?)", (quantity, level, session['dbdata']['pnr'], tmst))
                    last_id = cur.lastrowid

                    stored = []
                    sql = "INSERT INTO tUser(pnr,seclevel,pnrcreate,histid,freecode,createDate) values(?,?,?,?,?,?)"
                    for i in range(quantity):
                        cur.execute(sql, (max_pnr+i, level, session['dbdata']['pnr'], last_id, generateCode(), tmst))
                        if cur.rowcount == 1:
                            stored.append(cur.lastrowid)
                    if len(stored) == quantity:
                        conf.error['result_succ'] = "Erstellung wurde erfolgreich durchgeführt. Das Ergebnis wird per Download bereit gestellt."
                        db.commit()
                    else:
                        conf.error['result_err'] = "Erstellung wurde NICHT erfolgreich durchgeführt."
                        db.rollback()
                    cur.close()
                    db.close()
                except mariadb.IntegrityError as err:
                    # rc_code["status"] = "DBL"
                    current_app.logger.warning("Datenbank-doppelter Eintrag: %s/ax-submit-coaches/%s", bp.name, err)
                    db.rollback()
                    db.close()
                except mariadb.Error as err:
                    db.close()
                    current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
                    abort(500)
    
    if auth_code_valid:
        conf.append("show_navall", True)
        conf.append("seclevel", session['dbdata']['seclevel'])
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    return render_template("service/confcreate.html", conf=conf, javascript=conf.javascript.getOut())


@bp.route("/", methods=['GET', 'POST'])
def unused():
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
        conf.append("show_navall", True)
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

    return render_template("service/confcreate.html", conf=conf)


