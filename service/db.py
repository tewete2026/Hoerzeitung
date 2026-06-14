from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .. import version

class Javascript:
    def __init__(self, prefix:str, app:str, user:str):
        if user is None: user = "--"
        self.__js = {'PREFIX':prefix, 'APP':app, 'USER':user, 'form_submit':'no'}
        self.__outline = "const SERVER_OPTIONS = "
    def add(self, attr:dict):
        self.__js.update(attr)
    def getOut(self) -> str:
        for key, value in self.__js.items():
            if isinstance(value, list):
                self.__js[key] = str(value).replace("'", '"')
            elif not isinstance(value, str):
                self.__js[key] = str(value)
        return self.__outline + str(self.__js)
    
    @staticmethod
    def toOptions(rows:list[dict]) -> str:
        opts = ""
        for elem in rows:
            opts += "<option value=\"" + str(elem["id"]) + "\">" + elem["bezeichnung"] + "</option>"
        return opts
    

class Configure:
    def __init__(self, request, current_app, title:str, header:list, prefix:str, app:str, link:str, label:str, category:str, overview:str, 
                 pag_search:str, pag_type:str="text", btn_type:str="button"):
        self.credits = {
            "title":title,
            "header":header,
            "app":app,
            "user":request.remote_user,
            "addr":request.remote_addr,
            "created":version.Configs.APP_CREATED,
            "version":version.Configs.APP_VERSION,
            "author":version.Configs.APP_AUTHOR
        }
        ts = current_app.config["TS"]
        if self.credits["user"] is None: self.credits["user"] = "--"
        current_app.logger.info("%s started; Modname=%s; Remote-Addr=%s; Method=%s", title, current_app.name, request.remote_addr, request.method)
        self.today=date.today()
        self.todaytime=ts.todaytime()
        self.timeformat=self.todaytime.strftime("%Y-%m-%dT%H:%M:%S")
        self.pag_type = pag_type
        self.pag_search = pag_search
        self.btn_type = btn_type
        self.overview = overview
        self.min_date = self.today - relativedelta(months=12)
        self.max_date = self.today + relativedelta(months=12)
        self.map = {}
        self.javascript = Javascript(prefix, app, self.credits["user"])
        self.javascript.add({'modname':f"/{current_app.name}/", 'today':self.today, 'min_date':self.min_date, 'max_date':self.max_date, 'link_active':link, 'header':header})
        self.javascript.add({'overview_label':label, 'category':category})
    def append(self, key:str, value:str):
        self.map.update({key: value})
    def has(self, key:str) -> bool:
        valid = self.map.get(key) is not None
        return valid
