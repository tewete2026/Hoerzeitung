import mariadb, os, smtplib, re
from flask import current_app, render_template, session
from datetime import date
from dateutil.relativedelta import relativedelta
from . import version, credentials, tools
from pathlib import Path
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.utils import COMMASPACE, formatdate

class Javascript:
    def __init__(self, app:str, user:str):
        if user is None: user = "--"
        self.content = {}
        self.__outline = "const SERVER_OPTIONS = {'APP':'" + app + "', 'USER':'" + user + "'"
    def add(self, attr:dict):
        self.content.update(attr)
    def getOut(self) -> str:
        for key, value in self.content.items():
            if isinstance(value, list):
                value = str(value).replace("'", '"')
                self.__outline += ", '" + key + "':'" + value + "'"
            elif isinstance(value, dict) or isinstance(value, int):
                self.__outline += ", '" + key + "':" + str(value)
            elif not isinstance(value, str):
                self.__outline += ", '" + key + "':'" + str(value) + "'"
            else:
                self.__outline += ", '" + key + "':'" + value + "'"
        return self.__outline + "}"
    
    @staticmethod
    def toOptions(rows:list[dict]) -> str:
        opts = ""
        for elem in rows:
            opts += "<option value=\"" + str(elem["id"]) + "\">" + elem["bezeichnung"] + "</option>"
        return opts
    

class Configure:
    def __init__(self, title:str, request, current_app, app:str='', link:str=''):
        self.credits = {
            "title":title,
            "user":request.remote_user,
            "addr":request.remote_addr,
            "hostname":current_app.config["HOSTNAME"],
            "created":version.Configs.APP_CREATED,
            "version":version.Configs.APP_VERSION,
            "author":version.Configs.APP_AUTHOR
        }
        if self.credits["user"] is None: self.credits["user"] = "--"
        current_app.logger.info("%s started; Modname=%s; Remote-Addr=%s; Method=%s; Mimetype=%s", title, current_app.name, request.remote_addr, request.method, request.mimetype)
        self.today=date.today()
        self.min_date = self.today - relativedelta(months=12)
        self.max_date = self.today + relativedelta(months=12)
        self.javascript = Javascript(app, self.credits["user"])
        self.map = {}
        self.error = {}
        self.javascript.add({'today':self.today, 'min_date':self.min_date, 'max_date':self.max_date, 'link_active':link})
        cpath = current_app.config["SESSION_COOKIE_PATH"]
        self.javascript.add({'drk_nhz_favorites':{'audios':[]}, 'modpath':cpath})
    def initlogin(self, dbdata):
        rolls = ["Hörer", "Vorleser", "Redakteur", "Admin", "Super-Admin"]
        self.credits.update({'pnr': dbdata['pnr']})
        self.credits.update({'guest': dbdata['guest']})
        seclevel = dbdata['seclevel']
        self.credits.update({'seclevel': seclevel})
        roll = rolls[seclevel]
        if dbdata['guest']: roll = "Gast"
        self.credits.update({'seclevel_text': roll})
    def append(self, key:str, value:str):
        self.map.update({key: value})
    def get(self, key:str):
        return self.map.get(key)
    def has(self, key:str) -> bool:
        valid = self.map.get(key) is not None
        return valid
    def haserror(self, key:str) -> bool:
        valid = self.error.get(key) is not None
        return valid

def get_db():
    try:
        pool=current_app.config["DB_POOL"]
        if pool is not None:
            db = pool.get_connection()
            current_app.logger.debug("Create Connection von Pool: %s, ID=%s", pool.pool_name, db.connection_id)
        else:
            db = None
    except mariadb.Error as e:
        db = None
        current_app.logger.critical("Error opening connection from pool: %s", e)

    return db


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    try:
        if not app.config["DB_POOL"]:
            config_pool = {
                "pool_name":app.name,
                "pool_size":20
            }
            config_conn = {
                "user":credentials.Passwords.MYSQL_USER,
                "password":credentials.Passwords.MYSQL_PWD,
                "unix_socket":"/run/mysqld/mysqld.sock",
                "host":"localhost",
                "database":"nhz",
                "autocommit":False
            }
            pool = mariadb.ConnectionPool(**config_pool, **config_conn)
            app.logger.debug("Created Pool: Name=%s, connection_count=%s", pool.pool_name, pool.connection_count)
            app.config.update({"DB_POOL":pool})
            db = pool.get_connection()
            if not db:
                raise mariadb.PoolError("Fehler bei get_connection().")
            cur = db.cursor()
            """ Einlesen Konfigurations-Elemente aus der Datenbanktabelle _Config """
            cur.execute("select item,value,amount as value from _Config order by id")
            result = cur.fetchall()
            cache = []
            for item, value, amount in result:
                if value is None: cache.append((item, amount))
                else: cache.append((item, value))
            app.config.update(cache)
            app.logger.debug(f"Import _Config {len(cache)} Einträge.")
            cur.close()
            db.close()
            rc = "OK"
    except mariadb.Error as err:
        app.logger.critical("Anlegen Pool nicht möglich!")
        rc = "ERR"

    return rc


