/* Main.js */
/*
Map.prototype.toJson = function toJson() {
  return JSON.stringify(Array.from(this.entries()));
}
*/

/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Define Global Values and Functions----------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
const bx_main_block = this.document.getElementById("main-block");
const bx_frm_regist = this.document.getElementById("frm-regist");
const bx_frm_release = this.document.getElementById("frm-release");
const bx_auth_code = this.document.getElementById("auth-code");
const bx_uploadfile = this.document.getElementById("uploadfile");


/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Set all Listener at LOAD-Event--------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
window.addEventListener('load', () => {
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  this.document.getElementById(SERVER_OPTIONS.link_active).classList.add("active");

  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  // for (const elem of frm_local_storage) {
  //   elem.addEventListener("change", setChangeEvent);
  // }
  if (bx_frm_regist) {
    bx_frm_regist.addEventListener("submit", bx_performRegist);
  }
  // if (bx_frm_release) {
  //   for (const elem of bx_frm_release) {
  //     if (elem.type == "button") {
  //       elem.addEventListener("click", bx_performRelease);
  //     }
  //   }
  // }

  if (SERVER_OPTIONS.scroll_To) {
    const elem = document.getElementById(SERVER_OPTIONS.scroll_To);
    if (elem) {
        elem.scrollIntoView({
            behavior: 'smooth'
        });
    }    
  }

  if (SERVER_OPTIONS.no_backgr) {
    const elem = document.getElementById("banner-bg1");
    if (elem) {
        elem_style = elem.style;
        elem_style.setProperty("background-image", "none");
        elem_style.setProperty("background-color", "#2d2d2d");
    }    
  }
  
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  /* -----MAIN Reset----------------------------------------------------------------------------------------------------------------------------------*/
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  // btn_main_reset.addEventListener("click", performRelease);
  
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  /* -----MAIN Submit---------------------------------------------------------------------------------------------------------------------------------*/
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  // btn_main_store.addEventListener("click", performSubmit);
  
  /* -------------------------------------------------------------------------------------------------------------------------------------------------*/
  // bx_fillMainBlock();
  // bx_env_init();
});


async function bx_env_init() {
  // removeDismissible();
  // showAlertsAfterInit();

}


/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Füllen des Haupt-Blocks---------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
// async function bx_fillMainBlock() {
//   const authcode = localStorage.getItem(bx_auth_code);
//   const submit_map = new SubmitParm([["auth_valid", false]]);
//   if (authcode) {
//     submit_map.add("auth_valid", true);
//   }
//   const result_data = await execFetch(HTTP.getURL("ax-get-main-block/"), submit_map.getString());
//   if (result_data.status == "OK") {
//     bx_main_block.innerHTML = result_data.html;
//   }
//   else {
//     // appendAlert(`Anzeigen der ${SERVER_OPTIONS.overview_label} konnte nicht erfolgreich beendet werden!`, 'danger');
//   }
// }

// console.log(target);

/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Absenden der Registrieung-------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
// async function bx_performRelease(event) {
//   if (bx_auth_code && bx_auth_code.value) {
//     const wcs = window.cookieStore;
//     // Set cookie: passing options
//     const day = 24 * 60 * 60 * 1000;
//     try {
//       await wcs.set({
//         name: BX_AUTH_CODE,
//         value: bx_auth_code.value,
//         expires: Date.now() + day,
//         partitioned: true
//       });
//       bx_localStorage.setItem(BX_AUTH_CODE, bx_auth_code.value);
//       window.location.reload();
//     } catch (error) {
//       console.log(`Error setting cookie ${BX_AUTH_CODE}: ${error}`);
//     }
//   }
// }


/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Absenden der Registrieung-------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
function bx_performRegist(event) {
  let errorText = "";
  let missing = false;
  let missing_radio = true;
  for (const elem of bx_frm_regist.elements) {
    if (["BUTTON", "FIELDSET"].includes(elem.nodeName) || elem.type == "hidden") continue;
    elem.classList.remove("is-invalid","is-valid");
    if ((elem.type == "checkbox" && !elem.checked) ||
    (elem.type == "text" && !elem.value) ||
    (elem.type == "email" && !elem.value)) {
      if (["text", "email"].includes(elem.type)) elem.classList.add("is-invalid");
      missing = true;
    }
    if (elem.type == "radio" && elem.checked) {
        missing_radio = false;
    }
  }
  if (missing || missing_radio) {
    errorText = "<div>Es fehlen noch erforderliche Eingaben. Bitte vervollständigen.</div>";
  }
  bx_uploadfile.classList.remove("is-invalid","is-valid");
  const fieldvalue = bx_uploadfile.value;
  if (fieldvalue) {
    const type = fieldvalue.split('.').pop().toLowerCase();
    if ( ! ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'pdf'].includes(type)) {
      errorText = errorText + "<div>Die Art der angegebenen Datei ist nicht zulässig. <br>Mögliche Arten: jpg, jpeg, png, gif, tiff, tif, pdf</div>";
    }
  }
  else {
    errorText = errorText + "<div>Es wurde keine Datei zum Hochladen ausgewählt. Bitte eine Datei auswählen.</div>";
  }
  if (errorText) {
    bx_uploadfile.classList.add("is-invalid");
    bx_uploadfile.nextElementSibling.innerHTML = errorText;
    event.returnValue = false;
  }
}
