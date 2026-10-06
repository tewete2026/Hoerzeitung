import mariadb, os, subprocess, sys
from flask import Blueprint
from flask import current_app, session
from flask import request, make_response
from flask import render_template
from flask import redirect, url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from ..db import Configure
from ..db import get_db, getLogin
from .. import version, tools

bp = Blueprint("s_service", __name__, url_prefix="/S-Service")


'''@bp.route("/Verwalten-Codes", methods=['GET', 'POST'])
def confmanage():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]
    error = False
    post_request = False
    auth_code_valid = False
    quantity = "1"
    level = "-1"

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    
    if auth_code_valid:
        conf.initlogin(session['dbdata'])
    
    if auth_code_valid:
        conf.append("show_navall", True)
        if session['dbdata']['seclevel'] > 1:
            conf.append("show_navtop", True)

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    return render_template("service/confmanage.html", conf=conf, javascript=conf.javascript.getOut())
'''


@bp.route("/Upload-Episode", methods=['GET', 'POST'])
def confupload():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
        file = request.files['frm-main-file']
        filename = secure_filename(file.filename)
        print(form_data)
        # if len(filename) > 0 and "frm-main-set-base" in form_data: 
        if len(filename) > 0: 
            frm_main_datum = form_data["frm-main-datum"]
            frm_main_title = form_data["frm-main-title"]
            frm_main_summary = form_data["frm-main-summary"]
            frm_main_supporter = form_data["frm-main-supporter"]
            frm_main_team = form_data["frm-main-team"]
            suff = filename.rsplit('.')[1]
            basename = filename.rstrip(suff) + 'mp3'
            temp_name = current_app.instance_path + "/upload/" + filename
            temp_target = current_app.instance_path + "/upload/" + basename
            target_name = current_app.instance_path + "/long/" + basename
            file.save(temp_name)
            if not suff == 'mp3':
                shell_path = current_app.root_path + '/static/service/shell/convert_audio.sh'
                subprocess.run([shell_path, temp_name, temp_target])
            tools.setMp3Info(temp_target, (frm_main_title, frm_main_summary, frm_main_datum, frm_main_supporter, frm_main_team))
            # (title, description, published, size, duration, chapter, chapter_dict, image_dict) = tools.getMP3Info(temp_target)
            # print(title, description, published, size, duration, chapter, chapter_dict, image_dict)
            (size, duration) = tools.getMpegInfo(temp_target)
            # rc_code = submit_album(request.form, filename, target_name, size, duration)
            rc_code = {'submit_status':'OK'}
            if rc_code["submit_status"] == "OK":
                if target_name is not None:
                    os.replace(temp_target, target_name)
            else:
                if temp_name is not None and os.path.exists(temp_name):
                    os.remove(temp_name)
                if temp_target is not None and os.path.exists(temp_target):
                    os.remove(temp_target)

            return redirect(url_for("bx_s_start.s_album"))
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    conf.append('datetimenow', ts.now_local())
    
    if auth_code_valid:
        conf.initlogin(session['dbdata'])
        conf.append("show_navall", True)
        if session['dbdata']['seclevel'] > 1:
            conf.append("show_navtop", True)

    return render_template("service/confupload.html", conf=conf)


