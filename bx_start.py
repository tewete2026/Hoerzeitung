import mariadb, os
from podgen import Podcast, Episode, Person, Category, Media
from flask import Blueprint
from flask import current_app, session
from flask import request, make_response
from flask import render_template, redirect
from flask import redirect, url_for, send_from_directory
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from .db import get_db, Configure, get_s_episodes, send_mail, getLogin
from . import version, credentials
from .podcast_texte import podcast_texte

bp = Blueprint("bx_start", __name__)


@bp.route("/media/<file>")
def media(file):
    path = ""
    if file.startswith("Logo"):path = ""
    elif file.endswith(".jpg"):path = "/galerie"
    elif file.endswith(".pdf"):path = "/docs"
    elif file.endswith(".mp3"):
        auth_code_valid = False
        if "authcode" in session:
            rc_code = getLogin(session["authcode"])
            auth_code_valid = rc_code['status']
        elif "authcode" in request.args:
            rc_code = getLogin(request.args["authcode"])
            auth_code_valid = rc_code['status']
        
        if auth_code_valid:
            dbdata = rc_code['dbdata']
            auth_code_guest = dbdata['guest']
            if auth_code_guest:
                path = "/short"
                is_guest = 1
            else:
                path = "/long"
                is_guest = 0
            pnr = dbdata['pnr']
            seclevel = dbdata['seclevel']
            freecode = dbdata['freecode']
            last_access = dbdata['last_access']
            # Nur für seclevel = 0 (nur externe Hörer) protokollieren
            if seclevel == 0:
                try:
                    db = get_db()
                    if not db:
                        raise mariadb.PoolError("Kein Databasepool vorhanden.")
                    cur = db.cursor(dictionary=True)
                    cur.execute("INSERT INTO tLog(pnr,seclevel,freecode,accessDate,media,accesscount,guest) values(?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE accesscount=accesscount+1", (pnr, seclevel, freecode, last_access, file, 1, is_guest))
                    if cur.rowcount <= 0:
                        current_app.logger.error("Datenbank-Fehler INSERT INTO tLog: %s/media, Rowcount=%s", bp.name, cur.rowcount)
                    db.commit()
                    cur.close()
                    db.close()
                except mariadb.Error as err:
                    if db: db.close()
                    current_app.logger.error("Datenbank-Fehler: %s/media/%s", bp.name, err)
        else:
            path = "/short"

        # werkzeug.datastructures.headers.EnvironHeaders
        if current_app.config['TEST_RUN'] == 'PROD':
            current_app.logger.info("Empfangener HTTP-Header für %s, %s, %s: %s", file, request.remote_addr, request.origin, request.headers)
    path = current_app.instance_path + path
    file_arr = file.split('_')
    if len(file_arr) > 1:
        path += "/" + file_arr[0]
        file = file_arr[1]
    return send_from_directory(path, file)


""" @bp.route("/Abmelden")
def logout():
    if "authcode" in session:
        session.pop("authcode")
        session.pop('Kdnr')
        session.pop('Id')
    return redirect(url_for("bx_start.start"))


@bp.route("/Kontakt", methods=['GET', 'POST'])
def contact():
    conf = Configure(title="Norderstedter Hörzeitung - Kontakt-Impressum", app='contact', link='link-contact', request=request, current_app=current_app)
    return render_template('contact.html', conf=conf, javascript=conf.javascript.getOut())


@bp.route("/Start", methods=['GET', 'POST'])
def start():
    ts = current_app.config["TS"]
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)

    auth_code_valid = False
    auth_code_set = False
    register_request = False
    scroll_request = False
    no_backgr = False
    set_no_backgr = False
    set_with_backgr = False
    post_request = False
    regist_map = {}
    if not session.permanent: session.permanent = True
    
    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if "no_backgr" in session:
        no_backgr = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    if not auth_code_valid:
        if post_request:
            if form_data.get("release") is not None and form_data["release"] == "set":
                auth_code_set = True
                rc_code = getLogin(form_data["authcode"].upper())
                if rc_code['status']:
                    auth_code_valid = True
                    session['authcode'] = form_data["authcode"].upper()
            elif form_data.get("register") is not None and form_data["register"] == "set":
                regist_map.update({"uploadfile":request.files.get("uploadfile")})
                register_request = True
                for k, v in regist_map.items():
                    if not v: register_request = False
    
    galerie = []
    episodes = []
    
    # rc_code = get_episodes(episodes, auth_code_valid)
    # if not rc_code['status']:
    abort(500)
    if auth_code_valid:
        galerie = sorted(os.listdir(current_app.instance_path + "/galerie"))

    conf = Configure(title="Norderstedter Hörzeitung - Online-Version", app='start', link='link-main', request=request, current_app=current_app)
    conf.append("header_class", True)
    conf.append("show_banner", True)
    conf.append("show_player", True)
    if auth_code_valid: 
        html = "main.html"
        conf.append("last_play", "Aktuelle Episode anhören")
        # conf.append("show_galerie", True)
        # conf.append("show_blog", True)
        conf.append("show_upload", True)
        conf.append("show_logout", True)
        if auth_code_set:
            html = "authcode_valid.html"
    else:
        conf.append("last_play", "Den Trailer anhören")
        conf.append("show_more_trailer", True)
        if register_request:
            html = "register_request.html"
            conf.append("regist_map", regist_map)
            rc_code = send_mail(subject="Neue Registrierung eines Interessenten für die Hörzeitung", msg_template='confirm_upload', parms=regist_map, attached_file=regist_map['uploadfile'])
            current_app.logger.info("Ergebnis von send_mail: %s", rc_code)
            if rc_code["status"] != 'OK':
                if rc_code["status"] == 'INVALID_TYPE':
                    html = "register_invalid_type.html"
                else:
                    html = "register_error.html"
        elif auth_code_set:
            html = "authcode_invalid.html"
        else:
            html = "register.html"

    if "q" in request.args:
        if request.args["q"] == "episodes": 
            scroll_request = True
        elif request.args["q"] == "no-backgr": 
            set_no_backgr = True
        elif request.args["q"] == "with-backgr": 
            if no_backgr: set_with_backgr = True
    
    if (no_backgr or set_no_backgr) and not set_with_backgr:
        conf.append("show_no_backgr", True)
        conf.javascript.add({"no_backgr":1})
    if auth_code_set or scroll_request or register_request:
        conf.javascript.add({"scroll_To":"main-block"})
    if auth_code_valid:
        conf.append("user_name", session['Kdnr'])
    if set_with_backgr:
        session.pop("no_backgr")
    elif set_no_backgr:
        session["no_backgr"] = "True"
    return render_template(html, episodes=episodes, episodes1=episodes[1:], last_episode=episodes[0], galerie=galerie, javascript=conf.javascript.getOut(), conf=conf)
 """

