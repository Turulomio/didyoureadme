import os,  datetime,  configparser,  hashlib,   psycopg2,  psycopg2.extras,  pytz,  smtplib,  urllib.parse, threading,  time
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

version="20150128"
version_date=datetime.date(int(version[0:4]),int(version[5:6]), int(version[7:8]))


dirTmp=os.path.expanduser("/tmp/didyoureadme/")
dirDocs=os.path.expanduser("~/.didyoureadme/docs/")
dirReaded=os.path.expanduser("~/.didyoureadme/readed/")

class Connection(QObject):
    """Futuro conection object
    COPIADA DE XULPYMONEY NO EDITAR"""
    inactivity_timeout=pyqtSignal()
    def __init__(self):
        QObject.__init__(self)
        
        self.user=None
        self.password=None
        self.server=None
        self.port=None
        self.db=None
        self._con=None
        self._active=False
        
        self.restart_timeout()
        self.inactivity_timeout_minutes=30
        self.init=None
        
    def init__create(self, user, password, server, port, db):
        self.user=user
        self.password=password
        self.server=server
        self.port=port
        self.db=db
        return self
        
    def _check_inactivity(self):
        if datetime.datetime.now()-self._lastuse>datetime.timedelta(minutes=self.inactivity_timeout_minutes):
            self.disconnect()
            self._timerlastuse.stop()
            self.inactivity_timeout.emit()
        print ("Remaining time {}".format(self._lastuse+datetime.timedelta(minutes=self.inactivity_timeout_minutes)-datetime.datetime.now()))

    def cursor(self):
        self.restart_timeout()#Datetime who saves the las use of connection
        return self._con.cursor()
        
    def restart_timeout(self):
        """Resets timeout, usefull in long process without database connections"""
        self._lastuse=datetime.datetime.now()
        
    
    def mogrify(self, sql, arr):
        """Mogrify text"""
        cur=self._con.cursor()
        s=cur.mogrify(sql, arr)
        cur.close()
        return  s
        
    def cursor_one_row(self, sql, arr=[]):
        """Returns only one row"""
        self.restart_timeout()
        cur=self._con.cursor()
        cur.execute(sql, arr)
        row=cur.fetchone()
        cur.close()
        return row        
        
    def cursor_one_column(self, sql, arr=[]):
        """Returns un array with the results of the column"""
        self.restart_timeout()
        cur=self._con.cursor()
        cur.execute(sql, arr)
        for row in cur:
            arr.append(row[0])
        cur.close()
        return arr
        
    def commit(self):
        self._con.commit()
        
    def rollback(self):
        self._con.rollback()
        
        
    def connection_string(self):
        return "dbname='{}' port='{}' user='{}' host='{}' password='{}'".format(self.db, self.port, self.user, self.server, self.password)
        
    def connect(self, connection_string=None):
        """Used in code to connect using last self.strcon"""
        if connection_string==None:
            s=self.connection_string()
        else:
            s=connection_string        
        try:
            self._con=psycopg2.extras.DictConnection(s)
        except psycopg2.Error as e:
            print (e.pgcode, e.pgerror)
            return
        self._active=True
        self.init=datetime.datetime.now()
        self.restart_timeout()
        self._timerlastuse = QTimer()
        self._timerlastuse.timeout.connect(self._check_inactivity)
        self._timerlastuse.start(300000)
        
    def disconnect(self):
        self._active=False
        if self._timerlastuse.isActive()==True:
            self._timerlastuse.stop()
        self._con.close()
        
    def is_active(self):
        return self._active
        
        
    def is_superuser(self):
        """Checks if the user has superuser role"""
        res=False
        cur=self.cursor()
        cur.execute("SELECT rolsuper FROM pg_roles where rolname=%s;", (self.user, ))
        if cur.rowcount==1:
            if cur.fetchone()[0]==True:
                res=True
        cur.close()
        return res

class Backup:
    def __init__(self):
        pass
    def save(self):
        pass
            
        
class SetCommons:
    """Base clase to create Sets, it needs id and name attributes, as index. It has a list arr and a dics dic_arr to access objects of the set"""
    def __init__(self):
        self.dic_arr={}
        self.arr=[]
        self.id=None
        self.name=None
        self.selected=None#Used to select a item in the set. Usefull in tables. Its a item
    
    def arr_position(self, id):
        """Returns arr position of the id, useful to select items with unittests"""
        for i, a in enumerate(self.arr):
            if a.id==id:
                return i
        return None
            

    def append(self,  obj):
        self.arr.append(obj)
        self.dic_arr[str(obj.id)]=obj
        
    def remove(self, obj):
        self.arr.remove(obj)
        del self.dic_arr[str(obj.id)]
        
    def length(self):
        return len(self.arr)
        
    def find(self, id,  log=False):
        """Finds by id"""
        try:
            return self.dic_arr[str(id)]    
        except:
            if log:
                print ("SetCommons ({}) fails finding {}".format(self.__class__.__name__, id))
            return None

    def find_by_id(self, id,  log=False):
        """Finds by id"""
        try:
            return self.dic_arr[str(id)]    
        except:
            if log:
                print ("SetCommons ({}) fails finding {}".format(self.__class__.__name__, id))
            return None
            
    def find_by_arr(self, id,  log=False):
        """log permite localizar errores en find. Ojo hay veces que hay find fallidos buscados como en UNION
                inicio=datetime.datetime.now()
        self.mem.data.products_all().find(80230)
        print (datetime.datetime.now()-inicio)
        self.mem.agrupations.find_by_arr(80230)
        print (datetime.datetime.now()-inicio)
        Always fister find_by_dict
        0:00:00.000473
        0:00:00.000530

        """
        for a in self.arr:
            if a.id==id:
                return a
        if log:
            print ("SetCommons ({}) fails finding  by arr {}".format(self.__class__.__name__, id))
        return None
                
    def order_by_id(self):
        """Orders the Set using self.arr"""
        try:
            self.arr=sorted(self.arr, key=lambda c: c.id,  reverse=False)     
            return True
        except:
            return False
        
    def order_by_name(self):
        """Orders the Set using self.arr"""
        try:
            self.arr=sorted(self.arr, key=lambda c: c.name,  reverse=False)       
            return True
        except:
            return False

    def qcombobox(self, combo,  selected=None):
        """Load set items in a comobo using id and name
        Selected is and object
        It sorts by name the arr""" 
        self.order_by_name()
        combo.clear()
        for a in self.arr:
            combo.addItem(a.name, a.id)

        if selected!=None:
            combo.setCurrentIndex(combo.findData(selected.id))
                
    def clean(self):
        """Deletes all items"""
        self.arr=[]
        self.dic_arr={}
