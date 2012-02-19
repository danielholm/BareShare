#!/usr/bin/env python
#
# BareShare
# Authors: Daniel Holm, <admin@danielholm.se>, 120110 Updated 120203
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

version = "0.2"

# Settingsdir and -file.
home = os.getenv('HOME')
configdir = home + "/.bareshare"
configfile = home + "/.bareshare/bareshare.conf"
lsyncdconfig = home + "/.bareshare/lsyncd.conf"
lsyncdlog = home + "/.bareshare/lsyncd.log"
baresharelog = home + "/.bareshare/bareshare.log"
path = os.path.realpath(__file__)
path = path.strip('bareshare.py')

# Some other variables
icon = path+"icons/bareshare-dark.png"
picon = path+"icons/bareshare-dark-passive.png"
uicon = path+"icons/bareshare-dark-upload.png"
sicon = path+"icons/bareshare-dark-sync.png"
lighticon = path+"icons/bareshare-light.png"

# Messages
startingM = "Starting..."
syncingM = "Syncing..."
finishedM = "All files are up to date."
buildM = "Building file list..."
uploadM = "Uploading..."
downloadM = "Downloading..."

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
		self.first_run()

	# Some log file stuff
	os.system("cp "+lsyncdlog+" "+lsyncdlog+".1 && rm "+lsyncdlog) # Move old log file
