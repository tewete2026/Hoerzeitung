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


@bp.route("/Verwalten-Codes", methods=['GET', 'POST'])
def confmanage():
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
    
    if auth_code_valid:
        conf.append("show_navall", True)
        conf.append("seclevel", session['dbdata']['seclevel'])
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    return render_template("service/confmanage.html", conf=conf, javascript=conf.javascript.getOut())



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
    
    if auth_code_valid and post_request:
        # Löschen Chargen-Nummern aktiviert
        if 'trashid' in form_data:
            trashid = form_data['trashid']
            try:
                db = get_db()
                if not db:
                    raise mariadb.PoolError("Kein Databasepool vorhanden.")
                db.begin()
                cur = db.cursor(dictionary=True)
                cur.execute(f"DELETE from tUser WHERE histid in ({trashid})")
                if cur.rowcount < 1:
                    conf.error['result_err_trash'] = "Keine User-Einträge gelöscht."
                else:
                    conf.error['result_succ_trash'] = f"{cur.rowcount} User-Einträge gelöscht."
                cur.execute(f"DELETE from tHistory WHERE id in ({trashid})")
                if cur.rowcount < 1:
                    t = "Keine Chargen-Einträge gelöscht."
                    if 'result_err_trash' in conf.error:
                        t += "/" + conf.error['result_err_trash']
                    conf.error['result_err_trash'] = t
                else:
                    t = f"{cur.rowcount} Chargen-Einträge gelöscht."
                    if 'result_succ_trash' in conf.error:
                        t += "/" + conf.error['result_succ_trash']
                    conf.error['result_succ_trash'] = t
                db.commit()
                cur.close()
                db.close()
            except mariadb.Error as err:
                conf.error['result_err_trash'] = f"Datenbankfehler: {err}. Löschen Chargen wurde NICHT erfolgreich durchgeführt."
                if db: db.close()
                current_app.logger.error("Datenbank-Fehler: %s/confcreate/%s", bp.name, err)
                error = True
            
        # Download aktiviert
        if 'histid' in form_data:
            histid = form_data['histid']
            try:
                db = get_db()
                if not db:
                    raise mariadb.PoolError("Kein Databasepool vorhanden.")
                cur = db.cursor(dictionary=True)
                cur.execute("SELECT histid as Charge_Nr,pnr as Konto_Nr,pnrcreate as Erstellt_Von,seclevel as Berechtigungsebene,freecode as Freischaltcode,DATE_FORMAT(DATE(createDate),'%d.%m.%Y') as Erstellt_Am from tUser WHERE histid=? ORDER BY pnr", (histid,))
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

        if 'quantity' in form_data:
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
                if session['dbdata']['seclevel'] == 1 and level > 0:
                    conf.error['level'] = "Die Berechtigungsebene darf nicht größer 0 sein!"
                    error = True
                elif session['dbdata']['seclevel'] == 2 and level > 1:
                    conf.error['level'] = "Die Berechtigungsebene darf nicht größer 1 sein!"
                    error = True
                elif session['dbdata']['seclevel'] == 3 and level > 2:
                    conf.error['level'] = "Die Berechtigungsebene darf nicht größer 2 sein!"
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
                            cur.execute(sql, (max_pnr+i, level, session['dbdata']['pnr'], last_id, generateCode(level), tmst))
                            if cur.rowcount == 1:
                                stored.append(cur.lastrowid)
                        if len(stored) == quantity:
                            conf.error['result_succ'] = f"Erstellung der Charge {last_id} wurde erfolgreich durchgeführt. Das Ergebnis wird per Download im JSON-Format bereit gestellt."
                            conf.error['histid'] = last_id
                            db.commit()
                        else:
                            conf.error['result_err'] = f"Erstellung der Charge {last_id} wurde NICHT vollständig durchgeführt."
                            db.rollback()
                        cur.close()
                        db.close()
                    except mariadb.IntegrityError as err:
                        conf.error['result_err'] = f"Datenbankfehler: {err}. Erstellung der Charge wurde NICHT erfolgreich durchgeführt."
                        current_app.logger.warning("Datenbank-doppelter Eintrag: %s/confcreate/%s", bp.name, err)
                        db.rollback()
                        db.close()
                    except mariadb.Error as err:
                        conf.error['result_err'] = f"Datenbankfehler: {err}. Erstellung der Charge wurde NICHT erfolgreich durchgeführt."
                        if db: db.rollback()
                        if db: db.close()
                        current_app.logger.error("Datenbank-Fehler: %s/confcreate/%s", bp.name, err)
    
    if auth_code_valid:
        conf.append("show_navall", True)
        conf.append("seclevel", session['dbdata']['seclevel'])
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)

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

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    return render_template("service/confcreate.html", conf=conf, javascript=conf.javascript.getOut())


@bp.route("/Export-Liste-<level>", methods=['GET'])
def export(level):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] == 0:
        abort(403)
    
    ts = current_app.config["TS"]
    auth_code_valid = False

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True

    conf = Configure("Norderstedter Hörzeitung - Export", request, current_app)

    if auth_code_valid:
        error = False
        if level.isnumeric:
            level = int(level)
        else:
            level = 0
            error = True
            conf.error['level'] = "Parameter 'level' ist nicht numerisch!"
        if session['dbdata']['seclevel'] == 1 and level > 0:
            conf.error['level'] = "Die Berechtigungsebene darf nicht größer 0 sein!"
            error = True
        elif session['dbdata']['seclevel'] == 2 and level > 1:
            conf.error['level'] = "Die Berechtigungsebene darf nicht größer 1 sein!"
            error = True
        elif session['dbdata']['seclevel'] == 3 and level > 2:
            conf.error['level'] = "Die Berechtigungsebene darf nicht größer 2 sein!"
            error = True
        if not error:
            try:
                db = get_db()
                if not db:
                    raise mariadb.PoolError("Kein Databasepool vorhanden.")
                cur = db.cursor(dictionary=True)
                cur.execute("SELECT histid as Charge_Nr,pnr as Konto_Nr,pnrcreate as Erstellt_Von,seclevel as Berechtigungsebene,freecode as Freischaltcode,DATE_FORMAT(DATE(createDate),'%d.%m.%Y') as Erstellt_Am from tUser WHERE seclevel=? ORDER BY pnr", (level,))
                dbdata = cur.fetchall()
                cur.close()
                db.close()
                resp = make_response(dbdata)
                resp.content_encoding = "UTF-8"
                resp.automatically_set_content_length = True
                resp.mimetype = "application/json"
                resp.default_mimetype = "text/csv"
                resp.headers['Content-Disposition']=f'attachment; filename="Export_Freischaltcodes_Ber-Ebene_{level}.json"'
                resp.access_control_max_age = 0
                resp.headers['Cache-Control']='no-cache'
                resp.headers['Pragma']='no-cache'
                return resp
            except mariadb.Error as err:
                if db: db.close()
                conf.error['result_err'] = f"Datenbankfehler: {err}. Export wurde NICHT erfolgreich durchgeführt."
                current_app.logger.error("Datenbank-Fehler: %s/export/%s", bp.name, err)

    return render_template("internalError.html", conf=conf)


