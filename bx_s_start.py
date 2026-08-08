# import mariadb
# import feedparser
from flask import Blueprint
from flask import current_app
from flask import request
from flask import render_template, session
from flask import redirect, url_for
from werkzeug.exceptions import abort
from markdown import markdown
from .db import get_db, Configure, getLogin, get_s_episodes
from . import version

bp = Blueprint("bx_s_start", __name__)


@bp.route("/Open", methods=['GET'])
def s_open():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    clear_session()
    return show_content("album.html", " - Album Übersicht - Open-Version", guest=True)


@bp.route("/Online/<authcode>", methods=['GET'])
def s_online(authcode):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    clear_session()
    return show_content("album.html", " - Album Übersicht - Online-Version", online=True, parm_authcode=authcode)


@bp.route("/S-Album", methods=['GET', 'POST'])
def s_album():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("album.html", " - Album Übersicht")


@bp.route("/S-Episoden/<subdir>", methods=['GET', 'POST'])
def s_episodes(subdir):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("episodes.html", " - Einzel Beiträge", subdir=subdir)


@bp.route("/S-Archiv", methods=['GET', 'POST'])
def s_archive():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("archive.html", " - Archiv Übersicht", archive=True)


@bp.route("/S-Archiv-Album/<year>", methods=['GET', 'POST'])
def s_arc_album(year):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("album.html", " - Archiv Beiträge", archive_dir=year)


@bp.route("/S-Archiv-Episoden/<year>/<subdir>", methods=['GET', 'POST'])
def s_arc_episodes(year, subdir):
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    return show_content("episodes.html", " - Archiv-Einzel Beiträge", archive_dir=year, subdir=subdir)


@bp.route("/S-Impressum", methods=['GET'])
def s_impress():
    conf = Configure("Norderstedter Hörzeitung - Impressum", request, current_app)
    if "authcode" in session:
        conf.append("show_navall", True)
    return render_template("impressum.html", conf=conf)


@bp.route("/S-Release-Info", methods=['GET'])
def s_releases():
    conf = Configure("Norderstedter Hörzeitung - Aktualisierungen", request, current_app)
    if "authcode" in session:
        conf.append("show_navall", True)
    with open(current_app.root_path + "/static/doc/history.md") as markdn:
        conf.append("content", markdown(text=markdn.read(), output_format='html'))
    return render_template("releaseInfo.html", conf=conf)


@bp.route("/S-Abmelden", methods=['GET'])
def s_logout():
    clear_session()
    return redirect(url_for('bx_s_start.s_album'))


def clear_session():
    if 'dbdata' in session:
        session.pop('dbdata')
        session.pop('authcode')
        session.pop('max_pageview')
        session.pop('guest')


def show_content(html_form, header, subdir=None, guest=False, online=False, parm_authcode=None, archive=False, archive_dir=None):
    ts = current_app.config["TS"]
    auth_code_valid = False
    auth_code_set = False
    auth_code_empty = False
    post_request = False
    single_view = True
    if subdir is None: 
        single_view = False
        if 'max_pageview' not in session:
            max_pageview = current_app.config["max_pageview"]
            session['max_pageview'] = max_pageview
        else:
            max_pageview = session['max_pageview']
    else:
        max_pageview = -1
    
    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if guest:
        form_data = {"authcode":current_app.config["GUEST_CODE"]}
        post_request = True
    elif online:
        form_data = {"authcode":parm_authcode}
        post_request = True
    elif request.method == "POST":
        form_data = request.form
        post_request = True

    conf = Configure("Norderstedter Hörzeitung" + header, request, current_app)
    
    if not auth_code_valid:
        html = 'login.html'
        conf.javascript.add({'guestcode':current_app.config['GUEST_CODE']})
        if post_request and 'authcode' in form_data:
            auth_code_set = True
            authcode = form_data["authcode"].strip()
            if len(authcode) > 0:
                rc_code = getLogin(authcode)
                if rc_code['status']:
                    auth_code_valid = True
                    if not session.permanent: session.permanent = True
                    session['dbdata'] = rc_code['dbdata']
                    session['authcode'] = rc_code['dbdata']['freecode']
                    session['guest'] = rc_code['dbdata']['guest']
                    current_app.logger.info("Login erfolgreich: pnr=%s, seclevel=%s, freecode=%s", rc_code['dbdata']['pnr'], rc_code['dbdata']['seclevel'], rc_code['dbdata']['freecode'])
            else:
                auth_code_empty = True
    
    if auth_code_set and auth_code_empty:
        conf.error['authcode'] = "Es wurde kein Code eingegeben. Bitte im Feld oberhalb einen gültigen Code eingeben."
    elif auth_code_set and not auth_code_valid:
        conf.error['authcode'] = "Der eingegebene Code ist nicht gültig."
    
    if auth_code_valid:
        conf.initlogin(session['dbdata'])
        auth_code_guest = session['guest']
        html = html_form
        if post_request and not single_view:
            if 'morepage' in form_data:
                morepage = form_data['morepage']
                if morepage.isnumeric():
                    max_pageview += int(morepage)
                elif morepage == 'ALL':
                    max_pageview = -1
                session['max_pageview'] = max_pageview
            if 'setpage' in form_data:
                setpage = form_data['setpage']
                if setpage.isnumeric():
                    max_pageview = int(setpage)
                elif setpage == 'ALL':
                    max_pageview = -1
                session['max_pageview'] = max_pageview
        show_max_pageview = max_pageview
        if max_pageview < 0: show_max_pageview ="Alles"
        conf.append("show_max_pageview", show_max_pageview)
        conf.append("show_navall", True)
        if session['dbdata']['seclevel'] > 1:
            conf.append("show_navtop", True)
        if auth_code_guest:
            path = "/short"
        else:
            if archive or archive_dir is not None:
                path = "/archive"
            else:
                path = "/long"
        full_dir = current_app.instance_path + path
        rc_code = get_s_episodes(full_dir, subdir, conf, max_pageview, archive=archive, archive_dir=archive_dir)
        conf.append('episodes', rc_code['episodes'])
        if rc_code['is_more']:
            conf.append('is_more', True)

    return render_template(html, conf=conf, javascript=conf.javascript.getOut())