def get_episodes(episodes, auth_code_valid, limit:bool=True):
    ts = current_app.config["TS"]
    rc_code = {'status':True}
    if auth_code_valid:
        try:
            db = get_db()
            if not db:
                raise mariadb.PoolError("Kein Pool gesetzt, keine Verbindung zur DB.")
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT * from tEpisode WHERE active=1 ORDER BY kdnr DESC")
            dbdata = cur.fetchall()
            cur.close()
            db.close()
        except mariadb.Error as err:
            current_app.logger.error("Datenbank-Fehler get_episodes: %s", err)
            rc_code['status'] = False
            rc_code['type'] = 'DBERR'
            db.close()
        if rc_code['status']:
            max_entries = current_app.config['max-line-episodes']
            for mp3 in dbdata:
                path = "/long"
                rawname = current_app.instance_path + path + "/" + mp3["audiofile"]
                # MariaDB speichert keine Zeitzonen-Info, daher wird diese angefügt (wird für RSS benötigt)
                published = ts.addtimezone(mp3["published"])
                episode = {}
                episode.update({"rawname":rawname})
                episode.update({"title":mp3["title"]})
                episode.update({"kdnr":mp3["kdnr"]})
                episode.update({"published":published})
                episode.update({"summary":mp3["summary"]})
                episode.update({"chapter":mp3["chapter"]})
                episode.update({"duration":mp3["duration"]})
                episode.update({"length":mp3["size"]})
                episode.update({"image":mp3["image"]})
                episode.update({"audio":mp3["audiofile"]})
                episodes.append(episode)
                if limit: max_entries -= 1
                if limit and max_entries == 0: break
    else:
        path = "/short"
        content = sorted(os.listdir(current_app.instance_path + path), reverse=True)
        for mp3 in content:
            rawname = current_app.instance_path + path + "/" + mp3
            episode = {}
            episode.update({"rawname":rawname})
            episode.update({"title":mp3.rstrip("mp3")})
            episode.update({"audio":mp3})
            episode.update({"length":0})
            episodes.append(episode)

    return rc_code


def get_s_episodes(full_dir, subdir=None, conf=None, max_pageview=-1, archive=False, archive_dir=None):
    rc_code = {"status":"OK"}
    ts = current_app.config["TS"]
    episodes = {}
    reverse = True
    if archive_dir is not None: 
        full_dir += "/" + archive_dir
        conf.append('archive_dir', archive_dir)
    if subdir is not None: 
        full_dir += "/" + subdir
        reverse = False
        conf.append('subdir', subdir)
    content = sorted(os.listdir(full_dir), reverse=reverse)
    page = 1
    is_more = False
    for element in content:
        if max_pageview > 0 and page > max_pageview:
            is_more = True
            break
        episode = {}
        rawname = f"{full_dir}/{element}"
        if os.path.isdir(rawname) and archive:
            key = element.strip()
            nextdir = f"{full_dir}/{key}"
            dir_list = os.listdir(nextdir)
            content_count = len(dir_list)
            if content_count > 0:
                episode.update({"dirname":key})
                episode.update({"amount":content_count})
                page += 1
        elif os.path.isdir(rawname):
            key = element.strip()
            if key in episodes:
                episode = episodes.get(key)
            episode.update({"subdir":element})
        else:
            if not element.endswith(".mp3"): continue
            key = element.split('.')[0].strip()
            audio_name = element
            if subdir is not None: 
                audio_name = f"{subdir},{audio_name}"
            if archive_dir is not None: 
                audio_name = f"{archive_dir}!{audio_name}"
            if key in episodes:
                episode = episodes.get(key)
            (title, description, published, size, dur, chapter, image_dict) = tools.getMP3Info(rawname)
            (si, duration) = tools.getMpegInfo(rawname)
            published = ts.addtimezone(published)
            episode.update({"rawname":rawname})
            episode.update({"name":key})
            episode.update({"title":str(title)})
            episode.update({"description":str(description)})
            episode.update({"summary":str(description)})
            episode.update({"chapter":chapter})
            episode.update({"audio":audio_name})
            episode.update({"length":size})
            episode.update({"duration":duration})
            if 'data' in image_dict: episode.update({"image":f'{audio_name}_ximg.jpg'})
            episode.update({"size":size})
            episode.update({"published":str(published)})
            episode.update({"date":str(published)[:19]})
            page += 1
        if len(episode) > 0: episodes.update({key:episode})
    rc_code['episodes'] = episodes.values()
    rc_code['is_more'] = is_more
    return rc_code


