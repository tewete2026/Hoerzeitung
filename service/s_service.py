import mariadb, os, subprocess, sys, json
from flask import Blueprint
from flask import current_app, session
from flask import request, make_response
from flask import render_template
from flask import redirect, url_for, g
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
    return doUpload()


@bp.route("/Upload-Episode/<albumid>", methods=['GET', 'POST'])
def confuploadChapter(albumid):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)
    return doUpload(albumid)


def doUpload(albumid=None):
    if "authcode" not in session or not getLogin(session["authcode"])['status']:
        abort(403)

    ts = current_app.config["TS"]
    teams = current_app.config["teams"]

    if albumid is None:
        isChapter = False
    else:
        isChapter = True
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Databasepool vorhanden.")
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT id,title,supporter,summary,media,publicationDate,team,duration FROM tJournal WHERE id=?", (albumid,))
            dbdata = cur.fetchone()
            if cur.rowcount <= 0:
                current_app.logger.error("Datenbank SELECT FROM tJournal: %s/doUpload, Rowcount=%s", bp.name, cur.rowcount)
                raise mariadb.DataError(f"Kein Datensatz für {albumid} gefunden.")
            cur.close()
            db.close()
        except mariadb.Error as err:
            if cur: cur.close()
            if db: db.close()
            current_app.logger.error("Datenbank-Fehler: %s/doUpload/%s", bp.name, err)
            g.errors.append(err.args[0])
            abort(500)
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    conf.append('datetimenow', ts.now_local())
    
    if request.method == "POST":
        form_data = request.form
        file = request.files['frm-main-file']
        filename = secure_filename(file.filename)
        pnr = session['dbdata']['pnr']
        seclevel = session['dbdata']['seclevel']
        if len(filename) > 0: 
            frm_main_datum = form_data.get("frm-main-datum")
            frm_main_title = form_data.get("frm-main-title")
            frm_main_summary = form_data.get("frm-main-summary")
            frm_main_supporter = form_data.get("frm-main-supporter")
            frm_main_team = form_data.get("frm-main-team")
            frm_main_author = form_data.get("frm-main-author")
            frm_main_license = form_data.get("frm-main-license")
            frm_main_allowed = form_data.get("frm-main-allowed")
            frm_main_reader = form_data.get("frm-main-reader")
            frm_main_source_date = form_data.get("frm-main-source-date")
            if frm_main_allowed is not None:
                allowed = True
            else:
                allowed = False
            filearr = filename.rsplit('.')
            namebase = filearr[0]
            suff = filearr[1]
            audioname = namebase + '.mp3'
            temp_name = current_app.instance_path + "/upload/" + filename
            temp_target = current_app.instance_path + "/upload/" + audioname
            target_path = current_app.instance_path + "/long/"
            if isChapter:
                album_path = current_app.instance_path + "/long/" + dbdata['media']
                filearr = dbdata['media'].rsplit('.')
                mediabase = filearr[0]
                dirname = current_app.instance_path + "/long/" + mediabase
                if not os.path.isdir(dirname):
                    os.mkdir(dirname)
                target_path = dirname + "/"
            file.save(temp_name)
            if not suff == 'mp3':
                shell_path = current_app.root_path + '/static/service/shell/convert_audio.sh'
                subprocess.run([shell_path, temp_name, temp_target])
            (size, duration) = tools.getMpegInfo(temp_target)
            if isChapter:
                (notused, notused, notused, notused, notused, notused, chapter_dict, notused, notused, notused) = tools.getMP3Info(album_path)
                next_track = "{0:02.0f}".format(len(chapter_dict.values()) + 1)
                # albumId,seclevel,pnr,title,author,source,reader,summary,media,duration,publicationDate,sourceDate,allowed,track
                rc_code = submit_chapter((albumid, seclevel, pnr, frm_main_title, frm_main_author, frm_main_license, frm_main_reader, frm_main_summary, audioname, duration, frm_main_datum, frm_main_source_date, allowed, next_track))
            else:
                # seclevel,pnr,title,supporter,summary,media,publicationDate,team,duration
                rc_code = submit_album((seclevel, pnr, frm_main_title, frm_main_supporter, frm_main_summary, audioname, frm_main_datum, frm_main_team, duration))
            if rc_code["submit_status"] == "OK":
                if isChapter:
                    basemedia = current_app.instance_path + "/long/" + dbdata['media']
                    teamlogo = current_app.instance_path + '/' + teams[str(dbdata['team'])][1]
                    if allowed: lic_allowed = "Ja"
                    else: lic_allowed = "Nein"
                    rc_chp = tools.setMp3Chapter(temp_target, basemedia, (frm_main_title, frm_main_summary, frm_main_datum, frm_main_author, frm_main_license, frm_main_reader, lic_allowed, teamlogo, rc_code['last_id'], albumid, frm_main_source_date))
                else:
                    teamlogo = current_app.instance_path + '/' + teams[frm_main_team][1]
                    tools.setMp3Info(temp_target, (frm_main_title, frm_main_summary, frm_main_datum, frm_main_supporter, frm_main_team, teamlogo, rc_code['last_id']))
                if isChapter:
                    goto = url_for("bx_s_start.s_episodes", subdir=mediabase)
                    audioname = rc_chp['track'] + "_" + audioname
                else:
                    goto = url_for("bx_s_start.s_album")
                if os.path.exists(temp_target):
                    os.replace(temp_target, target_path + audioname)
                if temp_name is not None and os.path.exists(temp_name):
                    os.remove(temp_name)
                return redirect(goto)
            else:
                if temp_name is not None and os.path.exists(temp_name):
                    os.remove(temp_name)
                if temp_target is not None and os.path.exists(temp_target):
                    os.remove(temp_target)
                g.errors.append(rc_code['err_msg'])
                abort(500)

    conf.initlogin(session['dbdata'])
    conf.append("show_navall", True)
    if session['dbdata']['seclevel'] > 1:
        conf.append("show_navtop", True)
    conf.append("teams", current_app.config["teams"])

    if isChapter:
        herausgeber = []
        vorleser = []
        with open(current_app.instance_path + "/data/Herausgeber.txt", mode='r') as text_file:
            for line in text_file:
                herausgeber.append(line.rstrip())
            conf.append("herausgeber", sorted(herausgeber))
        with open(current_app.instance_path + "/data/Vorleser.txt", mode='r') as text_file:
            for line in text_file:
                vorleser.append(line.rstrip())
            conf.append("vorleser", sorted(vorleser))
        conf.append("title", dbdata['title'])
        html = "service/confuploadChapter.html"
    else:
        techniker = []
        with open(current_app.instance_path + "/data/Techniker.txt", mode='r') as text_file:
            for line in text_file:
                techniker.append(line.rstrip())
            conf.append("techniker", sorted(techniker))
        html = "service/confupload.html"

    return render_template(html, conf=conf)


