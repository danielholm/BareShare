#!/usr/bin/env python
#
# BareShare
# Authors: Daniel Holm, <admin@danielholm.se>, 120110 Updated 120116
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU Lesser General Public License version 3, as published by the 
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the applicable version of the GNU Lesser General Public 
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public 
# License version 3 along with this program.  If not, see 
# <http://www.gnu.org/licenses/>
#

# Imports needed modules
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import appindicator
import pynotify
import os
import sys

# Settingsdir and -file.
home = os.getenv('HOME')
configdir = home + "/.bareshare"
configfile = home + "/.bareshare/config.xml"
lsyncdconfig = home + "/.bareshare/lsyncd.conf"
lsyncdlog = home + "/.bareshare/lsyncd.log"
rsynclog = home + "/.bareshare/rsync.log"

# Some other variables
icon = "/home/daniel/Dokument/BareShare/icons/bareshare-dark.png" # Fix 
trickle="trickle -s -d " + download + " -u " + upload + " "

# Messages
startingM = "Starting..."
syncingM = "Syncing..."
finishedM = "All files are up to date"
buildM = "Building file list..."

# Processes 
lsyncd=os.system("lsyncd " + lsyncdconfig + " &")
rsync=os.system("rsync --log-file=" + rsynclog + "all of the parameters from settings file")

# Get the needed info from the config file
# Later in 0.2 perhaps

# Start the sync daemon in the background
os.system("lsyncd " + lsyncdconfig + " &")
# Also start rsync to see if all of the files are up to date
#os.system("rsync --log-file=" + rsynclog + "all of the parameters from settings file")

# Creates the class for the application
class BareShareAppIndicator:

	# Check if config files and dirs exist. If not, create them.
	if not os.path.exists(configdir):
		print "Config dir and file did not exist. Creating..."
		os.makedirs(configdir)
	if not os.path.exists(configfile):
		print "Configfile did not exist. Creating..."
		open(configfile,'w').close()
	if not os.path.exists(lsyncdconfig):
		print "Configfile for lsyncd did not exist. Creating..."
		open(configfile,'w').close()
		# Start the "first run" dialog comes in 0.2
		# self.first_run()

	# Get actions from menu and print 'em (debug)
	def menuitem_response(w, buf):
		print buf

	def __init__(self):

		gobject.timeout_add(1000, self.lsyncdOutput, None)

		self.ind = appindicator.Indicator ("BareShare", icon, appindicator.CATEGORY_APPLICATION_STATUS)
		self.ind.set_status (appindicator.STATUS_ACTIVE)
		self.ind.set_icon(icon)

		# Create a menu
		self.menu = gtk.Menu()
	
        	# Dynamic label here
		# Get the last row from log
#		info = self.lsyncdOutput()
		self.label = gtk.MenuItem()
		self.label.set_label(startingM)
		self.label.set_sensitive(False)
		self.label.show()
		self.menu.append(self.label)

		# Separator
		sep = gtk.SeparatorMenuItem()
		sep.show()
		self.menu.append(sep)

		# Add share guide
		add = "Add Share"
		add_share = gtk.ImageMenuItem(gtk.STOCK_ADD)
		add_share.connect("activate", self.first_run, None)
		add_share.show()
		self.menu.append(add_share)

		# Pause/Resume sync
		# Check weather lsyncd is running or not
		self.ppus = gtk.MenuItem()
		self.ppus.set_label("Pause Sync")
		self.ppus.connect("activate", self.pauseUn)
