INSTALLPATH="/usr/share/watchmyfolder"
INSTALLTEXT="Watch My Folder is now installed"
UNINSTALLTEXT="Watch My Folder has been removed"

install-req:
	@mkdir -p $(INSTALLPATH)
	@cp watch/* $(INSTALLPATH) -f
	@cp README $(INSTALLPATH) -f
	@cp AUTHORS $(INSTALLPATH) -f
	@cp LICENSE $(INSTALLPATH) -f
	@cp bin/watchmyfolder /usr/bin/ -f
	@cp share/watchmyfolder.png /usr/share/pixmaps -f
	@cp share/watchmyfolder.desktop /usr/share/applications/ -f

install: install-req
	@echo $(INSTALLTEXT)

uninstall-req:
	@rm -rf $(INSTALLPATH)
	@rm /usr/share/pixmaps/watchmyfolder.png
	@rm /usr/share/applications/watchmyfolder.desktop
	@rm /usr/bin/watchmyfolder

uninstall: uninstall-req
	@echo $(UNINSTALLTEXT)