@bp.route("/Neue-Codes", methods=['GET', 'POST'])
def confcreate():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]
    conf_max_freecodes = current_app.config["max_freecodes"]
    error = False
    post_request = False
    auth_code_valid = False
    quantity = "1"
    level = "-1"

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    conf.append('conf_max_freecodes', conf_max_freecodes)
    
    if auth_code_valid:
        conf.initlogin(session['dbdata'])
    
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
                """ 
                    Prüfen, ob betroffene zu löschende Konto-Nummern ihrerseits Freischaltcodes für weitere Konto-Nummern erzeugt haben.
                    Wenn z.B. ein Konto der Ebene Leitung Freischaltcodes für Redakteur erzeugt hat und dieses Redakteur-Konto wiederum Konten für Hörer erzeugt hat,
                    dann kann die Charge mit dem zugehörigen Konto Redakteur nicht gelöscht werden. Erst muss das Redakteur-Konto seine Freischaltcodes löschen.
                    Dazu wird die Tabelle tUser mit sich selbst verknüpft über die Felder pnrcreate und pnr. Es dürfen keine Einträge geliefert werden, dann ist die Prüfung korrekt.
                """
                cur.execute(f"select a.id as a_id,b.id as b_id,a.pnr as a_pnr,b.pnr as b_pnr,a.pnrcreate as a_pnrcreate,b.pnrcreate as b_pnrcreate,a.histid as a_histid,b.histid as b_histid from tUser a join tUser b on a.pnr=b.pnrcreate where a.histid in ({trashid})")
                if cur.rowcount > 0:
                    dbdata = cur.fetchall()
                    a_pnr_err = []
                    b_pnr_err = []
                    for entry in dbdata:
                        a_spnr = str(entry['a_pnr'])
                        if a_pnr_err.count(a_spnr) <= 0: a_pnr_err.append(a_spnr)
                        b_spnr = str(entry['b_pnr'])
                        if b_pnr_err.count(b_spnr) <= 0: b_pnr_err.append(b_spnr)
                    conf.error['result_err_trash'] = f"Keine Löschung der gewählten Chargen erlaubt, da betroffene Konto-Nummern {",".join(a_pnr_err)} wiederum Freischaltcodes für Konto-Nummern {",".join(b_pnr_err)} erzeugt haben."
                else:
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
                cur.execute("SELECT histid as Charge_Nr,pnr as Konto_Nr,pnrcreate as Erstellt_Von,seclevel as Berechtigungsebene,freecode as Freischaltcode,DATE_FORMAT(createDate,'%d.%m.%Y') as Erstellt_Am,IF(active=1,TRUE,FALSE) as Ist_Aktiv,IF(guest=1,TRUE,FALSE) as Ist_Gast from tUser WHERE histid=? ORDER BY pnr", (histid,))
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
            quantity = form_data['quantity']
            if len(quantity) == 0:
                conf.error['quantity'] = "Die Anzahl darf nicht leer sein!"
                error = True
            else:
                if not quantity.isnumeric():
                    conf.error['quantity'] = "Die Anzahl muss numerisch sein!"
                    error = True
                else:
                    quantity = int(quantity)
                    if quantity > conf_max_freecodes:
                        conf.error['quantity'] = f"Die Anzahl darf z.Zt. nicht größer {conf_max_freecodes} sein!"
                        error = True
            if len(form_data['level']) == 0 or form_data['level'] == '-1':
                conf.error['level'] = "Die Berechtigungsebene muss ausgewählt werden!"
                error = True
            else:
                level = int(form_data['level'])
                if session['dbdata']['seclevel'] == 2 and level > 1:
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
                        cur.execute(sql, (max_pnr+i, level, session['dbdata']['pnr'], last_id, tools.generateCode(level), tmst))
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
        if session['dbdata']['seclevel'] > 1:
            conf.append("show_navtop", True)
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Databasepool vorhanden.")
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT id,DATE_FORMAT(createDate,'%d.%m.%Y') as createDate,quantity from tHistory WHERE pnrcreate=? ORDER BY id DESC", (session['dbdata']['pnr'],))
            dbdata = cur.fetchall()
            conf.append('history', dbdata)
        except mariadb.Error as err:
            if db: db.close()
            current_app.logger.error("Datenbank-Fehler Lesen History: %s/confcreate/%s", bp.name, err)

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    return render_template("service/confcreate.html", conf=conf)


@bp.route("/Export-Liste-<level>", methods=['GET'])
def export(level):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]
    auth_code_valid = False

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True

    conf = Configure("Norderstedter Hörzeitung - Export", request, current_app)

    if auth_code_valid:
        conf.initlogin(session['dbdata'])
        error = False
        if level.isnumeric():
            level = int(level)
        else:
            level = 0
            error = True
            conf.error['level'] = "Parameter 'level' ist nicht numerisch!"
        if session['dbdata']['seclevel'] == 2 and level > 1:
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
                cur.execute("SELECT histid as Charge_Nr,pnr as Konto_Nr,pnrcreate as Erstellt_Von,seclevel as Berechtigungsebene,freecode as Freischaltcode,DATE_FORMAT(createDate,'%d.%m.%Y') as Erstellt_Am,IF(active=1,TRUE,FALSE) as Ist_Aktiv,IF(guest=1,TRUE,FALSE) as Ist_Gast from tUser WHERE seclevel<=? ORDER BY seclevel DESC,pnr", (level,))
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


