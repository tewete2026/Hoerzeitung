# Analyse des bestehenden Bestands der Audio-Dateien

Als Basis dienen alle Audio-Dateien im Ordner `Episoden` mit Verknüpfung der Excel-Datei `Leseliste.xlsx`.   
Aus den Audio-Dateien werden die Tag-Metadaten des ID3-Formats ausgelesen. Voraussetzung ist hier, dass entsprechende Meta-Daten im Audio-Format abgelegt wurden. Wichtigster Tag-Eintrag ist der Titel.

Verknüpfungspunkte sind der Albumname (entspricht der CD-Version) zusammen mit der Nummer des jeweiligen Kapitels. Diese Nummer wird durch eine laufende Nummer beginnend bei 1 innerhalb eines Albums erzeugt.   
Zur Herstellung einer gültigen Verknüpfung wird die laufende Nummer mit der Spalte `TitelNr`. und der Albumname mit der Spalte `CD` in der Excel-Liste verknüpft. 

Wird **keine** erfolgreiche Verknüpfung erreicht, werden die Werte mit "---" dargestellt und **fett** hervorgehoben. In der Regel trifft dieses auf die Kapitel "Begrüßung" und "Verabschiedung" zu.

In den Tag-Metadaten kann ebenfalls eine Folge-Nr. (Track) angelegt werden. Diese Nummer wird nur dokumentarisch abgebildet. Im folgenden Ausdruck wird die laufende Nummer mit der Track-Nr. verglichen, die Angaben sind bei Abweichungen **fett** hervorgehoben.

Die Titel-Einträge sowohl in den ID3-Einträgen als auch in der Excel-Liste werden verglichen und im folgenden Ausdruck bei Abweichung **fett** dargestellt.

Die Kapitel entsprechen den Detaileinträgen zum jeweiligen Album. Um Kapitel zu organisieren und einem Album zuzuordnen wird im Dateiverzeichnis ein Unterverzeichnis angelegt mit demselben Namen des Albums (Dateiname ohne Endung .mp3). Sind für ein Album keine Kapitel (gleichnamiges - zum Album-Titel - passendes Verzeichnis) angelegt, wird eine Zeile nur mit "---" Werten angezeigt.

Per Tag-Eintrag können dem Album Kapitel (Chapter) Einträge zugeordnet werden. Diese sollten exakt den Kapiteleinträgen im Verzeichnis entsprechen. Die Chapter-Einträge in den Album-Dateien werden hier nicht berücksichtigt.

### Legende:

Referenz = bezieht sich auf die Excel-Liste  
Dat.-Titel = Titel aus den Meta-ID3-Daten  
Ref.-Titel = Titel aus der Excel-Liste  
Step = laufende Nummer (arithmetische Folge)  
Track = Folgenr. aus den Meta-ID3-Daten  
Quelle = Ursprung des Artikels  
Quelle-Datum = Veröffentlichungsdatum der Quelle  
Lizenz = ist eine erlaubte Verwendung vorhanden = 1, andernfalls 0  
Team = die Nummer 1 bis 4 (unbekannt=0). Ist nicht Bestandteil der Excel-Liste, sondern wird abhängig vom Techniker gebildet.