#        for a in self.arr:
#            self.remove(a)
                
    def clone(self,  *initparams):
        """Returns other Set object, with items referenced, ojo con las formas de las instancias
        initparams son los parametros de iniciación de la clase"""
        result=self.__class__(*initparams)#Para que coja la clase del objeto que lo invoca
        for a in self.arr:
            result.append(a)
        return result
        
    def union(self,  set,  *initparams):
        """Returns a new set, with the union comparing id
        initparams son los parametros de iniciación de la clse"""        
        resultado=self.__class__(*initparams)#Para que coja la clase del objeto que lo invoca SetProduct(self.mem), luego será self.mem
        for p in self.arr:
            resultado.append(p)
        for p in set.arr:
            if resultado.find(p.id, False)==None:
                resultado.append(p)
        return resultado
        
class SetCommonsQListView(SetCommons):
    def __init__(self):
        SetCommons.__init__(self)
        
    def qlistview(self, list, selected):
        """Shows a list with the items of arr,
        selected lista de group a seleccionar"""
        self.order_by_name()
        model=QStandardItemModel (len(self.arr), 1); # 3 rows, 1 col
        for i,  g in enumerate(self.arr):
            item = QStandardItem(g.name)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled);
            if g in selected.arr:
                item.setData(Qt.Checked, Qt.CheckStateRole)
            else:
                item.setData(Qt.Unchecked, Qt.CheckStateRole); #para el role check
            item.setData(g.id, Qt.UserRole) # Para el role usuario
            model.setItem(i, 0, item);
        list.setModel(model)
        
    def qlistview_getselected(self, list, *initparams):
        """Returns a new set, with the selected in the list
        initparams son los parametros de iniciación de la clse"""        
        resultado=self.__class__(*initparams)#Para que coja la clase del objeto que lo invoca SetProduct(self.mem), luego será self.mem   
        for i in range(list.model().rowCount()):
            if list.model().index(i, 0).data(Qt.CheckStateRole)==Qt.Checked:
                id=list.model().index(i, 0).data(Qt.UserRole)
                resultado.append(self.find(id))   
        return resultado
        

class SetGroups(SetCommonsQListView):
    def __init__(self, mem):
        SetCommonsQListView.__init__(self)
        self.mem=mem
        
    def quit_user_from_all_groups(self, user):
        """Se quita un usuario de todos los grupos tanto lógicamente como físicamente"""
        
        todelete=None#Se usa para no borrar en iteracion
        for g in self.arr:
            for u in g.members.arr:
                if u.id==user.id:
                    todelete=u
            if todelete!=None:
                g.members.remove(user)
                g.save()# Para no grabar en bd salvoi que encuente se pone aquí
                todelete=None
                    
           
    def qtablewidget(self, table):
        """Section es donde guardar en el config file, coincide con el nombre del formulario en el que está la table
        Devuelve sumatorios"""
        table.setColumnCount(2)
        table.setHorizontalHeaderItem(0, QTableWidgetItem(QApplication.translate("Core", "Name" )))
        table.setHorizontalHeaderItem(1, QTableWidgetItem(QApplication.translate("Core", "Users" )))    
        table.clearContents()
        table.setRowCount(len(self.arr))
        for i, p in enumerate(self.arr):
            table.setItem(i, 0, QTableWidgetItem(p.name))
            table.setItem(i, 1, QTableWidgetItem(p.members.string_of_names()))
        table.clearSelection()    

    def load(self, sql):
        cur=self.mem.con.cursor()
        cur.execute(sql)
        for row in cur:
            members=SetUsers(self.mem)
            if row['id']==1:#Caso de todos
                for u in self.mem.data.users_active.arr:
                    members.append(u)
            else:
                for id_user in row['members']:
                    u=self.mem.data.users_all().find(id_user)
                    if u.active==True:
                        members.append(u)
            self.append( Group(self.mem, row['name'], members, row['id']))        
        cur.close()


        
#    def qlistview(self, list, selected):
#        """selected lista de group a seleccionar"""
#        self.order_by_name()
#        model=QStandardItemModel (len(self.arr), 1); # 3 rows, 1 col
#        for i,  g in enumerate(self.arr):
#            item = QStandardItem(g.name)
#            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled);
#            if g in selected:
#                item.setData(Qt.Checked, Qt.CheckStateRole)
#            else:
#                item.setData(Qt.Unchecked, Qt.CheckStateRole); #para el role check
#            item.setData(g.id, Qt.UserRole) # Para el role usuario
#            model.setItem(i, 0, item);
#        list.setModel(model)
        
        
class Group:
    def __init__(self, mem,   name, members,  id=None):
        """members es un SetUsers"""
        self.members=members
        self.name=name
        self.id=id
        self.mem=mem
        
    def delete(self):
        #Borra de la base de datos
        cur=self.mem.con.cursor()
        cur.execute("delete from groups where id=%s", (self.id, ))
        cur.close()
        
    def save(self):
        def members2pg():
            if self.members.length()==0:
                return "'{}'"
            resultado=""
            for m in self.members.arr:
                resultado=resultado + str(m.id)+", "
            return "ARRAY["+resultado[:-2]+"]"
            
        cur=self.mem.con.cursor()
        if self.id==None:
            #Crea registro en base de datos
            cur.execute("insert into groups (name,members) values(%s, "+members2pg() +") returning id", (self.name, ))
            self.id=cur.fetchone()[0]
        else:
            #Modifica registro en base de datos
            cur.execute("update groups set name=%s, members="+members2pg()+" where id=%s",(self.name, self.id ))
        cur.close()
            