def get_s_favorites(base_dir, path_sub, content, conf=None, max_pageview=-1):
    rc_code = {"status":"OK"}
    ts = current_app.config["TS"]
    episodes = {}
    page = 1
    is_more = False
    for element in content['audios']:
        path = path_sub
        if max_pageview > 0 and page > max_pageview:
            is_more = True
            break
        episode = {}
        audio_name = element
        file_arr = audio_name.split('!')
        if len(file_arr) > 1:
            path = "/archive/" + file_arr[0]
            audio_name = file_arr[1]
        file_arr = audio_name.split(',')
        if len(file_arr) > 1:
            path += "/" + file_arr[0]
            audio_name = file_arr[1]
        rawname = f"{base_dir}{path}/{audio_name}"
        if not audio_name.endswith(".mp3"): continue
        key = audio_name.split('.')[0].strip()
        (title, description, published, size, dur, chapter, image_dict) = tools.getMP3Info(rawname)
        (si, duration) = tools.getMpegInfo(rawname)
        published = ts.addtimezone(published)
        episode.update({"rawname":rawname})
        episode.update({"name":key})
        episode.update({"title":str(title)})
        episode.update({"description":str(description)})
        episode.update({"summary":str(description)})
        episode.update({"chapter":chapter})
        episode.update({"audio":element})
        episode.update({"length":size})
        episode.update({"duration":duration})
        if 'data' in image_dict: episode.update({"image":f'{audio_name}_ximg.jpg'})
        episode.update({"size":size})
        episode.update({"published":str(published)})
        episode.update({"date":str(published)[:19]})
        page += 1
        if len(episode) > 0: episodes.update({key:episode})
    rc_code['episodes'] = episodes.values()
    rc_code['is_more'] = is_more
    return rc_code


