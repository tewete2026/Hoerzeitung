import mariadb, os, random
from flask import Blueprint
from flask import current_app
from flask import request
from flask import render_template
from flask import redirect, url_for
from werkzeug.exceptions import abort
import random
from ..db import get_db
from .. import version, tools
from ..podcast_texte import podcast_texte

bp = Blueprint("srv_tool", __name__, url_prefix="/service/toolfix")


# @bp.before_request
# def check_authority():
#     auth_code_valid = False
#     if "authcode" in session:
#         # code = session["authcode"]
#         auth_code_valid = True
#     if not auth_code_valid:
#         abort(403)


@bp.route("/")
def toolfix_default():
    return render_template('service/base_toolfix.html', rules=current_app.url_map.iter_rules())


@bp.route("/reorg-members")
def reorg_members():
    dbdata={}
    max_rec = 0
    try:
        db = get_db()
        if not db:
            raise mariadb.PoolError()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT id,KundenNr,sperre,Nachname,Vorname,IFNULL(Anrede,-1) as Anrede,IFNULL(Strasse,'') as Strasse,IFNULL(Ort,'') as Ort,IFNULL(PLZ,'') as PLZ,IFNULL(EMail,'') as EMail,IFNULL(Telefon,'') as Telefon,\
                    IF(Aktiv=TRUE,TRUE,FALSE) as Aktiv,IF(Newsletter=TRUE,TRUE,FALSE) as Newsletter,IFNULL(Bemerkung,'') as Bemerkung,DATE_FORMAT(DATE(AufnDatum),'%Y-%m-%d') as datum \
                    FROM tBesucher")
        dbdata.update({"members":cur.fetchall()})

        vornamen = []    
        nachnamen = []
        emaildomain = ["web.de", "yahoo.com", "hotmail.com", "mail.de", "online.de", "hamburg.de", "gmx.de", "wtnet.de", "wt.de"]
        telefonnrn = ["815", "902", "91", "261", "811", "77", "100", "771", "892", "881", "777", "995", "810"]

        for member in dbdata["members"]:
            vornamen.append(member["Vorname"])
            nachnamen.append(member["Nachname"])

        for member in dbdata["members"]:
            vorname = random.choice(vornamen)
            nachname = random.choice(nachnamen)
            telefon = "040" + random.choice(telefonnrn) + random.choice(telefonnrn) + random.choice(telefonnrn)
            email = vorname + "_" + str(random.randint(1, 9999)) + "@" + random.choice(emaildomain)
            cur.execute("UPDATE tBesucher SET Vorname=?, Nachname=?, Telefon=?, EMail=? WHERE id=?", (vorname, nachname, telefon, email, member["id"]))
            db.commit()
            max_rec += 1
    
        cur.close()
        db.close()

    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        abort(500)

    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}</p></body></html>"


@bp.route("/init-episodes")
def init_episodes():
    max_rec = 0
    db = get_db()
    if not db:
        raise mariadb.PoolError()

    try:
        cur = db.cursor(dictionary=True)
        path = "/long"
        content = sorted(os.listdir(current_app.instance_path + path), reverse=True)
        imageindex = 1
        for mp3 in content:
            rawname = current_app.instance_path + path + "/" + mp3
            descr = podcast_texte.get(mp3.rstrip(".mp3"))
            if descr is None: description = "----"
            else: description = descr
            (title, mp3description, published, size, dur, chapter) = tools.getMP3Info(rawname)
            cur.execute("INSERT INTO tEpisode(title,kdnr,audiofile,summary,published,size,duration,chapter,image) values(?,?,?,?,?,?,?,?,?)", (title, title, mp3, description, published, size, dur, chapter, f"LogoGruppe-{imageindex}.jpg"))
            imageindex += 1
            if imageindex > 5: imageindex = 1
            max_rec += 1
    
        db.commit()
        cur.close()
        db.close()

    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        abort(500)

    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}</p></body></html>"


@bp.route("/reorg-duration")
def reorg_duration():
    max_rec = 0
    db = get_db()
    if not db:
        raise mariadb.PoolError()

    try:
        db.begin()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id,audiofile FROM tEpisode")
        content = cur.fetchall()
        for mp3 in content:
            (id, audiofile) = mp3.items()
            rawname = current_app.instance_path + "/long/" + audiofile[1]
            (size, duration) = tools.getMpegInfo(rawname)
            cur.execute("UPDATE tEpisode SET duration=? WHERE id=?", (duration, id[1]))
            max_rec += 1
    
        db.commit()
        cur.close()
        db.close()

    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        abort(500)

    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}</p></body></html>"


@bp.route("/reorg-title")
def reorg_title():
    ts = current_app.config["TS"]
    max_rec = 0
    db = get_db()
    if not db:
        raise mariadb.PoolError()

    try:
        db.begin()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id,kdnr,published FROM tEpisode")
        content = cur.fetchall()
        for mp3 in content:
            (id, kdnr, published) = mp3.items()
            cal = ts.isocalendar(published[1])
            new_title = "Folge {0:04.0f} in Woche {1:04.0f}/{2:02.0f}".format(kdnr[1], cal[0], cal[1])
            cur.execute("UPDATE tEpisode SET title=? WHERE id=?", (new_title, id[1]))
            max_rec += 1
    
        db.commit()
        cur.close()
        db.close()

    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        abort(500)

    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}</p></body></html>"


@bp.route("/init-freecode")
def init_freecode():
    ts = current_app.config["TS"]
    max_rec = 0
    db = get_db()
    if not db:
        raise mariadb.PoolError()

    try:
        db.begin()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id FROM tBesucher")
        content = cur.fetchall()
        count = 1
        for row in content:
            id = row['id']
            cur.execute("UPDATE tBesucher SET FreeCode=?, KundenNr=? WHERE id=?", (tools.generateCode(''), count, id))
            max_rec += 1
            count += 1
        db.commit()
        cur.close()
        db.close()

    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        abort(500)

    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}</p></body></html>"