class SetLanguages(SetCommons):
    def __init__(self, mem):
        SetCommons.__init__(self)
        self.mem=mem
        
    def load_all(self):
        self.append(Language(self.mem, "en","English" ))
        self.append(Language(self.mem, "es","Español" ))
        self.append(Language(self.mem, "fr","Français" ))
        self.append(Language(self.mem, "ro","Rom\xe2n" ))
        self.append(Language(self.mem, "ru",'\u0420\u0443\u0441\u0441\u043a\u0438\u0439' ))

    def qcombobox(self, combo, selected=None):
        """Selected is the object"""
        self.order_by_name()
        for l in self.arr:
            combo.addItem(self.mem.countries.find_by_id(l.id).qicon(), l.name, l.id)
        if selected!=None:
                combo.setCurrentIndex(combo.findData(selected.id))

    def cambiar(self, id):  
        """language es un string"""
        self.mem.qtranslator.load("/usr/lib/xulpymoney/xulpymoney_" + id + ".qm")
        qApp.installTranslator(self.mem.qtranslator);
#        def cargarQTranslator(cfgfile):  
#    """language es un string"""
#    so=os.environ['didyoureadmeso']
#    if so=="src.linux":
#        cfgfile.qtranslator.load("/usr/share/didyoureadme/didyoureadme_" + cfgfile.language + ".qm")
#    elif so=="src.windows":
#        cfgfile.qtranslator.load("../share/didyoureadme/didyoureadme_" + cfgfile.language + ".qm")
#    elif so=="bin.windows" or so=="bin.linux":
#        cfgfile.qtranslator.load("didyoureadme_" + cfgfile.language + ".qm")
#    qApp.installTranslator(cfgfile.qtranslator);
        
class SetUsers(SetCommonsQListView):
    def __init__(self, mem):
        SetCommonsQListView.__init__(self)
        self.mem=mem
    

    def user_from_hash(self, hash):
        for u in self.arr:
            if u.hash==hash:
                return u
        print ("User not found")
        return None
        
    def load(self, sql):
        cur=self.mem.con.cursor()
        cur.execute(sql)
        for row in cur:
            self.append(User(self.mem, row['datetime'],  row['post'], row['name'], row['mail'], row['active'], row['hash'],  row['id']))
        cur.close()
            
            
    def string_of_names(self):
        "String of names sorted"
        self.order_by_name()
        users=""
        for u in self.arr:
            users=users+u.name+"\n"
        return users[:-1]
        

    
#    def qlistview(self, list, inactivos, selected):
#        """inactivos si muestra inactivos
#        selected lista de user a seleccionar"""
#        self.order_by_name()
#        model=QStandardItemModel (len(self.arr), 1); # 3 rows, 1 col
#        for i,  u in enumerate(self.arr):
#            if inactivos==False and u.active==False:
#                continue
#            item = QStandardItem(u.name)
#            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled);
#            if u in selected.arr:
#                item.setData(Qt.Checked, Qt.CheckStateRole)
#            else:
#                item.setData(Qt.Unchecked, Qt.CheckStateRole); #para el role check
#            item.setData(u.id, Qt.UserRole) # Para el role usuario
#            model.setItem(i, 0, item);
#        list.setModel(model)
           
    def qtablewidget(self, table):
        """Section es donde guardar en el config file, coincide con el nombre del formulario en el que está la table
        Devuelve sumatorios"""
        table.setColumnCount(6)
        table.setHorizontalHeaderItem(0, QTableWidgetItem(QApplication.translate("Core", "Start date" )))
        table.setHorizontalHeaderItem(1, QTableWidgetItem(QApplication.translate("Core", "Post" )))    
        table.setHorizontalHeaderItem(2, QTableWidgetItem(QApplication.translate("Core", "Full name" )))    
        table.setHorizontalHeaderItem(3, QTableWidgetItem(QApplication.translate("Core", "Mail" )))    
        table.setHorizontalHeaderItem(4, QTableWidgetItem(QApplication.translate("Core", "Read" )))    
        table.setHorizontalHeaderItem(5, QTableWidgetItem(QApplication.translate("Core", "Sent" )))    
        table.clearContents()
        table.setRowCount(len(self.arr))
        for i, u in enumerate(self.arr):
            table.setItem(i, 0, qdatetime(u.datetime, self.mem.cfgfile.localzone))
            if u.post==None:
                post=""
            else:
                post=u.post
            table.setItem(i, 1, QTableWidgetItem(post))
            table.setItem(i, 2, QTableWidgetItem(u.name))
            table.setItem(i, 3, QTableWidgetItem(u.mail))
            table.setItem(i, 4, QTableWidgetItem(str(u.read)))
            table.item(i, 4).setTextAlignment(Qt.AlignHCenter)
            table.setItem(i, 5, QTableWidgetItem(str(u.sent)))
            table.item(i, 5).setTextAlignment(Qt.AlignHCenter)
        table.clearSelection()    
        
#        for i, u in enumerate(self.mem.users.arr):
#            if (inactive==True and u.active==True) or (inactive==False and u.active==False):
#                continue
#            self.users.append(u)
        

    def updateTablesOnlyNums(self, table):
        for i, u in enumerate(self.arr):
            table.setItem(i, 4, QTableWidgetItem(str(u.read)))
            table.item(i, 4).setTextAlignment(Qt.AlignHCenter)
            table.setItem(i, 5, QTableWidgetItem(str(u.sent)))
            table.item(i, 5).setTextAlignment(Qt.AlignHCenter)
