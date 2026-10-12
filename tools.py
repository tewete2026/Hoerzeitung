import os, random
from math import floor
from flask import current_app
from mutagen.mp3 import MP3
from mutagen.id3 import CHAP, TIT2, TLEN, COMM, TXXX, ID3, TPE1, TDRC, TALB, TCON, APIC, TYER
from sox import file_info as audio_info

''' mutagen.id3.Encoding.UTF8 has the value 3 so I presume that encoding=3 forces utf-8 encoding.
    # Encoding the string to UTF-16
    utf16_encoded = text.encode('utf-16')
'''

def getMP3Info(rawname:str):
    ts = current_app.config["TS"]
    # audio = MP3(current_app.instance_path + "/" + mp3, ID3=EasyID3)
    audio = MP3(rawname)
    if rawname.endswith("1105.mp3"): print(audio)
    chapter_dict = {}
    image_dict = {}
    description = "- - - -"
    title = "---"
    tlen = None
    current_app.logger.debug(rawname)
    for key in audio.keys():
        cont = audio.get(key)
        current_app.logger.debug((key, type(cont)))
        if isinstance(cont, CHAP):
            text = cont.sub_frames["TIT2"].text[0]
            current_app.logger.debug("%s, %s, %s", text, cont.start_time, cont.end_time)
            if len(text) > 0:
                chapter_dict.update({key.removeprefix("CHAP:"):(text, cont.start_time)})
        if key == 'TIT2':
            title = cont.text[0]
            current_app.logger.debug("%s, %s", title, cont.encoding)
        elif key == 'TLEN':
            tlen = cont.text[0]
            current_app.logger.debug("%s, %s", tlen, cont.encoding)
        elif key[:5] == 'CTOC:':
            current_app.logger.debug("%s, flags=%s", cont.child_element_ids, cont.flags)
        elif key[:5] == 'TXXX:':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TPE1':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TDRC':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TCON':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TSSE':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TENC':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TALB':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key == 'TYER':
            current_app.logger.debug("%s, %s", cont.text[0], cont.encoding)
        elif key[:5] == 'COMM:':
            description = cont.text[0]
            current_app.logger.debug("%s, %s", description, cont.encoding)
        elif key[:5] == 'APIC:':
            image_dict.update({'mime': cont.mime})
            image_dict.update({'desc': cont.desc})
            image_dict.update({'data': cont.data})
            current_app.logger.debug("Mime: %s, Desc: %s, Len: %s", cont.mime, cont.desc, len(cont.data))
    # keys = ["TALB", "TPE1", "TDRC", "TIT2", "TENC", "TLEN"]
    # for key in keys:
    #     print(key, audio.get(key))
    size = os.stat(rawname).st_size
    chapter = ""
    counter = 1
    for key, (text, start) in chapter_dict.items():
        chapter += "{0:02}. {1}<br>".format(counter, text)
        counter += 1
    published = ts.fromtimestamp(os.stat(rawname).st_mtime)
    if tlen is None:
        dur = audio.info.length
    else:
        dur = float(tlen[0]) / 1000
    min = dur / 60
    sec = dur % 60
    duration = "{0:02.0f}:{1:02.0f}".format(min, sec)
    # print(tlen, dur, min, sec, duration, audio, audio.keys())
    return (title, description, published, size, duration, chapter, chapter_dict, image_dict)


def setMp3Info(rawname:str, fields:tuple):
    audio = ID3(rawname)
    audio['TIT2'] = TIT2(text=[fields[0]], encoding=3) # Titel / Encoding 3 = UTF-8
    audio['COMM'] = COMM(desc="summary", lang='ger', text=[fields[1]], encoding=3) # Beschreibung
    audio['TDRC'] = TDRC(text=[fields[2]], encoding=3) # Produktionsdatum
    audio.add(TXXX(desc="Supporter", text=[fields[3]], encoding=3)) # Techniker
    audio.add(TXXX(desc="Team", text=[fields[4]], encoding=3)) # Team
    playtime = audio_info.duration(rawname)
    audio['TLEN'] = TLEN(text=[str(playtime*1000)], encoding=3) # Spiellänge in Millisekunden
    with open(fields[5], mode='rb') as image_file:
        audio['APIC'] = APIC(mime='image/jpeg', desc='CoverImage', data=image_file.read()) # Cover Foto
    audio.add(TXXX(desc="AlbumId", text=[fields[6]], encoding=3)) # Album-ID
    audio['TPE1'] = TPE1(text=["DRK-OV-Norderstedt"], encoding=3) # Künstler
    audio['TALB'] = TALB(text=["Hörzeitung DRK-Norderstedt"], encoding=3) # Album
    audio['TCON'] = TCON(text=["Podcast"], encoding=3) # Genre
    audio.save()


def getMpegInfo(rawname:str):
    sec = audio_info.duration(rawname)
    if sec is None: dur = 0.00
    else: dur = sec
    duration = "{0:02.0f}:{1:02.0f}".format(floor(dur / 60), floor(dur % 60))
    size = os.stat(rawname).st_size
    return (size, duration)


def calcFileName(fname:str, path:str=None, guest:bool=False):
    if not path: path = "/long"
    if not guest and fname.startswith('B!'):
        path = "/bonus/"
        fname = fname[2:]
    else:
        if not guest:
            file_arr = fname.split('!')
            if len(file_arr) > 1:
                path = "/archive/" + file_arr[0]
                fname = file_arr[1]
        file_arr = fname.split(',')
        if len(file_arr) > 1:
            path += "/" + file_arr[0]
            fname = file_arr[1]
    return (path, fname)


def generateCode(prefix:str):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    chars_list = list(chars)
    code = ''
    for z in range(1, 5):
        code += "".join(random.sample(chars_list, 4))
        if z < 4: code += '-'
    return str(prefix) + code
