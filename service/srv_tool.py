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
from markdown import markdown
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
    ref_err = 0
    chap_err = 0
    db = get_db()
    cur = db.cursor(dictionary=True)
    output = ["<!DOCTYPE html><html lang='en'><head>\
              <title>Initialisieren Audio-Files mit Referenz-Liste (Leseliste.xlsx)</title>  \
              <style>\
                h4 {line-height: 0.2em;}\
                p {line-height: 1.2em; margin-left:3em; margin-bottom:0.5em; margin-top: 0;}\
                h3 {line-height: 1.1em; margin-left:2em; margin-bottom:0.5em; margin-top: 1em;}\
              </style>\
              </head><body><h1>Initialisieren Audio-Files mit Referenz-Liste (Leseliste.xlsx)</h1>"]

    for element in content:
        rawname = f"{full_dir}/{element}"
        if os.path.isdir(rawname) or not element.endswith(".mp3"): continue
        (alb_title, description, pub, size, tlen, chapter, chapter_dict, image_dict, notused, notused) = tools.getMP3Info(rawname)
        mtime = os.stat(rawname).st_mtime
        published = ts.fromtimestamp(mtime)
        duration = tools.getTimeFormat(tlen/1000)
        if not tlen:
            (size, duration) = tools.getMpegInfo(rawname)
        cur.execute("SELECT team,supporter FROM tReference WHERE cd=?", (alb_title,))
        refalbum = cur.fetchone()
        if cur.rowcount <= 0:
            refalbum = {'team':0,'supporter':'---'}
            ref_err += 1
        # seclevel,pnr,title,supporter,summary,media,publicationDate,team,duration
        rc_album = submit_album((session['dbdata']['seclevel'], session['dbdata']['pnr'], alb_title, refalbum['supporter'], description, element, published, refalbum['team'], duration))
        output.append(f"<h4>Album: {alb_title}; Datum: {published}; Dauer: {duration}; Techniker: {refalbum['supporter']}; Team: {refalbum['team']}")
        if rc_album["submit_status"] == "OK":
            albumid = rc_album['last_id']
            output.append(f"; Status: {rc_album["submit_status"]}; Album-ID:{albumid} </h4>")
            audio = ID3(rawname)
            audio.add(TXXX(desc="Supporter", text=[refalbum['supporter']], encoding=3)) # Techniker
            audio.add(TXXX(desc="Team", text=[refalbum['team']], encoding=3)) # Team
            audio.add(TXXX(desc="AlbumId", text=[albumid], encoding=3)) # Album-ID
            audio.save()
            os.utime(rawname, (mtime, mtime)) # Dateidatum wiederherstellen, da audio.save() das Datum ändert.
            key = element.split('.')[0].strip()
            dirname = f"{full_dir}/{key}"
            if os.path.isdir(dirname):
                dircontent = os.listdir(dirname)
                dircontent.sort()
                step = 1
                for entry in dircontent:
                    entryname = f"{dirname}/{entry}"
                    if os.path.isdir(entryname) or not entry.endswith(".mp3"): continue
                    (entry_title, description, entry_published, size, tlen, notused, chapter_dict, image_dict, notused, entry_track) = tools.getMP3Info(entryname)
                    mtime = os.stat(entryname).st_mtime
                    published = ts.fromtimestamp(mtime)
                    duration = tools.getTimeFormat(tlen/1000)
                    if not tlen:
                        (size, duration) = tools.getMpegInfo(entryname)
                    cur.execute("SELECT cd,team,track,title,DATE_FORMAT(DATE(sourceDate),'%Y-%m-%d') as sourceDate,author,source,reader,allowed,supporter,DATE_FORMAT(DATE(pubDate),'%Y-%m-%d') as pubDate FROM tReference WHERE cd=? && track=?", (alb_title, step))
                    refchapter = cur.fetchone()
                    if cur.rowcount <= 0:
                        chp_author = chp_source = chp_reader = chp_title = chp_track = "---"
                        chp_sourcedate = "0000-00-00"
                        chp_pubdate = "0000-00-00"
                        chp_allowed = 0
                        ref_err += 1
                    else:
                        chp_title = refchapter['title']
                        chp_track = refchapter['track']
                        chp_sourcedate = refchapter['sourceDate']
                        chp_pubdate = refchapter['pubDate']
                        chp_author = refchapter['author']
                        chp_source = refchapter['source']
                        chp_reader = refchapter['reader']
                        chp_allowed = refchapter['allowed']
                    if chp_title != '---': title = chp_title
                    else: title = entry_title
                    # albumId,seclevel,pnr,title,author,source,reader,summary,media,duration,publicationDate,sourceDate,allowed,track
                    rc_chapter = submit_chapter((albumid, session['dbdata']['seclevel'], session['dbdata']['pnr'], title, chp_author, chp_source, chp_reader, description, entry, duration, published, chp_sourcedate, chp_allowed, step))
                    if entry_track != str(step):
                        err_style_trk = "style='font-weight:800;'"
                    else:
                        err_style_trk = "style='font-weight:100;'"
                    if entry_title.strip() != chp_title.strip():
                        err_style_tit = "style='font-weight:800;'"
                    else:
                        err_style_tit = "style='font-weight:100;'"
                    if entry_published != chp_pubdate:
                        err_style_pub = "style='font-weight:800;'"
                    else:
                        err_style_pub = "style='font-weight:100;'"
                    if entry_published != published:
                        err_style_pubtag = "style='font-weight:800;'"
                    else:
                        err_style_pubtag = "style='font-weight:100;'"
                    output.append(f"<p><span {err_style_tit}>Dat.-Titel: {entry_title.strip()}</span>; Datum: {published}; <span {err_style_pubtag}>ID3-Datum: {entry_published}</span>; <span {err_style_trk}>Step: {str(step)}; Track: {entry_track}</span>; Dauer: {duration} <br>\
                                    <span>Ref.-Titel: {chp_title}; <span {err_style_pub}>Datum: {chp_pubdate}</span>; TitelNr: {chp_track}; Quelle: {chp_source}; Quelle-Datum: {chp_sourcedate}; Autor: {chp_author}; Lizenz: {chp_allowed}; Vorleser: {chp_reader}</span>")
                    if rc_chapter["submit_status"] == "OK":
                        output.append(f"; Status: {rc_chapter["submit_status"]}; Chapter-ID: {rc_chapter['last_id']}</p>")
                        tit2_title = title.replace('?', '_').replace('/', '_').replace('\\', '_').replace('"', '_').replace('*', '_')
                        audio = ID3(entryname)
                        audio.add(TIT2(text=[tit2_title], encoding=3)) # Titel
                        audio.add(TRCK(text=[str(step)], encoding=3)) # Track
                        audio.add(TXXX(desc="ChapterId", text=[rc_chapter['last_id']], encoding=3)) # Chapter-ID
                        audio.add(TXXX(desc="AlbumId", text=[albumid], encoding=3)) # Album-ID
                        audio.save()
                        os.utime(entryname, (mtime, mtime)) # Dateidatum wiederherstellen, da audio.save() das Datum ändert.
                    else:
                        output.append(f"; Status: {rc_chapter["submit_status"]}; Chapter-ID: ---</p>")
                        chap_err += 1
                    step += 1
        else:
            output.append(f"; Datenbank-Fehler={rc_album["err_msg"]} </h4>")
            album_err += 1
        max_rec += 1

    cur.close()
    db.close()
    
    output.append(f"<h4>Anzahl Records verarbeitet: {max_rec}, Album-Fehler: {album_err}, Chapter-Fehler: {chap_err}, Referenz-Fehler: {ref_err}</h4></body></html>")
    return "\n".join(output)

