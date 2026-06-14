import os
from podgen import Podcast, Episode, Person, Category, Media
from flask import Blueprint
from flask import current_app, session
from flask import request, make_response
from flask import render_template, redirect
from flask import redirect, url_for, send_from_directory
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from .db import get_db, Configure, get_episodes, send_mail, getLogin
from . import version, credentials
from .podcast_texte import podcast_texte

bp = Blueprint("bx_start", __name__)


@bp.route("/media/<file>")
def media(file):
    path = ""
    if not file.endswith(".jpg"):
        path = "/short"
        auth_code_valid = False
        if "authcode" in session:
            auth_code_valid = True
        elif "authcode" in request.args:
            auth_code_valid = getLogin(request.args["authcode"])['status']
        if auth_code_valid:
            path = "/long"
        # werkzeug.datastructures.headers.EnvironHeaders
        if current_app.config['TEST_RUN'] == 'PROD':
            current_app.logger.info("Empfangener HTTP-Header für %s, %s, %s: %s", file, request.remote_addr, request.origin, request.headers)
    else:
        if file.startswith("IMG_"):path = "/galerie"
    path = current_app.instance_path + path
    return send_from_directory(path, file)


@bp.route("/Abmelden")
def logout():
    if "authcode" in session:
        session.pop("authcode")
        session.pop('Vorname')
        session.pop('Nachname')
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
                    session['Vorname'] = rc_code['vorname']
                    session['Nachname'] = rc_code['nachname']
                    session['Kdnr'] = rc_code['kdnr']
                    session['Id'] = rc_code['id']
                    session['authcode'] = form_data["authcode"].upper()
            elif form_data.get("register") is not None and form_data["register"] == "set":
                regist_map.update({"name":form_data.get("name")})
                regist_map.update({"email":form_data.get("email")})
                regist_map.update({"street":form_data.get("street")})
                regist_map.update({"city":form_data.get("city")})
                regist_map.update({"commit":form_data.get("commit")})
                regist_map.update({"options":form_data.get("options")})
                regist_map.update({"uploadfile":request.files.get("uploadfile")})
                register_request = True
                for k, v in regist_map.items():
                    if not v: register_request = False
    
    galerie = []
    episodes = []
    
    rc_code = get_episodes(episodes, auth_code_valid)
    if not rc_code['status']:
        abort(500)
    if auth_code_valid:
        galerie = sorted(os.listdir(current_app.instance_path + "/galerie"))

    conf = Configure(title="Norderstedter Hörzeitung - Online-Version", app='start', link='link-main', request=request, current_app=current_app)
    conf.append("header_class", True)
    conf.append("show_banner", True)
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
        conf.append("user_name", session['Vorname'] + " " + session['Nachname'])
    if set_with_backgr:
        session.pop("no_backgr")
    elif set_no_backgr:
        session["no_backgr"] = "True"
    # print(conf.map['user_name'])
    return render_template(html, episodes=episodes, episodes1=episodes[1:], last_episode=episodes[0], galerie=galerie, javascript=conf.javascript.getOut(), conf=conf)


@bp.route("/<auth_code>/feed.rss")
def feed_rss(auth_code):
    http = current_app.config["OWN_URL"]
    ts = current_app.config["TS"]
    auth_code_valid = False
    if auth_code is not None:
        if getLogin(auth_code)['status']:
            auth_code_valid = True
    pod = Podcast()
    pod.name = "Online-Version Norderstedter Hörzeitung"
    pod.description = "Die Norderstedter Hörzeitung bietet Lokales aus Norderstedt und hat auch einen Blick auf die Welt"
    if not auth_code_valid: pod.subtitle = "Sie hören hier nur einzelne Episoden als Kostproben. Die kompletten Episoden erhalten Sie mit dem korrekten Freischaltcode."
    pod.website = credentials.EMails.WEBSITE
    pod.explicit = False
    pod.image = http.goTo(url_for('bx_start.media', file='Logo-NHZ.jpg'))
    pod.copyright = credentials.EMails.COPYRIGHT
    pod.language = "de-DE"
    pod.authors = [Person(name="DRK-Norderstedt", email=credentials.EMails.OFFICE)]
    pod.feed_url = http.goTo(url_for('bx_start.feed_rss', auth_code='reqired-auth-code'))
    pod.category = Category("News", "Daily News")
    pod.owner = pod.authors[0]
    pod.web_master = pod.authors[0]
    pod.last_updated = ts.todaytime()
    episodes = []
    position = 1
    rc_code = get_episodes(episodes=episodes, auth_code_valid=auth_code_valid, limit=False)
    if not rc_code['status']:
        abort(500)
    for episode in episodes:
        pod_ep = pod.add_episode(Episode(title=episode["title"]))
        pod_ep.id = http.goTo(url_for('bx_start.media', file=episode["audio"]))
        if auth_code_valid:
            pod_ep.summary = episode["summary"]
            pod_ep.long_summary = episode["chapter"]
            pod_ep.publication_date = episode["published"]
            pod_ep.image = http.goTo(url_for('bx_start.media', file=episode["image"]))
            attach = "?authcode=" + auth_code
            pod_ep.media = Media(url=http.goTo(url_for('bx_start.media', file=episode["audio"]) + attach), 
                                size=episode["length"], 
                                type="audio/mpeg")
        else: 
            pod_ep.media = Media(url=http.goTo(url_for('bx_start.media', file=episode["audio"])), 
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
