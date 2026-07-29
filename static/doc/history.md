---

### Release: 1.1.7

Die Paginierung der Anzahl Zeilen in der Detail-Ansicht wurde entfernt. Die Zeilen in der Detail-Ansicht werden nun immer komplett angezeigt.   
Die Album-Ansicht kann weiterhin paginiert angezeigt werden.  
Der Grund: bisher galt die Paginierung gleichbedeutend für Album- und Detail-Ansicht, was nicht unbedingt immer gewünscht ist.  
Es wird davon ausgegangen, dass die Anzahl der jeweiligen Detail-Zeilenanzahl nicht mehr als eine Seite ausmacht.

### Release: 1.1.6

RSS-Feed: Die Ausgabe im Link der im MP3-Audio eingebetteten Images war unvollständig und ist jetzt vollständig implementiert.  
In einer MP3-Datei eingebette Grafiken, Bilder werden im RSS-Feed berücksichtigt und können von MP3-Playern angezeigt werden.  
Sind keine Grafiken, Bilder eingebettet, werden keine entsprechenden Links im RSS-Feed ausgegeben.