class User:
    def __init__(self, mem,  dt, post, name, mail, active=True, hash="hash no calculado",  id=None):
        self.mem=mem
        self.id=id
        self.name=name
        self.datetime=dt#incorporation date
        self.mail=mail
        self.hash=hash
        self.post=post
        self.sent=0
        self.read=0
        self.active=active

    def __repr__(self):
        return "{0} ({1})".format(self.name, self.id)
                
                
    def isDeletable(self):
        for g in self.mem.data.groups.arr:
            if g.members.find(self.id)!=None and g.id!=1:
                return False
        
        cur=self.mem.con.cursor()
        cur.execute("select count(*) from userdocuments where id_users=%s", (self.id, ))
        num=cur.fetchone()[0]
        cur.close()
        if num>0:
            return False
        return True
        
    def delete(self):
        cur=self.mem.con.cursor()
        cur.execute("delete from users where id=%s", (self.id, ))
        cur.close()
        
    def calculateHash(self):
        if self.id==None:
            return None
        return hashlib.sha256(("u."+str(self.id)+str(self.datetime)).encode('utf-8')).hexdigest()
    
    def save(self):
        cur=self.mem.con.cursor()        
        if self.id==None:
            cur.execute("insert into users (datetime,post,name,mail, hash, active) values(%s,%s,%s,%s,%s, %s) returning id ", (self.datetime, self.post, self.name, self.mail, self.hash, self.active))
            self.id=cur.fetchone()[0]
            self.hash=self.calculateHash()
            self.sent=0
            self.read=0
            cur.execute("update users set hash=%s where id=%s", (self.hash, self.id))
        else:
            cur.execute("update users set datetime=%s, post=%s, name=%s, mail=%s, active=%s where id=%s", (self.datetime, self.post, self.name, self.mail,  self.active, self.id))
        cur.close()

    def updateSent(self):
        cur=self.mem.con.cursor()
        cur.execute("select count(*) from userdocuments where id_users=%s", (self.id, ))
        self.sent= cur.fetchone()[0]
        cur.close()


    def updateRead(self):
        cur=self.mem.con.cursor()
        cur.execute("select count(*) from userdocuments where id_users=%s and read is not null", (self.id, ))
        self.read=cur.fetchone()[0]
        cur.close()


class TUpdateData(threading.Thread):
    def __init__(self, mem):
        threading.Thread.__init__(self)
        self.mem=mem
        self.errorupdating=0
    
    def run(self):    
        con=self.mem.connect()
        cur=con.cursor()
        #Actualiza userdocuments
        for file in os.listdir(dirReaded):
            try:
                (userhash, documenthash)=file.split("l")
                d=Document(self.mem).init__from_hash(documenthash)
                ud=UserDocument(self.mem.data.users_all().user_from_hash(userhash), d, self.mem)
                ud.readed( self.mem.cfgfile.localzone)
                con.commit()
            except:
                self.errorupdating=self.errorupdating+1
                f=open(self.mem.pathlogupdate, "a")
                f.write(QApplication.translate("didyoureadme","{0} Error updating data with hash: {1}\n").format(now(self.mem.cfgfile.localzone), file))
                f.close()
            finally:
                os.remove(dirReaded+file)
            
        #Actualiza users
        for u in self.mem.data.users_active.arr:
            u.updateSent()
            u.updateRead()
            
        #Consulta
        for i, d in enumerate(self.mem.data.documents_active.arr):
            if d.isExpired()==False:
                d.updateNums()            
        cur.close()  
        self.mem.disconnect(con)

class TSend(threading.Thread):
    def __init__(self, mem):
        threading.Thread.__init__(self)
        self.mem=mem
        self.errorsending=0

    
    def run(self):    
        con=self.mem.connect()#NO SE PORQUE NO ACTUALIZABA SI USABA CONEXIóN DE PARAMETRO
        cur=con.cursor()
        #5 minutos delay
        cur.execute("select id_documents, id_users from userdocuments, documents where userdocuments.id_documents=documents.id and sent is null and now() > datetime + interval '1 minute';")
        for row in cur:
            doc=self.mem.data.documents_active.find(row['id_documents'])
            u=self.mem.data.users_active.find(row['id_users'])
            mail=Mail(doc, u, self.mem)
            mail.send()
            
            if mail.sent==True:
                print ("Send message of document {0} to {1}".format(mail.document.id, mail.user.mail))
                d=UserDocument(mail.user, mail.document, self.mem)
                if d.sent==None:
                    d.sent=datetime.datetime.now(pytz.timezone(self.mem.cfgfile.localzone))
                d.save()
                con.commit()
            else:
                self.errorsending=self.errorsending+1  
                try: #Unicode en mail
                    f=open(self.mem.pathlogmail, "a")
                    f.write(QApplication.translate("didyoureadme","{0} Error sending message {1} to {2}\n").format(now(self.mem.cfgfile.localzone), mail.document.id, mail.user.mail))
                    f.close()          
                except:
                    print ("TSend error al escribir log")
            mail.document.updateNums()
            time.sleep(5)                  
        cur.close()
        self.mem.disconnect(con)
        
            
class Language:
    def __init__(self, mem, id, name):
        self.id=id
        self.name=name
    

