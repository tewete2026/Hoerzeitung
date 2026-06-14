# import mariadb
import feedparser
from flask import Blueprint
from flask import current_app
from flask import request
from flask import render_template
from flask import redirect, url_for
from werkzeug.exceptions import abort
# from .db import get_db
from . import version

bp = Blueprint("main", __name__)


@bp.after_request
def add_security_headers(response):
    response.headers['Cache-Control']='no-cache'
    response.headers['Pragma']='no-cache'
    return response


@bp.route("/")
def index():
    return redirect(url_for("bx_start.start"))


@bp.route("/test")
def test():
    if current_app.config["NO_POOL_AVAILABLE"]:
        abort(500)
    
    # rss_url = "https://nhz.podcaster.de/hoerzeitung.rss"
    # feed = feedparser.parse(rss_url)
    # outstr = "<h2>Ausgabe RSS</h2>"
    # if feed.status == 200:
    #     print("Feed", feed.feed)
    #     for key in feed.feed:
    #         print("Feed.key", key)
    #     outstr = f"<h2>{feed.feed["title"]}</h2>"
    #     content = {}
    #     content.update({"title":feed.feed["title"]})
    #     outstr += f"<h5>{feed.feed["subtitle"]}</h5>"
    #     outstr += f"<h6>{feed.feed["summary"]}</h6>"
    #     content.update({"subtitle":feed.feed["summary"].replace("\n", "\\n")})
    #     printed = False
    #     for entry in feed.entries:
    #         if not printed:
    #             print("content", type(entry["content"]))
    #             for cont in entry["content"]:
    #                 print("Content", cont)
    #             print("title_detail", entry["title_detail"])
    #             print("summary_detail", entry["summary_detail"])
    #             print("published_parsed", entry["published_parsed"])
    #             print("published", type(entry["published"]))
    #             print("published_parsed", type(entry["published_parsed"]))
    #             print("itunes_duration", type(entry["itunes_duration"]))
    #             print("itunes_episode", type(entry["itunes_episode"]))
    #             print("itunes_episodetype", type(entry["itunes_episodetype"]))
    #             if "subtitle" in entry: subtitle = entry["subtitle"]
    #             else: subtitle = "--"
    #             content.update({"episode":entry["title"]})
    #             content.update({"episode_subtitle":subtitle})
    #             content.update({"image":entry["image"]["href"]})
    #             content.update({"published":entry["published"]})
    #             content.update({"duration":entry["itunes_duration"]})
    #             summ = str(entry["summary"])
    #             summ = summ.replace("\n", "\\n")
    #             content.update({"summary":summ})
    #             for link in entry["links"]:
    #                 if link["type"] == 'audio/mpeg':
    #                     content.update({"audio":link["href"]})
    #             print(content)
    #             for key in entry:
    #                 print("Entry.key", key)
    #             printed = True
    #         for link in entry["links"]:
    #             if link["type"] == 'audio/mpeg':
    #                 mp3 = link["href"]

    #         timestruct = entry["published_parsed"]
    #         dst = 0
    #         if timestruct.tm_mon >= 3 and timestruct.tm_mon <= 10:
    #             dst += 1
    #         dt = datetime.fromtimestamp(mktime(timestruct))
    #         dt_n = datetime(day=dt.day, month=dt.month, year=dt.year, hour=dt.hour + dst, minute=dt.minute, second=dt.second)
    #         published = dt_n.strftime("%d.%m.%Y %H:%M")
    #         # published = "{0:02d}.{1:02d}.{2:4d} {3:02d}:{4:02d}".format(timestruct.tm_mday, timestruct.tm_mon, timestruct.tm_year, timestruct.tm_hour, timestruct.tm_min)
    #         if "subtitle" in entry: subtitle = entry["subtitle"]
    #         else: subtitle = "--"
    #         outstr += "<p>\
    #             <span><strong>ID:</strong> " + entry["id"] + "</span> <br> \
    #             <span><strong>Titel:</strong> " + entry["title"] + "</span> <br> \
    #             <span><strong>Subtitel:</strong> " + subtitle + "</span> <br> \
    #             <span><strong>Published:</strong> " + entry["published"] + "</span> <br> \
    #             <span><strong>Published:</strong> " + published + "</span> <br> \
    #             <span><strong>Content:</strong> " + entry["summary"] + "</span> <br> \
    #             <span><strong>Author:</strong> " + entry["author"] + "</span> <br> \
    #             <span><strong>Link:</strong> " + entry["link"] + "</span> <br> \
    #             <span><strong>Duration:</strong> " + entry["itunes_duration"] + "</span> <br> \
    #             <span><strong>Audio:</strong> " + mp3 + "</span>\
    #             </p>"
    # else:
    #     outstr += "<h3>Failed to get RSS feed. Status code:" + feed.status + "</h3"

    # return render_template("test.html", outstr=outstr, content=content)
    return "Deactivated"
