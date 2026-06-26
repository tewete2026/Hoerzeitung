window.addEventListener('load', () => {

    const elements = this.document.getElementsByClassName('list-table-rows');
    for (const element of elements) {
        element.addEventListener('click', event => {
            let target = event.target;
            // Durchhangeln nach oben bis zum <tr> Element
            while(target.nodeName != 'TR') {
                target = target.parentElement;
            }
            // Das anschließende <tr> Element umschalten auf sichtbar/nicht sichtbar, weil es die Beschreibung enthält.
            target.nextElementSibling.classList.toggle('d-none');
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
        })
    }

    const chapters = this.document.getElementsByClassName('list-table-rows-chapter');
    for (const element of chapters) {
        element.addEventListener('click', event => {
            let target = event.target;
            // Durchhangeln nach oben bis zum <tr> Element
            while(target.nodeName != 'TR') {
                target = target.parentElement;
            }
            // Das anschließende 2.<tr> Element umschalten auf sichtbar/nicht sichtbar, weil es die Kapitel enthält.
            target.nextElementSibling.nextElementSibling.classList.toggle('d-none');
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
        })
    }
});