class Mail:
    def __init__(self, document, user,  mem):
        self.mem=mem
        self.user=user
        self.document=document
        self.sender=""
        self.receiver=user.mail
        self.name=document.name
        self.sent=None


    def message(self):
        def weekday(noww):
            """Se hace esta función para que no haya problemas con la localización de %a"""
            if noww.isoweekday()==1:
                return "Mon"
            if noww.isoweekday()==2:
                return "Tue"
            if noww.isoweekday()==3:
                return "Wed"
            if noww.isoweekday()==4:
                return "Thu"
            if noww.isoweekday()==5:
                return "Fri"
            if noww.isoweekday()==6:
                return "Sat"
            if noww.isoweekday()==7:
                return "Sun"
                
        def month(noww):
            """Se hace esta función para que no haya problemas con la localización de %b"""
            if noww.month==1:
                return "Jan"
            elif noww.month==2:
                return "Feb"
            elif noww.month==3:
                return "Mar"
            elif noww.month==4:
                return "Apr"
            elif noww.month==5:
                return "May"
            elif noww.month==6:
                return "Jun"
            elif noww.month==7:
                return "Jul"
            elif noww.month==8:
                return "Aug"
            elif noww.month==9:
                return "Sep"
            elif noww.month==10:
                return "Oct"
            elif noww.month==11:
                return "Nov"
            elif noww.month==12:
                return "Dec"
            
        url="http://{0}:{1}/get/{2}l{3}/{4}".format(self.mem.cfgfile.webserver,  self.mem.cfgfile.webserverport, self.user.hash, self.document.hash, urllib.parse.quote(os.path.basename(self.document.filename.lower())))

        comment=""
        if self.document.comment!="":
            comment=self.document.comment+"\n\n___________________________________________________________\n\n"
        noww=now(self.mem.cfgfile.localzone)
        s= ("From: "+self.mem.cfgfile.smtpfrom+"\n"+
        "To: "+self.user.mail+"\n"+
        "MIME-Version: 1.0\n"+
        "Subject: "+ self.document.name+"\n"+
        "Date: " + weekday(noww)+", " + str(noww.strftime("%d"))+" "+ month(noww)+" "+ str(noww.strftime("%Y %X %z")) +"\n"+
        "Content-Type: text/plain; charset=UTF-8\n" +
        "\n"+
        comment +
        QApplication.translate("DidYouReadMe","This is an automatic and personal mail from DidYouReadMe.")+"\n\n"+
        QApplication.translate("DidYouReadMe", "Don't answer and don't resend this mail.")+"\n\n"+
        QApplication.translate("DidYouReadMe", "When you click the next link, you will get the document associated to this mail and it will be registered as read:")+"\n\n"+
        url +"\n\n"+
        self.mem.cfgfile.smtpsupport)
        return s.encode('UTF-8')
    
    def send(self):      
        if self.mem.cfgfile.smtpTLS=="True":
            server = smtplib.SMTP(self.mem.cfgfile.smtpserver)
            try:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.mem.cfgfile.smtpuser,self.mem.cfgfile.smtppwd)
                server.sendmail(self.mem.cfgfile.smtpfrom, self.user.mail, self.message())
                self.sent=True        
            except:
                self.sent=False
            finally:     
                server.quit()
        else:  #ERA EL ANTIVIRUS
            server = smtplib.SMTP(self.mem.cfgfile.smtpserver, 25)
            try:
                server.login(self.mem.cfgfile.smtpuser,self.mem.cfgfile.smtppwd)
                server.helo()
                server.sendmail(self.mem.cfgfile.smtpfrom, self.user.mail, self.message())
                self.sent=True        
            except:
                self.sent=False
            finally:     
                server.quit()
        return self.sent



class SetCountries(SetCommons):
    def __init__(self, mem):
        SetCommons.__init__(self)
        self.mem=mem   
        
    def load_all(self):
        self.append(Country().init__create("es",QApplication.translate("Core","Spain")))
        self.append(Country().init__create("be",QApplication.translate("Core","Belgium")))
        self.append(Country().init__create("cn",QApplication.translate("Core","China")))
        self.append(Country().init__create("de",QApplication.translate("Core","Germany")))
        self.append(Country().init__create("en",QApplication.translate("Core","United Kingdom")))
        self.append(Country().init__create("eu",QApplication.translate("Core","Europe")))
        self.append(Country().init__create("fi",QApplication.translate("Core","Finland")))
        self.append(Country().init__create("fr",QApplication.translate("Core","France")))
        self.append(Country().init__create("ie",QApplication.translate("Core","Ireland")))
        self.append(Country().init__create("it",QApplication.translate("Core","Italy")))
        self.append(Country().init__create("jp",QApplication.translate("Core","Japan")))
        self.append(Country().init__create("nl",QApplication.translate("Core","Netherlands")))
        self.append(Country().init__create("pt",QApplication.translate("Core","Portugal")))
        self.append(Country().init__create("us",QApplication.translate("Core","United States of America")))
        self.append(Country().init__create("ro",QApplication.translate("Core","Romanian")))
        self.append(Country().init__create("ru",QApplication.translate("Core","Rusia")))
        self.order_by_name()

    def qcombobox(self, combo,  country=None):
        """Función que carga en un combo pasado como parámetro y con un SetAccounts pasado como parametro
        Se ordena por nombre y se se pasa el tercer parametro que es un objeto Account lo selecciona""" 
        for cu in self.arr:
            combo.addItem(cu.qicon(), cu.name, cu.id)

        if country!=None:
                combo.setCurrentIndex(combo.findData(country.id))

    def qcombobox_translation(self, combo,  country=None):
        """Función que carga en un combo pasado como parámetro con los países que tienen traducción""" 
        for cu in [self.find("es"),self.find("fr"),self.find("ro"),self.find("ru"),self.find("en") ]:
            combo.addItem(cu.qicon(), cu.name, cu.id)

        if country!=None:
                combo.setCurrentIndex(combo.findData(country.id))

class SetDocuments(SetCommons):
    def __init__(self, mem):
        SetCommons.__init__(self)
        self.mem=mem #solo se usa para conexion, los datos se guardan en arr
                
    def load(self, sql):
        """Carga según el sql pasado debe ser un select * from documents ...."""
        cur=self.mem.con.cursor()
        cur.execute(sql)
        for row in cur:
            d=Document(self.mem).init__create( row['datetime'], row['title'], row['filename'], row['comment'],  row['expiration'],  row['hash'], row['id']  )
            self.append(d)        
        for d in self.arr:
            d.updateNums()
        cur.close()

    def qtablewidget(self, table):
        """Section es donde guardar en el config file, coincide con el nombre del formulario en el que está la table
        Devuelve sumatorios"""
        table.setColumnCount(6)
        table.setHorizontalHeaderItem(0, QTableWidgetItem(QApplication.translate("Core", "Datetime" )))
        table.setHorizontalHeaderItem(1, QTableWidgetItem(QApplication.translate("Core", "Planned" )))    
        table.setHorizontalHeaderItem(2, QTableWidgetItem(QApplication.translate("Core", "Sent" )))    
        table.setHorizontalHeaderItem(3, QTableWidgetItem(QApplication.translate("Core", "Read" )))    
        table.setHorizontalHeaderItem(4, QTableWidgetItem(QApplication.translate("Core", "Expiration" )))    
        table.setHorizontalHeaderItem(5, QTableWidgetItem(QApplication.translate("Core", "Title" )))    
        table.clearContents()
        table.setRowCount(len(self.arr))
        for i, d in enumerate(self.arr):
            table.setItem(i, 0, qdatetime(d.datetime, self.mem.cfgfile.localzone))
            table.setItem(i, 1, QTableWidgetItem(str(d.numplanned)))
            table.item(i, 1).setTextAlignment(Qt.AlignHCenter)
            table.setItem(i, 2, QTableWidgetItem(str(d.numsents)))
            table.item(i, 2).setTextAlignment(Qt.AlignHCenter)
            table.setItem(i, 3, QTableWidgetItem(str(d.numreads)))
            table.item(i, 3).setTextAlignment(Qt.AlignHCenter)
            table.setItem(i, 4, qdatetime(d.expiration, self.mem.cfgfile.localzone))
            table.setItem(i, 5, QTableWidgetItem(d.name))
            if d.numreads==d.numplanned and d.numplanned>0:
                for column in range( 1, 4):
                    print("Migration must colorize")
