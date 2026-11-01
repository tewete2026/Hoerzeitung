SELECT  j.title as Album_Titel,j.supporter as Techniker,FORMAT(j.team,0) as Team,j.media as Medium,j.duration as Spiellänge,DATE_FORMAT(j.publicationDate,'%d.%m.%Y %H:%i:%s') as Datum_Angelegt,
        c.title as Kapitel_Titel,FORMAT(c.track,0) as Kapitel_Nr,c.author as Autor,c.source as Quelle,DATE_FORMAT(c.sourceDate,'%d.%m.%Y') as Datum_Quelle,c.reader as Vorleser,c.summary As Kapitel_Beschreibung,c.media as Kapitel_Medium,c.duration as Kapitel_Spiellänge,DATE_FORMAT(c.publicationDate,'%d.%m.%Y %H:%i:%s') as Kapitel_Datum_Angelegt,FORMAT(c.allowed,0) as Kapitel_Lizenz 
        from tChapter c
        join tJournal j ON c.albumId=j.id
        order by c.albumId,c.track