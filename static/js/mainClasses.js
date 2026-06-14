/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Define important Classes--------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
class HttpUrl {
  url="";
  prefix="";
  sep="?";
  delim="";
  constructor(prefix="", url="") {
    this.prefix = prefix;
    this.url = url;
  }
  addParm(key, value) {
    this.url += this.sep + this.delim + key + "=" + value;
    if (this.sep) this.sep = "";
    if (!this.delim) this.delim = "&";
  }
  getURL(uri="") {
    return this.prefix + this.url + uri;
  }
}


class SessionStorage {
  inner_map = new Map();
  has_storage = true;
  write_storage = true;
  prefix_str = "";
  
  constructor(prefix_str="", has_storage=true) {
    this.has_storage = has_storage;
    this.prefix_str = prefix_str;
  }
  getItem(key, default_value="") {
    if (this.has_storage) {
      const storedKey = this.prefix_str + key;
      const value = window.sessionStorage.getItem(storedKey);
      if (value) {
        if (["true", "false"].includes(value)) {
          if (value == "true") return true;
             else return false;
        }
        return value;
      } else {
        if (default_value) {
          return default_value;
        }
        else {
          return value;
        }
      }
    } else {
      return this.inner_map.get(key);
    }
  }
  setItem(key, value) {
    if (this.has_storage && this.write_storage) {
      try {
        const storedKey = this.prefix_str + key;
        window.sessionStorage.setItem(storedKey, value);
      } catch (e) {
        appendError("Fehler bei sessionStorage.setItem: " + e);
        this.inner_map.set(key, value);
        this.write_storage = false;
      }
    } else {
      this.inner_map.set(key, value);
    }
  }
  removeItem(key) {
    if (this.has_storage && this.write_storage) {
      try {
        const storedKey = this.prefix_str + key;
        window.sessionStorage.removeItem(storedKey);
      } catch (e) {
        appendError("Fehler bei sessionStorage.setItem: " + e);
        this.inner_map.delete(key);
        this.write_storage = false;
      }
    } else {
      this.inner_map.delete(key);
    }
  }
  keys(prefix=true) {
    let rt_keys = [];
    if (this.has_storage && this.write_storage) {
      try {
        for (let i = 0; i < window.sessionStorage.length; i++) {
          const key = window.sessionStorage.key(i);
          if (prefix && !key.startsWith(this.prefix_str)) {
            continue;
          }
          else {
            if (prefix && key.startsWith(this.prefix_str)) {
              rt_keys.push(key.replace(this.prefix_str, ''));
            } else {
              rt_keys.push(key);
            }
          }
        }
      } catch (e) {
        appendError("Fehler bei sessionStorage.keys: " + e);
        rt_keys = this.inner_map.keys();
      }
    } else {
      rt_keys = this.inner_map.keys();
    }
    return rt_keys;
  }
  clear(exclude=[]) {
    if (this.has_storage) {
      const storedKeys = this.keys();
      for (const key of storedKeys) {
        if (exclude.length == 0 || !exclude.includes(key)) {
          window.sessionStorage.removeItem(this.prefix_str + key);
        }
      }
    } else {
      this.inner_map.clear();
    }
  }
}

/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Define Global Values and Functions----------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
const SESS_STORAGE_AVAILABLE = storageAvailable("sessionStorage");
const LOC_STORAGE_AVAILABLE = storageAvailable("localStorage");
const bx_localStorage = window["localStorage"];
const HTTP = new HttpUrl();
const BX_AUTH_CODE = "bx-authcode";
const main_errors_flashed = this.document.getElementById("main-errors-flashed");

// const extStorage = new SessionStorage(SERVER_OPTIONS.PREFIX + "_", SESS_STORAGE_AVAILABLE);


/* -------------------------------------------------------------------------------------------------------------------------------------------------*/
/* -----Define Classes------------------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------------------------------------------------------------------------------------------------------------------*/


class SubmitParm {
  submit_map;
  constructor(initparms=[]) {
    this.submit_map = new Map(initparms);
  }
  add(key, value) {
    this.submit_map.set(key, value);
  }
  add_if(key, elem, compare) {
    if (compare == elem.name) {
      if (elem.type == 'checkbox') {
        this.submit_map.set(key, elem.checked);
      }
      else this.submit_map.set(key, elem.value);
      return true;
    } else return false;
  }
  getString() {
    return JSON.stringify(arrayifyMap(this.submit_map));
  }
}
