---

### Release: 1.1.10

Korrektur SEND MAIL an ADMIN. Bei Systemfehlern wurde keine Mail an den Admin gesendet.

### Release: 1.1.9

Korrektur Systemfehler bei der Medienausgabe.

### Release: 1.1.8

Ab 1.1.8 wird nun auch der Nextcloud-Teamordner "Historie" berücksichtigt. Hier werden unterhalb des jeweiligen Jahrgangs-Ordners
die einzelnen älteren Audio-Dateien abgelegt. Auch können hier die Einzelbeiträge genau so wie im Team-Ordner "Episoden" in einem Unterordner,
der genau so heißt, wie die Album-Datei (ohne .mp3), abgelegt werden.
In der Web-Anzeige gibt es den neuen Navigations-Punkt "Archiv". Hier wird zunächst der Jahrgang gewählt, dann erfolgt die zugehörige Album-Ansicht.
Auch können hier wieder über "Details" die Einzelbeiträge angezeigt und abgehört werden.
Voraussetzung für "Archiv" ist die Befüllung des Nextcloud-Teamordners "Historie" der jeweiligen Jahrgänge.

### Release: 1.1.7

Die Paginierung der Anzahl Zeilen in der Detail-Ansicht wurde entfernt. Die Zeilen in der Detail-Ansicht werden nun immer komplett angezeigt.   
Die Album-Ansicht kann weiterhin paginiert angezeigt werden.  
Der Grund: bisher galt die Paginierung gleichbedeutend für Album- und Detail-Ansicht, was nicht unbedingt immer gewünscht ist.  
Es wird davon ausgegangen, dass die Anzahl der jeweiligen Detail-Zeilenanzahl nicht mehr als eine Seite ausmacht.

### Release: 1.1.6

RSS-Feed: Die Ausgabe im Link der im MP3-Audio eingebetteten Images war unvollständig und ist jetzt vollständig implementiert.  
In einer MP3-Datei eingebette Grafiken, Bilder werden im RSS-Feed berücksichtigt und können von MP3-Playern angezeigt werden.  
Sind keine Grafiken, Bilder eingebettet, werden keine entsprechenden Links im RSS-Feed ausgegeben.