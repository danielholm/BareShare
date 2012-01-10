#
# BareShare
# Authors: Daniel Holm, <admin@danielholm.se>, 120110
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of either or both of the following licenses:
#
# 1) the GNU Lesser General Public License version 3, as published by the 
# Free Software Foundation; and/or
# 2) the GNU Lesser General Public License version 2.1, as published by 
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the applicable version of the GNU Lesser General Public 
# License for more details.
#
# You should have received a copy of both the GNU Lesser General Public 
# License version 3 and version 2.1 along with this program.  If not, see 
# <http://www.gnu.org/licenses/>
#

import gobject
import gtk
import appindicator


def menuitem_response(w, buf):
  print buf

if __name__ == "__main__":
  ind = appindicator.Indicator ("BareShare",
                              "indicator-messages",
                              appindicator.CATEGORY_APPLICATION_STATUS)
  ind.set_status (appindicator.STATUS_ACTIVE)
  ind.set_attention_icon ("indicator-messages-new")

  # create a menu
  menu = gtk.Menu()

  # Add a new share/backup
  new = "Add Share"
  menu_items1 = gtk.MenuItem(new)
  menu.append(menu_items1)

  # Add a new share/backup
  pref = "Preferences"
  menu_items2 = gtk.MenuItem(pref)
  menu.append(menu_items2)

  # ABout dialog
  about = "About"
  menu_items3 = gtk.MenuItem(about)
  menu.append(menu_items3)

  # Connect menu items to functions
  menu_items1.connect("activate", menuitem_response, new)
  menu_items2.connect("activate", menuitem_response, pref)
  menu_items3.connect("activate", menuitem_response, about)

  # show the items
  menu_items1.show()
  menu_items2.show()
  menu_items3.show()

  ind.set_menu(menu)

  gtk.main()