@bp.route("/Export-Liste-Letzter-Login", methods=['GET'])
def export_last_login():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]
    auth_code_valid = False

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True

    conf = Configure("Norderstedter Hörzeitung - Export Liste letzter Login", request, current_app)

    if auth_code_valid:
        conf.initlogin(session['dbdata'])
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Databasepool vorhanden.")
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT seclevel as Berechtigungs_Ebene,pnr as Konto_Nr,freecode as Freischaltcode,IFNULL(DATE_FORMAT(lastActive,'%d.%m.%Y'),'--') as Letzter_Login_Am,IF(active=1,TRUE,FALSE) as Ist_Aktiv,IF(guest=1,TRUE,FALSE) as Ist_Gast from tUser WHERE seclevel=0 ORDER BY pnr")
            dbdata = cur.fetchall()
            cur.close()
            db.close()
            resp = make_response(dbdata)
            resp.content_encoding = "UTF-8"
            resp.automatically_set_content_length = True
            resp.mimetype = "application/json"
            resp.default_mimetype = "text/csv"
            resp.headers['Content-Disposition']=f'attachment; filename="Export_Letzter_Login_Ber-Ebene_0.json"'
            resp.access_control_max_age = 0
            resp.headers['Cache-Control']='no-cache'
            resp.headers['Pragma']='no-cache'
            return resp
        except mariadb.Error as err:
            if db: db.close()
            conf.error['result_err'] = f"Datenbankfehler: {err}. Export wurde NICHT erfolgreich durchgeführt."
            current_app.logger.error("Datenbank-Fehler: %s/export_last_login/%s", bp.name, err)

    return render_template("internalError.html", conf=conf)


@bp.route("/Export-Liste-Media-Zugriff", methods=['GET'])
def export_media_access():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    
    ts = current_app.config["TS"]
    auth_code_valid = False

    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True

    conf = Configure("Norderstedter Hörzeitung - Export Liste Media Zugriff", request, current_app)

    if auth_code_valid:
        conf.initlogin(session['dbdata'])
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Databasepool vorhanden.")
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT seclevel as Berechtigungs_Ebene,pnr as Konto_Nr,freecode as Freischaltcode,DATE_FORMAT(accessDate,'%d.%m.%Y') as Medien_Zugriff_Am,media as Medien_Datei,accesscount as Anzahl_Zugriffe,IF(guest=1,TRUE,FALSE) as Ist_Gast from tLog ORDER BY accessDate DESC,pnr")
            dbdata = cur.fetchall()
            cur.close()
            db.close()
            resp = make_response(dbdata)
            resp.content_encoding = "UTF-8"
            resp.automatically_set_content_length = True
            resp.mimetype = "application/json"
            resp.default_mimetype = "text/csv"
            resp.headers['Content-Disposition']=f'attachment; filename="Export_Media_Zugriff.json"'
            resp.access_control_max_age = 0
            resp.headers['Cache-Control']='no-cache'
            resp.headers['Pragma']='no-cache'
            return resp
        except mariadb.Error as err:
            if db: db.close()
            conf.error['result_err'] = f"Datenbankfehler: {err}. Export wurde NICHT erfolgreich durchgeführt."
            current_app.logger.error("Datenbank-Fehler: %s/export_last_login/%s", bp.name, err)

    return render_template("internalError.html", conf=conf)


