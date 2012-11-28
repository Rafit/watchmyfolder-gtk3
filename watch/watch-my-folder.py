#!/usr/bin/env python

""" Watch My Folder

    ----------------Authors----------------
    Lachlan de Waard <lachlan.00@gmail.com>
    ----------------Licence----------------
    GNU General Public License version 3

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import os
import time
import shutil
import ConfigParser
import threading

from multiprocessing import Process
from xdg.BaseDirectory import xdg_config_dirs
from gi.repository import Gtk
from gi.repository import GLib

WINDOWOPEN = True
STOP = False
STARTED = False
CONFIG = xdg_config_dirs[0] + '/watchmyfolder.conf'
OS = os.name
INSTALLPATH = '/usr/share/watchmyfolder/'
if OS == 'nt':
    SLASH = '\\'
elif OS == 'posix':
    import socket
    SLASH = '/'

class WorkerThread(threading.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window):
        """Init Worker Thread Class."""
        super(WorkerThread, self).__init__()
        self._notify_window = notify_window
        self._want_abort = 0
        self._stop = threading.Event()
        self.setDaemon(True)
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
        return None

    def run(self):
        """ run background thread """
        WATCH.main(WATCH())
        threading.Thread.__init__(self)


class WATCHMYFOLDER(Gtk.Builder):
    """ Initialise Main Window """
    def __init__(self):
        """ ??? """
        self.builder = Gtk.Builder()
        self.builder.add_from_file(INSTALLPATH + "watch-my-folder.ui")
        # main window
        self.window = self.builder.get_object("main_window")
        self.statuslabel = self.builder.get_object("statuslabel")
        self.settingsbutton = self.builder.get_object("settingsbutton")
        self.quitbutton = self.builder.get_object("quitbutton")
        self.startbutton = self.builder.get_object("startbutton")
        self.stopbutton = self.builder.get_object("stopbutton")
        # conf window
        self.confwindow = self.builder.get_object("config_window")
        self.inputentry = self.builder.get_object('inputentry')
        self.backupentry = self.builder.get_object('backupentry')
        self.skipfilesentry = self.builder.get_object('skipfilesentry')
        self.skipfoldersentry = self.builder.get_object('skipfoldersentry')
        self.waittimeentry = self.builder.get_object('waittimeentry')
        self.hiddenfilecheck = self.builder.get_object('hiddenfilecheck')
        self.hiddenfoldercheck = self.builder.get_object('hiddenfoldercheck')
        self.tildecheck = self.builder.get_object('tildecheck')
        self.backupcheck = self.builder.get_object('backupcheck')
        self.watchdeletecheck = self.builder.get_object('watchdeletecheck')
        self.applybutton = self.builder.get_object("applyconf")
        self.closebutton = self.builder.get_object("closeconf")
        self.inputfolder = None
        self.outputfolder = None
        self.skipfiles = None
        self.skipfolders = None
        self.waittime = None
        self.enabletilde = None
        self.enableskipfolder = None
        self.enableskipfile = None
        self.enablebackup = None
        self.enablewatchdelete = None
        # main window actions
        self.window.connect("delete-event", self.delete_event)
        self.settingsbutton.connect("clicked", self.showconfig)
        self.quitbutton.connect("clicked", self.quit)
        self.startbutton.connect("clicked", self.start_scan)
        self.stopbutton.connect("clicked", self.stop_scan)
        # config window actions
        self.applybutton.connect("clicked", self.saveconf)
        self.closebutton.connect("clicked", self.closeconf)
        # get config info
        self.checkconfig()
        self.conf = ConfigParser.RawConfigParser()
        self.readconfig()
        # prep and show main window
        self.statuslabel.set_text('Running')
        self.window.show_all()
        # Make a status icon
        icon = '/usr/share/pixmaps/watchmyfolder.png'
        self.statusicon = Gtk.StatusIcon.new_from_file(icon)
        self.statusicon.connect('activate', self.status_clicked )
        self.statusicon.set_tooltip_text("Watch My Folder")
        #self.window.hide()
        # Start main function first
        self.worker = None
        if not self.worker:
            self.worker = WorkerThread(self)
        # Start the Gtk main loop
        Gtk.main()


    def start_scan(self, *args):
        """ Start the scan process separate of the GUI """
        self.statuslabel.set_text('Running')
        global STOP
        if not self.worker:
            self.worker = WorkerThread(self)
        # Attempt to stop the watch process
        try:
            STOP = False
            self.worker.start()
        except RuntimeError:
            # Error will occur when trying to restart a started thread
            print 'already running'

    def stop_scan(self, *args):
        """ Stop the scan process """
        global STOP
        self.statuslabel.set_text('Stopped')
        if not self.worker:
            self.worker = WorkerThread(self)
        # Tell us if the process is stopping/stopped already
        if STOP:
            print 'already stopped'
        # Stop if we haven't already
        else:
            STOP = True
            self.worker._stop.set()
            print 'stopping'
        return
                

    def quit(self, button):
        """ Close down the program and quit the main loop """
        self.stop_scan()
        # Permanently stop the process thread
        self.worker._Thread__stop()
        # Remove the icon and window
        self.statusicon.set_visible(False)
        self.window.destroy()
        # Quit the Gtk main loop
        Gtk.main_quit()
        return False


    def delete_event(self, window, event):
        """ Hide the window then the close button is clicked """
        global WINDOWOPEN
        # Don't delete; hide instead
        self.window.hide_on_delete()
        WINDOWOPEN = False
        return True
 

    def status_clicked(self, status):
        """ hide and unhide the window when clicking the status icon """
        global WINDOWOPEN
        # Unhide the window
        if not WINDOWOPEN:
            self.window.show_all()
            WINDOWOPEN = True
        elif WINDOWOPEN:
            self.delete_event(self, self.window)

    def readconfig(self, *args):
        """ read config and load values """
        self.conf.read(CONFIG)
        self.inputfolder = self.conf.get('conf', 'FolderPath')
        self.outputfolder = self.conf.get('conf', 'BackupPath')
        self.skipfiles = self.conf.get('conf', 'SkipFiles')
        self.skipfolders = self.conf.get('conf', 'SkipFolders')
        self.waittime = int(self.conf.get('conf', 'WaitTime'))
        self.enabletilde = self.conf.get('conf', 'SkipTildeFiles')
        self.enableskipfolder = self.conf.get('conf', 'SkipHiddenFolders')
        self.enableskipfile = self.conf.get('conf', 'SkipHiddenFiles')
        self.enablebackup = self.conf.get('conf', 'BackupEnabled')
        self.enablewatchdelete = self.conf.get('conf', 'MonitorDeletion')
        if self.enablebackup == 'True':
            self.enablebackup = True
        else:
            self.enablebackup = False
        if self.enablewatchdelete == 'True':
            self.enablewatchdelete = True
        else:
            self.enablewatchdelete = False

        if self.enabletilde == 'True':
            self.enabletilde = True
        else:
            self.enabletilde = False
        if self.enableskipfile == 'True':
            self.enableskipfile = True
        else:
            self.enableskipfile = False
        if self.enableskipfolder == 'True':
            self.enableskipfolder = True
        else:
            self.enableskipfolder = False
        return

    def showconfig(self, *args):
        """ fill and show the config window """
        self.readconfig()
        self.inputentry.set_text(self.inputfolder)
        self.backupentry.set_text(self.outputfolder)
        self.waittimeentry.set_text(str(self.waittime))
        self.skipfilesentry.set_text(self.skipfiles)
        self.skipfoldersentry.set_text(self.skipfolders)
        self.backupcheck.set_active(self.enablebackup)
        self.watchdeletecheck.set_active(self.enablewatchdelete)
        self.tildecheck.set_active(self.enabletilde)
        self.hiddenfilecheck.set_active(self.enableskipfile)
        self.hiddenfoldercheck.set_active(self.enableskipfolder)
        self.confwindow.show()
        return

    def saveconf(self, *args):
        """ save any config changes and update live settings"""
        self.conf.read(CONFIG)
        self.conf.set('conf', 'FolderPath', self.inputentry.get_text())
        self.conf.set('conf', 'BackupPath', self.backupentry.get_text())
        self.conf.set('conf', 'WaitTime', self.waittimeentry.get_text())
        self.conf.set('conf', 'SkipFiles', self.skipfilesentry.get_text())
        self.conf.set('conf', 'SkipFolders',
                          self.skipfoldersentry.get_text())
        self.conf.set('conf', 'SkipTildeFiles',
                          str(self.tildecheck.get_active()))
        self.conf.set('conf', 'BackupEnabled',
                          self.backupcheck.get_active())
        self.conf.set('conf', 'MonitorDeletion',
                          str(self.watchdeletecheck.get_active()))
        self.conf.set('conf', 'SkipHiddenFolders',
                          self.hiddenfilecheck.get_active())
        self.conf.set('conf', 'SkipHiddenFiles',
                          self.hiddenfoldercheck.get_active())
        # write to conf file
        conffile = open(CONFIG, "w")
        self.conf.write(conffile)
        conffile.close()
        # reload new conf values
        self.readconfig()
        return

    def checkconfig(self):
        """ create a default config if not available """
        if not os.path.isfile(CONFIG):
            conffile = open(CONFIG, "w")
            conffile.write("[conf]\n\n# Input Folder #\nFolderPath = /home/" +
                           "$USER\n# Destination Folder #\nBackupPath = " +
                           "$HOME/.backup/$HOSTNAME\n\n# Skip files with the" +
                           " following file types #\nSkipFiles = .backup " +
                           ".hdrive .pst .ost .mp3 .avi .iso .mpg .msi .exe " +
                           ".mpeg .aac .wav .mp4 .wma .mov .mod .mts .tmp " +
                           ".dat .xbel .old .deleted .db .xsession-errors " +
                           ".bash_history .esd_auth .lock .ICEauthority " +
                           ".pulse-cookie application_state\n\n# Skip fold" +
                           "ers that contain the following paths #\nSkipFol" +
                           "ders =    /drive_c    /dosdevices    /.config/go" +
                           "ogle-chrome/Default    /.cache    /.csync    /.m" +
                           "ozilla/firefox    /.fontconfig    /.thumbnails  " +
                           "  /.local/share/Trash    /.backup    /.gvfs    /" +
                           ".dbus\n\n# Time to wait between opening the next" +
                           " folder #\nWaitTime = 3\n\n# Create Shadow Copie" +
                           "s for basic versioning #\nBackupEnabled = True\n" +
                           "MonitorDeletion = True\n\n# Linux style hidden f" +
                           "iles/folders #\nSkipTildeFiles = True\nSkipHidde" +
                           "nFiles = True\nSkipHiddenFolders = True\n")
            conffile.close()
        return

    def closeconf(self, *args):
        """ hide the config window """
        self.confwindow.hide()
        return



class WATCH(Process):
    """ Class that controls the scan process """
    def __init__(self):
        global STOP
        global SLASH
        global ORIGINAL_DIR
        if STOP:
            return
        # Set default file names according to OS
        if OS == 'nt':
            profile_var = os.getenv("userprofile")
            user_var = os.getenv("username")
            comp_var = os.getenv("computername")
            homeshare = os.getenv("homeshare")
            conf_file = 'config-windows.txt'
        elif OS == 'posix':
            profile_var = os.getenv("HOME")
            user_var = os.getenv("USER")
            comp_var = socket.gethostname()
            conf_file = '/usr/share/watchmyfolder/config-linux.txt'
        else:
            STOP = True
        # Read config values
        self.conf = ConfigParser.RawConfigParser()
        self.conf.read(conf_file)
        self.skip_files = self.conf.get('conf', 'SkipFiles').split(' ')
        self.skip_dirs = self.conf.get('conf', 'SkipFolders').split('    ')
        if self.conf.get('conf', 'MonitorDeletion') == 'True':
            self.check_delete = True
        else:
            self.check_delete = False
        if self.conf.get('conf', 'BackupEnabled') == "True":
            self.backup_enabled = True
        else:
            self.backup_enabled = False
        try:
            self.wait_time = int(self.wait_time)
        except:
            self.wait_time = 1
        if self.conf.get('conf', 'SkipTildeFiles') == 'True':
            self.skip_tilde =  True
        else:
            self.skip_tilde =  False
        if self.conf.get('conf', 'SkipHiddenFiles') == 'True':
            self.skip_hidden_files = True
        else:
            self.skip_hidden_files = False
        if self.conf.get('conf', 'SkipHiddenFolders') == 'True':
            self.skip_hidden_dirs = True
        else:
            self.skip_hidden_dirs = False
        self.destin = self.conf.get('conf', 'BackupPath')
        self.ORIGINAL_DIR = self.conf.get('conf', 'FolderPath')
        # Set OS specific config values
        if OS == 'nt':
            self.destin = self.destin.replace('%username%', 
                                                        user_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('%username%', 
                                                          user_var)
            self.destin = self.destin.replace('%computername%', 
                                                        comp_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('%computername%', 
                                                          comp_var)
            self.destin = self.destin.replace('%userprofile%', profile_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('%userprofile%', 
                                                          profile_var)
            if not homeshare == None:
                self.destin = self.destin.replace('%homeshare%', homeshare)
                self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('%homeshare%', 
                                                              homeshare)
            self.skip_tilde = False
        if OS == 'posix':
            self.destin = self.destin.replace('$USER', user_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('$USER', user_var)
            self.destin = self.destin.replace('$HOSTNAME', comp_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('$HOSTNAME', comp_var)
            self.destin = self.destin.replace('$HOME', profile_var)
            self.ORIGINAL_DIR = self.ORIGINAL_DIR.replace('$HOME', profile_var)
        # Attempt to make the backup path
        if not os.path.isdir(self.destin):
            try:
                os.makedirs(self.destin)
            except:
                self.destin = (profile_var + SLASH + '.backup' + SLASH + 
                               'BACKUP')
        if not os.path.isdir(self.ORIGINAL_DIR):
            self.ORIGINAL_DIR = profile_var
        # Used to strip useless folders from the backup path
        ORIGINAL_DIR = self.ORIGINAL_DIR
        

    def check_file(self, *args):
        """ File operation Function """
        global STOP
        global SLASH
        global ORIGINAL_DIR
        if STOP:
            return
        in_file = args[0]
        backup_path = args[1]
        insplit = os.path.dirname(in_file).split(SLASH)
        orig_dir =  ORIGINAL_DIR.split(SLASH)
        outdir = ''
        # Remove the base folder from the backup base path
        for items in orig_dir:
            if not len(insplit) == 0:
                for folders in insplit:
                    if items in folders:
                        try:
                            insplit.remove(items)
                        except ValueError:
                            pass
        for items in insplit:
            outdir = outdir + SLASH + items
        backup_file = (os.path.normpath(backup_path + outdir + SLASH + 
                        (os.path.basename(in_file))))
        backup_dir = os.path.dirname(backup_file)
        # Only backup files that contain data
        if os.stat(in_file)[6] == 0:
            pass
        if self.skip_hidden_files and os.path.split(in_file)[-1][0] == '.':
            print 'Skipping: ' + in_file
        # Copy file if it doesn't exist in backup location
        elif not os.path.isfile(backup_file):
            if not os.path.exists(backup_dir):
                try:
                    os.makedirs(backup_dir)
                    shutil.copystat(os.path.dirname(in_file), backup_dir)
                except:
                    pass
            try:
                shutil.copy2(in_file, backup_file)
                print 'New Backup: ' + backup_file
            except IOError:
                pass
        elif os.path.isfile(backup_file):
            # Compare files and backup modified versions since the last cycle.
            if (not os.stat(in_file)[6] == os.stat(backup_file)[6] or 
                os.stat(in_file)[8] > os.stat(backup_file)[8]):
                new_file = backup_file
                new_count = 0
                # Create new destination (for versioning)
                while os.path.isfile(new_file):
                    if new_count == 6:
                        five = (os.path.join(os.path.dirname(new_file), 
                                             (os.path.basename(new_file) + 
                                             '-5.old')))
                        zero = (os.path.join(os.path.dirname(new_file), 
                                             (os.path.basename(new_file) + 
                                             '-0.old')))
                        shutil.copy2(five, zero)
                        temp_count = ['1', '2', '3', '4', '5']
                        for count in temp_count:
                            temp = '-' + count + '.old'
                            os.remove(os.path.join(os.path.dirname(new_file), 
                                                  (os.path.basename(new_file) +
                                                  temp)))
                        new_count = 1
                    temp = '-' + str(new_count) + '.old'
                    old_file = os.path.join(os.path.dirname(new_file), 
                                           (os.path.basename(new_file) + temp))
                    if not os.path.isfile(old_file):
                        new_file = old_file
                    new_count = new_count + 1
                if self.backup_enabled:
                    shutil.move(backup_file, new_file)
                    print 'Backup Created: ' + new_file
                try:
                    shutil.copy2(in_file, backup_file)
                    print 'New Version: ' + backup_file
                except IOError:
                    # Error: File in Use
                    pass
        return

    def check_folder(self, *args):
        """ Recursive loop function for watch_folder function """
        global STOP
        if STOP:
            return
        input_string = args[0]
        backup_path = args[1]
        if os.path.isdir(input_string):
            # Wait to reduce load
            time.sleep(self.wait_time)
            strtest = os.path.split(input_string)[-1][0]
            if STOP:
                return False
            elif self.skip_hidden_dirs and strtest == '.':
                print 'Skipping: ' + input_string
            else:
                print 'Opening: ' + input_string
                self.watch_folder(backup_path, input_string)
        return


    def watch_folder(self, *args):
        """ Search recursively through folders looking for files """
        global STOP
        if STOP:
            return
        backup_path = args[0]
        input_dir = args[1]
        skip_me = False
        for items in self.skip_dirs:
            if items.lower() in input_dir.lower():
                skip_me = True
                print 'skipping ' + items
        if not skip_me and not STOP:
            try:
                for items in os.listdir(input_dir):
                    skipme = False
                    for ignored in self.skip_files:
                        # Don't try to process blank items
                        if not items == '' and not ignored == '':
                            if ignored.lower() in items.lower():
                                skipme = True
                            elif os.path.splitext(items)[1] in self.skip_files:
                                if not os.path.splitext(items)[1] == '':
                                    skipme = True
                            elif self.skip_tilde:
                                if items[-1] == '~':
                                    skipme = True
                    # Run check_file if a file is found
                    if (os.path.isfile(os.path.join(input_dir, items)) and 
                            not skipme):
                        self.check_file(os.path.join(input_dir, items), 
                                        backup_path)
                    # Run check_folder if a folder is found
                    if (os.path.isdir(os.path.join(input_dir, items)) and 
                            not skipme):
                        self.check_folder(os.path.join(input_dir, items), 
                                          backup_path)
            # Ignore Inaccessible Directories
            except:
                # Error: Inaccessible Directory
                pass
        return

    #def check_deletions(self, *args):

    def watch_deletions(self, *args):
        """ mark files/folder in the backup that have been deleted """
        global STOP
        if self.check_delete:
            backup_folder = args[0]
            source_folder = args[1]
            for items in os.listdir(backup_folder):
                if STOP:
                    return
                tmp_backup = os.path.join(backup_folder, items)
                tmp_source = os.path.join(source_folder, items)
                skip_list = ['.old', '.deleted']
                # check for deletion if a file is found
                check1 = os.path.isfile(tmp_backup)
                check2 = os.path.isfile(tmp_source)
                if check1 and not check2:
                    if not os.path.splitext(items)[1] in skip_list:
                        new_file = tmp_backup + '.deleted'
                        try:
                            # rename files that don't exist
                            print 'Found Deleted File: ' + new_file
                            shutil.move(tmp_backup, new_file)
                        except:
                            pass
                if (os.path.isdir(tmp_backup)):
                    try:
                        check1 = os.path.isdir(tmp_source)
                        check2 = tmp_backup[-8:] == '.deleted'
                        if not check1 and not check2:
                            # rename folders that don't exist
                            removed_dir = tmp_backup + '.deleted'
                            print 'Renaming deleted folder: ' + removed_dir
                            shutil.move(tmp_backup, removed_dir)
                        elif os.listdir(tmp_backup) == []:
                            # cleanup empty folders
                            print 'Removing empty folder: ' + tmp_backup
                            os.rmdir(tmp_backup)
                        else:
                            # recheck when folder is found
                            if not tmp_backup[-8:] == skip_list[1]:
                                self.watch_deletions(tmp_backup, tmp_source)
                    except:
                        pass
        return True

    def main(self, *args):
        """ Main Function """
        global STOP
        global ORIGINAL_DIR
        if STOP:
            return
        global STARTED
        if not STARTED:
            STARTED = True
            while 1 and not STOP:
                time.sleep(self.wait_time)
                #try:
                if not os.path.exists(self.destin):
                    os.makedirs(self.destin)
                if not os.path.exists(self.ORIGINAL_DIR):
                    os.makedirs(self.ORIGINAL_DIR)
                shutil.copystat(self.ORIGINAL_DIR, self.destin)
                self.watch_folder(self.destin, self.ORIGINAL_DIR)
                #self.watch_deletions(self.destin, self.ORIGINAL_DIR)
                #except:
                #    # Skip error when directory is missing
                #    pass
                try:
                    print ''
                except exceptions.AttributeError:
                    pass
            STARTED = False

if __name__ == "__main__":
    GLib.threads_init()
    WATCHMYFOLDER()

