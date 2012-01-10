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

import pygtk
pygtk.require('2.0')
import gobject
import gtk
import appindicator

def menuitem_response(w, buf):
  print buf

class BareShareIndicator:
# The about dialog
    def show_about(widget):
        about = gtk.AboutDialog()
        about.set_program_name("BareShare")
        about.set_version("0.1")
        about.set_copyright("(c) Daniel Holm")
        about.set_comments("Backup and Share Service")
        about.set_website("https://github.com/danielholm/BareShare")
        about.set_logo(gtk.set_icon("nautilus"))
	about.set_license('GPL v3')
        about.run()
        about.destroy()

if __name__ == "__main__":
  indicator = appindicator.Indicator ("BareShare",
                              "nautilus",
                              appindicator.CATEGORY_APPLICATION_STATUS)
  indicator.set_status (appindicator.STATUS_ACTIVE)
  indicator.set_attention_icon ("indicator-messages-new")
#gtk.set_from_image

  # create a menu
  menu = gtk.Menu()

  # This should just be a name and then, when runing, show transfer speed and current file
  label = "BareShare"
  menu_label = gtk.MenuItem(label)
  menu.append(menu_label)

  # Add a new share/backup
  new = "Add Share"
  menu_add = gtk.MenuItem(new)
  menu.append(menu_add)

  # Preferences
  pref = "Preferences"
  menu_pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
  menu.append(menu_pref)

  # Separator
  item = gtk.SeparatorMenuItem()
  item.show()
  menu.append(item)

  # About dialog
  #about = "About" // Remove
  menu_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
  menu.append(menu_about)

  # Separator
  item = gtk.SeparatorMenuItem()
  item.show()
  menu.append(item)

  #Quit button
  menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
  menu.append(menu_quit)

  # Connect menu items to functions
  menu_add.connect("activate", menuitem_response, new)
  menu_pref.connect("activate", menuitem_response, pref)
#  menu_about.connect("activate", show_about)
  menu_quit.connect("activate", gtk.main_quit)

  # show the items
  menu_label.show()
  menu_add.show()
  menu_pref.show()
  menu_about.show()
  menu_quit.show()
  menu.show()

  indicator.set_menu(menu)

#  about = AboutDialog()
#  about.main()

  gtk.main()