@bp.route("/analyse-tagging")
def analyse_tagging():
    if 'dbdata' not in session or session['dbdata']['seclevel'] < 4:
        abort(403)
    '''
        DATE_FORMAT(DATE(publicationDate),'%Y-%m-%d %H:%i:%s') as publicationDate
    '''
    ts = current_app.config["TS"]
    full_dir = current_app.instance_path + "/long"
    content = os.listdir(full_dir)
    content.sort()
    max_rec = 0
    album_err = 0
    chap_err = 0
    db = get_db()
    cur = db.cursor(dictionary=True)
    output = ["<!DOCTYPE html><html lang='en'><head>\
              <title>Analyse Audio-Files mit Referenz-Liste (Leseliste.xlsx)</title>  \
              <style>\
                h4 {line-height: 0.2em;}\
                p {line-height: 1.2em; margin-left:3em; margin-bottom:0.5em; margin-top: 0;}\
                h3 {line-height: 1.1em; margin-left:2em; margin-bottom:0.5em; margin-top: 1em;}\
              </style>\
              </head><body>"]
    with open(current_app.root_path + "/static/doc/analyse_tagging.md") as markdn:
        output.append(markdown(text=markdn.read(), output_format='html'))

    for element in content:
        rawname = f"{full_dir}/{element}"
        if not os.path.isdir(rawname):
            if not element.endswith(".mp3"): continue
            (alb_title, description, pub, size, tlen, chapter, chapter_dict, image_dict, notused, notused) = tools.getMP3Info(rawname)
            mtime = os.stat(rawname).st_mtime
            published = ts.fromtimestamp(mtime)
            if not tlen:
                (size, duration) = tools.getMpegInfo(rawname)
            else:
                duration = tools.getTimeFormat(tlen/1000)
            cur.execute("SELECT id,cd,supporter,team FROM tReference WHERE cd=?", (alb_title,))
            refalbum = cur.fetchone()
            if cur.rowcount <= 0:
                refalbum = {'id':'---','cd':'---','supporter':'---','team':'---'}
            albumcd = refalbum['cd']
            supporter = refalbum['supporter']
            team = refalbum['team']
            output.append(f"<h4>Album: {alb_title}; Datum: {published}; Dauer: {duration}; Referenz= CD:{albumcd}; Techniker: {supporter}; Team: {team}</h4>")
            key = element.split('.')[0].strip()
            dirname = f"{full_dir}/{key}"
            if os.path.isdir(dirname):
                dircontent = os.listdir(dirname)
                dircontent.sort()
                step = 1
                for entry in dircontent:
                    entryname = f"{dirname}/{entry}"
                    if os.path.isdir(entryname) or not entry.endswith(".mp3"): continue
                    (entry_title, description, pub, size, tlen, notused, chapter_dict, image_dict, notused, entry_track) = tools.getMP3Info(entryname)
                    mtime = os.stat(entryname).st_mtime
                    published = ts.fromtimestamp(mtime)
                    duration = tools.getTimeFormat(tlen/1000)
                    if not tlen:
                        (size, duration) = tools.getMpegInfo(entryname)
                    cur.execute("SELECT cd,team,track,title,DATE_FORMAT(DATE(sourceDate),'%Y-%m-%d') as sourceDate,author,source,reader,allowed,supporter,DATE_FORMAT(DATE(pubDate),'%Y-%m-%d') as pubDate FROM tReference WHERE cd=? && track=?", (alb_title, step))
                    refchapter = cur.fetchone()
                    if cur.rowcount <= 0:
                        err_style = "style='font-weight:800;'"
                        chp_author = chp_source = chp_reader = chp_title = "---"
                        chp_sourcedate = "---"
                        chp_allowed = 0
                    else:
                        err_style = "style='font-weight:100;'"
                        chp_title = refchapter['title'].strip()
                        chp_sourcedate = refchapter['sourceDate']
                        chp_author = refchapter['author']
                        chp_source = refchapter['source']
                        chp_reader = refchapter['reader']
                        chp_allowed = refchapter['allowed']
                    if entry_track != str(step):
                        err_style_trk = "style='font-weight:800;'"
                    else:
                        err_style_trk = "style='font-weight:100;'"
                    if entry_title.strip() != chp_title.strip():
                        err_style_tit = "style='font-weight:800;'"
                    else:
                        err_style_tit = "style='font-weight:100;'"
                    output.append(f"<p><span {err_style_tit}>Dat.-Titel: {entry_title.strip()}</span>; <span {err_style_trk}>Step: {str(step)}; Track: {entry_track}</span>; Dauer: {duration} <br>\
                                    <span {err_style}>Ref.-Titel: {chp_title}; Quelle: {chp_source}; Quelle-Datum: {chp_sourcedate}; Autor: {chp_author}; Lizenz: {chp_allowed}; Vorleser: {chp_reader}</span></p>")
                    step += 1
            else:
                    output.append(f"<p><span>Dat.-Titel: ---</span>; <span>Step: ---; Track: ---</span>; Dauer: --- </p><br>")
            '''
            '''
        max_rec += 1

    cur.close()
    db.close()
    
    output.append(f"<h4>Anzahl Records verarbeitet: {max_rec}</h4></body></html>")
    return "\n".join(output)
