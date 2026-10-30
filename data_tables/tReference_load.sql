TRUNCATE TABLE tReference;
LOAD DATA LOCAL INFILE '/tmp/Leseliste.csv'
INTO TABLE tReference
FIELDS TERMINATED BY '\t' 
LINES TERMINATED BY '\n'
IGNORE 2 ROWS
(cd,track,title,@sourceDate,author,source,reader,@allowed,supporter,@pubDate)
SET sourceDate = CONCAT(MID(@sourceDate,7,4), '-',MID(@sourceDate,4,2), '-',MID(@sourceDate,1,2)), 
    pubDate = CONCAT(MID(@pubDate,7,4), '-', MID(@pubDate,4,2), '-', MID(@pubDate,1,2)),
    allowed = IF(@allowed='Frei', 1, IF(@allowed='Vorhanden', 2, IF(@allowed='Eigene Formulierungen', 3, IF(@allowed='Genehmigung vorhanden', 4, 0)))),
    team = IF(supporter='Ditmar Rapp', 2, IF(supporter in ('Angela Fendner', 'Thomas Düßler'), 3, IF(supporter='Thomas Klueß' || supporter='Thomas Klüss', 1, IF(supporter='Peter Geukes', 4, 0))));
