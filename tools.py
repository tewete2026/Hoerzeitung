import os, random
from math import floor
from flask import current_app
from mutagen.mp3 import MP3
from mutagen.id3 import CHAP, TIT2, TLEN, COMM, TXXX, ID3, TPE1, TDRC, TALB, TCON, APIC, TYER, CTOC, CTOCFlags
from sox import file_info as audio_info

''' mutagen.id3.Encoding.UTF8 has the value 3 so I presume that encoding=3 forces utf-8 encoding.
    # Encoding the string to UTF-16
    utf16_encoded = text.encode('utf-16')
'''

def getMP3Info(rawname:str):
    ts = current_app.config["TS"]
    # audio = MP3(current_app.instance_path + "/" + mp3, ID3=EasyID3)
    audio = MP3(rawname)
    chapter_dict = {}
    image_dict = {}
    description = "- - - -"
    title = "---"
    albumid = "---"
    tlen = None
    current_app.logger.debug(rawname)
    for key in audio.keys():
        cont = audio.get(key)
        current_app.logger.debug((key, type(cont)))
        if key == 'TIT2':
            title = cont.text[0]
            current_app.logger.debug("%s, %s", title, cont.encoding)
        elif key == 'TLEN':
            tlen = cont.text[0]
            current_app.logger.debug("%s, %s", tlen, cont.encoding)
        elif key[:5] == 'CTOC:':
            current_app.logger.debug("child_element_ids=%s, flags=%s, element_id=%s", cont.child_element_ids, cont.flags, cont.element_id)
            for elem in cont.child_element_ids:
                chap_key = 'CHAP:' + elem
                chap = audio.get(chap_key)
                chapter_dict.update({chap.element_id:(chap.sub_frames['TIT2'].text[0], chap.start_time, chap.end_time)})
        elif key[:5] == 'CHAP:':
            current_app.logger.debug("element_id=%s, start=%s, end=%s", cont.element_id, cont.start_time, cont.end_time)
            for sub in cont.sub_frames:
                tit2 = cont.sub_frames[sub]
                tit2_text = tit2.text[0]
                current_app.logger.debug("sub_frame=%s,%s,%s", tit2_text, tit2.encoding, type(tit2))
        elif key[:5] == 'TXXX:':
            if cont.desc == 'AlbumId':
                albumid = cont.text[0]
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
            current_app.logger.debug("%s, %s, %s, %s", description, cont.desc, cont.lang, cont.encoding)
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
    for key, (text, start, end) in chapter_dict.items():
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
    return (title, description, published, size, duration, chapter, chapter_dict, image_dict, albumid)


def setMp3Info(rawname:str, fields:tuple):
    audio = ID3(rawname)
    audio.add(TIT2(text=[fields[0]], encoding=3)) # Titel / Encoding 3 = UTF-8
    audio.add(COMM(desc="summary", lang='ger', text=[fields[1]], encoding=3)) # Beschreibung
    audio.add(TDRC(text=[fields[2]], encoding=3)) # Produktionsdatum
    audio.add(TXXX(desc="Supporter", text=[fields[3]], encoding=3)) # Techniker
    audio.add(TXXX(desc="Team", text=[fields[4]], encoding=3)) # Team
    playtime = int(audio_info.duration(rawname) * 1000)
    audio.add(TLEN(text=[str(playtime)], encoding=3)) # Spiellänge in Millisekunden
    with open(fields[5], mode='rb') as image_file:
       audio.add(APIC(mime='image/jpeg', desc='CoverImage', data=image_file.read())) # Cover Foto
    audio.add(TXXX(desc="AlbumId", text=[fields[6]], encoding=3)) # Album-ID
    audio.add(TPE1(text=["DRK-OV-Norderstedt"], encoding=3)) # Künstler
    audio.add(TALB(text=["Hörzeitung DRK-Norderstedt"], encoding=3)) # Album
    audio.add(TCON(text=["Podcast"], encoding=3)) # Genre
    audio.save()


def setMp3Chapter(rawname:str, basemedia:str, fields:tuple):
    baseaudio = ID3(basemedia)
    ctoc_key = 'CTOC:toc'
    base_ctoc = baseaudio.get(ctoc_key)
    if base_ctoc is None:
        next_toc = 'chp0'
        base_ctoc = CTOC(element_id='toc', flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED, child_element_ids=[next_toc])
        starttime = 0
        baseaudio['CTOC'] = base_ctoc
    else:
        element_ids = base_ctoc.child_element_ids
        last_chap = baseaudio.get('CHAP:' + element_ids[-1])
        starttime = last_chap.end_time
        size = len(element_ids)
        next_toc = 'chp' + str(size)
        element_ids.append(next_toc)
    audio = ID3(rawname)
    audio.add(TIT2(text=[fields[0]], encoding=3)) # Titel / Encoding 3 = UTF-8
    audio.add(COMM(desc="summary", lang='ger', text=[fields[1]], encoding=3)) # Beschreibung
    audio.add(TDRC(text=[fields[2]], encoding=3)) # Produktionsdatum
    audio.add(TXXX(desc="Author", text=[fields[3]], encoding=3)) # Autor
    audio.add(TXXX(desc="License", text=[fields[4]], encoding=3)) # Urheber
    audio.add(TXXX(desc="Reader", text=[fields[5]], encoding=3)) # Vorleser
    audio.add(TXXX(desc="LicenseAllowed", text=[fields[6]], encoding=3)) # Vorleser
    playtime = int(audio_info.duration(rawname) * 1000)
    audio.add(TLEN(text=[str(playtime)], encoding=3)) # Spiellänge in Millisekunden
    with open(fields[7], mode='rb') as image_file:
       audio.add(APIC(mime='image/jpeg', desc='CoverImage', data=image_file.read())) # Cover Foto
    audio.add(TXXX(desc="ChapterId", text=[fields[8]], encoding=3)) # Chapter-ID
    audio.add(TXXX(desc="AlbumId", text=[fields[9]], encoding=3)) # Album-ID
    audio.add(TXXX(desc="SourceDate", text=[fields[10]], encoding=3)) # Veröffentlichungsdatum der Quelle
    audio.add(TPE1(text=["DRK-OV-Norderstedt"], encoding=3)) # Künstler
    audio.add(TALB(text=["Hörzeitung DRK-Norderstedt"], encoding=3)) # Album
    audio.add(TCON(text=["Podcast"], encoding=3)) # Genre
    # Neues Kapitel ins Album schreiben:
    next_chap = CHAP(element_id=next_toc, start_time=starttime, end_time=starttime + playtime, sub_frames=[TIT2(text=[fields[0]], encoding=3)])
    baseaudio.add(next_chap)
    audio.save()
    baseaudio.save()


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