def send_mail(subject:str, msg_template:str, parms:dict, send_from:str=None, send_to:str=None, attached_file:FileStorage=None, server:str=None, port:int=None, username:str=None, password:str=None, use_tls:bool=False):
    """Compose and send email with provided info and attachments.
    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    rc_code = {'status':'OK', 'message':'send_ok'}
    temp_name = None
    if not server:
        server = current_app.config['SMTP_HOST']
        port = current_app.config['SMTP_PORT']
    if not send_from:
        send_from = current_app.config['SEND_FROM']
    if not send_to:
        send_to = current_app.config['SEND_TO']
        if isinstance(send_to, list):
            send_to = COMMASPACE.join(send_to)
    if not username:
        username = current_app.config['SMTP_USER']
        password = current_app.config['SMTP_PWD']
    if attached_file:
        filename = secure_filename(attached_file.filename)
        if len(filename) > 0: 
            temp_name = current_app.instance_path + "/upload/" + filename
            attached_file.save(temp_name)
            current_app.logger.info("Datei hochgeladen: %s", filename)
    try:
        message = MIMEMultipart()
        message['From'] = send_from
        message['To'] = send_to
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = subject
        content = MIMEMultipart('alternative')
        content.attach(MIMEText(render_template(msg_template + '.txt', parms=parms), 'plain'))
        content.attach(MIMEText(render_template(msg_template + '.html', parms=parms), 'html'))
        message.attach(content)
        if temp_name:
            type = filename.split(".").pop().lower()
            valid = True
            with open(temp_name, 'rb') as file:
                if ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif'].count(type):
                    if type == 'jpg': type = 'jpeg'
                    elif type == 'tif': type = 'tiff'
                    attachment = MIMEImage(file.read(), type)
                elif ['mp3', 'mp2', 'mpeg', 'flac', 'ogg'].count(type):
                    if ['mp3', 'mp2'].count(type): type = 'mpeg'
                    attachment = MIMEAudio(file.read(), type)
                elif ['pdf'].count(type):
                    attachment = MIMEApplication(file.read(), type)
                else:
                    valid = False
                if valid:
                    attachment.add_header('Content-Disposition', 'attachment; filename="{}"'.format(Path(filename).name))
                    message.attach(attachment)
                    rc_code['attached_file'] = filename
                else:
                    rc_code['status'] = 'INVALID_TYPE'
                    return rc_code
        smtp = smtplib.SMTP(server, port)
        # smtp = smtplib.SMTP_SSL(server, port)
        if use_tls:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.sendmail(send_from, send_to, message.as_string())
        smtp.quit()
        rc_code['send_to'] = message['To']
        rc_code['send_from'] = message['From']
        rc_code['send_date'] = message['Date']
        rc_code['subject'] = message['Subject']
        rc_code['server'] = server
        if temp_name is not None and os.path.exists(temp_name):
            os.remove(temp_name)
            current_app.logger.info("Datei aus 'Upload' entfernt: %s", filename)
    except Exception as err:
        current_app.logger.error("Send Mail Exception: %s", err.args)
        rc_code['status'] = 'ERR'
        rc_code['message'] = err

    return rc_code


def getLogin(freeCode:str, fav_cookie:str=None):
    rc_code = {'status':True}
    try:
        db = get_db()
        if not db:
            raise mariadb.PoolError("Kein Pool gesetzt, keine Verbindung zur DB.")
        re_m = re.fullmatch(r'^[0-4][1-9A-Z]{4}-[1-9A-Z]{4}-[1-9A-Z]{4}-[1-9A-Z]{4}', freeCode.upper())
        if re_m is None:
            raise mariadb.NotSupportedError("Kein gültiges Freischaltcode-Format.")
        db.begin()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT id,pnr,seclevel,pnrcreate,lastVersion,histid,freecode,IF(active=1,TRUE,FALSE) as active,IF(guest=1,TRUE,FALSE) as guest,createDate,lastActive,curdate() as last_access from tUser WHERE freecode=? && active=1 FOR UPDATE", (freeCode.upper(),))
        dbdata = cur.fetchone()
        if cur.rowcount > 0:
            rc_code['dbdata'] = dbdata
            cur.execute("UPDATE tUser SET lastActive=curdate(),lastVersion=? WHERE id=?", (version.Configs.APP_RELEASE, rc_code['dbdata']['id']))
            if fav_cookie is not None:
                cur.execute("INSERT INTO tUser_fav(pnr_id,favorites) VALUES(?,?) ON DUPLICATE KEY UPDATE favorites=?", (rc_code['dbdata']['id'], fav_cookie, fav_cookie))
            else:
                cur.execute("SELECT id,pnr_id,favorites from tUser_fav WHERE pnr_id=?", (rc_code['dbdata']['id'],))
                if cur.rowcount > 0:
                    dbdata['favorites'] = cur.fetchone()
        else:
            rc_code["status"] = False
            rc_code['type'] = 'NOTFOUND'
        db.commit()
        cur.close()
        db.close()
    except mariadb.NotSupportedError as err:
        current_app.logger.warning("Format-Fehler getLogin: %s - %s", freeCode, err)
        rc_code['status'] = False
        rc_code['type'] = 'FORMERR'
        if db: 
            db.rollback()
            db.close()
    except mariadb.Error as err:
        current_app.logger.error("Datenbank-Fehler getLogin: %s - %s", freeCode, err)
        rc_code['status'] = False
        rc_code['type'] = 'DBERR'
        if db: 
            db.rollback()
            db.close()
    return rc_code
