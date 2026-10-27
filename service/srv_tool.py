import mariadb, os, random
from flask import Blueprint
from flask import current_app, session
from flask import request
from flask import render_template
from flask import redirect, url_for
from mutagen.mp3 import MP3
from mutagen.id3 import CHAP, TIT2, TLEN, COMM, TXXX, ID3, TPE1, TDRC, TALB, TCON, APIC, TRCK, CTOC, CTOCFlags
from werkzeug.exceptions import abort
import random
from ..db import get_db
from .s_service import submit_album, submit_chapter
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

'''
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
'''


@bp.route("/init-tagging")
def init_tagging():
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 4:
        abort(403)

    ts = current_app.config["TS"]
    full_dir = current_app.instance_path + "/long"
    content = os.listdir(full_dir)
    content.sort()
    max_rec = 0
    album_err = 0
    chap_err = 0
    db = get_db()
    cur = db.cursor(dictionary=True)

    for element in content:
        rawname = f"{full_dir}/{element}"
        if not os.path.isdir(rawname):
            if not element.endswith(".mp3"): continue
            (alb_title, description, pub, size, tlen, chapter, chapter_dict, image_dict, notused, notused) = tools.getMP3Info(rawname)
            mtime = os.stat(rawname).st_mtime
            published = ts.fromtimestamp(mtime)
            duration = tools.getTimeFormat(tlen/1000)
            if not tlen:
                (size, duration) = tools.getMpegInfo(rawname)
            cur.execute("SELECT team,supporter FROM tReference WHERE cd=?", (alb_title,))
            refalbum = cur.fetchone()
            # seclevel,pnr,title,supporter,summary,media,publicationDate,team,duration
            rc_album = submit_album((session['dbdata']['seclevel'], session['dbdata']['pnr'], alb_title, refalbum['supporter'], description, element, published, refalbum['team'], duration))
            if rc_album["submit_status"] == "OK":
                albumid = rc_album['last_id']
                audio = ID3(rawname)
                audio.add(TXXX(desc="Supporter", text=[refalbum['supporter']], encoding=3)) # Techniker
                audio.add(TXXX(desc="Team", text=[refalbum['team']], encoding=3)) # Team
                audio.add(TXXX(desc="AlbumId", text=[albumid], encoding=3)) # Album-ID
                audio.save()
                os.utime(rawname, (mtime, mtime))
                key = element.split('.')[0].strip()
                dirname = f"{full_dir}/{key}"
                if os.path.isdir(dirname):
                    dircontent = os.listdir(dirname)
                    for entry in dircontent:
                        entryname = f"{dirname}/{entry}"
                        if os.path.isdir(entryname) or not entry.endswith(".mp3"): continue
                        (chp_title, description, pub, size, tlen, notused, chapter_dict, image_dict, notused, chp_track) = tools.getMP3Info(entryname)
                        mtime = os.stat(entryname).st_mtime
                        published = ts.fromtimestamp(mtime)
                        duration = tools.getTimeFormat(tlen/1000)
                        if not tlen:
                            (size, duration) = tools.getMpegInfo(entryname)
                        cur.execute("SELECT cd,team,track,title,DATE_FORMAT(DATE(sourceDate),'%Y-%m-%d') as sourceDate,author,source,reader,allowed,supporter,DATE_FORMAT(DATE(pubDate),'%Y-%m-%d') as pubDate FROM tReference WHERE cd=? && track=?", (alb_title, chp_track))
                        refchapter = cur.fetchone()
                        if cur.rowcount <= 0:
                            chp_author = chp_source = chp_reader = ""
                            chp_sourcedate = "0000-00-00"
                            chp_allowed = 0
                        else:
                            chp_sourcedate = refchapter['sourceDate']
                            chp_author = refchapter['author']
                            chp_source = refchapter['source']
                            chp_reader = refchapter['reader']
                            chp_allowed = refchapter['allowed']
                        # albumId,seclevel,pnr,title,author,source,reader,summary,media,duration,publicationDate,sourceDate,allowed,track
                        rc_chapter = submit_chapter((albumid, session['dbdata']['seclevel'], session['dbdata']['pnr'], chp_title, chp_author, chp_source, chp_reader, description, entry, duration, published, chp_sourcedate, chp_allowed, chp_track))
                        if rc_chapter["submit_status"] == "OK":
                            audio = ID3(entryname)
                            audio.add(TXXX(desc="ChapterId", text=[rc_chapter['last_id']], encoding=3)) # Chapter-ID
                            audio.add(TXXX(desc="AlbumId", text=[albumid], encoding=3)) # Album-ID
                            audio.save()
                            os.utime(entryname, (mtime, mtime))
                        else:
                            chap_err += 1
            else:
                album_err += 1
        max_rec += 1

    cur.close()
    db.close()
    
    return f"<!DOCTYPE html><html lang='en'><head></head><body><p>Anzahl Records verarbeitet: {max_rec}, Album-Fehler: {album_err}, Chapter-Fehler: {chap_err}</p></body></html>"