@bp.route("/Neue-Codes", methods=['GET', 'POST'])
def confcreate():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)

    if "authcode" not in session or not getLogin(session["authcode"])['status']:
        abort(403)
    
    ts = current_app.config["TS"]
    conf_max_freecodes = current_app.config["max_freecodes"]
    error = False
    post_request = False
    quantity = "1"
    level = "-1"
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    conf = Configure("Norderstedter Hörzeitung - Service Ebene", request, current_app)
    conf.append('conf_max_freecodes', conf_max_freecodes)
    
    conf.initlogin(session['dbdata'])
    
    if post_request:
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
                    current_app.logger.warning("Datenbank-Integrität Eintrag: %s/confcreate/%s", bp.name, err)
                    db.rollback()
                    db.close()
                except mariadb.Error as err:
                    conf.error['result_err'] = f"Datenbankfehler: {err}. Erstellung der Charge wurde NICHT erfolgreich durchgeführt."
                    if db: db.rollback()
                    if db: db.close()
                    current_app.logger.error("Datenbank-Fehler: %s/confcreate/%s", bp.name, err)
    
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
        conf.append('history', {})

    conf.javascript.add({'quantity':quantity})
    conf.javascript.add({'level':level})
    
    return render_template("service/confcreate.html", conf=conf)


