import mariadb, os
from flask import Blueprint
from flask import current_app, session
from flask import request, make_response
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
    auth_code_valid = False
    quantity = "1"
    level = "-1"
    if session['dbdata']['seclevel'] == 1:
        level = "0"

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    conf.error['histid'] = ""
    try:
        db = get_db()
        if not db:
            raise mariadb.PoolError("Kein Databasepool vorhanden.")
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id,DATE_FORMAT(DATE(createDate),'%d.%m.%Y') as createDate,quantity from tHistory WHERE pnrcreate=? ORDER BY id DESC", (session['dbdata']['pnr'],))
        dbdata = cur.fetchall()
        conf.append('history', dbdata)
    except mariadb.Error as err:
        if db: db.close()
        current_app.logger.error("Datenbank-Fehler Lesen History: %s/confcreate/%s", bp.name, err)
    
    if auth_code_valid and post_request:
        # Download aktiviert
        histid = form_data['histid']
        if len(histid) > 0:
            try:
                db = get_db()
                if not db:
                    raise mariadb.PoolError("Kein Databasepool vorhanden.")
                cur = db.cursor(dictionary=True)
                cur.execute("SELECT histid as Eintrag_Nr,pnr as Persoenl_Nr,pnrcreate as Erstellt_Von,seclevel as Berechtigungsebene,freecode as Freischaltcode,DATE_FORMAT(DATE(createDate),'%d.%m.%Y') as Erstellt_Am from tUser WHERE histid=? ORDER BY pnr", (histid,))
                dbdata = cur.fetchall()
                cur.close()
                db.close()
                resp = make_response(dbdata)
                resp.content_encoding = "UTF-8"
                resp.automatically_set_content_length = True
                resp.mimetype = "application/json"
                resp.default_mimetype = "text/csv"
                resp.headers['Content-Disposition']=f'attachment; filename="Neue_Freischaltcodes_{histid}.json"'
                resp.access_control_max_age = 0
                resp.headers['Cache-Control']='no-cache'
                resp.headers['Pragma']='no-cache'
                return resp
            except mariadb.Error as err:
                conf.error['result_err'] = f"Datenbankfehler: {err}. Download wurde NICHT erfolgreich durchgeführt."
                if db: db.close()
                current_app.logger.error("Datenbank-Fehler: %s/confcreate/%s", bp.name, err)
                error = True

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
            level = int(form_data['level'])
        if not error:
            if quantity > 10:
                conf.error['quantity'] = "Die Anzahl darf z.Zt. nicht größer 10 sein!"
                error = True
            if session['dbdata']['seclevel'] == 0:
                conf.error['level'] = "Die Berechtigungsebene darf nichts erstellen!"
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
                        conf.error['result_succ'] = f"Erstellung {last_id} wurde erfolgreich durchgeführt. Das Ergebnis wird per Download im JSON-Format bereit gestellt."
                        conf.error['histid'] = last_id
                        db.commit()
                    else:
                        conf.error['result_err'] = "Erstellung wurde NICHT vollständig durchgeführt."
                        db.rollback()
                    cur.close()
                    db.close()
                except mariadb.IntegrityError as err:
                    conf.error['result_err'] = f"Datenbankfehler: {err}. Erstellung wurde NICHT erfolgreich durchgeführt."
                    current_app.logger.warning("Datenbank-doppelter Eintrag: %s/confcreate/%s", bp.name, err)
                    db.rollback()
                    db.close()
                except mariadb.Error as err:
                    conf.error['result_err'] = f"Datenbankfehler: {err}. Erstellung wurde NICHT erfolgreich durchgeführt."
                    if db: db.rollback()
                    if db: db.close()
                    current_app.logger.error("Datenbank-Fehler: %s/confcreate/%s", bp.name, err)
    
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