#	os.system("cp "+baresharelog+" "+baresharelog+".1 && rm "+baresharelog) # Move old log file

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
				# Backup old logs if they exist
				if os.path.exists(rsynclog):
					os.system("cp "+rsynclog+" "+rsynclog+".1 && rm "+rsynclog) # Move and remove old log

				print 'DEBUG: Starting "'+sharename+'" '+way # Debugging

				# Run rsync of each share - but check for which direction
				if way == "download":
					self.rsyncRun = subprocess.Popen(["rsync","--bwlimit="+download,"--stats","--progress","-azvv","-e","ssh",remotedir,local,"--log-file="+rsynclog], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					# The status message
					self.statusM = downloadM

				if way == "upload":
 					self.rsyncRun = subprocess.Popen(["rsync","--bwlimit="+upload,"--stats","--progress","-azvv","-e","ssh",local,remotedir,"--log-file="+rsynclog], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					# The status message
					self.statusM = uploadM

				# Print whats happening
				self.line = self.rsyncRun.stdout.readline()
				rsyncM = self.line.rstrip()
				print "DEBUG: "+rsyncM
				print "DEBUG: Done, next!"
				os.system('notify-send "Sync finished" "'+sharename+' is finished syncing" -i '+icon)

		self.t = threading.Thread(target = worker)
		self.t.daemon = True
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
		self.ind.set_icon(icon) 

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

		# Pause/Resume sync
		# Check weather lsyncd is running or not
		self.ppus = gtk.MenuItem()
		self.ppus.set_label("Pause Sync")
		self.ppus.connect("activate", self.pauseUn)
		self.ppus.show()
		self.menu.append(self.ppus)

		# Add share guide
		add = "Add Share"
		add_share = gtk.ImageMenuItem(gtk.STOCK_ADD)
		add_share.connect("activate", self.first_run, None)
		add_share.show()
		self.menu.append(add_share)

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
		os.system("killall -9 lsyncd rsync")

	# Pause or unpause function
	def pauseUn(self, widget):
		# Check if lsyncd is running
		if pidL: #if it isnt
			# Resume sync
			self.ppus.set_label("Pause Sync")
			self.label.set_label(startingM)
			self.ind.set_icon(icon) # Set to active icon

		else: # if it is
			# Pause sync
			self.ppus.set_label("Resume Sync")
			self.label.set_label("Paused")
			self.ind.set_icon(picon) # Passive icon

	# Updates the label about rsync transer data
	def rsyncOutput(self, widget):
		self.labelR.set_label(rsyncM)
		print "DEBUG: "+rsyncM

		return True # make it go on

	# Updates the label about lsyncd transer data
	def lsyncdOutput(self, widget):
		# Get output from lsyncd subprocess
#		self.line = self.lsyncdRun.stdout.readline()
#		lsyncdM = self.line.rstrip()
#		self.labelR.set_label(lsyncdM)

#		print "DEBUG: "+lsyncdM

		return True # Keep it go on
			
	# About
	def show_about(self, widget, data):
		# Create AboutDialog object
		dialog = gtk.AboutDialog()

		# Add the application name to the dialog
		dialog.set_name('BareShare')

		# Add a application icon to the dialog
		dialog.set_logo(gtk.gdk.pixbuf_new_from_file(lighticon))

		# Set the application version
		dialog.set_version(version)

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
		# Create window dialog
		self.dialog = gtk.Window()

		# Set some window settings
		self.dialog.set_title("BareShare - Add new share")
		self.dialog.set_size_request(300, 230)
		self.dialog.set_position(gtk.WIN_POS_CENTER)

		# Use fixed positions
		self.fix = gtk.Fixed()	

		# Add a info message
		self.message = gtk.Label('Please enter the info for the new share.')
		self.fix.put(self.message, 10, 10)

		# Share name
		self.name = gtk.Entry()
		self.name.set_text("Name of share")
		self.fix.put(self.name, 10, 40)

		# Server adress
		self.adress = gtk.Entry()
		self.adress.set_text("Server adress (domain)")
		self.fix.put(self.adress, 10, 70)

		# Server username
		self.username = gtk.Entry()
		self.username.set_text("Username on server")
		self.fix.put(self.username, 10, 100)

		# local directory
		self.local = gtk.Entry()
		self.local.set_text("Directory on machine")
		self.fix.put(self.local, 10, 130)

		# remote directory
		self.remote = gtk.Entry()
		self.remote.set_text("Directory on server")
		self.fix.put(self.remote, 10, 160)

		# Ok battun to save
		self.ok = gtk.Button(stock="gtk-ok")
		self.fix.put(self.ok, 200, 190)

		# Close button
		self.close = gtk.Button(stock="gtk-close")
		self.fix.put(self.close, 240, 190)

		self.dialog.add(self.fix)
		self.dialog.show_all()

		# When clicked ok send the data
		self.ok.connect("clicked", self.addShare)
		# Close the window
		self.close.connect("clicked", self.closeDialog)

	# Closes new share window
	def closeDialog(self, widget):
		self.dialog.destroy()

	# Collect the data from the add share dialog and modify the config
	def addShare(self, event):
		# Get the new values from preferences
		name = self.name.get_text()
		adress = self.adress.get_text()
		username = self.username.get_text()
		local = self.local.get_text()
		remote = self.remote.get_text()

		# Debugging
		print "Added new share:"
		print "Share name: "+ name
		print "Domain: "+ adress
		print "Username: "+ username
		print "Local dir: "+ local
		print "Remote dir: "+ remote

		# Backup the old config file
		os.system("cp "+configfile+" "+configfile+".bak")

		# Set up the share settings template variable
		tpl = "\n["+name+"]\nname = "+name+"\nusername = "+username+"\nway = download\nlocal = "+local+"/\nremote = "+remote+"/\ndomain = "+adress+"\n"
		ltpl = '\nsync{default.rsyncssh, source="'+local+'/", host="'+adress+'", targetdir="'+remote+'", rsyncOpts="-ltus", "-azvv"}\n'

		# Parse the config file to get the previous shares
		parser = SafeConfigParser()
		parser.read(configfile)
		shares = parser.get('profile', 'shares')

		# Add the new share to the variable and replace the row in the config file
		sharesNew = "shares = "+shares+", "+name+"\n"

		# Replace the row in config file
		lines = open(configfile, 'r').readlines()
		lines[3] = sharesNew
		out = open(configfile, 'w')
		out.writelines(lines)
		out.close()

		# Close the window
		self.dialog.destroy()

		# Add the new share to the config file
		with open(configfile, "a") as f:
			f.write(tpl)

		# Add a new row to the lsyncd config too
		with open(lsyncdconfig, "a") as f:
			f.write(ltpl)

		# Show notification
		os.system('notify-send "Added share" "You have to restart BareShare" -i '+icon)


	# Preferences window
	def prefD(self, widget, data):
		# Get current settings from config
		parser = SafeConfigParser()
		parser.read(configfile)
		Cdownload = parser.get('profile', 'download')
		Cupload = parser.get('profile', 'upload')

		self.pref = gtk.Window()

		self.pref.set_title("BareShare - Preferences")
		self.pref.set_size_request(260, 160)
		self.pref.set_position(gtk.WIN_POS_CENTER)

		# Use fixed positions
		self.fix = gtk.Fixed()	

		# Set a label for the settings (Bandwidth)
		self.speedL = gtk.Label("Bandwidth limit:")
		self.fix.put(self.speedL, 10, 10)
		
		# Set upload speed
		self.uploadL = gtk.Label("Upload:")
		self.fix.put(self.uploadL, 10, 43)
		self.upload = gtk.Entry()
		self.upload.set_text(Cupload)
		self.fix.put(self.upload, 90, 40)

		# Set download speed
		self.downloadL = gtk.Label("Download:")
		self.fix.put(self.downloadL, 10, 73)
		self.download = gtk.Entry()
		self.download.set_text(Cdownload)
		self.fix.put(self.download, 90, 70)

		# Checkbox for support of LAN sync  * NOT IMPLEMENTED YET! *
		self.check = gtk.CheckButton("LAN Sync")
#		self.fix.put(self.check, 10, 10)
		self.check.set_active(False)
		self.check.unset_flags(gtk.CAN_FOCUS)
#		self.check.connect("clicked", self.on_clicked)

		# Ok battun to save
		self.ok = gtk.Button(stock="gtk-ok")
		self.fix.put(self.ok, 160, 120)

		# Close button
		self.close = gtk.Button(stock="gtk-close")
		self.fix.put(self.close, 200, 120)

		self.pref.add(self.fix)
		self.pref.show_all()

		# When clicked ok send the data or, if close, close it of course
		self.ok.connect("clicked", self.savePref)
		self.close.connect("clicked", self.closePref)

	def closePref(self, widget):
		self.pref.destroy()

	def savePref(self, event):
		# Get the new values from preferences
		upload = self.upload.get_text()
		download = self.download.get_text()
		# Debugging
		print "Saved settings:"
		print "Upload: "+ upload
		print "Download: "+ download

		# Backup the old config file
		os.system("cp "+configfile+" "+configfile+".bak")

		tplU = "upload = "+upload+"\n"
		tplD = "download = "+download+"\n"

		# Change the upload row in config
		lines = open(configfile, 'r').readlines()
		lines[2] = tplU
		out = open(configfile, 'w')
		out.writelines(lines)
		out.close()

		# Change the download row in config
		lines = open(configfile, 'r').readlines()
		lines[1] = tplD
		out = open(configfile, 'w')
		out.writelines(lines)
		out.close()
		
		# Close the preferences window
		self.pref.destroy()


def main():
	gtk.main()
	return 0

if __name__ == "__main__":
	indicator = BareShareAppIndicator()
	main()