@bp.route("/Export-Liste-<level>", methods=['GET'])
def export(level):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)

    if "authcode" not in session or not getLogin(session["authcode"])['status']:
        abort(403)
    
    ts = current_app.config["TS"]
    conf = Configure("Norderstedter Hörzeitung - Export", request, current_app)

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
            current_app.logger.error("Datenbank-Fehler: %s/export/%s", bp.name, err)
            g.errors.append(f"Export wurde NICHT erfolgreich durchgeführt: {err.args[0]}. ")
            abort(500)


@bp.route("/Export-Liste-Letzter-Login", methods=['GET'])
def export_last_login():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)

    if "authcode" not in session or not getLogin(session["authcode"])['status']:
        abort(403)
    
    ts = current_app.config["TS"]

    conf = Configure("Norderstedter Hörzeitung - Export Liste letzter Login", request, current_app)
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
        current_app.logger.error("Datenbank-Fehler: %s/export_last_login/%s", bp.name, err)
        g.errors.append(f"Export wurde NICHT erfolgreich durchgeführt: {err.args[0]}. ")
        abort(500)


@bp.route("/Export-Liste-Media-Zugriff", methods=['GET'])
def export_media_access():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 2:
        abort(403)

    if "authcode" not in session or not getLogin(session["authcode"])['status']:
        abort(403)
    
    ts = current_app.config["TS"]

    conf = Configure("Norderstedter Hörzeitung - Export Liste Media Zugriff", request, current_app)
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
        current_app.logger.error("Datenbank-Fehler: %s/export_last_login/%s", bp.name, err)
        g.errors.append(f"Export wurde NICHT erfolgreich durchgeführt: {err.args[0]}. ")
        abort(500)


def submit_album(form_data):
    rc_code = {"submit_status":"OK", "last_id":"(Neu)", "last_mode":"(none)"}
    try:
        item_id = None
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
                '''
                cur.execute("insert into tJournal(albumId,seclevel,pnr,title,author,source,reader,summary,media,publicationDate,sourceDate,allowed) \
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
                '''
            else:
                #     0     1    2       3        4      5          6         7      8
                # seclevel,pnr,title,supporter,summary,media,publicationDate,team,duration
                cur.execute("insert into tJournal(seclevel,pnr,title,supporter,summary,media,publicationDate,team,duration) \
                            values               (?,       ?,  ?,    ?,        ?,      ?,    ?,              ?,   ?)", form_data)
                last_id = str(cur.lastrowid)
                rc_code["last_id"] = last_id

            if update_allowed:
                if item_id is not None:
                    current_app.logger.info("Datensatz in tJournal aktualisiert: ID=%s, Titel=%s", last_id, form_data[2])
                    rc_code["last_mode"] = "CHG"
                else:
                    current_app.logger.info("Datensatz in tJournal hinzugefügt: ID=%s, Titel=%s, Dateiname=%s", last_id, form_data[2], form_data[5])
                    rc_code["last_mode"] = "INS"
            db.commit()
            cur.close()
            db.close()
        except mariadb.PoolError as err:
            current_app.logger.error("Pool-Fehler: %s/submit-album/%s", bp.name, err)
            rc_code["submit_status"] = "ERR"
            rc_code["err_msg"] = f"Datenbank ist nicht initialisiert: {err}"
        except mariadb.IntegrityError as err:
            rc_code["submit_status"] = "DBL"
            current_app.logger.warning("Datenbank Integrität Eintrag: %s/submit-album/%s", bp.name, err)
            rc_code["DB_Error"] = err
            rc_code["err_msg"] = f"Datenbank Integrität verletzt Eintrag: {err}"
            db.rollback()
            db.close()
            current_app.logger.warning("Datenbank-Rollback Integrität Eintrag")
        except mariadb.Error as err:
            current_app.logger.error("Datenbank-Fehler: %s/submit-album/%s", bp.name, err)
            rc_code["submit_status"] = "ERR"
            rc_code["err_msg"] = f"Allgemeiner Datenbank-Fehler: {err}"
            db.rollback()
            db.close()
            current_app.logger.error("Datenbank-Rollback")
    except:
        (type, value, traceback) = sys.exc_info()
        current_app.logger.critical("Unexpected error: Type=%s; Exception=%s; Trace-Line=%s",type, value, traceback.tb_lineno)
        rc_code["submit_status"] = "ERR"
        rc_code["err_msg"] = f"Allgemeiner Programm-Fehler: {type};{value}"

    return rc_code