def submit_album(form_data, episode_filename, file_path, size, duration):
    rc_code = {"submit_status":"OK", "last_id":"(Neu)", "last_mode":"(none)"}
    try:
        item_id = item_timestamp = None
        episode_datum = form_data["frm-main-datum"]
        episode_title = form_data["frm-main-title"]
        episode_summary = form_data["frm-main-summary"]
        episode_chapter = form_data["frm-main-chapter"]
        episode_image = form_data["frm-main-team"]
        if "frm-main-aktiv" in form_data:
            episode_aktiv = form_data["frm-main-aktiv"]
        else: episode_aktiv = ''
        if "frm-main-replace" in form_data:
            episode_replace = form_data["frm-main-replace"]
        else: episode_replace = ''
        if len(form_data["frm-main-id"]) > 0:
            item_id = form_data["frm-main-id"]
        if len(form_data["frm-item-timestamp"]) > 0:
            item_timestamp = form_data["frm-item-timestamp"]
        if episode_aktiv == 'on': episode_aktiv = True
        else: episode_aktiv = False
        if episode_replace == 'on':episode_replace = True
        else: episode_replace = False
        if item_id and episode_filename:
            can_replace = episode_replace
            rc_code["can_replace"] = can_replace
        else: 
            can_replace = False
            
        if episode_filename and os.path.exists(file_path):
            rc_code["submit_status"] = "NO_Upload"
            rc_code["upload_status"] = episode_filename
        
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Pool gesetzt.")
            db.begin()
            cur = db.cursor(dictionary=True)

            update_allowed = True
            if item_id is not None:
                rc_code["last_id"] = item_id
                last_id = item_id
                cur.execute("SELECT IFNULL(Sperre,'INVALID') as sperre,kdnr FROM tEpisode WHERE id=? FOR UPDATE", (item_id,))
                row_data = cur.fetchone()
                timestamp = str(row_data["sperre"])
                rc_code["last_kdnr"] = str(row_data["kdnr"])
                if timestamp == item_timestamp:
                    if can_replace:
                        cur.execute("update tEpisode set Sperre=null,title=?,summary=?,chapter=NULLIF(?,''),image=NULLIF(?,''),active=?,published=?,audiofile=? where id=?", 
                                    (episode_title, episode_summary, episode_chapter, episode_image, episode_aktiv, episode_datum, episode_filename, item_id))
                    else:
                        cur.execute("update tEpisode set Sperre=null,title=?,summary=?,chapter=NULLIF(?,''),image=NULLIF(?,''),active=?,published=? where id=?", 
                                    (episode_title, episode_summary, episode_chapter, episode_image, episode_aktiv, episode_datum, item_id))
                elif timestamp == "INVALID":
                    update_allowed = False
                    rc_code["submit_status"] = "INVALID"
                else:
                    update_allowed = False
                    rc_code["submit_status"] = "NOTALWD"
            else:
                cur.execute("select GET_LOCK('tEpisode',20) as get_lock")
                is_locked = cur.fetchone()
                if is_locked["get_lock"] == 0:
                    current_app.logger.error("Für Datensatz: Titel=%s, konnte kein GET_LOCK ausgeführt werden.", episode_title)
                    raise mariadb.OperationalError("Kein Lock für tEpisode möglich.")
                cur.execute("select MAX(kdnr)+1 as kdnr from tEpisode")
                max_kdnr = cur.fetchone()["kdnr"]
                cur.execute("select RELEASE_LOCK('tEpisode') as unlocked")
                is_unlocked = cur.fetchone()
                if is_unlocked["unlocked"] == 0:
                    current_app.logger.error("Für Datensatz: ID=%s, Titel=%s, Kd-Nr=%s, konnte kein RELEASE_LOCK ausgeführt werden.", last_id, episode_title, max_kdnr)
                if not episode_filename or not size or not duration:
                    rc_code["submit_status"] = "MISS"
                    current_app.logger.error("Werte für filename=%s, size=%s, oder duration=%s fehlen.", episode_filename, size, duration)
                    update_allowed = False
                else:
                    cur.execute("insert into tEpisode(kdnr,title,audiofile,summary,chapter,image,size,duration,published,active) \
                                values(?,?,?,?,NULLIF(?,''),NULLIF(?,''),?,?,?,?)", 
                                (max_kdnr, episode_title, episode_filename, episode_summary, episode_chapter, episode_image, size, duration, episode_datum, episode_aktiv))
                    last_id = str(cur.lastrowid)
                    rc_code["last_id"] = last_id
                    rc_code["last_kdnr"] = max_kdnr

            if update_allowed:
                if item_id is not None:
                    current_app.logger.info("Datensatz aktualisiert: ID=%s, Titel=%s", last_id, episode_title)
                    rc_code["last_mode"] = "CHG"
                else:
                    current_app.logger.info("Datensatz hinzugefügt: ID=%s, Titel=%s, Dateiname=%s", last_id, episode_title, episode_filename)
                    rc_code["last_mode"] = "INS"
            db.commit()
            cur.close()
            db.close()
        except mariadb.IntegrityError as err:
            rc_code["submit_status"] = "DBL"
            current_app.logger.warning("Datenbank-doppelter Eintrag: %s/ax-submit-episode/%s", bp.name, err)
            rc_code["DB_Error"] = err
            db.rollback()
            db.close()
            current_app.logger.warning("Datenbank-Rollback-doppelter Eintrag")
        except mariadb.Error as err:
            current_app.logger.error("Datenbank-Fehler: %s/ax-submit-episode/%s", bp.name, err)
            rc_code["submit_status"] = "ERR"
            db.rollback()
            db.close()
            current_app.logger.error("Datenbank-Rollback")
    except:
        (type, value, traceback) = sys.exc_info()
        current_app.logger.critical("Unexpected error: Type=%s; Exception=%s; Trace-Line=%s",type, value, traceback.tb_lineno)
        rc_code["submit_status"] = "ERR"

    return rc_code
