window.addEventListener('load', () => {
    
    const quantity = this.document.getElementById('quantity');
    const level = this.document.getElementById('level');
    const histid = this.document.getElementById('histid');
    const trashid = this.document.getElementById('trashid');
    const logininput = this.document.getElementById('logininput');
    const go_to_guest = this.document.getElementById('go-to-guest');
    const morepage = this.document.getElementById('morepage');
    const setpage = this.document.getElementById('setpage');
    const btn_submit = this.document.getElementById('btn-submit');
    const btn_download = this.document.getElementById('btn-download');
    const btn_trash_hist = this.document.getElementById('btn-submit-trash-hist');
    const btn_trash_run = this.document.getElementById('btn-submit-trash-run');
    const btn_arrow_repeat = this.document.getElementById('btn-arrow-repeat');
    const main_form = this.document.getElementById('main-form');
    const history_form = this.document.getElementById('history-form');
    const morepage_form = this.document.getElementById('morepage-form');
    const setpage_form = this.document.getElementById('setpage-form');
    const login_form = this.document.getElementById('login-form');

    const trash_hist_list = [];

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

    const histories = this.document.getElementsByClassName('list-history');
    for (const element of histories) {
        element.addEventListener('click', event => {
            let target = event.target;
            // Durchhangeln nach oben bis zum <a> Element
            while(target.nodeName != 'svg') {
                target = target.parentElement;
            }
            if (target.nodeName == 'svg') target.classList.replace('opacity-100', 'opacity-50');
            while(target.nodeName != 'A') {
                target = target.parentElement;
            }
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
            const id = target.getAttribute('data-id');
            if (main_form && histid && id) {
                histid.value = id;
                main_form.submit();
            }
        })
    }

    const favorites = this.document.getElementsByClassName('set-favorites');
    for (const element of favorites) {
        const audio = element.getAttribute('data-audio');
        const target = element.firstChild.firstChild; // Durchhangeln zum <use> Element
        const favs = SERVER_OPTIONS.drk_nhz_favorites.audios;
        if (favs.includes(audio)) {
            target.setAttribute('href', '#heart-fill');
        } else {
            target.setAttribute('href', '#heart');
        }
        element.addEventListener('click', event => {
            let allow_fav = false;
            if (SERVER_OPTIONS.drk_nhz_favorites.audios.length < SERVER_OPTIONS.max_favorites) {
                allow_fav = true;
            }
            let target = event.target;
            let is_set = false;
            if (target.nodeName == 'use') target = target.parentElement;  // zum <svg> Element
            if (target.nodeName == 'svg') {
                const anchor = target.parentElement;  // das <a> Element bereithalten
                for (const child of target.children) {
                    if (child.nodeName == 'use') {
                        const att = child.getAttribute('href');
                        if (att == '#heart' || att == '#heartbreak') {
                            if (allow_fav) {
                                child.setAttribute('href', '#heart-fill');
                                anchor.setAttribute('title', 'Favoriten wieder entfernen');
                                is_set = true;
                            } else {
                                child.setAttribute('href', '#heartbreak');
                                anchor.setAttribute('title', 'Die maximale Anzahl Favoriten ist überschritten');
                            }
                        }
                        else {
                            child.setAttribute('href', '#heart');
                            anchor.setAttribute('title', 'Als Favoriten auswählen');
                        }
                    }
                }
                target = anchor
            }
            if (is_set) {
                const audio = target.getAttribute('data-audio');
                SERVER_OPTIONS.drk_nhz_favorites.audios.push(audio);
            } else {
                const audio = target.getAttribute('data-audio');
                const i = SERVER_OPTIONS.drk_nhz_favorites.audios.indexOf(audio);
                if (i >= 0) {
                    SERVER_OPTIONS.drk_nhz_favorites.audios.splice(i, 1);
                }
            }
            const fav_string = JSON.stringify(SERVER_OPTIONS.drk_nhz_favorites);
            this.document.cookie = `drk-nhz-favorites=${fav_string};path=${SERVER_OPTIONS.modpath}`;

            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
        })
    }

    const morepages = this.document.getElementsByClassName('list-morepage');
    for (const element of morepages) {
        element.addEventListener('click', event => {
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
            const target = event.target;
            const id = target.getAttribute('data-morepage');
            if (morepage_form && morepage && id) {
                morepage.value = id;
                morepage_form.submit();
            }
        })
    }

    const setpages = this.document.getElementsByClassName('list-setpage');
    for (const element of setpages) {
        element.addEventListener('click', event => {
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
            const target = event.target;
            const id = target.getAttribute('data-setpage');
            if (setpage_form && setpage && id) {
                setpage.value = id;
                setpage_form.submit();
            }
        })
    }

    const trashes = this.document.getElementsByClassName('list-trash');
    for (const element of trashes) {
        element.addEventListener('click', event => {
            let target = event.target;
            // Durchhangeln nach oben bis zum <a> Element
            while(target.nodeName != 'svg') {
                target = target.parentElement;
            }
            if (target.nodeName == 'svg') {
                const elem_svg = target;
                while(target.nodeName != 'A') {
                    target = target.parentElement;
                }
                const id = target.getAttribute('data-id');
                for (const child of elem_svg.children) {
                    if (child.nodeName == 'use') {
                        const att = child.getAttribute('href');
                        if (btn_trash_hist && att == '#trash') {
                            child.setAttribute('href', '#check');
                            btn_trash_run.setAttribute('type', 'submit');
                            btn_trash_hist.removeAttribute('disabled');
                            history_form.classList.remove('d-none');
                            trash_hist_list.push(id);
                        }
                        else {
                            child.setAttribute('href', '#trash');
                            trash_hist_list.splice(trash_hist_list.indexOf(id), 1);
                            if (btn_trash_hist && trash_hist_list.length == 0) {
                                btn_trash_run.setAttribute('type', 'button');
                                btn_trash_hist.setAttribute('disabled', true);
                                history_form.classList.add('d-none');
                            }
                        }
                    }
                }
            }
            if (trash_hist_list.length > 0) {
                trashid.value = trash_hist_list.join(",");
            } else {
                trashid.value = "";
            }
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
        })
    }
    
    if (quantity) quantity.value = SERVER_OPTIONS.quantity;
    if (level) level.value = SERVER_OPTIONS.level;
    
    if (btn_submit) {
        btn_submit.addEventListener('click', event => {
            histid.remove();
        })
    }
    
    if (go_to_guest) {
        go_to_guest.addEventListener('click', event => {
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
            logininput.value = SERVER_OPTIONS.guestcode;
            login_form.submit();
        })
    }
    
    if (btn_arrow_repeat) {
        btn_arrow_repeat.addEventListener('click', event => {
            event.preventDefault(); // Verhindern, dass der Anker-Link ausgeführt wird, weil das hier nicht erwünscht ist.
            window.location.replace(window.location.href);
        })
    }

});

