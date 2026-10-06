import mariadb, os
from flask import Blueprint
from flask import render_template
from flask import current_app
from flask import request
from datetime import date
import sys

from ..db import get_db
from .. import version
from . import tools

bp = Blueprint("ax_episode", __name__, url_prefix="/service")


@bp.route("/ax-get-episode-edit/", methods=['POST'])
def ax_get_episode_edit():
    result = request.get_json()
    result_map = dict(result)
    episode_id = result_map["main-id"]
    timestamp_N = tools.getTS(current_app.config)
    timestamp_P = None
    item_id_head = None
    dbdata={}
    try:
        dbdata.update({"status":"OK"})
        db = get_db()
        if not db:
            raise mariadb.PoolError()
        db.begin()
        cur = db.cursor(dictionary=True)
        
        if "timestamp" in result_map:
            timestamp_P = result_map["timestamp"]
        if "item_id_head" in result_map:
            item_id_head = result_map["item_id_head"]
            if timestamp_P is not None and item_id_head != episode_id:
                """ Vorherige episode-ID entsperren """
                cur.execute("update tEpisode set sperre=null where id=? and sperre IS NOT NULL and sperre=?", (item_id_head, timestamp_P))
                current_app.logger.debug("Vorherige Sperre=%s für Episode=%s aufgehoben.", timestamp_P, item_id_head)
            
        cur.execute("UPDATE tEpisode SET Sperre=? WHERE Sperre IS NULL AND id=?", (timestamp_N, episode_id))
        db.commit()
        cur.execute("SELECT id,kdnr,sperre,title,summary,IFNULL(chapter,'') as chapter,IFNULL(image,'') as image,audiofile,IF(active=TRUE,'on','') as aktiv,DATE_FORMAT(published,'%Y-%m-%dT%H:%i:%s') as datum \
                    FROM tEpisode WHERE id=?", (episode_id,))
        dbdata.update({"episode":cur.fetchone()})

        act_timestamp = str(dbdata["episode"]["sperre"])
        if act_timestamp == timestamp_N:
            dbdata.update({"timestamp":timestamp_N})
            current_app.logger.debug("Neue Sperre=%s für Episode=%s eingerichtet.", timestamp_N, episode_id)
        elif timestamp_P is not None and act_timestamp == timestamp_P:
            dbdata.update({"timestamp":timestamp_P})
        else:
            dbdata.update({"status":"LCK"})
        
        cur.close()
        db.close()
    except mariadb.Error as err:
        current_app.logger.error("Datenbank-Fehler: %s/ax-get-episode-edit/%s/%s", bp.name, episode_id, err)
        dbdata.update({"status":"ERR"})

    return dbdata


@bp.route("/ax-submit-episode-release/", methods=['POST'])
def ax_submit_episode_release():
    result = request.get_json()
    current_app.logger.info("Empfangene Daten: " + request.headers.get('Content-Type') + "; Remote-Addr=" + request.remote_addr + "; Method=" + request.method + "; Content-length=" + str(request.content_length) + "; Remote-User=" + str(request.remote_user))
    rc_code = {"status":"OK", "contentlength":request.content_length, "contentype":request.content_type, "remoteaddr":request.remote_addr}
    try:
        main_id = None
        item_timestamp = None
        for pkey, parm in result:
            if pkey == "item-id":
                main_id = parm
            elif pkey == "item-timestamp":
                item_timestamp = parm
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError()
            db.begin()
            cur = db.cursor(dictionary=True)

            if main_id is not None:
                rc_code["id"] = main_id
                cur.execute("SELECT IFNULL(sperre,'IGNORE') as sperre FROM tEpisode WHERE id=? FOR UPDATE", (main_id,))
                timestamp = str(cur.fetchone()["sperre"])
                if timestamp == item_timestamp:
                    cur.execute("update tEpisode set sperre=null where id=? and sperre=?", (main_id, item_timestamp))
                    current_app.logger.debug("RELEASE: Timestamp entfernt. Id=%s, Timestamp=%s, RowCount=%s, Warnings=%s", main_id, item_timestamp, cur.rowcount, cur.warnings)
                else:
                    rc_code["status"] = "IGNORE"
            db.commit()
            cur.close()
            db.close()
        except mariadb.Error as err:
            current_app.logger.error("Datenbank-Fehler: %s/ax-submit-episode-release/%s", bp.name, err)
            rc_code["status"] = "ERR"
            db.rollback()
            db.close()
            current_app.logger.error("Datenbank-Rollback")
    except:
        (type, value, traceback) = sys.exc_info()
        current_app.logger.critical("Unexpected error: Type=%s; Exception=%s; Trace-Line=%s",type, value, traceback.tb_lineno)
        rc_code["status"] = "ERR"

    return rc_code


@bp.route("/ax-get-episode-overview/", methods=['POST'])
def ax_get_episode_overview():
    result_map = dict(request.get_json())
    rc_code = {"status":"OK", "contentlength":request.content_length, "contentype":request.content_type, "remoteaddr":request.remote_addr}
    overview_search = result_map["overview-search"]
    overview_page = int(result_map["overview-page"])
    overview_maxlines = current_app.config["max-line-overview"]
    overview_offset = (overview_page - 1) * overview_maxlines
    overview_readlines = overview_maxlines + 1

    sql_parms = ""
    if overview_search is not None and len(overview_search) > 0 and overview_search != "ALL":
        if overview_search.isnumeric():
            sql_parms = f"WHERE kdnr={overview_search}"
        elif not overview_search.isspace():
            search_like = "'%" +  overview_search + "%'"
            sql_parms = f"WHERE title like {search_like}"

    dbdata={}
    try:
        db = get_db()
        if not db:
            raise mariadb.PoolError()
        cur = db.cursor(dictionary=True)
        is_more_lines = False

        cur.execute(f"SELECT id,kdnr,title,audiofile,summary,IF(active=0,'','*') as aktiv, \
                    DATE_FORMAT(DATE(published),'%d.%m.%Y') as datum, DATE_FORMAT(TIME(published),'%H:%i:%s') as zeit \
                    from tEpisode \
                    {sql_parms} \
                    ORDER BY published DESC LIMIT {overview_offset}, {overview_readlines}")
        dbdata.update({"episodes":cur.fetchall()})
        len_vis = len(dbdata["episodes"])
        show_lines = len_vis
        if len_vis > overview_maxlines:
            show_lines = overview_maxlines
            is_more_lines = True
            
        current_app.logger.debug("Episodes RowCount=%s, Warnings=%s, ShowLines=%s", cur.rowcount, cur.warnings, show_lines)
        rc_code["html"] = render_template("service/verwEpisoden_body.html", episodes=dbdata["episodes"][0:show_lines])
        rc_code["pagination"] = is_more_lines
        cur.close()
        db.close()
    except mariadb.Error as err:
        db.close()
        current_app.logger.error("Datenbank-Fehler: %s/%s", bp.name, err)
        rc_code["status"] = "ERR"

    return rc_code
