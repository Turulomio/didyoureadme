DESTDIR ?= /usr


PREFIXBIN=$(DESTDIR)/bin
PREFIXLIB=$(DESTDIR)/lib/didyoureadme
PREFIXSHARE=$(DESTDIR)/share/didyoureadme
PREFIXPIXMAPS=$(DESTDIR)/share/pixmaps
PREFIXAPPLICATIONS=$(DESTDIR)/share/applications
PREFIXSQL=$(PREFIXSHARE)/sql

all: compile install
compile:
	pyuic4 ui/frmAbout.ui > ui/Ui_frmAbout.py
	pyuic4 ui/frmAccess.ui > ui/Ui_frmAccess.py
	pyuic4 ui/frmHelp.ui > ui/Ui_frmHelp.py
	pyuic4 ui/frmMain.ui > ui/Ui_frmMain.py
	pyuic4 ui/frmSettings.ui > ui/Ui_frmSettings.py
	pyuic4 ui/frmDocumentsIBM.ui > ui/Ui_frmDocumentsIBM.py
	pyuic4 ui/frmGroupsIBM.ui > ui/Ui_frmGroupsIBM.py
	pyuic4 ui/frmUsersIBM.ui > ui/Ui_frmUsersIBM.py
	pyrcc4 -py3  images/didyoureadme.qrc > images/didyoureadme_rc.py
	pylupdate4 -noobsolete didyoureadme.pro
	lrelease didyoureadme.pro

install:
	install -o root -d $(PREFIXBIN)
	install -o root -d $(PREFIXLIB)
	install -o root -d $(PREFIXSHARE)
	install -o root -d $(PREFIXPIXMAPS)
	install -o root -d $(PREFIXAPPLICATIONS)
	install -o root -d $(PREFIXSQL)

	install -m 755 -o root didyoureadme.py $(PREFIXBIN)/didyoureadme
	install -m 644 -o root libdidyoureadme.py bottle.py $(PREFIXLIB)
	install -m 644 -o root ui/*.py $(PREFIXLIB)
	install -m 644 -o root images/*.py $(PREFIXLIB)
	install -m 644 -o root images/didyoureadme.png $(PREFIXPIXMAPS)/didyoureadme.png
	install -m 644 -o root didyoureadme.desktop $(PREFIXAPPLICATIONS)
	install -m 644 -o root i18n/*.qm $(PREFIXSHARE)
	install -m 644 -o root sql/* $(PREFIXSQL)
#	install -m 644 -o root AUTHORS-EN.txt  AUTHORS-ES.txt  CHANGELOG-EN.txt  CHANGELOG-ES.txt  GPL-3.txt  INSTALL-EN.txt  INSTALL-ES.txt  RELEASES-EN.txt  RELEASES-ES.txt  $(PREFIXSHARE)
	install -m 644 -o root images/didyoureadme.ico $(PREFIXSHARE)

uninstall:
	rm $(PREFIXBIN)/didyoureadme
	rm -Rf $(PREFIXLIB)
	rm -Rf $(PREFIXSHARE)
	rm -fr $(PREFIXPIXMAPS)/didyoureadme.png
	rm -fr $(PREFIXAPPLICATIONS)/didyoureadme.desktop