#                    table.item(i, column).setBackgroundColor(QColor(198, 205, 255))

        table.setCurrentCell(len(self.arr)-1, 0)       
        table.clearSelection()    


    def order_by_datetime(self):
        """Ordena por datetime"""
        self.arr=sorted(self.arr, key=lambda d: d.datetime)        

#    def document_from_hash(self, hash):
#        for d in self.arr:
#            if d.hash==hash:
#                return d
#        print ("Document not found from hash")
#        return None


class Country:
    def __init__(self):
        self.id=None
        self.name=None
        
    def init__create(self, id, name):
        self.id=id
        self.name=name
        return self
            
    def qicon(self):
        icon=QIcon()
        icon.addPixmap(self.qpixmap(), QIcon.Normal, QIcon.Off)    
        return icon 
        
    def qpixmap(self):
        if self.id=="be":
            return QPixmap(":/belgium.gif")
        elif self.id=="cn":
            return QPixmap(":/china.gif")
        elif self.id=="fr":
            return QPixmap(":/france.png")
        elif self.id=="ie":
            return QPixmap(":/ireland.gif")
        elif self.id=="it":
            return QPixmap(":/italy.gif")
        elif self.id=="es":
            return QPixmap(":/spain.png")
        elif self.id=="eu":
            return QPixmap(":/eu.gif")
        elif self.id=="de":
            return QPixmap(":/germany.gif")
        elif self.id=="fi":
            return QPixmap(":/fi.jpg")
        elif self.id=="nl":
            return QPixmap(":/nethland.gif")
        elif self.id=="en":
            return QPixmap(":/uk.png")
        elif self.id=="jp":
            return QPixmap(":/japan.gif")
        elif self.id=="pt":
            return QPixmap(":/portugal.gif")
        elif self.id=="us":
            return QPixmap(":/usa.gif")
        elif self.id=="ro":
            return QPixmap(":/rumania.png")
        elif self.id=="ru":
            return QPixmap(":/rusia.png")
        else:
            return QPixmap(":/star.gif")
            
        
class DBData:
    def __init__(self, mem):
        self.mem=mem


    def load(self):
        inicio=datetime.datetime.now()
        self.users_active=SetUsers(self.mem)
        self.users_active.load("select * from users where active=true order by name")
        self.users_inactive=SetUsers(self.mem)
        self.users_inactive.load("select * from users where active=false order by name")    
        self.groups=SetGroups(self.mem)
        self.groups.load( "select * from groups order by name")
        self.documents_active=SetDocuments(self.mem)
        self.documents_active.load("select  id, datetime, title, comment, filename, hash, expiration  from documents where expiration>now() order by datetime")
        self.documents_inactive=SetDocuments(self.mem)#Carga solo los de un mes y un año.
        print("Cargando dbdata",  datetime.datetime.now()-inicio)

    def users_all(self):
        return self.users_active.union(self.users_inactive, self.mem)
            
    def users_set(self, active):
        """Function to point to list if is active or not"""
        if active==True:
            return self.users_active
        else:
            return self.users_inactive    
    def documents_set(self, active):
        """Function to point to list if is active or not"""
        if active==True:
            return self.documents_active
        else:
            return self.documents_inactive    
    


class Document:
    def __init__(self, mem):
        self.mem=mem
        
    def init__create(self,  dt, name, filename, comment, expiration,   hash='Not calculated',  id=None):
        self.id=id
        self.datetime=dt
        self.name=name
        self.filename=filename
        self.comment=comment
        self.hash=hash
        self.numreads=0
        self.numsents=0
        self.numplanned=0
        self.expiration=expiration
        return self
        
    def init__from_hash(self, hash):
        cur=self.mem.con.cursor()
        cur.execute("select  id, datetime, title, comment, filename, hash, expiration  from documents where hash=%s", (hash, ))
        if cur.rowcount==1:
            row=cur.fetchone()
            self.init__create(row['datetime'], row['title'], row['filename'], row['comment'],  row['expiration'],  row['hash'], row['id']  )
            cur.close()
            return self
        elif cur.rowcount>1:
            print ("There are several documents with the same hash")
            cur.close()
            return None
        else:
            cur.close()
            print ("I couldn't create document from hash {}".format(hash ))
            return None
        
    def __repr__(self):
        return "{0} ({1})".format(self.name, self.id)
        
    def hasPendingMails(self):
        """Returns a boolean, if the document has pending mails searching in database"""
        cur=self.mem.con.cursor()
        cur.execute("select count(*) from userdocuments  where id_documents=%s and sent is null", (self.id, ))
        number=cur.fetchone()[0]
        cur.close()
        if number==0:
            return False
        else:
            return True
        
    def isExpired(self):
        if self.expiration>now(self.mem.cfgfile.localzone):
            return False
        return True
        
    def calculateHash(self):
        """Se mete el datetime porque sino se podría adivinar el ocmunicado"""
        return hashlib.sha256(("d."+str(self.id)+str(self.datetime)).encode('utf-8')).hexdigest()


    def delete(self):
        """Database delete and fisical delete"""
        cur=self.mem.con.cursor()
        cur.execute("delete from documents where id=%s", (self.id, ))        
        cur.close()
        self.unlink()
        
        
    def unlink(self):
        """Physical deletion of the document"""
        try:
            os.unlink(dirDocs+self.hash)
        except:
            print ("Error deleting {}. Document {}".format(dirDocs+self.hash,  self.id))
        
        
    def save(self):
        """No se puede modificar, solo insertar de nuevo
        Modificar es cambiar expiration
        It creates or unlinks file in dirDocs según proceda
        Si hubiera necesidad de modificar sería borrar y crear"""
        cur=self.mem.con.cursor()        
        if self.id==None:
            cur.execute("insert into documents (datetime, title, comment, filename, hash, expiration) values (%s, %s, %s, %s, %s, %s) returning id", (self.datetime, self.name, self.comment, self.filename, self.hash,  self.expiration))
            self.id=cur.fetchone()[0]
            self.hash=self.calculateHash()
            cur.execute("update documents set hash=%s where id=%s", (self.hash,  self.id))
            self.file_to_bytea(self.filename)
            self.bytea_to_file(dirDocs+self.hash)
        else:
            cur.execute("update documents set expiration=%s where id=%s", (self.expiration, self.id ))
            if self.isExpired()==False:
                self.bytea_to_file(dirDocs+self.hash)
            else:
                self.unlink()
        cur.close()
        
    def bytea_to_file(self, filename):