#		self.ppus.connect("activate", self.lsyncdOutput)
		self.ppus.show()
		self.menu.append(self.ppus)

		# Open preferences dialog
		pref = "Preferences"
		settings = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		settings.connect("activate", self.prefD, None)
		settings.show()
		self.menu.append(settings)

		# Separator
		sep = gtk.SeparatorMenuItem()
		sep.show()
		self.menu.append(sep)

		# Open About
		about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		about.connect("activate", self.show_about, None)
		about.show()
		self.menu.append(about)

		# Quit-item
		image = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		image.connect("activate", self.quit)
		image.show()
		self.menu.append(image)
                    
		self.menu.show()

		self.ind.set_menu(self.menu)

	# Close the indicator and kill the sync daemon
	def quit(self, widget, data=None):
		os.system("killall -9 lsyncd")
		gtk.main_quit()

	# Pause or unpause function
	def pauseUn(self, widget):
		# get pid
		pid = os.system("pidof -s lsyncd")
		# Check if lsyncd is running
		if os.system("pgrep lsyncd"): #if it isnt
			print "Starting lsyncd again"
			# Resume sync
			os.system("kill -CONT " + pid)
			self.ppus.set_label("Pause Sync")
			self.label.set_label(startingM)

		else: # if it is
			print "Killing lsyncd"
			# Pause sync
			os.system("kill -STOP " + pid)
			self.ppus.set_label("Resume Sync")
			self.label.set_label("Paused")

	def lsyncdOutput(self, widget):
		# Get the last row from log file
		fileHandle = open ( lsyncdlog,"r" )
		lineList = fileHandle.readlines()
		fileHandle.close()
		lastline = lineList[-1]
#		print lastline
#		return lastline

		# Then be sure that the row contains the needed info
		if "value" in lastline:
			print "True"
			# Then strip it down to just the data we need.
			info = lastline[-2:]
			print info
			self.label.set_label(info)

		# Standby message
		if "building" in lastline:
			self.label.set_label(buildM)
		if "recursive startup rsync" in lastline:
			self.label.set_label(buildM)
		
		# If neither
		else:
			self.label.set_label(syncingM)

		return True #Have to return True for it to keep on
		
			
	# About
	def show_about(self, widget, data):
		# Create AboutDialog object
		dialog = gtk.AboutDialog()

		# Add the application name to the dialog
		dialog.set_name('BareShare')

		# Add a application icon to the dialog
		dialog.set_logo(gtk.gdk.pixbuf_new_from_file("/home/daniel/Dokument/BareShare/icons/bareshare-light.png"))

		# Set the application version
		dialog.set_version('0.1')

		# Set a list of authors.
		dialog.set_authors(['Daniel Holm - Dev', 'Icons by Gentleface - http://www.gentleface.com/'])

		# "coyright" - I'd like to see copyleft ;)
	        dialog.set_copyright("Daniel Holm")

		# Add a short comment about the application.
		dialog.set_comments('Backup and Share Service')

		# Add license information.
		license = "This program is free software: you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation, either version 3 of the License, or\n(at your option) any later version.\n\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License\nalong with this program.  If not, see <http://www.gnu.org/licenses/>."
		dialog.set_license(license)

		# Add a homepage to the dialog.
		dialog.set_website("https://github.com/danielholm/BareShare")

		# Show the dialog
		dialog.run()

		# The destroy method must be called otherwise the 'Close' button will
		# not work.
		dialog.destroy()

	def hide_dialog(self, widget, data):
		widget.hide()

	# First run
	def first_run(self, widget, data):
		first = gtk.MessageDialog(None, 
		    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, 
		    gtk.BUTTONS_CLOSE, "Not yet implented")

		first.set_title("First run guide - Add share")
		first.set_size_request(250, 150)
		first.set_position(gtk.WIN_POS_CENTER)
		first.run()
		first.destroy()


	# Preferences window
	def prefD(self, widget, data):
		pref = gtk.MessageDialog(None, 
		    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, 
		    gtk.BUTTONS_CLOSE, "Not yet implented")

		pref.set_title("Preferences")
		pref.set_size_request(500, 300)
		pref.set_position(gtk.WIN_POS_CENTER)
		pref.run()
		pref.destroy()

def main():
	gtk.main()
	return 0

if __name__ == "__main__":
	indicator = BareShareAppIndicator()
	main()
