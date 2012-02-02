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
import subprocess
import threading
import csv
from ConfigParser import SafeConfigParser

# Settingsdir and -file.
home = os.getenv('HOME')
configdir = home + "/.bareshare"
configfile = home + "/.bareshare/bareshare.conf"
lsyncdconfig = home + "/.bareshare/lsyncd.conf"
lsyncdlog = home + "/.bareshare/lsyncd.log"

os.system("cp "+lsyncdlog+" "+lsyncdlog+".1 && rm "+lsyncdlog) # Move old log file

# Some other variables
icon = "/home/daniel/Dokument/BareShare/icons/bareshare-dark.png" # Fix 
picon = "/home/daniel/Dokument/BareShare/icons/bareshare-dark-passive.png" # Fix 
uicon ="/home/daniel/Dokument/BareShare/icons/bareshare-dark-upload.png" # Fix 
sicon ="/home/daniel/Dokument/BareShare/icons/bareshare-dark-sync.png" # Fix 

# Messages
startingM = "Starting..."
syncingM = "Syncing..."
finishedM = "All files are up to date."
buildM = "Building file list..."
uploadM = "Uploading..."

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
		# Get settings from config (sections)
		parser = SafeConfigParser()
		parser.read(configfile)
		# Bandwith speed and use rsync --bwlimit=value
		value = 0 # Default bandwidth value
		download = parser.get('profile', 'download')
		upload = parser.get('profile', 'upload')
		shares = parser.get('profile', 'shares')
		print "DEBUG: Shares: "+shares
		# Count the shares and divide transfer speed with the shares count
		if upload is not "0": # Should not be run if the transfer speed is set to zero
			number = (shares.count(' ')+1)
			speed = int(upload)/int(number)
			upload = str(speed)

		# For each section of shares in conf, get data from its own section
		def worker():
			for share in shares.split(', '):
				username = parser.get(share, 'username')
				sharename = parser.get(share, 'name')
				way = parser.get(share, 'way')
				local = parser.get(share, 'local')
				remote = parser.get(share, 'remote')
				domain = parser.get(share, 'domain')
				remotedir = username+"@"+domain+":"+remote
				rsynclog = home + "/.bareshare/"+share+"rsync.log"
				os.system("cp "+rsynclog+" "+rsynclog+".1 && rm "+rsynclog) # MOve and remove old log
				print 'DEBUG: Starting "'+sharename+'" '+way # Debugging

				# Run rsync of each share - but check for which direction
				if way == "download":
					self.rsyncRun = subprocess.Popen(["rsync","--bwlimit="+download,"--stats","--progress","-azvv","-e","ssh",remotedir,local,"--log-file="+rsynclog], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

				if way == "upload":
 					self.rsyncRun = subprocess.Popen(["rsync","--bwlimit="+upload,"--stats","--progress","-azvv","-e","ssh",local,remotedir,"--log-file="+rsynclog], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

				self.line = self.rsyncRun.stdout.readline()
				rsyncM = self.line.rstrip()
				print "DEBUG: "+rsyncM

				self.rsyncRun.communicate()
#				self.outData, self.errData = self.rsyncRun.communicate()  # this will return the data read from stdout, and stderr
#				print "DEBUG: "+self.outData

		self.t = threading.Thread(target = worker)
		self.t.start()
#		self.t.join()

		# Start the sync daemon in the background
		print "DEBUG: Starting lsyncd."
		self.lsyncdRun = subprocess.Popen(["lsyncd",lsyncdconfig], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		# Print the debugging
#		self.lineL = self.lsyncdRun.stdout.readline()
#		lsyncdM = self.lineL.rstrip()
#		print "DEBUG: "+lsyncdM

		# Keep the labels updated
		gobject.timeout_add(1000, self.lsyncdOutput, None)
#		gobject.timeout_add(100, self.rsyncOutput, None)

		# Create the appindicator
		self.ind = appindicator.Indicator ("BareShare", icon, appindicator.CATEGORY_APPLICATION_STATUS)
		self.ind.set_status (appindicator.STATUS_ACTIVE)
		self.ind.set_icon(icon) # THis should change on pause

		# Create a menu
		self.menu = gtk.Menu()
	
        	# Dynamic label here
		self.label = gtk.MenuItem()
		self.label.set_label(startingM)
		self.label.set_sensitive(False)
		self.label.show()
		self.menu.append(self.label)

		# Dyamic label for fileinfo
		self.labelR = gtk.MenuItem()
		self.labelR.set_label("Fileinfo here")
		self.labelR.set_sensitive(False)
		self.labelR.hide()
		self.menu.append(self.labelR)

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

		# Show it all                    
		self.menu.show()
		self.ind.set_menu(self.menu)

	# Close the indicator and kill the sync daemon
	def quit(self, widget, data=None):
		gtk.main_quit()

	# Pause or unpause function
	def pauseUn(self, widget):
		# get pid
		pidL = subprocess.call(["pgrep", "lsyncd"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
		pidR = subprocess.call(["pgrep", "rsync"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
		# Check if lsyncd is running
		if pidL: #if it isnt
			print "Debug: Starting lsyncd and rsync again"
			# Resume sync
			pid = str(pidL)
			os.system("kill -CONT "+pid)
#			if pidR:
#				pidr = str(pidR)
#				os.system("kill -CONT "+pidr)
			self.ppus.set_label("Pause Sync")
			self.label.set_label(startingM)
			self.ind.set_icon(icon) # Set to active icon

		else: # if it is
			print "Debug: Killing lsyncd and rsync"
			# Pause sync
			pid = str(pidL)
			os.system("kill -STOP "+pid)
			# Also stop rsync, if running
#			if not pidR:
#				pidr = str(pidR)
#				os.system("kill -STOP "+pidr)
			self.ppus.set_label("Resume Sync")
			self.label.set_label("Paused")
			self.ind.set_icon(picon) # Passive icon

	# Updates the label about rsync transer data
	def rsyncOutput(self, widget):
#		self.line = self.rsyncRun.stdout.readline()
#		rsyncM = self.line.rstrip()
#		self.outData, self.errData = self.rsyncRun.communicate()  # this will return the data read from stdout, and stderr
		self.labelR.set_label(rsyncM)
		print "DEBUG: "+rsyncM

		return True # make it go on

	# Updates the label about lsyncd transer data
	def lsyncdOutput(self, widget):
		# check if rsync' running and if it is, use it first
		pidR = subprocess.call(["pgrep", "rsync"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
		if not pidR:
			self.label.set_label(uploadM)
			self.ind.set_icon(uicon) # uploading icon

		# If rsync isn't running, just use lsyncd data instead
		else:
			# Get output from lsyncd subprocess
			self.line = self.lsyncdRun.stdout.readline()
			lsyncdM = self.line.rstrip()
			self.labelR.set_label(lsyncdM)

			pid = subprocess.call(["pgrep", "lsyncd"], stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

			print "DEBUG: "+self.line

			# Then be sure that the row contains the needed info
			if "value" in self.line:
				print "True"
				print "DEBUG: "+lsyncdM
				self.label.set_label(lsyncdM)

			if pid: #if it isnt running
				self.label.set_label("Paused")
				self.ind.set_icon(picon) # Passive icon

			else:
				# Standby message
				if "building" in self.line:
					self.label.set_label(buildM)
					self.ind.set_icon(icon) # default icon
				if "recursive startup rsync" in self.line:
					self.label.set_label(buildM)
					self.ind.set_icon(icon) # default icon
				if "Finished" in self.line:
					self.label.set_label(finishedM)
					self.ind.set_icon(icon) # default icon
				if "Rsyncing list" in self.line:
					self.label.set_label(syncingM)
					self.ind.set_icon(sicon) # sync icon
				if not "Normal:" in self.line:
					self.label.set_label(syncingM)
					self.ind.set_icon(sicon) # sync icon

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