#        print("bytea_to_file", filename)
        cur=self.mem.con.cursor()
        cur.execute("SELECT fileb FROM documents where id=%s and fileb is not null;", (self.id, ))#Si es null peta el open, mejor que devuelva fals3ee3 que pasar a variable
        if cur.rowcount==1:
            open(filename, "wb").write(cur.fetchone()[0])
            cur.close()
            return True
        cur.close()
        return False
        
    def file_to_bytea(self, filename):
#        print("file_to_bytea", filename)
        bytea=open(filename,  "rb").read()        
        cur=self.mem.con.cursor()
        cur.execute("update documents set fileb=%s where id=%s", (bytea, self.id))
        cur.close()

    def updateNums(self):
        cur=self.mem.con.cursor()
        cur.execute("select count(*) from userdocuments where id_documents=%s and sent is not null;", (self.id, ))
        self.numsents=cur.fetchone()[0]
        cur.execute("select count(*) from userdocuments where id_documents=%s and numreads>0;", (self.id, ))
        self.numreads=cur.fetchone()[0]
        cur.execute("select count(*) from userdocuments where id_documents=%s;", (self.id, ))
        self.numplanned=cur.fetchone()[0]
        cur.close()
        
class UserDocument:
    def __init__(self, user, document, mem):
        self.user=user
        self.document=document
        self.mem=mem
        cur=mem.con.cursor()
        cur.execute("select * from userdocuments where id_users=%s and id_documents=%s", (self.user.id, self.document.id))
        if cur.rowcount==0:
            self.sent=None
            self.read=None
            self.numreads=0
            self.new=True #Variable que controla si el registro es nuevo o esta en la base de datos
        else:
            row=cur.fetchone()
            self.sent=row['sent']
            self.read=row['read']
            self.numreads=row['numreads']
            self.new=False
        cur.close()
        
    def save(self):
        cur=self.mem.con.cursor()
        if self.new==True:
            cur.execute("insert into userdocuments(id_users,id_documents,sent,read,numreads) values (%s,%s,%s,%s,%s)", 
                                (self.user.id, self.document.id, self.sent, self.read, self.numreads))
        else:
            cur.execute("update userdocuments set sent=%s,read=%s,numreads=%s where id_users=%s and id_documents=%s", 
                                (self.sent, self.read, self.numreads, self.user.id, self.document.id))
        self.mem.con.commit()
        cur.close()
            
        
    def readed(self, localzone):
        """Actualiza datos y salva"""
        
        if self.read==None:
            self.read=datetime.datetime.now(pytz.timezone(localzone))
        self.numreads=self.numreads+1
        self.save()
        
class ConfigFile:
    def __init__(self, file):
        self.error=False#Variable que es True cuando se produce un error
        self.file=file
        self.language="en"
        self.localzone="Europe/Madrid"
        self.database="didyoureadme"
        self.port="5432"
        self.user="Usuario"
        self.server="127.0.0.1"
        self.pwd="None"
        self.lastupdate=datetime.date.today().toordinal()
        self.smtpfrom="didyoureadme@donotanswer.com"
        self.smtpserver="127.0.0.1"
        self.smtpuser="UsuarioSMTP"
        self.smtpsupport="Please contact system administrator if you have any problem"
        self.smtppwd="pass"       
        self.smtpport="25"
        self.smtpTLS="False"
        self.webserver="127.0.0.1"
        self.webserverport="8000"
        self.webinterface="127.0.0.1"
        self.autoupdate="True"
        
        self.config=configparser.ConfigParser()
        self.load()
        
    def load(self):
        try:
            self.config.read(self.file)
            self.language=self.config.get("frmSettings", "language")
            self.localzone=self.config.get("frmSettings", "localzone")
            self.lastupdate=self.config.getint("frmMain", "lastupdate")
            self.database=self.config.get("frmAccess", "database")
            self.port=self.config.get("frmAccess", "port")
            self.user=self.config.get("frmAccess", "user")
            self.server=self.config.get("frmAccess", "server")        
            self.smtpfrom=self.config.get("smtp", "from")
            self.smtpserver=self.config.get("smtp", "smtpserver")
            self.smtpport=self.config.get("smtp", "smtpport")
            self.smtpuser=self.config.get("smtp", "smtpuser")
            self.smtppwd=self.config.get("smtp", "smtppwd")
            self.smtpsupport=self.config.get("smtp", "support")
            self.smtpTLS=self.config.get("smtp", "tls")
            self.webserver=self.config.get("webserver", "ip")
            self.webserverport=self.config.get("webserver", "port")
            self.webinterface=self.config.get("webserver", "interface")
            self.autoupdate=self.config.get("frmSettings", "autoupdate")
        except:
            self.error=True
        
    def save(self):
        if self.config.has_section("frmMain")==False:
            self.config.add_section("frmMain")
        if self.config.has_section("frmSettings")==False:
            self.config.add_section("frmSettings")
        if self.config.has_section("frmAccess")==False:
            self.config.add_section("frmAccess")
        if self.config.has_section("smtp")==False:
            self.config.add_section("smtp")
        if self.config.has_section("webserver")==False:
            self.config.add_section("webserver")
        self.config.set("frmAccess",  'database', self.database)
        self.config.set("frmAccess",  'port', self.port)
        self.config.set("frmAccess",  'user', self.user)
        self.config.set("frmAccess",  'server', self.server)
        self.config.set("frmSettings",  'language', self.language)
        self.config.set("frmSettings",  'localzone', self.localzone)
        self.config.set("frmSettings",  'autoupdate', self.autoupdate)
        self.config.set("frmMain",  'lastupdate', str(self.lastupdate))
        self.config.set("smtp", "from", self.smtpfrom)
        self.config.set("smtp", "smtpserver", self.smtpserver)
        self.config.set("smtp", "smtpport", self.smtpport)
        self.config.set("smtp", "smtpuser", self.smtpuser)
        self.config.set("smtp", "smtppwd", self.smtppwd)
        self.config.set("smtp", "tls", self.smtpTLS)
        self.config.set("smtp", "support", self.smtpsupport)
        self.config.set("webserver", "ip", self.webserver)
        self.config.set("webserver", "port", self.webserverport)
        self.config.set("webserver", "interface", self.webinterface)
        with open(self.file, 'w') as configfile:
            self.config.write(configfile)
            
