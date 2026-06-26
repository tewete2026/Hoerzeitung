# import mariadb
import os, pathlib
# import feedparser
from flask import Blueprint
from flask import current_app
from flask import request
from flask import render_template, session
from flask import redirect, url_for
from werkzeug.exceptions import abort
from .service.srv_tool import getMP3Info, getMpegInfo
from .db import get_db, Configure, getLogin
from . import version

bp = Blueprint("bx_s_start", __name__)


@bp.route("/S-Album", methods=['GET', 'POST'])
def s_album():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("/long", "album.html", " - Album Übersicht")


@bp.route("/S-Episoden/<subdir>", methods=['GET', 'POST'])
def s_episodes(subdir):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("/long", "episodes.html", " - Einzel Beiträge", subdir=subdir)


@bp.route("/S-Impressum", methods=['GET'])
def s_impress():
    conf = Configure("Norderstedter Hörzeitung - Impressum", request, current_app)
    return render_template("impressum.html", conf=conf)


@bp.route("/S-Abmelden", methods=['GET'])
def s_logout():
    session.pop('id')
    session.pop('pnr')
    session.pop('seclevel')
    session.pop('authcode')
    return redirect(url_for('bx_s_start.s_album'))


def show_content(path, html_form, header, subdir=None):
    ts = current_app.config["TS"]
    auth_code_valid = False
    auth_code_set = False
    auth_code_empty = False
    post_request = False
    episodes = {}
    
    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
        form_data = request.form
        post_request = True
    
    if not auth_code_valid:
        html = 'login.html'
        if post_request:
            auth_code_set = True
            authcode = form_data["authcode"].strip()
            if len(authcode) > 0:
                rc_code = getLogin(authcode.upper())
                if rc_code['status']:
                    auth_code_valid = True
                    if not session.permanent: session.permanent = True
                    session['dbdata'] = rc_code['dbdata']
                    session['authcode'] = rc_code['dbdata']['freecode']
                    html = html_form
                    current_app.logger.info("Login erfolgreich: pnr=%s, seclevel=%s, freecode=%s", rc_code['dbdata']['pnr'], rc_code['dbdata']['seclevel'], rc_code['dbdata']['freecode'])
            else:
                auth_code_empty = True
    else:
        html = html_form

    conf = Configure("Norderstedter Hörzeitung" + header, request, current_app)
    
    if auth_code_set and auth_code_empty:
        conf.error['authcode'] = "Es wurde kein Code eingegeben. Bitte im Feld oberhalb einen gültigen Code eingeben."
    elif auth_code_set and not auth_code_valid:
        conf.error['authcode'] = "Der eingegebene Code ist nicht gültig."
    
    if auth_code_valid:
        if session['dbdata']['seclevel'] > 0:
            conf.append("show_navtop", True)
        full_dir = current_app.instance_path + path
        reverse = True
        if subdir is not None: 
            full_dir += "/" + subdir
            reverse = False
            conf.map['subdir'] = subdir
        content = sorted(os.listdir(full_dir), reverse=reverse)
        for element in content:
            episode = {}
            rawname = f"{full_dir}/{element}"
            if os.path.isdir(rawname):
                key = element.strip()
                if key in episodes:
                    episode = episodes.get(key)
                episode.update({"subdir":element})
            else:
                if not element.endswith(".mp3"): continue
                key = element.split('.')[0].strip()
                audio_name = element
                if subdir is not None: 
                    audio_name = f"{subdir}_{element}"
                if key in episodes:
                    episode = episodes.get(key)
                (title, description, published, size, dur, chapter) = getMP3Info(rawname)
                (si, duration) = getMpegInfo(rawname)
                episode.update({"rawname":rawname})
                episode.update({"name":key})
                episode.update({"title":title})
                episode.update({"description":description})
                episode.update({"chapter":chapter})
                episode.update({"audio":audio_name})
                episode.update({"length":duration})
                episode.update({"size":size})
                episode.update({"published":str(published)[:19]})
            episodes.update({key:episode})
    return render_template(html, episodes=episodes.values(), conf=conf, javascript=conf.javascript.getOut())