@bp.route("/<auth_code>/feed.rss")
def feed_rss(auth_code):
    """
    https://hoerzeitung.drk-norderstedt.ipv64.net/s-nhz/0C145-C5UI-YD72-NKQ1/feed.rss
    """
    http = current_app.config["OWN_URL"]
    ts = current_app.config["TS"]
    auth_code_guest = True
    auth_code_valid = False
    if auth_code is not None:
        rc_code = getLogin(auth_code)
        if rc_code['status']:
            auth_code_guest = rc_code['dbdata']['guest']
            auth_code_valid = True
    pod = Podcast()
    pod.description = "Die Norderstedter Hörzeitung bietet Lokales aus Norderstedt und hat auch einen Blick auf die Welt"
    if auth_code_guest: pod.subtitle = "Sie hören hier als Gast nicht die reguläre Version der Hörzeitung, sondern Ausschnitte aus einigen Produktionen. Die kompletten Episoden erhalten Sie mit dem korrekten Freischaltcode."
    pod.website = credentials.EMails.WEBSITE
    pod.explicit = False
    pod.copyright = credentials.EMails.COPYRIGHT
    pod.language = "de-DE"
    pod.authors = [Person(name="DRK-Norderstedt", email=credentials.EMails.OFFICE)]
    pod.feed_url = http.goTo(url_for('bx_start.feed_rss', auth_code='reqired-auth-code'))
    pod.category = Category("News", "Daily News")
    pod.owner = pod.authors[0]
    pod.web_master = pod.authors[0]
    pod.last_updated = ts.todaytime()
    position = 1
    if auth_code_guest:
        path = "/short"
        pod.name = "Open-Version Norderstedter Hörzeitung"
        pod.image = http.goTo(url_for('bx_start.media', file='LogoGruppe-4.jpg'))
    else:
        path = "/long"
        pod.name = "Online-Version Norderstedter Hörzeitung"
        pod.image = http.goTo(url_for('bx_start.media', file='Logo-NHZ.jpg'))
    full_dir = current_app.instance_path + path
    rc_code = get_s_episodes(full_dir)
    if not rc_code['status']:
        abort(500)
    episodes = rc_code['episodes']
    for episode in episodes:
        pod_ep = pod.add_episode(Episode(title=episode["title"]))
        pod_ep.id = http.goTo(url_for('bx_start.media', file=episode["audio"]))
        if auth_code_valid: 
            attach = "?authcode=" + auth_code
            image = episode["image"]
        else: 
            attach = ""
            image = "LogoGruppe-4k.jpg"
        pod_ep.summary = episode["summary"]
        pod_ep.long_summary = episode["chapter"]
        pod_ep.publication_date = episode["published"]
        pod_ep.image = http.goTo(url_for('bx_start.media', file=image))
        pod_ep.media = Media(url=http.goTo(url_for('bx_start.media', file=episode["audio"]) + attach), 
                            size=episode["length"], 
                            type="audio/mpeg")
        pod_ep.media.populate_duration_from(episode["rawname"])
        pod_ep.position = position
        position += 1
        
    resp = make_response(pod.rss_str())
    resp.content_encoding = "UTF-8"
    resp.automatically_set_content_length = True
    if current_app.config["TEST_RUN"]:
        resp.mimetype = "text/xml"
    else:
        resp.mimetype = "application/rss+xml"
    resp.access_control_max_age = 0
    resp.default_mimetype = "text/xml"
    resp.headers['Accept']='application/rss+xml, application/rdf+xml;q=0.8, application/atom+xml;q=0.6, application/xml;q=0.4, text/xml;q=0.4'
    resp.headers['Cache-Control']='no-cache'
    resp.headers['Pragma']='no-cache'
    return resp
