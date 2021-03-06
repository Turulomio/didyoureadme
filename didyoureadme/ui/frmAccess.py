from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from didyoureadme.ui.Ui_frmAccess import *
from didyoureadme.libdidyoureadme import Connection

class frmAccess(QDialog, Ui_frmAccess):
    def __init__(self, mem, parent = None, name = None, modal = False):
        """Returns accepted if conection is done, or rejected if there's an error"""""
        QDialog.__init__(self,  parent)
        self.mem=mem
        self.setModal(True)
        self.setupUi(self)
        self.parent=parent
        self.mem.languages.qcombobox(self.cmbLanguages,self.mem.language)
        self.setPixmap(QPixmap(":didyoureadme.png"))
        self.setTitle(self.tr("DidYouReadMe - Access"))
        self.con=Connection()#Pointer to connection

    def setPixmap(self, qpixmap):
        icon = QtGui.QIcon()
        icon.addPixmap(qpixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)        
        
    def setTitle(self, text):
        self.setWindowTitle(text)
        
    def setLabel(self, text):
        self.lbl.setText(text)
        
    def showLanguage(self, boolean):
        if boolean==False:
            self.cmbLanguages.hide()
            self.lblLanguage.hide()
        
        
    def config_load(self):
        self.txtDB.setText(self.mem.settings.value("frmAccess/db", "didyoureadme" ))
        self.txtPort.setText(self.mem.settings.value("frmAccess/port", "5432"))
        self.txtUser.setText(self.mem.settings.value("frmAccess/user", "postgres" ))
        self.txtServer.setText(self.mem.settings.value("frmAccess/server", "127.0.0.1" ))
        self.txtPass.setFocus()
        
    def config_save(self):
        self.mem.settings.setValue("frmAccess/db", self.txtDB.text() )
        self.mem.settings.setValue("frmAccess/port",  self.txtPort.text())
        self.mem.settings.setValue("frmAccess/user" ,  self.txtUser.text())
        self.mem.settings.setValue("frmAccess/server", self.txtServer.text())   

    @pyqtSlot(str)      
    def on_cmbLanguages_currentIndexChanged(self, stri):
        self.mem.language=self.mem.languages.find_by_id(self.cmbLanguages.itemData(self.cmbLanguages.currentIndex()))
        self.mem.settings.setValue("mem/language", self.mem.language.id)
        self.mem.languages.cambiar(self.mem.language.id)
        #REtranslate
        self.retranslateUi(self)
        self.setLabel(QApplication.translate("DidYouReadMe", self.lbl.text()))#Doesn't work

    def make_connection(self):
        """Función que realiza la conexión devolviendo true o false con el éxito"""
        try:
            self.con.init__create(self.txtUser.text(), self.txtPass.text(), self.txtServer.text(), self.txtPort.text(), self.txtDB.text())
            self.con.connect()
            return self.con.is_active()
        except:
            print ("Error in function make_connection",  self.mem.con)
            return False
    
    @QtCore.pyqtSlot() 
    def on_cmdYN_accepted(self):
        self.con.init__create(self.txtUser.text(), self.txtPass.text(), self.txtServer.text(), self.txtPort.text(), self.txtDB.text())
        self.con.connect()
        if self.con.is_active():
            self.accept()
        else:
            self.reject()

    @QtCore.pyqtSlot() 
    def on_cmdYN_rejected(self):
        self.reject()




