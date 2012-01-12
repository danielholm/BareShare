#!/usr/bin/env python
#
# BareShare
# Authors: Daniel Holm, <admin@danielholm.se>, 120110
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
import xml.dom.minidom

# Settingsdir and -file.
home = os.getenv('HOME')
configdir = home + "/.bareshare"
configfile = home + "/.bareshare/config.xml"

# Some other variables
icon = "/home/daniel/Dokument/BareShare/icons/bareshare-dark.png"

# Get the needed info from the config file
dom = xml.dom.minidom.parse(configfile)

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def handleSlideshow(slideshow):
    handleSlideshowTitle(slideshow.getElementsByTagName("name")[0])
    shares = slideshow.getElementsByTagName("share")
    handleToc(shares)
    handleSlides(shares)

def handleSlides(shares):
    for share in shares:
        handleSlide(share)

def handleSlide(share):
    handleSlideTitle(share.getElementsByTagName("name")[0])
    handleURLs(share.getElementsByTagName("locale_url"))

def handleSlideshowTitle(name):
    realname = getText(name.childNodes)
    print realname

def handleSlideTitle(name):
    name = getText(name.childNodes)
    print name

def handleURLs(locale_url):
    for url in locale_url:
        handleURL(url)

def handleURL(locale_url):
    l_url = getText(locale_url.childNodes)
    print l_url

def handleToc(shares):
    for share in shares:
        name = share.getElementsByTagName("name")[0]
        share_name = getText(name.childNodes)

handleSlideshow(dom)


# Start the sync daemon in the background
# os.system("lsyncd -rsyncssh /home remotehost.org backup-home/")


# When starting, save the pid of the sync process
#pid = os.system("ps -ef | awk '/process/{ print $2 }'")
#print pid

# Check if config files and dirs exist. If not, create them.
if not os.path.exists(configdir):
	print "Config dir and file did not exist. Creating..."
	os.makedirs(configdir)
if not os.path.exists(configfile):
	print "Configfile did not exist. Creating..."
	open(configfile,'w').close()

# Get actions from menu and print 'em (debug)
def menuitem_response(w, buf):
	print buf

# Creates the class for the application
class BareShareAppIndicator:

	def __init__(self):
		self.ind = appindicator.Indicator ("BareShare", icon, appindicator.CATEGORY_APPLICATION_STATUS)
		self.ind.set_status (appindicator.STATUS_ACTIVE)
		self.ind.set_icon(icon)

		# Create a menu
		self.menu = gtk.Menu()
	
        	# Dynamic label here

		# Open Profile Creator
		add = "Add Share"
		add_share = gtk.ImageMenuItem(gtk.STOCK_ADD)
		add_share.connect("activate", menuitem_response, add)
		add_share.show()
		self.menu.append(add_share)

		# Create Submenu
#		self.pmenu = gtk.Menu()

#		importm = gtk.MenuItem("Profile")
#		importm.set_submenu(self.pmenu)
#		importm.show()
		
		# Item for adding new profiles
#		addprofile = gtk.ImageMenuItem(gtk.STOCK_ADD)
#		addprofile.connect("activate", self.show_filechooser, None)
#		addprofile.show()
#		self.pmenu.append(addprofile)

		# Pause/Unpause sync
		ppust = "Pause Sync"
		ppus = gtk.MenuItem(ppust)
		ppus.connect("activate", menuitem_response, ppus)
		ppus.show()
		self.menu.append(ppus)

		# Open Settings dialog
		pref = "Preferences"
		settings = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		settings.connect("activate", menuitem_response, pref)
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

	def quit(self, widget, data=None):
		gtk.main_quit()

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

def main():
	gtk.main()
	return 0

if __name__ == "__main__":
	indicator = BareShareAppIndicator()
	main()