class Mem:
    def __init__(self):     
        self.con=None
        self.adminmodeinparameters=False
        self.adminmode=False#Autenticated adminmode
        self.settings=QSettings()
        self.cfgfile=ConfigFile(os.path.expanduser("~/.didyoureadme/")+ "didyoureadme.cfg")
        self.cfgfile.save()
        self.pathlogmail=os.path.expanduser("~/.didyoureadme/mail.log")
        self.pathlogupdate=os.path.expanduser("~/.didyoureadme/updatedata.log")
        self.qtranslator=None
        self.countries=SetCountries(self)
        self.countries.load_all()
        self.languages=SetLanguages(self)
        self.languages.load_all()
        self.data=DBData(self)
        self.language=self.languages.find_by_id(self.settings.value("mem/language", "en"))
        
    def __del__(self):
        if self.con:#Needed when reject frmAccess
            self.disconnect(self.con)
                
    def qicon_admin(self):
        icon = QIcon()
        icon.addPixmap(QPixmap(":/admin.png"), QIcon.Normal, QIcon.Off)
        return icon

    def setQTranslator(self, qtranslator):
        self.qtranslator=qtranslator
            
    def set_admin_mode(self, pasw):
        cur=self.con.cursor()
        cur.execute("update globals set value=md5(%s) where id_globals=6;", (pasw, ))
        cur.close()
        
    def check_admin_mode(self, pasw):
        """Returns: 
                - None: No admin password yet
                - True: parameter pasw is ok
                - False: parameter pasw is wrong"""
        cur=self.con.cursor()
        cur.execute("select value from globals where id_globals=6")
        val=cur.fetchone()[0]
        if val==None or val=="":
            resultado=None
        else:
            cur.execute("select value=md5(%s) from globals where id_globals=6;", (pasw, ))
            resultado=cur.fetchone()[0]
        cur.close()
        print (resultado,  "check_admin_mode")
        return resultado
        


#    def connect(self):
#        strmq="dbname='%s' port='%s' user='%s' host='%s' password='%s'" % (self.cfgfile.database,  self.cfgfile.port, self.cfgfile.user, self.cfgfile.server,  self.cfgfile.pwd)
#        try:
#            mq=psycopg2.extras.DictConnection(strmq)
#            return mq
#        except psycopg2.Error:
#            m=QMessageBox()
#            m.setText(QApplication.translate("DidYouReadMe","Connection error. Try again"))
#            m.exec_()
#            sys.exit()

#    def disconnect(self,  mq):
#        mq.close()



def qdatetime(dt, localzone):
    """dt es un datetime con timezone
    dt, tiene timezone, 
    Convierte un datetime a string, teniendo en cuenta los microsehgundos, para ello se convierte a datetime local
    SE PUEDE OPTIMIZAR
    No hace falta cambiar antes a dt con local.config, ya que lo hace la función
    """
    if dt==None:
        resultado="None"
    else:
        dt=dt_changes_tz(dt,  localzone)#sE CONVIERTE A LOCAL DE dt_changes_tz 2012-07-11 08:52:31.311368-04:00 2012-07-11 14:52:31.311368+02:00
        resultado=str(dt.date())+" "+str(dt.hour).zfill(2)+":"+str(dt.minute).zfill(2)+":"+str(dt.second).zfill(2)
    a=QTableWidgetItem(resultado)
    if dt==None:
        a.setTextColor(QColor(0, 0, 255))
    a.setTextAlignment(Qt.AlignVCenter|Qt.AlignRight)
    return a
    
def dt(date, hour, zonename):
    """Función que devuleve un datetime con zone info.
    Zone is an object."""
    z=pytz.timezone(zonename)
    a=datetime.datetime(date.year,  date.month,  date.day,  hour.hour,  hour.minute,  hour.second, hour.microsecond)
    a=z.localize(a)
    return a

def dt_changes_tz(dt,  tztarjet):
    """Cambia el zoneinfo del dt a tztarjet. El dt del parametre tiene un zoneinfo"""
    if dt==None:
        return None
    tzt=pytz.timezone(tztarjet)
    tarjet=tzt.normalize(dt.astimezone(tzt))
    return tarjet

def now(localzone):
    return datetime.datetime.now(pytz.timezone(localzone))

def c2b(state):
    """QCheckstate to python bool"""
    if state==Qt.Checked:
        return True
    else:
        return False
        


def b2c(booleano):
    """QCheckstate to python bool"""
    if booleano==True:
        return Qt.Checked
    else:
        return Qt.Unchecked     
