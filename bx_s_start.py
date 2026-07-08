# import mariadb
# import feedparser
from flask import Blueprint
from flask import current_app
from flask import request
from flask import render_template, session
from flask import redirect, url_for
from werkzeug.exceptions import abort
from .db import get_db, Configure, getLogin, get_s_episodes
from . import version

bp = Blueprint("bx_s_start", __name__)


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


@bp.route("/S-Impressum", methods=['GET'])
def s_impress():
    conf = Configure("Norderstedter Hörzeitung - Impressum", request, current_app)
    if "authcode" in session:
        conf.append("show_navall", True)
    return render_template("impressum.html", conf=conf)


@bp.route("/S-Abmelden", methods=['GET'])
def s_logout():
    session.pop('dbdata')
    session.pop('authcode')
    session.pop('max_pageview')
    session.pop('guest')
    return redirect(url_for('bx_s_start.s_album'))


def show_content(html_form, header, subdir=None):
    ts = current_app.config["TS"]
    auth_code_valid = False
    auth_code_set = False
    auth_code_empty = False
    post_request = False
    if 'max_pageview' not in session:
        max_pageview = current_app.config["max_pageview"]
        session['max_pageview'] = max_pageview
    else:
        max_pageview = session['max_pageview']
    
    if "authcode" in session:
        if getLogin(session["authcode"])['status']:
            auth_code_valid = True
    
    if request.method == "POST":
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
                rc_code = getLogin(authcode.upper())
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
        if post_request:
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
            path = "/long"
        full_dir = current_app.instance_path + path
        rc_code = get_s_episodes(full_dir, subdir, conf, max_pageview)
        conf.append('episodes', rc_code['episodes'])
        if rc_code['is_more']:
            conf.append('is_more', True)
    return render_template(html, conf=conf, javascript=conf.javascript.getOut())
