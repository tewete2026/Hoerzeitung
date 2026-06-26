import mariadb, os, random
from math import floor
from flask import Blueprint
from flask import current_app, session
from flask import request
from flask import render_template
from flask import redirect, url_for
from werkzeug.exceptions import abort
from mutagen.mp3 import MP3
from mutagen.id3 import CHAP
from sox import file_info as audio_info
import random
from ..db import get_db
from .. import version
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
            (title, mp3description, published, size, dur, chapter) = getMP3Info(rawname)
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
            (size, duration) = getMpegInfo(rawname)
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
            cur.execute("UPDATE tBesucher SET FreeCode=?, KundenNr=? WHERE id=?", (generateCode(), count, id))
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


def getMP3Info(rawname:str):
    ts = current_app.config["TS"]
    # audio = MP3(current_app.instance_path + "/" + mp3, ID3=EasyID3)
    audio = MP3(rawname)
    episode_kap = {}
    for key in audio.keys():
        cont = audio.get(key)
        if isinstance(cont, CHAP):
            text = cont.sub_frames["TIT2"][0]
            if len(text) > 0:
                episode_kap.update({key.removeprefix("CHAP:"):text})
    description = audio.get("COMM::eng")
    # keys = ["TALB", "TPE1", "TDRC", "TIT2", "TENC", "TLEN"]
    # for key in keys:
    #     print(key, audio.get(key))
    if description is None: description = "- - - -"
    title = audio.get("TIT2")
    if title is None: title = ["---"]
    size = os.stat(rawname).st_size
    chapter = ""
    counter = 1
    for key, text in episode_kap.items():
        chapter += "{0:02}. {1}<br>".format(counter, text)
        counter += 1
    published = ts.fromtimestamp(os.stat(rawname).st_mtime)
    tlen = audio.get("TLEN")
    if tlen is None:
        dur = audio.info.length
    else:
        dur = float(tlen[0]) / 1000
    min = dur / 60
    sec = dur % 60
    duration = "{0:02.0f}:{1:02.0f}".format(min, sec)
    # print(tlen, dur, min, sec, duration, audio, audio.keys())

    return (title, description, published, size, duration, chapter)


def getMpegInfo(rawname:str):
    sec = audio_info.duration(rawname)
    if sec is None: dur = 0.00
    else: dur = sec
    duration = "{0:02.0f}:{1:02.0f}".format(floor(dur / 60), floor(dur % 60))
    size = os.stat(rawname).st_size
    return (size, duration)


def generateCode():
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    chars_list = list(chars)
    code = ''
    for z in range(1, 5):
        code += "".join(random.sample(chars_list, 4))
        if z < 4: code += '-'
    return code