def submit_chapter(form_data):
    rc_code = {"submit_status":"OK", "last_id":"(Neu)", "last_mode":"(none)"}
    try:
        item_id = None
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
                '''
                cur.execute("insert into tChapter(albumId,seclevel,pnr,title,author,source,reader,summary,media,publicationDate,sourceDate,allowed) \
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
                '''
            else:
                #     0     1       2    3     4      5       6      7      8      9           10            11        12
                # albumId,seclevel,pnr,title,author,source,reader,summary,media,duration,publicationDate,sourceDate,allowed
                cur.execute("insert into tChapter(albumId,seclevel,pnr,title,author,source,reader,summary,media,duration,publicationDate,sourceDate,allowed,track) \
                            values               (?,      ?,       ?,  ?,    ?,     ?,     ?,     ?,      ?,    ?,       ?,              ?,         ?,      ?)", form_data)
                last_id = str(cur.lastrowid)
                rc_code["last_id"] = last_id

            if update_allowed:
                if item_id is not None:
                    current_app.logger.info("Datensatz in tChapter aktualisiert: ID=%s, Titel=%s", last_id, form_data[3])
                    rc_code["last_mode"] = "CHG"
                else:
                    current_app.logger.info("Datensatz in tChapter hinzugefügt: ID=%s, Titel=%s, Dateiname=%s", last_id, form_data[3], form_data[8])
                    rc_code["last_mode"] = "INS"
            db.commit()
            cur.close()
            db.close()
        except mariadb.PoolError as err:
            current_app.logger.error("Pool-Fehler: %s/submit-chapter/%s", bp.name, err)
            rc_code["submit_status"] = "ERR"
            rc_code["err_msg"] = f"Datenbank ist nicht initialisiert: {err}"
        except mariadb.IntegrityError as err:
            rc_code["submit_status"] = "DBL"
            current_app.logger.warning("Datenbank-Integrität Eintrag: %s/submit-chapter/%s", bp.name, err)
            rc_code["DB_Error"] = err
            rc_code["err_msg"] = f"Datenbank hat Integrität verletzt Eintrag: {err}"
            db.rollback()
            db.close()
            current_app.logger.warning("Datenbank-Rollback-Integrität Eintrag")
        except mariadb.Error as err:
            current_app.logger.error("Datenbank-Fehler: %s/submit-chapter/%s", bp.name, err)
            rc_code["submit_status"] = "ERR"
            rc_code["err_msg"] = f"Allgemeiner Datenbank-Fehler: {err}"
            db.rollback()
            db.close()
            current_app.logger.error("Datenbank-Rollback")
    except:
        (type, value, traceback) = sys.exc_info()
        current_app.logger.critical("Unexpected error: Type=%s; Exception=%s; Trace-Line=%s",type, value, traceback.tb_lineno)
        rc_code["submit_status"] = "ERR"
        rc_code["err_msg"] = f"Allgemeiner Programm-Fehler: {type};{value}"

    return rc_code
