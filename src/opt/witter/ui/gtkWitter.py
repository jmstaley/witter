#!/usr/bin/env python2.5
# coding= utf-8
# 
# Copyright (c) 2009 Daniel Would
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#

# ============================================================================
# Name        : gtkWitter.py
# Author      : Daniel Would
# Version     : 0.1
# Description : Witter ui code, gtk
# ============================================================================

#This is the bunch of things I wound up importing
#I think I need them all.. 
import gtk
import pygtk
import hildon
import pynotify
import re
import string
import osso
import os
import witter
import account

#The Witter UI class
class WitterUI():
    #first an init method to set everything up    
    TIMELINE_VIEW = 1
    MENTIONS_VIEW = 2
    DM_VIEW = 3
    SEARCH_VIEW = 4
    FRIENDS_VIEW = 5
    TRENDS_VIEW = 6
    PUBLIC_VIEW = 7
    USERHIST_VIEW = 8
    def __init__(self, controller):
        #pynotify.init("Witter")
        self.version = controller.getVersion()
        self.controller = controller
        #controller is the master program which handles all the events
        # set name of application: this shows in titlebar
        gtk.set_application_name("Witter")
        self.serviceName = "Witter"
        self.theme = "default"
        # 
        #we want to track our position in each tweet stream so we can 
        #return to it when we switch between them
        self.timelinePos = None
        self.mentionPos = None
        self.dmPos = None
        self.searchPos = None
        self.friendsPos = None
        self.trendsPos = None
        self.publicPos = None
        self.showingMore = False
        self.busyCounter = 0
        self.gesture_enabled=True
        self.orientation='Landscape'
        #Set the Glade file
        #self.gladefile = "/usr/share/witter/witter.glade"  
        #self.wTree = gtk.glade.XML(self.gladefile) 
        self.builder = gtk.Builder()
        self.builder.add_from_file("/usr/share/witter/witter.ui")
        print "UI elements loaded from file"
        #map all the signals
        dic = {
            "newTweet" : controller.enterPressed,
            "getTweets" : controller.updateSelectedView,
            "storecreds" : controller.store_creds,
            "getaccesstoken" : controller.getAccessToken,
            "on_timeline_clicked" : self.switchView,
            "on_mentions_clicked" : self.switchView,
            "on_direct_messages_clicked" : self.switchView,
            "on_search_clicked" : self.switchView,
            "on_trend_clicked" : self.switchView,
            "on_user_history_clicked" : self.switchView,
            "on_insert_clicked" : controller.twitPic,
            "on_friends_clicked" : self.switchView,
            "on_trends_clicked" : self.switchView,
            "on_public_clicked" : self.switchView,
            "on_Reply_clicked" : controller.replyTo,
            "on_ReplyAll_clicked" : controller.replyAll,
            "on_AtUser_clicked" : controller.tweetAt,
            "on_Retweet_clicked" : controller.reTweet,
            "on_DirectMessage_clicked" : controller.directMessage,
            "on_Follow_clicked" : controller.FollowTweetAuthor,
            "on_UnFollow_clicked" : controller.UnFollowTweetAuthor,
            "on_cancel_clicked" : self.gtk_widget_hide,
            "on_fullscr_clicked" : self.fullscr,
            "on_extra_clicked" : self.showMoreButtons,
            "on_plus20_clicked" : controller.get20More,
            "on_plus50_clicked" : controller.get50More,
            "on_plus100_clicked" : controller.get100More,
            "on_plus200_clicked" : controller.get200More,

        }
        self.builder.connect_signals(dic)
        print "signals connected to buttons"
        #GtkTreeView::grid-line-width = 20
        gtk.rc_parse_string("""
           style "my-style" 
           {
                 
                 GtkTreeView::even-row-color = "#00FF00"
                 GtkTreeView::odd-row-color = "#FF0000"
                 GtkTreeView::vertical-separator = 5
                 GtkTreeView::tree-line-pattern = "\111\111"
                 GtkTreeView::tree-line-width = 3
                 GtkTreeView::grid-line-width = 10
           }
           class "GtkTreeView" style "my-style"
         """)
        #self.wTree.signal_autoconnect( dic )
        self.icon_size = 48
        self.viewbutton_width=78
        self.viewbutton_depth=60
        #load all the icons and scale them
        print "Loading Theme Icons"
        self.load_theme_icons()
        print "defining ui buttons"
        self.define_ui_buttons()
        #fix the buttons to get the style right 
        


        

        okButton = self.builder.get_object("Ok")
        cancelButton = self.builder.get_object("Cancel")
        okoauthButton = self.builder.get_object("Ok-oauth")



        #action buttons for a tweet
        replybutton = self.builder.get_object("Reply")
        replyAllbutton = self.builder.get_object("ReplyAll")
        retweetbutton = self.builder.get_object("Retweet")
        dmbutton = self.builder.get_object("DirectMessage")
        atUserbutton = self.builder.get_object("AtUser")


        #followbutton = self.builder.get_object("Follow")
        #unfollowbutton = self.builder.get_object("UnFollow")
        #usersTimelinebutton = self.builder.get_object("UsersTimeline")

        okButton.set_name("HildonButton-finger")
        cancelButton.set_name("HildonButton-finger")
        okoauthButton.set_name("HildonButton-thumb")


        #action buttons
        #replybutton.set_name("HildonButton-finger")
        #replyAllbutton.set_name("HildonButton-finger")
        #retweetbutton.set_name("HildonButton-finger")
        #dmbutton.set_name("HildonButton-finger")
        #atUserbutton.set_name("HildonButton-finger")
        #followbutton.set_name("HildonButton-thumb")
        #unfollowbutton.set_name("HildonButton-thumb")
        #usersTimelinebutton.set_name("HildonButton-thumb")
        
        #self.define_portrait_keyboard()
        print "define portrait keyboard objects"
        self.define_portrait_keyboard()
        self.hide_portrait_keyboard()
        print "define general window"
        self.textcolour = "#FFFFFF"
        #default colours are the ones used in the hildon window buttons
        self.bg_top_color = gtk.gdk.color_parse("#6bd3ff")
        self.bg_bottom_color = gtk.gdk.color_parse("#0075b5")
        self.font_size = 18

        #at one point I had the text different colours
        #I may do again
        self.namecolour = self.textcolour
        self.tweetcolour = self.textcolour

        self.themewidth = 790
        #default to colours above, but check if we're on fremantle and change
        #to appropriate colours if we are

        #This being a hildon app we start with a hildon.Window
        self.window = hildon.StackableWindow()
        self.window.set_app_paintable(True)
        self.window.realize()
        #connect the delete event for closing the window
        self.window.connect("delete_event", self.controller.quit)
        #we default to the timeline view
        self.window.set_title("Witter" + " - timeline")
        #add window to self  
        self.controller.program.add_window(self.window)
        #reparent the vbox1 from glade to self.window
        # self.vbox = self.wTree.get_widget("vbox1")
        self.vbox = self.builder.get_object("vbox1")
        #pannedWindow = hildon.PannableArea()
        pannedWindow = self.builder.get_object("pannableArea")
        # hildon.hildon_pannable_area_new_full(mode, enabled, vel_min, vel_max, decel, sps)
        self.window.window.property_change("_HILDON_ZOOM_KEY_ATOM", "XA_INTEGER", 32, gtk.gdk.PROP_MODE_REPLACE, [1])
        #self.scrolled_window = self.wTree.get_widget("scrolled_window")
        self.vbox.reparent(self.window)
        #self.vbox.pack_end(pannedWindow)

        #self.urlmenu = self.build_right_click_menu()
        # create a menu object by calling a method to deine it
        self.menu = self.create_m5_menu(self)
        # add the menu to the window
        self.window.set_app_menu(self.menu)
        #

        # define a liststore we use this to store our tweets and some associated data
        #all the views store basically 'tweet' data in this form
        # the fields are : Name,nameColour,Tweet,TweetColour,id, type, timestamp, replyTo, source
        self.liststore = gtk.ListStore(str, str, str, str, str, str, str, str, str)

        #we want auto-complete of @references 
        #self.tweetText = self.wTree.get_widget("TweetText")
        self.tweetText = self.builder.get_object("TweetText")
        self.tweetText.connect("changed", self.CharsRemaining)
        self.tweetText.connect("focus-in-event", self.text_entry_selected)
        self.tweetText.connect("focus-out-event", self.text_entry_deselected)
        tweetComplete = gtk.EntryCompletion()
        tweetComplete.set_model(self.controller.activeAccount.getFriendsList())
        tweetComplete.set_text_column(0)
        tweetComplete.set_inline_completion(True)
        tweetComplete.set_minimum_key_length(2)
        
        self.tweetText.set_completion(tweetComplete)

        # create the TreeView using treestore this is the object which displays the
        print"setting up treeview"        
        # info stored in the liststore
        self.treeview = gtk.TreeView(self.liststore)
        #self.treeview = hildon.GtkTreeView(gtk.HILDON_UI_MODE_NORMAL)

        #self.treeview = hildon.hildon_gtk_tree_view_new(self.liststore)
        self.treeview.set_rules_hint(True)
        self.treeview.set_model(self.liststore)


        # create the TreeViewColumn to display the data, I decided on two colums
        # one for name and the other for the tweet
        #self.tvcname = gtk.TreeViewColumn('Name')
        #self.cell = witter.witter_cell_renderer.witterCellRender()
        #cell_text = gtk.CellRendererText()
        self.cell = gtk.CellRendererText()

        color = self.bg_top_color

        color2 = self.bg_bottom_color


        #self.cell.set_property('backgroundt_r', color.red)
        #self.cell.set_property('backgroundt_g', color.green)
        #self.cell.set_property('backgroundt_b', color.blue)
        #self.cell.set_property('backgroundt_p', color.pixel)
        #self.cell.set_property('backgroundb_r', color2.red)
        #self.cell.set_property('backgroundb_g', color2.green)
        #self.cell.set_property('backgroundb_b', color2.blue)
        #self.cell.set_property('backgroundb_p', color2.pixel)
        #self.cell.set_property('font_size', self.font_size)

        self.tvctweet = gtk.TreeViewColumn('Pango Markup', self.cell, markup=10)

        #Column 0 for the treeview
        renderer = gtk.CellRendererPixbuf()
        renderer.set_property('yalign', 0)
        #renderer.set_property('ypad', 10)
        #renderer.set_property('cell-background-gdk', gtk.gdk.color_parse("#6bd3ff"))

        column = gtk.TreeViewColumn()
        column.pack_start(renderer, True)
        column.add_attribute(renderer, "pixbuf", 9)
        self.treeview.append_column(column)

        #Column 1 for the treeview
        renderer = gtk.CellRendererText()

        self.tvctweet.set_property("expand", True)
        self.cell.set_property('wrap-mode', "word")
        self.cell.set_property('wrap-width', 730)
        self.cell.set_property('size-points', self.controller.font_size)


        self.treeview.append_column(self.tvctweet)



        self.treeview.set_property('enable-grid-lines', True)
        #self.tvctweet = gtk.TreeViewColumn('Tweet')
        # add the two tree view columns to the treeview
        #self.treeview.append_column(self.tvcname)



        # next we add a mapping to the tweet column, again the third field
        # in our list store is the tweet text
        self.tvctweet.add_attribute(self.cell, 'text', 10)
        #self.tvctweet.add_attribute(self.cell, 'timestamp', 6)
        #self.tvctweet.add_attribute(self.cell, 'replyto', 7)
        #self.tvctweet.add_attribute(self.cell, 'source', 8)

        # make it searchable (I found this in an example and thought I might use it
        # but currently I make no use of this setting
        self.treeview.set_search_column(2)
        self.treeview.set_rules_hint(True)

        #self.treeview.set_property('enable-grid-lines', True)

        # Allow sorting on the column. This is cool because no matter what order
        # we load tweets in, we always get a view which is sorted by the tweet id which
        # always increments, so we get them in order

        self.liststore.set_sort_column_id(4, gtk.SORT_DESCENDING)
        # I don't want to accidentally be dragging and dropping rows out of order
        self.treeview.set_reorderable(False)
        #with all that done I add the treeview to the scrolled window
        pannedWindow.add_with_viewport(self.treeview)
        box = gtk.HBox()
        one = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        one.set_title('1')
        one.connect("clicked", self.TypeLetter, "1")
        one.show()
        box.pack_start(one, expand=True)
        box.show
        print "adding button to panned area"
        pannedWindow.add_with_viewport(box)
        pannedWindow.connect('horizontal-movement', self.gesture)
        pannedWindow.connect('vertical-movement', self.scrolling)
        #self.treeview.connect("button-press-event", self.build_menu, None);
        selection = self.treeview.get_selection()
        selection.connect('changed', self.scrollToTweetCallback)
        #self.treeview.connect('row-activated', self.build_menu)
        self.treeview.connect('row-activated', self.build_stacked_menu)
        print "time to show the window"
        self.window.show_all()
        self.window.connect("key-press-event", self.on_key_press)
        #self.window.connect("button-press-event", self.on_button_pressed)
        self.window.connect("window-state-event", self.on_window_state_change)
        #hide the action buttons
        #self.builder.get_object("hbuttonbox-act1").hide_all()
        self.builder.get_object("hbuttonbox-act2").hide_all()
        self.builder.get_object("hbuttonbox-act3").hide_all()
        self.builder.get_object("hbuttonbox-act4").hide_all()
        self.builder.get_object("hbuttonbox-more").hide_all()
        self.hide_portrait_keyboard()
        self.activeView = self.TIMELINE_VIEW


    def load_theme_icons(self):
        if (os.path.isdir("/opt/witter/icons/" + self.theme) != True):
            self.theme = "default"
        self.tlpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/timeline_off.png")
        self.tlpixbuf_off  = self.tlpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.tlpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/timeline.png")
        self.tlpixbuf_on  = self.tlpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        tl_MapMask = self.tlpixbuf_on.render_pixmap_and_mask()
        self.Mask = tl_MapMask[1]
        
        self.menpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/mention_off.png")
        self.menpixbuf_off  = self.menpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.menpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/mention.png")
        self.menpixbuf_on  = self.menpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.dmpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/dm_off.png")
        self.dmpixbuf_off  = self.dmpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.dmpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/dm.png")
        self.dmpixbuf_on  = self.dmpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.serpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/search_off.png")
        self.serpixbuf_off  = self.serpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.serpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/search.png")
        self.serpixbuf_on  = self.serpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.friendspixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/friends_off.png")
        self.friendspixbuf_off  = self.friendspixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.friendspixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/friends.png")
        self.friendspixbuf_on  = self.friendspixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.trendpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/trends_off.png")
        self.trendpixbuf_off  = self.trendpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.trendpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/trends.png")
        self.trendpixbuf_on  = self.trendpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.pubpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/public_off.png")
        self.pubpixbuf_off  = self.pubpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.pubpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/public.png")
        self.pubpixbuf_on  = self.pubpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.userhistpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/userHistory_off.png")
        self.userhistpixbuf_off  = self.userhistpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.userhistpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/userHistory.png")
        self.userhistpixbuf_on  = self.userhistpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.lesspixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/minus.png")
        self.lesspixbuf_off  = self.lesspixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.morepixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/plus.png")
        self.morepixbuf_on  = self.morepixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.unfullscrpixbuf_off = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/unfullscr.png")
        self.unfullscrpixbuf_off  = self.unfullscrpixbuf_off.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.fullscrpixbuf_on = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/fullscr.png")
        self.fullscrpixbuf_on  = self.fullscrpixbuf_on.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.refreshpixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/refresh.png")
        self.refreshpixbuf  = self.refreshpixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.tweetpixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/tweet.png")
        self.tweetpixbuf = self.tweetpixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.plus20pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/plus20.png")
        self.plus20pixbuf  = self.plus20pixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.plus50pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/plus50.png")
        self.plus50pixbuf = self.plus20pixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        self.plus100pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/plus100.png")
        self.plus100pixbuf  = self.plus100pixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        self.plus200pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/" + self.theme + "/plus200.png")
        self.plus200pixbuf = self.plus200pixbuf.scale_simple(self.icon_size, self.icon_size, gtk.gdk.INTERP_BILINEAR)
        
        print "pixbufs loaded for "+ self.theme+" theme" 
        
        
        
    def define_ui_buttons(self):
        refreshButton = self.builder.get_object("Refresh")
        refImage = gtk.Image()
        refImage.set_from_pixbuf(self.refreshpixbuf)
        refImage.show()
        refreshButton.set_image(refImage)
        tweetButton = self.builder.get_object("Tweet")
        tweetImage = gtk.Image()
        tweetImage.set_from_pixbuf(self.tweetpixbuf)
        tweetImage.show()
        tweetButton.set_image(tweetImage)
        timelineButton = self.builder.get_object("timeline")
       
        tlImage = gtk.Image()
        
        tlImage.set_from_pixbuf(self.tlpixbuf_off)
        tlImage.show()
        timelineButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        hbox2 = self.builder.get_object("hbox2")     
        hbox2.shape_combine_mask(self.Mask,0,0)
        timelineButton.set_image(tlImage)
        mentionsButton = self.builder.get_object("mentions")
        
        menImage = gtk.Image()
        menImage.set_from_pixbuf(self.menpixbuf_off)
        menImage.show()
        mentionsButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        mentionsButton.set_image(menImage)
        dmsButton = self.builder.get_object("direct messages")
        dmImage = gtk.Image()
        dmImage.set_from_pixbuf(self.dmpixbuf_off)
        dmImage.show()
        dmsButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        dmsButton.set_image(dmImage)
        searchButton = self.builder.get_object("search")
        serImage = gtk.Image()
        serImage.set_from_pixbuf(self.serpixbuf_off)
        serImage.show()
        searchButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        searchButton.set_image(serImage)
        friendsButton = self.builder.get_object("friends")
        friendImage = gtk.Image()
        friendImage.set_from_pixbuf(self.friendspixbuf_off)
        friendImage.show()
        friendsButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        friendsButton.set_image(friendImage)
        publicButton = self.builder.get_object("public")
        pubImage = gtk.Image()
        pubImage.set_from_pixbuf(self.pubpixbuf_off)
        pubImage.show()
        publicButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        publicButton.set_image(pubImage)
        trendsButton = self.builder.get_object("trends")
        trendImage = gtk.Image()
        trendImage.set_from_pixbuf(self.trendpixbuf_off)
        trendImage.show()
        trendsButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        trendsButton.set_image(trendImage)
        userButton = self.builder.get_object("userhistory")
        userImage = gtk.Image()
        userImage.set_from_pixbuf(self.userhistpixbuf_off)
        userImage.show()
        userButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        userButton.set_image(userImage)
        fullscrButton = self.builder.get_object("fullscr")
        image = gtk.Image()
        image.set_from_pixbuf(self.fullscrpixbuf_on)
        image.show()
        fullscrButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        fullscrButton.set_image(image)
        extraButton = self.builder.get_object("extra-controls")
        image2 = gtk.Image()
        image2.set_from_pixbuf(self.morepixbuf_on)
        image2.show()
        extraButton.set_size_request(self.viewbutton_width,self.viewbutton_depth)
        extraButton.set_image(image2)
        
        plus20Button = self.builder.get_object("plus20")
        
        plus50Button = self.builder.get_object("plus50")
        plus100Button = self.builder.get_object("plus100")
        plus200Button = self.builder.get_object("plus200")
        plus20 = gtk.Image()
        plus20.set_from_pixbuf(self.plus20pixbuf)
        plus20.show()
        plus20Button.set_image(plus20)
        plus50 = gtk.Image()
        plus50.set_from_pixbuf(self.plus50pixbuf)
        plus50.show()
        plus50Button.set_image(plus50)
        plus100 = gtk.Image()
        plus100.set_from_pixbuf(self.plus100pixbuf)
        plus100.show()
        plus100Button.set_image(plus100)
        plus200 = gtk.Image()
        plus200.set_from_pixbuf(self.plus200pixbuf)
        plus200.show()
        plus200Button.set_image(plus200)
        plus20Button.set_name("HildonButton-finger")
        plus50Button.set_name("HildonButton-finger")
        plus100Button.set_name("HildonButton-finger")
        plus200Button.set_name("HildonButton-finger")
        
        refreshButton.set_name("HildonButton-finger")
        tweetButton.set_name("HildonButton-finger")
        timelineButton.set_name("HildonButton-finger")
        mentionsButton.set_name("HildonButton-finger")
        dmsButton.set_name("HildonButton-finger")
        searchButton.set_name("HildonButton-finger")
        friendsButton.set_name("HildonButton-finger")
        trendsButton.set_name("HildonButton-finger")
        publicButton.set_name("HildonButton-finger")
        userButton.set_name("HildonButton-finger")
        fullscrButton.set_name("HildonButton-finger")
        extraButton.set_name("HildonButton-finger")
        


    def setActiveListStore(self, liststore, sortcol):
        if (sortcol ==4):
            liststore.set_sort_column_id(sortcol, gtk.SORT_DESCENDING)
        else:
            liststore.set_sort_column_id(sortcol, gtk.SORT_ASCENDING)
        self.treeview.set_model(None)
        self.treeview.set_model(liststore)

    def create_m5_menu(self, widget):
        #a fairly standard menu create
        #I put in the same options as I have buttons
        # and linked to the same methods
        menu = hildon.AppMenu()


        ShortenUrl = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        ShortenUrl.set_label("Shorten URL")
        # Attach callback to clicked signal
        ShortenUrl.connect("clicked", self.shortenUrl)
        ShortenUrl.show()
        menu.append(ShortenUrl)

        TwitPic = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        TwitPic.set_label("TwitPic!")
        # Attach callback to clicked signal
        TwitPic.connect("clicked", self.controller.selectImage)
        TwitPic.show()
        menu.append(TwitPic)



        Properties = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Properties.set_label("Preferences")
        # Attach callback to clicked signal
        Properties.connect("clicked", self.show_props_window)
        Properties.show()
        menu.append(Properties)
        Accounts = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Accounts.set_label("Account Setup")
        # Attach callback to clicked signal
        Accounts.connect("clicked", self.show_account_window)
        Accounts.show()
        menu.append(Accounts)
        About = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        About.set_label("About")
        # Attach callback to clicked signal
        About.connect("clicked", self.about)
        About.show()
        menu.append(About)

        #invert no longer works
        #Invert = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        #Invert.set_label("Invert")
        # Attach callback to clicked signal
        #Invert.connect("clicked", self.flipTextColour)
        #Invert.show()
        #menu.append(Invert)

        #user can hit the big X for exit, no need for it in menu
        #Exit = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        #Exit.set_label("Exit")
        ## Attach callback to clicked signal
        #Exit.connect("clicked", self.quit)
        #Exit.show()
        #menu.append(Exit)

        menu.show_all()
        return menu

    def on_key_press(self, widget, event, *args):
        #this picks up the press of the full screen key and toggles
        #from one mode to the other
        #print "event key pressed" + str(event.keyval)
        curView = self.getCurrentView()
        if event.keyval == gtk.keysyms.F7:
            print "zoom in"
            if (self.controller.font_size < 30):
                self.treeview.hide()

                self.controller.font_size = self.controller.font_size + 1
                self.cell.set_property('size-points', self.controller.font_size)
                if (curView == self.TIMELINE_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getTimeline())
                elif (curView == self.DM_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getDmsList())
                elif (curView == self.MENTIONS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getMentionsList())
                elif (curView == self.PUBLIC_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getPublicList())
                elif (curView == self.TRENDS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getTrendsList())
                elif (curView == self.FRIENDS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getFriendsList())
                elif (curView == self.SEARCH_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getSearchList())
                elif (curView == self.USERHIST_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getUserHistoryList())
                self.treeview.show()

        elif event.keyval == gtk.keysyms.F8:
            print "zoom out"
            if (self.controller.font_size > 10):
                self.treeview.hide()

                self.controller.font_size = self.controller.font_size - 1
                self.cell.set_property('size-points', self.controller.font_size)
                if (curView == self.TIMELINE_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getTimeline())
                elif (curView == self.DM_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getDmsList())
                elif (curView == self.MENTIONS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getMentionsList())
                elif (curView == self.PUBLIC_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getPublicList())
                elif (curView == self.TRENDS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getTrendsList())
                elif (curView == self.FRIENDS_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getFriendsList())
                elif (curView == self.SEARCH_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getSearchList())
                elif (curView == self.USERHIST_VIEW):
                    self.treeview.set_model(None)
                    self.treeview.set_model(self.controller.activeAccount.getUserHistoryList())
                self.treeview.show()

        elif event.keyval == gtk.keysyms.F6:
             # The "Full screen" hardware key has been pressed 
             if self.window_in_fullscreen:
                 self.window.unfullscreen ()
                 #when we toggle off fullscreen set the cell render wrap
                 #to 500
                 self.cell.set_property('wrap-width', self.themewidth)
             else:
                self.window.fullscreen ()
                #when we toggle into fullscreen set the cell render wrap
                #wider
                self.cell.set_property('wrap-width', 630)
        elif event.keyval == 65364:
            print "scrolling down"
        elif event.keyval == 65362:
            print "scrolling up"
        else:
            self.builder.get_object("hbox1").show_all()
            self.builder.get_object("hbox2").show_all()
            #self.builder.get_object("hbuttonbox-act1").hide_all()
            self.builder.get_object("hbuttonbox-act2").hide_all()
            self.builder.get_object("hbuttonbox-act3").hide_all()
            self.builder.get_object("hbuttonbox-act4").hide_all()
            self.tweetText.grab_focus()
            self.window.unfullscreen ()



    def enterPressed(self, widget, *args):
        self.newTweet(self, widget, *args)
        #if we were in the search view, we want to restore the search terms after a tweet
        if (self.treeview.get_model() == self.searchliststore):
            self.tweetText.set_text(self.search_terms)


    def on_window_state_change(self, widget, event, *args):
        #this just sets a flag to keep track of what state we're in
       if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.window_in_fullscreen = True
       else:
            self.window_in_fullscreen = False

    def fullscr(self, *args):
        if (self.window_in_fullscreen == True):
            self.window.unfullscreen ()
            fullscrButton = self.builder.get_object("fullscr")
            image = gtk.Image()
            image.set_from_pixbuf(self.fullscrpixbuf_on)
            image.show()
            fullscrButton.set_image(image)
        else:
            self.window.fullscreen ()
            fullscrButton = self.builder.get_object("fullscr")
            image = gtk.Image()
            image.set_from_pixbuf(self.unfullscrpixbuf_off)
            image.show()
            fullscrButton.set_image(image)



    def build_menu(self, widget, *args):
        #first hide the other controls
        print "building menu"
        self.builder.get_object("hbox1").hide_all()
        self.builder.get_object("hbox2").hide_all()
        #
        #empty the dynamic buttons
        buttons = self.builder.get_object("hbuttonbox-act3").get_children()
        for button in buttons:
            self.builder.get_object("hbuttonbox-act3").remove(button)
            button.destroy()
        buttons2 = self.builder.get_object("hbuttonbox-act4").get_children()
        for button in buttons2:
            self.builder.get_object("hbuttonbox-act4").remove(button)
            button.destroy()
        #we need to track how many buttons we create
        #so we know when to create new horizontal button boxes
        b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        #b.set_title('Dismiss')
        disImage = gtk.Image()
        disImage.set_from_file("/opt/witter/icons/dismiss.png")
        disImage.show()
        b.set_image(disImage)
        b.connect("clicked", self.dismissActionButtons)
        self.builder.get_object("hbuttonbox-act4").pack_end(b, expand=True)


        #get the selection
        treeselection = self.treeview.get_selection()
        select1, select2 = treeselection.get_selected_rows()
        #entry1, entry2 = self.treeview.get_selection().get_selected()
        #we might one day have more than on element selected, for now we get 1 row
        try:
            #we want to scroll to the right place in pannable area, *after* we've shown conrolls
            #so the x/y need to be in the right scope
            selectedItem = None
            if select2 != None:

                for item in select2[0]:
                    #bring the selected item to the top of the view

                    #we want to access field 2 (0,1,2) which has our Tweet in it
                    entry = select1.get_value(select1.get_iter(item), 2)
                    #and we might as well list the person who provided the url
                    name = select1.get_value(select1.get_iter(item), 0)
                    id = select1.get_value(select1.get_iter(item), 4)
                    selectedItem = item
                    #exclude logged in user from the reply_all string
                    if (re.search(self.controller.activeAccount.getUsername().lower(), name.lower())):
                        self.reply_all = ""
                    else:
                        self.reply_all = name
                    if re.search("http", entry):
                        #convert the string to chunks deliniated on space (we assume the url 
                        #has spaces around it 
                        L = string.split(entry)
                        for word in L :
                            #find the 'word' which is our url
                            if re.search("http", word):
                                url = word

                                b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
                                b.set_title('Open Url')
                                b.set_value(url)
                                b.connect("clicked", self.controller.openBrowser, url)
                                self.builder.get_object("hbuttonbox-act3").pack_start(b, expand=True)
                    if re.search("@", entry):
                        L = string.split(entry)
                        for word in L :
                            if re.search("@", word):
                                user = word
                                if (user != name):
                                    if (re.search(self.controller.activeAccount.getUsername().lower(), user.lower())):
                                        print "excluding self from reply all"
                                    else:
                                        self.controller.reply_all = self.controller.reply_all + " " + user
                                    b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                                    b.set_title('Follow')
                                    b.set_value(user)
                                    b.connect("clicked", self.controller.activeAccount.FollowUser, user)
                                    self.builder.get_object("hbuttonbox-act4").pack_start(b, expand=True)
                                    b2 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                                    b2.set_value(user)
                                    b2.connect("clicked", self.controller.tweetAtUser, user)
                                    self.builder.get_object("hbuttonbox-act4").pack_start(b2, expand=True)
                                    b3 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                                    b3.set_title('History')
                                    b3.set_value(user)
                                    b3.connect("clicked", self.controller.showHist, user)
                                    self.builder.get_object("hbuttonbox-act4").pack_start(b3, expand=True)


                    #rect = self.treeview.get_background_area(item, self.tvctweet)
                    #x, y = self.treeview.convert_bin_window_to_tree_coords(rect.x, rect.y)
                #only provide a follow button if we aren't in our own timeline (in which case we're already following
                curView = self.getCurrentView()
                if (curView != self.TIMELINE_VIEW):
                    followButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
                    followButton.set_title('Follow')
                    followButton.set_value(name)
                    followButton.connect("clicked", self.controller.activeAccount.FollowUser, name)
                    self.builder.get_object("hbuttonbox-act3").pack_start(followButton, expand=True)
                unfollowButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                unfollowButton.set_title('unFollow')
                unfollowButton.set_value(name)
                unfollowButton.connect("clicked", self.controller.activeAccount.UnFollowUser, name)
                self.builder.get_object("hbuttonbox-act3").pack_start(unfollowButton, expand=True)
                histButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                histButton.set_title('History')
                histButton.set_value(name)
                histButton.connect("clicked", self.controller.showHist, name)
                self.builder.get_object("hbuttonbox-act3").pack_start(histButton, expand=True)

                self.builder.get_object("AtUser").set_label(name)

                self.controller.reply_to = id
                self.controller.reply_to_name = name

                self.controller.retweettext = entry
                self.controller.retweetname = name
                self.controller.retweetid = id

        except IndexError:
            print "nothing selected"

        #self.builder.get_object("hbuttonbox-act1").show_all()
        self.builder.get_object("hbuttonbox-act2").show_all()
        self.builder.get_object("hbuttonbox-act3").show_all()
        self.builder.get_object("hbuttonbox-act4").show_all()
        self.scrollToItem(selectedItem)

    def build_stacked_menu(self, widget, *args):
        #first hide the other controls
        print "building stacked menu"
        win = hildon.StackableWindow()
        win.set_title("tweet")
        pannedArea = hildon.PannableArea()
        vbox1 = gtk.VBox()
        hboxTweet = gtk.HBox()
        hbox0 = gtk.HBox()
        hbox1 = gtk.HBox()
        hbox2 = gtk.HBox()
        hbox3 = gtk.HBox()
        #empty the dynamic buttons
        self.controller.reply_all = ""
        #add avatar image and the tweet selected
        # then all the associated action buttons
        #standard buttons
        #reply
        reply = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        reply.set_title('Reply')
        reply.connect("clicked", self.controller.replyTo)
        hbox0.pack_start(reply, expand=True)
        #reply_all
        reply_all = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        reply_all.set_title('Reply All')
        reply_all.connect("clicked", self.controller.replyAll)
        hbox0.pack_start(reply_all, expand=True)
        retweet = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        retweet.set_title('Retweet')
        retweet.connect("clicked", self.controller.reTweet)
        hbox0.pack_start(retweet, expand=True)
        retweet2 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        retweet2.set_title('RT')
        retweet2.connect("clicked", self.controller.reTweetNew)
        hbox0.pack_start(retweet2, expand=True)
        #direct message
        dm = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
        dm.set_title('Direct Message')
        dm.connect("clicked", self.controller.directMessage)
        hbox0.pack_start(dm, expand=True)

        #get the selection
        treeselection = self.treeview.get_selection()
        select1, select2 = treeselection.get_selected_rows()
        #entry1, entry2 = self.treeview.get_selection().get_selected()
        #we might one day have more than on element selected, for now we get 1 row
        try:
            #we want to scroll to the right place in pannable area, *after* we've shown conrolls
            #so the x/y need to be in the right scope
            selectedItem = None
            if select2 != None:

                for item in select2[0]:
                    #bring the selected item to the top of the view

                    #we want to access field 2 (0,1,2) which has our Tweet in it
                    entry = select1.get_value(select1.get_iter(item), 2)
                    #and we might as well list the person who provided the url
                    name = select1.get_value(select1.get_iter(item), 0)
                    picture = select1.get_value(select1.get_iter(item), 9)
                    picture = picture.scale_simple(90, 90, gtk.gdk.INTERP_BILINEAR)
                    pic = gtk.Image()
                    pic.set_from_pixbuf(picture)
                    hboxTweet.pack_start(pic, expand=False)
                    label = gtk.Label()
                    label.set_text(select1.get_value(select1.get_iter(item), 10))
                    label.set_use_markup(True)
                    label.set_line_wrap(True)
                    label.set_selectable(True)

                    hboxTweet.pack_start(label, expand=True)

                    id = select1.get_value(select1.get_iter(item), 4)
                    selectedItem = item
                    bFav = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
                    bFav.set_title('Favorite')
                    bFav.connect("clicked", self.controller.FavouriteTweet, id)
                    hbox1.pack_start(bFav, expand=True)
                    #exclude logged in user from the reply_all string
                    if (re.search(self.controller.activeAccount.getUsername().lower(), name.lower())):
                        self.reply_all = ""
                    else:
                        self.reply_all = name
                    if re.search("http", entry):
                        #convert the string to chunks deliniated on space (we assume the url 
                        #has spaces around it 
                        L = string.split(entry)
                        for word in L :
                            #find the 'word' which is our url
                            if re.search("http", word):
                                url = word

                                b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
                                b.set_title('Open Url')
                                b.set_value(url)
                                b.connect("clicked", self.controller.openBrowser, url)
                                hbox1.pack_start(b, expand=True)
                    if re.search("@", entry):
                        L = string.split(entry)
                        for word in L :
                            if re.search("@", word):
                                if (word.endswith(".") | word.endswith(":")):
                                    word = word[0:len(word)-1]
                                user = word
                                if (re.search(self.controller.activeAccount.getUsername().lower(), user.lower())):
                                    print "excluding self from reply all"
                                else:
                                    self.controller.reply_all = self.controller.reply_all + " " + user
                         #       if (user != name):
#
 #                                   b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
  #                                                    hildon.BUTTON_ARRANGEMENT_VERTICAL)
   #                                 b.set_title('Follow')
    #                                b.set_value(user)
     #                               b.connect("clicked", self.controller.activeAccount.FollowUser, user)
      #                              hbox1.pack_start(b, expand=True)
       #                             b2 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
 #                                                     hildon.BUTTON_ARRANGEMENT_VERTICAL)
##
  #                                  b2.set_title(user)
   #                                 b2.connect("clicked", self.controller.tweetAtUser, user)
    #                                hbox1.pack_start(b2, expand=True)
     #                               b3 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
      #                                                hildon.BUTTON_ARRANGEMENT_VERTICAL)
#
 #                                   b3.set_title('History')
  #                                  b3.set_value(user)
   #                                 b3.connect("clicked", self.controller.showHist, user)
    #                                hbox1.pack_start(b3, expand=True)
#
#
                    #rect = self.treeview.get_background_area(item, self.tvctweet)
                    #x, y = self.treeview.convert_bin_window_to_tree_coords(rect.x, rect.y)
                #only provide a follow button if we aren't in our own timeline (in which case we're already following
#                curView = self.getCurrentView()
 #               if (curView != self.TIMELINE_VIEW):
  #                  followButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
   #                                                       hildon.BUTTON_ARRANGEMENT_VERTICAL)
    #                followButton.set_title('Follow')
     #               followButton.set_value(name)
      #              followButton.connect("clicked", self.controller.activeAccount.FollowUser, name)
       #             hbox2.pack_start(followButton, expand=True)
        #        unfollowButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
         #                                             hildon.BUTTON_ARRANGEMENT_VERTICAL)
          #      unfollowButton.set_title('unFollow')
           #     unfollowButton.set_value(name)
            #    unfollowButton.connect("clicked", self.controller.activeAccount.UnFollowUser, name)
             #   hbox2.pack_start(unfollowButton, expand=True)
#                histButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
 #                                                     hildon.BUTTON_ARRANGEMENT_VERTICAL)
  #              histButton.set_title('History')
   #             histButton.set_value(name)
    #            histButton.connect("clicked", self.controller.showHist, name)
     #           hbox2.pack_start(histButton, expand=True)

 #               atuser = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
  #                                                    hildon.BUTTON_ARRANGEMENT_VERTICAL)
   #             atuser.set_title(name)
    #            atuser.connect("clicked", self.controller.tweetAt, name)
     #           hbox2.pack_start(atuser, expand=True)

                userOptions = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                userOptions.set_title("Mentioned Users")
                userOptions.connect("clicked", self.buildUserActionMenu)
                hbox2.pack_start(userOptions, expand=True)

                translate = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                translate.set_title("Translate")
                translate.connect("clicked", self.controller.Translate, entry)
                hbox3.pack_start(translate, expand=True)


                self.controller.reply_to = id
                self.controller.reply_to_name = name

                self.controller.retweettext = entry
                self.controller.retweetname = name
                self.controller.retweetid = id

        except IndexError:
            print "nothing selected"

        vbox1.pack_start(hboxTweet, expand=False)
        vbox1.pack_start(hbox0, expand=False)
        vbox1.pack_start(hbox1, expand=False)
        vbox1.pack_start(hbox2, expand=False)
        vbox1.pack_start(hbox3, expand=False)
        pannedArea.add_with_viewport(vbox1)
        win.add(pannedArea)
        win.show_all()

    def buildUserActionMenu(self, widget, *args):
        #first hide the other controls
        print "building stacked menu for user actions"
        win = hildon.StackableWindow()
        win.set_title("User Options")
        pannedArea = hildon.PannableArea()
        hbox1 = gtk.HBox()
        hboxTweet = gtk.HBox()
        vbox0 = gtk.VBox()
        vbox1 = gtk.VBox()
        vbox2 = gtk.VBox()
        vbox3 = gtk.VBox()
        #empty the dynamic buttons

        #add avatar image and the tweet selected
        # then all the associated action buttons
        #standard buttons
        #reply

        #get the selection
        treeselection = self.treeview.get_selection()
        select1, select2 = treeselection.get_selected_rows()
        #entry1, entry2 = self.treeview.get_selection().get_selected()
        #we might one day have more than on element selected, for now we get 1 row
        try:
            #we want to scroll to the right place in pannable area, *after* we've shown conrolls
            #so the x/y need to be in the right scope
            selectedItem = None
            if select2 != None:

                for item in select2[0]:
                    #bring the selected item to the top of the view

                    #we want to access field 2 (0,1,2) which has our Tweet in it
                    entry = select1.get_value(select1.get_iter(item), 2)
                    #and we might as well list the person who provided the url
                    name = select1.get_value(select1.get_iter(item), 0)


                    id = select1.get_value(select1.get_iter(item), 4)
                    selectedItem = item
                    follow = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                    follow.set_title('Follow')
                    follow.set_value(name)
                    follow.connect("clicked", self.controller.activeAccount.FollowUser, name)
                    vbox0.pack_start(follow, expand=False)
                    unfollowButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                    unfollowButton.set_title('unFollow')
                    unfollowButton.set_value(name)
                    unfollowButton.connect("clicked", self.controller.activeAccount.UnFollowUser, name)
                    vbox1.pack_start(unfollowButton, expand=False)
                    tweetat = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                    tweetat.set_title(name)
                    tweetat.connect("clicked", self.controller.tweetAtUser, name)
                    vbox2.pack_start(tweetat, expand=False)
                    hist = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                    hist.set_title('History')
                    hist.set_value(name)
                    hist.connect("clicked", self.controller.showHist, name)
                    vbox3.pack_start(hist, expand=False)
                    if re.search("@", entry):
                        L = string.split(entry)
                        for word in L :
                            if re.search("@", word):
                                if (word.endswith(".") | word.endswith(":")):
                                    word = word[0:len(word)-1]
                                user = word

                                if (user != name):

                                    b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                                    b.set_title('Follow')
                                    b.set_value(user)
                                    b.connect("clicked", self.controller.activeAccount.FollowUser, user)
                                    vbox0.pack_start(b, expand=False)
                                    unfollowButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
                                    unfollowButton.set_title('unFollow')
                                    unfollowButton.set_value(user)
                                    unfollowButton.connect("clicked", self.controller.activeAccount.UnFollowUser, user)
                                    vbox1.pack_start(unfollowButton, expand=False)
                                    b2 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                                    b2.set_title(user)
                                    b2.connect("clicked", self.controller.tweetAtUser, user)
                                    vbox2.pack_start(b2, expand=False)
                                    b3 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)

                                    b3.set_title('History')
                                    b3.set_value(user)
                                    b3.connect("clicked", self.controller.showHist, user)
                                    vbox3.pack_start(b3, expand=False)




        except IndexError:
            print "nothing selected"

        hbox1.pack_start(vbox0, expand=False)
        hbox1.pack_start(vbox1, expand=False)
        hbox1.pack_start(vbox2, expand=False)
        hbox1.pack_start(vbox3, expand=False)
        pannedArea.add_with_viewport(hbox1)
        win.add(pannedArea)
        win.show_all()



    def scrollToItem(self, item):
        try:
            rect = self.treeview.get_background_area(item, self.tvctweet)
            x, y = self.treeview.convert_bin_window_to_tree_coords(rect.x, rect.y)

            self.builder.get_object("pannableArea").scroll_to(x, y + 100)
        except TypeError:
            print "couldn't scroll to item"

    def scrollToTweetCallback(self, widget):
        self.scrollToSelectedTweet()
        
    def scrollToSelectedTweet(self):
        #get the selection
        self.scrollToItem(self.getSelectedTweet())

    def getSelectedTweet(self):
        #get the selection
        try:
            treeselection = self.treeview.get_selection()
            select1, select2 = treeselection.get_selected_rows()
            if select2 != None:
               for item in select2[0]:
                    return item
        except IndexError:
            print "probably nothing selected"
            return None

    def dismissActionButtons(self, *args):
        #self.builder.get_object("hbuttonbox-act1").hide_all()
        self.builder.get_object("hbuttonbox-act2").hide_all()
        self.builder.get_object("hbuttonbox-act3").hide_all()
        self.builder.get_object("hbuttonbox-act4").hide_all()
        self.builder.get_object("hbox2").show_all()
    def hideActionButtons(self):
        stack = hildon.WindowStack.get_default()
        stack.pop(1)
        #self.dismissActionButtons()
    def showActionButtons(self):
        #self.builder.get_object("hbuttonbox-act1").show_all()
        self.builder.get_object("hbuttonbox-act2").show_all()
        self.builder.get_object("hbuttonbox-act3").show_all()
        self.builder.get_object("hbuttonbox-act4").show_all()
        self.builder.get_object("hbox2").show_all()
    def showBottomBar(self):
        self.builder.get_object("hbox1").show_all()
    def hideBottomBar(self):
        self.builder.get_object("hbox1").hide_all()
    def showTabs(self):
        self.builder.get_object("hbox2").show_all()
    def hideTabs(self):
        self.builder.get_object("hbox2").hide_all()

    def  gtk_widget_hide(self, widget, *args):
        widget.hide_all()
        #widget.destroy()

    def reparent_loc(self, widget, newParent):
        widget.reparent(newParent)

    def switchViewTo(self, widget, type):
        self.switch_view_to(type)

    def switch_view_to(self, type):
        if (self.getCurrentView() == self.SEARCH_VIEW):
            #switching out of search view, save search terms and reset text box
            self.controller.search_terms = self.tweetText.get_text()
            self.tweetText.set_text("")
        if (re.search("timeline", type)):
            self.setActiveListStore(self.controller.activeAccount.getTimeline(), 4)
            self.setCurrentView(self.TIMELINE_VIEW)
            self.window.set_title(self.serviceName + " - timeline")
            #ensure selected view has active button image
            self.define_ui_buttons()
            timelineButton = self.builder.get_object("timeline")
            tlImage = gtk.Image()
            tlImage.set_from_pixbuf(self.tlpixbuf_on)
            tlImage.show()
            timelineButton.set_image(tlImage)
            
        elif (re.search("direct", type)):
            self.setActiveListStore(self.controller.activeAccount.getDmsList(),4)
            self.setCurrentView(self.DM_VIEW)

            self.window.set_title(self.serviceName + " - direct messages")
            self.define_ui_buttons()
            dmsButton = self.builder.get_object("direct messages")
            dmImage = gtk.Image()
            dmImage.set_from_pixbuf(self.dmpixbuf_on)
            dmImage.show()
            dmsButton.set_image(dmImage)
           
        elif (re.search("mentions", type)):
            self.setActiveListStore(self.controller.activeAccount.getMentionsList(),4)
            self.setCurrentView(self.MENTIONS_VIEW)

            self.window.set_title(self.serviceName + " - mentions")
            self.define_ui_buttons()
            #ensure selected view has active button image
            mentionsButton = self.builder.get_object("mentions")
            menImage = gtk.Image()
            menImage.set_from_pixbuf(self.menpixbuf_on)
            menImage.show()
            mentionsButton.set_image(menImage)

        elif (re.search("public", type)):
            self.setActiveListStore(self.controller.activeAccount.getPublicList(),4)
            self.setCurrentView(self.PUBLIC_VIEW)

            self.window.set_title(self.serviceName + " - public")
            self.define_ui_buttons()
            publicButton = self.builder.get_object("public")
            pubImage = gtk.Image()
            pubImage.set_from_pixbuf(self.pubpixbuf_on)
            pubImage.show()
            publicButton.set_image(pubImage)
            
        elif (re.search("trends", type)):
            self.setActiveListStore(self.controller.activeAccount.getTrendsList(),4)
            self.setCurrentView(self.TRENDS_VIEW)

            self.window.set_title(self.serviceName + " - trends")
            self.define_ui_buttons()
            trendsButton = self.builder.get_object("trends")
            trendImage = gtk.Image()
            trendImage.set_from_pixbuf(self.trendpixbuf_on)
            trendImage.show()
            trendsButton.set_image(trendImage)
            
        elif (re.search("friends", type)):
            self.setActiveListStore(self.controller.activeAccount.getFriendsList(),0)
            self.setCurrentView(self.FRIENDS_VIEW)

            self.window.set_title(self.serviceName + " - friends")
            self.define_ui_buttons()
            friendsButton = self.builder.get_object("friends")
            friendImage = gtk.Image()
            friendImage.set_from_pixbuf(self.friendspixbuf_on)
            friendImage.show()
            friendsButton.set_image(friendImage)
            
        elif (re.search("search", type)):
            self.setActiveListStore(self.controller.activeAccount.getSearchList(),4)
            self.setCurrentView(self.SEARCH_VIEW)
            self.tweetText.set_text(self.controller.search_terms)
            self.define_ui_buttons()
            self.window.set_title(self.serviceName + " - search")
            searchButton = self.builder.get_object("search")
            serImage = gtk.Image()
            serImage.set_from_pixbuf(self.serpixbuf_on)
            serImage.show()
            searchButton.set_image(serImage)
            
        elif (re.search("user", type)):
            self.setActiveListStore(self.controller.activeAccount.getUserHistoryList(),4)
            self.setCurrentView(self.USERHIST_VIEW)

            self.window.set_title(self.serviceName + " - User History")
            self.define_ui_buttons()
            userButton = self.builder.get_object("userhistory")
            userImage = gtk.Image()
            userImage.set_from_pixbuf(self.userhistpixbuf_on)
            userImage.show()
            userButton.set_image(userImage)
            

        fullscrButton = self.builder.get_object("fullscr")
        image = gtk.Image()
        image.set_from_pixbuf(self.fullscrpixbuf_on)
        image.show()
        fullscrButton.set_image(image)
        extraButton = self.builder.get_object("extra-controls")
        image2 = gtk.Image()
        image2.set_from_pixbuf(self.morepixbuf_on)
        image2.show()
        extraButton.set_image(image2)
        plus20Button = self.builder.get_object("plus20")
        plus50Button = self.builder.get_object("plus50")
        plus100Button = self.builder.get_object("plus100")
        plus200Button = self.builder.get_object("plus200")

        imageplus20 = gtk.Image()
        imageplus20.set_from_file("/opt/witter/icons/" + self.theme + "/plus20.png")
        imageplus20.show()
        plus20Button.set_image(imageplus20)

        imageplus50 = gtk.Image()
        imageplus50.set_from_file("/opt/witter/icons/" + self.theme + "/plus50.png")
        imageplus50.show()
        plus50Button.set_image(imageplus50)

        imageplus100 = gtk.Image()
        imageplus100.set_from_file("/opt/witter/icons/" + self.theme + "/plus100.png")
        imageplus100.show()
        plus100Button.set_image(imageplus100)

        imageplus200 = gtk.Image()
        imageplus200.set_from_file("/opt/witter/icons/" + self.theme + "/plus200.png")
        imageplus200.show()
        plus200Button.set_image(imageplus200)


        self.builder.get_object("hbox1").show_all()
        self.builder.get_object("hbox2").show_all()

    def switchView(self, widget):
        #switches the active liststore to display what the user wants
        print widget
        type = widget.get_label()
        print type
        self.switchViewTo(widget, type)


    def CharsRemaining(self, widget):
         self.builder.get_object("hbox1").show_all()
         tweet = self.builder.get_object("TweetText").get_text()
         counter = self.builder.get_object("Counter")
         if (140 - len(tweet) < 0):
             counter.set_text("<span foreground=\"red\">" + (str(140 - len(tweet))) + "</span>")
         else:
             counter.set_text("<span foreground=\"white\">" + (str(140 - len(tweet))) + "</span>")
         counter.set_use_markup(True)


    def about(self, widget, *args):
        dlg = gtk.AboutDialog()
        dlg.set_version(self.version)
        dlg.set_name("Witter")
        #"Marcus Wikstrm (logo)"
        dlg.set_authors(["Daniel Would (programmer)", u"Marcus Wikstrￃﾶm (logo)"])
        dlg.set_website("Homepage : http://danielwould.wordpress.com/witter/\nBugtracker : http://garage.maemo.org/projects/witter")
        def close(w, res):
            if res == gtk.RESPONSE_CANCEL:
                w.hide()
        dlg.connect("response", close)
        dlg.show()

    def showBusy(self, increment, *args):
        #increment might be +1 or -1 to take the counter up or down
        self.busyCounter = self.busyCounter + increment
        print "running tasks: " + str(self.busyCounter)
        if (self.busyCounter > 0):
            #at least one thing running
            hildon.hildon_gtk_window_set_progress_indicator(self.window, 1)
        else:
            #no more tasks busy
            hildon.hildon_gtk_window_set_progress_indicator(self.window, 0)
            #in case we missed it somewhere, no longer getting Tweets
            self.gettingTweets = False
            

        return


    def gesture(self, widget, direction, startx, starty):
        if (self.gesture_enabled ==False):
            return
        #self.builder.get_object("hbuttonbox-act1").hide_all()
        self.builder.get_object("hbuttonbox-act2").hide_all()
        self.builder.get_object("hbuttonbox-act3").hide_all()
        self.builder.get_object("hbuttonbox-act4").hide_all()
        #get the selected tweet for the view we're in and scroll to what
        #we had selecte last time we were in the view we're switching to
        widget.scroll_to(0, 0)
        print "scroll to last known position"
        curView = self.getCurrentView()
        if (direction == 3):
            if (curView == self.TIMELINE_VIEW):
                self.switchViewTo(self.treeview, "user")
            elif (curView == self.DM_VIEW):
                self.switchViewTo(self.treeview, "mentions")
            elif (curView == self.MENTIONS_VIEW):
                self.switchViewTo(self.treeview, "timeline")
            elif (curView == self.PUBLIC_VIEW):
                self.switchViewTo(self.treeview, "trends")
            elif (curView == self.TRENDS_VIEW):
                self.switchViewTo(self.treeview, "friends")
            elif (curView == self.FRIENDS_VIEW):
                self.switchViewTo(self.treeview, "search")
            elif (curView == self.SEARCH_VIEW):
                self.switchViewTo(self.treeview, "direct")
            elif (curView == self.USERHIST_VIEW):
                self.switchViewTo(self.treeview, "public")


        if (direction == 2):
            if (curView == self.TIMELINE_VIEW):
                self.switchViewTo(self.treeview, "mentions")
            elif (curView == self.DM_VIEW):
                self.switchViewTo(self.treeview, "search")
            elif (curView == self.MENTIONS_VIEW):
                self.switchViewTo(self.treeview, "direct")
            elif (curView == self.PUBLIC_VIEW):
                self.switchViewTo(self.treeview, "user")
            elif (curView == self.TRENDS_VIEW):
                self.switchViewTo(self.treeview, "public")
            elif (curView == self.FRIENDS_VIEW):
                self.switchViewTo(self.treeview, "trends")
            elif (curView == self.SEARCH_VIEW):
                self.switchViewTo(self.treeview, "friends")
            elif (curView == self.USERHIST_VIEW):
                self.switchViewTo(self.treeview, "timeline")

    def scrolling (self, widget, direction, startx, starty):
        pass
        #decided to try keeping top row of buttons at all times
        #self.builder.get_object("hbox1").hide_all()
        #self.builder.get_object("hbox2").hide_all()
        #self.hideActionButtons()
        #self.window.fullscreen ()
        #fullscrButton = self.builder.get_object("fullscr")
        #image = gtk.Image()
        #image.set_from_file("/opt/witter/icons/unfullscr.png")
        #image.show()
        #fullscrButton.set_image(image)

    def top_colour_changed(self, widget):
        color = widget.get_color()
        print "Current color is: (red=%s, green=%s, blue=%s, pixel=%s)" % (color.red, color.green, color.blue, color.pixel)
        self.cell.set_property('backgroundt_r', color.red)
        self.cell.set_property('backgroundt_g', color.green)
        self.cell.set_property('backgroundt_b', color.blue)
        self.cell.set_property('backgroundt_p', color.pixel)
        self.bg_top_color = color
    def bottom_colour_changed(self, widget):
        color = widget.get_color()
        print "Current color is: (red=%s, green=%s, blue=%s, pixel=%s)" % (color.red, color.green, color.blue, color.pixel)
        self.cell.set_property('backgroundb_r', color.red)
        self.cell.set_property('backgroundb_g', color.green)
        self.cell.set_property('backgroundb_b', color.blue)
        self.cell.set_property('backgroundb_p', color.pixel)
        self.bg_bottom_color = color

    def show_props_window(self, widget):
       # a stacked window to contain all properties
       win = hildon.StackableWindow()
       win.set_title("Properties")

       pannedArea = hildon.PannableArea()
       #
       #define the property objects
       #


       bitlyId = gtk.Label("Bit.ly userid")
       bitlyEntry = gtk.Entry()
       bitlyEntry.set_text(self.controller.bitlyusername)
       bitlyEntry.connect("changed", self.controller.setBitlyuid)
       bitlyPwd = gtk.Label("Bit.ly apikey")

       bitlyPwdEntry = gtk.Entry()
       bitlyPwdEntry.set_text(self.controller.bitlyapikey)
       bitlyPwdEntry.set_input_mode(gtk.HILDON_GTK_INPUT_MODE_FULL)
       bitlyPwdEntry.connect("changed", self.controller.setBitlyapiki)
       #tllabel = gtk.Label("Timeline refresh interval")
       tl_picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       tl_picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       tl_picker_button.set_title("Set timeline refresh interval (mins)")
       tlNumEd = self.create_refresh_interval_selector(self.controller.timelineRefreshInterval)
       tl_picker_button.set_selector(tlNumEd)
       tl_picker_button.connect("value-changed", self.on_tl_refresh_value_changed)

       men_picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       men_picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       men_picker_button.set_title("Set mention refresh interval (mins)")
       menNumEd = self.create_refresh_interval_selector(self.controller.mentionsRefreshInterval)
       men_picker_button.set_selector(menNumEd)
       men_picker_button.connect("value-changed", self.on_men_refresh_value_changed)

       dm_picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       dm_picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       dm_picker_button.set_title("Set dm refresh interval (mins)")
       dmNumEd = self.create_refresh_interval_selector(self.controller.DMsRefreshInterval)
       dm_picker_button.set_selector(dmNumEd)
       dm_picker_button.connect("value-changed", self.on_dm_refresh_value_changed)
       pub_picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       pub_picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       pub_picker_button.set_title("Set public refresh interval (mins)")
       pubNumEd = self.create_refresh_interval_selector(self.controller.publicRefreshInterval)
       pub_picker_button.set_selector(pubNumEd)
       pub_picker_button.connect("value-changed", self.on_pub_refresh_value_changed)

       search_picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       search_picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       search_picker_button.set_title("Set search refresh interval (mins)")
       searchNumEd = self.create_refresh_interval_selector(self.controller.searchRefreshInterval)
       search_picker_button.set_selector(searchNumEd)
       search_picker_button.connect("value-changed", self.on_search_refresh_value_changed)



        # Create touch selector
       selector = self.create_theme_selector()

       # Create a picker button
       picker_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       picker_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       picker_button.set_title("Select a theme")

       # Attach the touch selector to the picker button
       picker_button.set_selector(selector)

       # Attach callback to the "value-changed" signal
       picker_button.connect("value-changed", self.select_theme, selector)
       
       rotation_selector = self.create_rotation_selector()
       rotation_picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       rotation_picker.set_name("HildonButton-thumb")
       # Set a title to the button 
       rotation_picker.set_title("Rotation Mode")

       # Attach the touch selector to the picker button
       rotation_picker.set_selector(rotation_selector)

       # Attach callback to the "value-changed" signal
       rotation_picker.connect("value-changed", self.select_rotation_theme, rotation_selector)

       gbutton = hildon.CheckButton(gtk.HILDON_SIZE_AUTO)
       gbutton.set_name("HildonButton-thumb")
       gbutton.set_label("Gestures")
       gbutton.set_active(self.gesture_enabled)
       gbutton.connect("toggled", self.gesture_button_toggled)

       gbutton2 = hildon.CheckButton(gtk.HILDON_SIZE_AUTO)
       gbutton2.set_name("HildonButton-thumb")
       gbutton2.set_label("Email style notifications")
       gbutton2.set_active(self.controller.emailnotifications)
       gbutton2.connect("toggled", self.notification_button_toggled)
       vbox = gtk.VBox(False, 0)
       vbox.pack_start(rotation_picker,True,True,0)
       vbox.pack_start(bitlyId, True, True, 0)
       vbox.pack_start(bitlyEntry, True, True, 0)
       vbox.pack_start(bitlyPwd, True, True, 0)
       vbox.pack_start(bitlyPwdEntry, True, True, 0)
       vbox.pack_start(tl_picker_button, True, True, 0)
       vbox.pack_start(men_picker_button, True, True, 0)
       vbox.pack_start(dm_picker_button, True, True, 0)
       vbox.pack_start(pub_picker_button, True, True, 0)
       vbox.pack_start(search_picker_button, True, True, 0)

       vbox.pack_start(picker_button, True, True, 0)
       vbox.pack_start(gbutton, True, True, 0)
       vbox.pack_start(gbutton2, True, True, 0)

       pannedArea.add_with_viewport(vbox)


       win.add(pannedArea)

       # This call show the window and also add the window to the stack
       win.show_all()
       
    def select_rotation_theme(self,widget, selector):
        print "switching rotation mode to " + selector.get_current_text()
        from portrait import FremantleRotation
        if (selector.get_current_text() == 'Landscape'):
            print "setting never rotate"
            self.controller.rotation.set_mode(FremantleRotation.NEVER)
            self.cell.set_property('wrap-width', 730)
            self.icon_size = 48
            self.load_theme_icons()
            self.define_ui_buttons()
            self.hide_portrait_keyboard()
        elif (selector.get_current_text() == 'Portrait'):
            print "setting always rotated"
            self.controller.rotation.set_mode(FremantleRotation.ALWAYS)
            self.cell.set_property('wrap-width', 400)
            self.icon_size = 30
            self.load_theme_icons()
            self.define_ui_buttons()
        elif (selector.get_current_text() == 'Automatic'):
            print "setting automatic"
            self.controller.rotation.set_mode(FremantleRotation.AUTOMATIC)
        self.orientation = selector.get_current_text()

        
        
    def gesture_button_toggled(self,checkbutton):
        if (checkbutton.get_active()):
            print "gestures on"
            self.gesture_enabled = True
        else:
            print "gestures off"
            self.gesture_enabled = False
    def notification_button_toggled(self,checkbutton):
        if (checkbutton.get_active()):
            print "email style notifications on"
            self.controller.emailnotifications = True
        else:
            print "email style notifications off"
            self.controller.emailnotifications = False


    def create_theme_selector(self):
       selector = hildon.TouchSelector(text=True)

       # Stock icons will be used for the example
       theme_list = []
       for f in os.listdir("/opt/witter/icons/"):
           if  os.path.isdir(os.path.join("/opt/witter/icons/", f)):
                theme_list.append(f)

       match_found = False
       # Populate model
       for item in theme_list:
           selector.append_text(item)


       selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
       return selector
   
    def create_rotation_selector(self):
       selector = hildon.TouchSelector(text=True)

       # Stock icons will be used for the example
       rotation_modes = ['Automatic', 'Landscape', 'Portrait']
       
       # Populate model
       for item in rotation_modes:
           selector.append_text(item)


       selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
       return selector

    def create_refresh_interval_selector(self, selected_value):
       # Create a touch selector 
       selector = hildon.TouchSelectorEntry(text=True)

       # Stock icons will be used for the example
       int_list = ["0", "1","5", "10", "15", "20", "25", "30", "60", "90", "120"]
       active_index = 0
       count = 0
       match_found = False
       # Populate model
       for item in int_list:
           if (re.search(item, str(selected_value))):
               match_found = True
               active_index = count
           selector.append_text(item)
           count = count + 1
       if match_found == False:
           active_index = 0
       print "setting active index to " + str(active_index)
       selector.set_active(0, active_index)
       selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
       return selector

    def on_picker_value_changed(self, button, user_data=None):
       print "Newly selected value: %s\n" % button.get_value()

    def on_tl_refresh_value_changed(self, button, user_data=None):
       self.controller.timelineRefreshInterval = int(button.get_value())

    def on_men_refresh_value_changed(self, button, user_data=None):
       self.controller.mentionsRefreshInterval = int(button.get_value())

    def on_dm_refresh_value_changed(self, button, user_data=None):
       self.controller.DMsRefreshInterval = int(button.get_value())
    def on_pub_refresh_value_changed(self, button, user_data=None):
       self.controller.publicRefreshInterval = int(button.get_value())
    def on_search_refresh_value_changed(self, button, user_data=None):
       self.controller.searchRefreshInterval = int(button.get_value())


    def showMoreButtons(self, *args):
        if (self.showingMore == True):
            self.builder.get_object("hbuttonbox-more").hide_all()
            
            self.showingMore = False
            extraButton = self.builder.get_object("extra-controls")
            image2 = gtk.Image()
            image2.set_from_file("/opt/witter/icons/" + self.theme + "/plus.png")
            image2.show()
            extraButton.set_image(image2)
        else:
            
            self.builder.get_object("hbuttonbox-more").show_all()
            self.showingMore = True
            extraButton = self.builder.get_object("extra-controls")
            image2 = gtk.Image()
            image2.set_from_file("/opt/witter/icons/" + self.theme + "/minus.png")
            image2.show()
            extraButton.set_image(image2)

    def promptForCredentials(self, *args):
        #dialog = self.wTree.get_widget("CredentialsDialog")
        dialog = self.builder.get_object("CredentialsDialog")
        password = self.builder.get_object("Password")
        password.set_input_mode(gtk.HILDON_GTK_INPUT_MODE_FULL)
        dialog.set_title("Twitter Credentials")
        dialog.connect("response", self.gtk_widget_hide)
        dialog.show_all()

    def showOauthPrompts(self):
         note = hildon.Note("confirmation", self.window, "authorise with twitter...")
         note.set_button_texts("ok", "cancel")
         note.connect("response", self.gtk_widget_hide)
         retcode = gtk.Dialog.run(note)

         if retcode == gtk.RESPONSE_OK:
            print "User pressed 'OK' button'"

         else:
            print "User pressed 'Cancel' button"
            return


         dialog = self.builder.get_object("OauthDialog")
         dialog.set_title("Twitter Credentials")
         dialog.connect("response", self.gtk_widget_hide)
         dialog.show_all()

    def getOauthPIN(self):
        '''returns the current value of the oauthDialogs PIN field'''
        return self.builder.get_object("PIN").get_text()

    def shortenUrl(self, widget, *args):
        # a stacked window to contain all properties
       win = hildon.StackableWindow()
       win.set_title("Properties")

       pannedArea = hildon.PannableArea()
       #
       #define the property objects
       #


       label = gtk.Label()#
       label.set_text("Enter URL to shorten")
       entry = gtk.Entry()

       ShortenButton = hildon.GtkButton(gtk.HILDON_SIZE_FINGER_HEIGHT)

       ShortenButton.set_label("Shorten URL")
       # Attach callback to clicked signal
       ShortenButton.set_name("HildonButton-finger")
       ShortenButton.connect("clicked", self.controller.getShortenedURL, entry)
       ShortenButton.show()
       label2 = gtk.Label()#
       label2.set_text("Shortened URL will be placed in tweet entry box")
       vbox = gtk.VBox(False, 0)
       vbox.pack_start(label, True, True, 0)
       vbox.pack_start(entry, True, True, 0)
       vbox.pack_start(ShortenButton, False, False, 0)
       vbox.pack_start(label2, True, True, 0)

       pannedArea.add_with_viewport(vbox)


       win.add(pannedArea)

       # This call show the window and also add the window to the stack
       win.show_all()

    def appendTweetText(self, text):
        self.tweetText.set_text(self.tweetText.get_text() + " " + text)

    def setTweetText(self, text):
        self.tweetText.set_text(text)

    def getEntryText(self):
        return self.tweetText.get_text()
    def set_title(self, title):
        self.window.set_title(title)

    def getCurrentView(self):
        return self.activeView
    def setCurrentView(self, viewId):
        self.activeView = viewId

    def setCursorAt(self, pos):
        self.tweetText.grab_focus()
        self.tweetText.set_position(pos);

    def show_account_window(self, widget):
       # a stacked window to contain all properties
       win = hildon.StackableWindow()
       win.set_title("Accounts")

       pannedArea = hildon.PannableArea()
       #
       #define the property objects
       #

       AccountTitle = gtk.Label("Accounts")
       selector = hildon.TouchSelector(text=True)

       # Stock icons will be used for the example
       account_list = self.controller.config.accountList

       match_found = False
       # Populate model
       for item in account_list:
           if (item.status == item.ACTIVE):
               selector.append_text(item.username + " - " + item.servicename + " - Active")
           else:
               selector.append_text(item.username + " - " + item.servicename)

       selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
       NewAccButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
       NewAccButton.set_title("New")
       NewAccButton.connect("clicked", self.edit_new_account)
       EditAccButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)

       EditAccButton.set_title("Edit")
       EditAccButton.connect("clicked", self.edit_selected_account, selector, self.controller.config.accountList)
       SetActiveAccButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
       SetActiveAccButton.set_title("Set Active")
       SetActiveAccButton.connect("clicked", self.setActiveAccount, selector, self.controller.config.accountList)

       DeleteAccButton = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                  hildon.BUTTON_ARRANGEMENT_VERTICAL)
       DeleteAccButton.set_title("Delete")
       DeleteAccButton.connect("clicked", self.deleteAccount, selector, self.controller.config.accountList)

       hbox = gtk.HBox(False, 0)
       vboxright = gtk.VBox(False, 0)
       vboxleft = gtk.VBox(False, 0)
       #vbox.pack_start(AccountTitle, True, True, 0)
       vboxright.pack_start(NewAccButton, False, False, 0)
       vboxright.pack_start(EditAccButton, False, False, 0)
       vboxright.pack_start(SetActiveAccButton, False, False, 0)
       vboxright.pack_start(DeleteAccButton, False, False, 0)
       vboxleft.pack_start(AccountTitle, False, False, 0)
       vboxleft.pack_start(selector, True, True, 0)
       hbox.pack_start(vboxleft, True, True, 0)

       hbox.pack_start(vboxright, True, True, 0)
       pannedArea.add_with_viewport(hbox)


       win.add(pannedArea)

       # This call show the window and also add the window to the stack
       win.show_all()

    def edit_selected_account(self, widget, selector, accList):
        selected = selector.get_current_text()
        for account in accList:
            if (re.search(account.username, selected)):
                if(re.search(account.servicename, selected)):
                   self.edit_account_details(widget, account)


    def edit_new_account(self, widget):
        accData = account.accountdata()
        self.edit_account_details(widget, accData)
        self.controller.config.accountList.append(accData)
        self.controller.addNewAccount(accData)


    def edit_account_details(self, widget, account):

       win = hildon.StackableWindow()
       win.set_title("Edit Account - " + account.username)

       pannedArea = hildon.PannableArea()
       #
       #define the property objects
       #


       AccountTitle = gtk.Label("Account")
       selector = self.create_account_type_selector(account.servicename)

       # Create a picker button
       accType_button = hildon.PickerButton(gtk.HILDON_SIZE_AUTO,
                                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
       accType_button.set_name("HildonButton-thumb")
       # Set a title to the button 
       accType_button.set_title("Account Type")

       # Attach the touch selector to the picker button
       accType_button.set_selector(selector)
       ServiceUrl = gtk.Entry()
       ServiceUrl.set_text(account.baseUrl)
       ServiceUrl.connect("changed", self.changed_base_url, account)
       SearchUrl = gtk.Entry()
       SearchUrl.set_text(account.searchUrl)
       SearchUrl.connect("changed", self.changed_search_url, account)
       selector.connect("changed", self.changed_account_type, ServiceUrl, SearchUrl, account)
       # Attach callback to the "value-changed" signal
       #AccountType = gtk.Label("Account Type: " + account.getServicename())

       UsernameLabel = gtk.Label("Username")
       UsernameEntry = gtk.Entry()
       UsernameEntry.connect("changed", self.changed_username, account)
       UsernameEntry.set_text(account.username)
       PasswordLabel = gtk.Label("Password")
       PasswordEntry = gtk.Entry()
       PasswordEntry.set_invisible_char("*")
       PasswordEntry.set_visibility(False)
       PasswordEntry.connect("changed", self.changed_password, account)

       if (account.password == None):
           PasswordEntry.set_text("Not Set")
       else:
           PasswordEntry.set_text(account.password)
       hbox = gtk.HBox(False, 0)
       vbox = gtk.VBox(False, 0)
       vbox.pack_start(AccountTitle, True, True, 0)
       vbox.pack_start(accType_button, True, True, 0)
       vbox.pack_start(UsernameLabel, True, True, 0)
       vbox.pack_start(UsernameEntry, True, True, 0)
       vbox.pack_start(PasswordLabel, True, True, 0)
       vbox.pack_start(PasswordEntry, True, True, 0)


       if (account.servicename == "Twitter"):
           if (account.access_token == None):
               AccessTokenIndicator = gtk.Label()
               AccessTokenIndicator.set_text("Oauth Not Configured")

           else:
               AccessTokenIndicator = gtk.Label()
               AccessTokenIndicator.set_text("Oauth Configured")
           hbox.pack_start(AccessTokenIndicator, True, True, 0)
           Creds2 = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                           hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
           Creds2.set_label("Configure Oauth")
           # Attach callback to clicked signal
           Creds2.connect("clicked", self.controller.configOauth, account)
           Creds2.show()
           hbox.pack_start(Creds2, False, False, 0)
           vbox.pack_start(hbox, True, True, 0)


       vbox.pack_start(ServiceUrl, True, True, 0)
       vbox.pack_start(SearchUrl, True, True, 0)



       pannedArea.add_with_viewport(vbox)


       win.add(pannedArea)
       win.connect("destroy", self.finished_account_edit)
       # This call show the window and also add the window to the stack
       win.show_all()


    def create_account_type_selector(self, type):
       selector = hildon.TouchSelector(text=True)

       # Stock icons will be used for the example
       type_list = ["Twitter", "Identi.ca", "Other"]
       count = 0
       match_found = False
       # Populate model
       for item in type_list:
           selector.append_text(item)
           if (item == type):
               selector.set_active(0, count)
           else:
               count = count + 1

       selector.set_column_selection_mode(hildon.TOUCH_SELECTOR_SELECTION_MODE_SINGLE)
       return selector

    def changed_account_type(self, selector, user_data, serviceUrl, searchUrl, account):
       selected = selector.get_current_text()
       if (selected == "Twitter"):
           serviceUrl.set_text("https://twitter.com/")
           searchUrl.set_text("https://search.twitter.com/")
           account.servicename = "Twitter"
       elif(selected == "Identi.ca"):
           account.servicename = "Identi.ca"
           serviceUrl.set_text("http://identi.ca/api/")
           searchUrl.set_text("http://identi.ca/api/")
       else:
           account.servicename = "Other"
           serviceUrl.set_text("Enter Twitter compatible base url")
           searchUrl.set_text("Enter Twitter Compatible search url")
       account.baseUrl = serviceUrl.get_text()
       account.searchUrl = searchUrl.get_text()


    def changed_username(self, widget, account):
        account.username = widget.get_text()

    def changed_password(self, widget, account):
        account.password = widget.get_text()

    def changed_base_url(self, widget, account):
        account.baseUrl = widget.get_text()

    def changed_search_url(self, widget, account):
        account.searchUrl = widget.get_text()

    def finished_account_edit(self, widget):
        stack = hildon.WindowStack.get_default()
        stack.pop(1)
        self.show_account_window(widget)
        self.controller.activeAccount.connect()

    def setActiveAccount(self, widget, selector, accList):
        selected = selector.get_current_text()
        for account in accList:
            if (re.search(account.username, selected)):
                if(re.search(account.servicename, selected)):
                   account.status = account.ACTIVE
                   self.controller.setActiveAccount(account)
                else:
                   account.status = account.INACTIVE
            else:
                account.status = account.INACTIVE
        stack = hildon.WindowStack.get_default()
        stack.pop(1)
        self.show_account_window(widget)


    def deleteAccount(self, widget, selector, accList):
        selected = selector.get_current_text()
        for account in accList:
            if (re.search(account.username, selected)):
                if(re.search(account.servicename, selected)):
                   if (account.status == account.ACTIVE):
                       #can't delete the active account
                       note = osso.SystemNote(self.controller.osso_c)
                       note.system_note_dialog("Can't delete the active account")
                   else:
                       self.controller.deleteAccount(account)

        stack = hildon.WindowStack.get_default()
        stack.pop(1)
        self.show_account_window(widget)

    def setWindowTitlePrefix(self, prefix):
        self.serviceName = prefix

    def setWindowTitle(self, title):
        self.window.set_title(title)

    def reload_account_window(self, widget, account):
        stack = hildon.WindowStack.get_default()
        stack.pop(1)
        self.edit_account_details(widget, account)

    def select_theme(self, widget, selector):
        self.select_ui_theme(selector.get_current_text())

    def select_ui_theme(self, theme_name):

        self.theme = theme_name
        self.load_theme_icons()
        curView = self.getCurrentView()
        if (curView == self.TIMELINE_VIEW):
            self.switch_view_to("timeline")
        elif (curView == self.DM_VIEW):
            self.switch_view_to("direct")
        elif (curView == self.MENTIONS_VIEW):
            self.switch_view_to("mentions")
        elif (curView == self.PUBLIC_VIEW):
            self.switch_view_to("public")
        elif (curView == self.TRENDS_VIEW):
            rself.switch_view_to("trends")
        elif (curView == self.FRIENDS_VIEW):
            self.switch_view_to("friends")
        elif (curView == self.SEARCH_VIEW):
            self.switch_view_to("search")
        elif (curView == self.USERHIST_VIEW):
            self.switch_view_to("user")
    
    def hide_portrait_keyboard(self):
        vbox1 = self.builder.get_object("qwerty1")
        vbox1.hide_all()  
        
              
    def show_portrait_keyboard(self):
        
        print "display portrait keyboard"        
        vbox1 = self.builder.get_object("qwerty1")
        vbox1.show_all()
    def text_entry_selected(self, widget,*args):
        if (self.orientation == "portrait"):  
            self.show_portrait_keyboard()
            
    def text_entry_deselected(self, widget, *args):
        if (self.orientation == "portrait"):  
            self.hide_portrait_keyboard()

    def define_portrait_keyboard(self):
        vbox1 = self.builder.get_object("qwerty1")
        hbox1 = gtk.HBox(homogeneous=True)
        hbox2 = gtk.HBox(homogeneous=True)
        hbox3 = gtk.HBox(homogeneous=True)
        hbox4 = gtk.HBox()
        buttons = vbox1.get_children()
        for button in buttons:
            button.destroy()
            
        q = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        q.set_title('q')
        q.connect("clicked", self.TypeLetter, "q")
        w = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        w.set_title('w')
        w.connect("clicked", self.TypeLetter, "w")   
        e = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        e.set_title('e')
        e.connect("clicked", self.TypeLetter, "e")   
        r = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        r.set_title('r')
        r.connect("clicked", self.TypeLetter, "r")   
        t = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        t.set_title('t')
        t.connect("clicked", self.TypeLetter, "t")   
        y = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        y.set_title('y')
        y.connect("clicked", self.TypeLetter, "y")   
        u = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        u.set_title('u')
        u.connect("clicked", self.TypeLetter, "u")   
        i = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        i.set_title('i')
        i.connect("clicked", self.TypeLetter, "i")   
        o = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        o.set_title('o')
        o.connect("clicked", self.TypeLetter, "o")   
        p = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        p.set_title('p')
        p.connect("clicked", self.TypeLetter, "p")   
        
        
        a = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        a.set_title('a')
        a.connect("clicked", self.TypeLetter, "a")   
        s = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        s.set_title('s')
        s.connect("clicked", self.TypeLetter, "s")   
        d = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        d.set_title('d')
        d.connect("clicked", self.TypeLetter, "d")   
        f = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        f.set_title('f')
        f.connect("clicked", self.TypeLetter, "f")   
        g = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        g.set_title('g')
        g.connect("clicked", self.TypeLetter, "g")   
        h = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        h.set_title('h')
        h.connect("clicked", self.TypeLetter, "h")   
        j = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        j.set_title('j')
        j.connect("clicked", self.TypeLetter, "j")   
        k = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        k.set_title('k')
        k.connect("clicked", self.TypeLetter, "k")   
        l = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        l.set_title('l')
        l.connect("clicked", self.TypeLetter, "l")   
        z = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        z.set_title('z')
        z.connect("clicked", self.TypeLetter, "z")   
        x = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        x.set_title('x')
        x.connect("clicked", self.TypeLetter, "x")   
        c = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        c.set_title('c')
        c.connect("clicked", self.TypeLetter, "c")   
        v = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        v.set_title('v')
        v.connect("clicked", self.TypeLetter, "v")   
        b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        b.set_title('b')
        b.connect("clicked", self.TypeLetter, "b")   
        n = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        n.set_title('n')
        n.connect("clicked", self.TypeLetter, "n")   
        m = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        m.set_title('m')
        m.connect("clicked", self.TypeLetter, "m")   
        space = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        space.set_title('Space')
        space.connect("clicked", self.TypeLetter, " ")
        shift = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        shift.set_title('Shift')
        shift.connect("clicked", self.show_uppercase_keyboard)   
        delete = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        delete.set_title('Del')
        delete.connect("clicked", self.TypeLetter, "*delete*") 
        At = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        At.set_title('@')
        At.connect("clicked", self.TypeLetter, "@")
        hash= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        hash.set_title('#')
        hash.connect("clicked", self.TypeLetter, "#")
        stop= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        stop.set_title('.')
        stop.connect("clicked", self.TypeLetter, ".")
        comma= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        comma.set_title(',')
        comma.connect("clicked", self.TypeLetter, ",")
        numbers= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        numbers.set_title('123')
        numbers.connect("clicked", self.show_number_keyboard)
        hbox1.pack_start(q, expand=True)
        hbox1.pack_start(w, expand=True)
        hbox1.pack_start(e, expand=True)
        hbox1.pack_start(r, expand=True)
        hbox1.pack_start(t, expand=True)
        hbox1.pack_start(y, expand=True)
        hbox1.pack_start(u, expand=True)
        hbox1.pack_start(i, expand=True)
        hbox1.pack_start(o, expand=True)
        hbox1.pack_start(p, expand=True)
        hbox2.pack_start(a, expand=True)
        hbox2.pack_start(s, expand=True)
        hbox2.pack_start(d, expand=True)
        hbox2.pack_start(f, expand=True)
        hbox2.pack_start(g, expand=True)
        hbox2.pack_start(h, expand=True)
        hbox2.pack_start(j, expand=True)
        hbox2.pack_start(k, expand=True)
        hbox2.pack_start(l, expand=True)
        
        hbox3.pack_start(z, expand=True)
        hbox3.pack_start(x, expand=True)
        hbox3.pack_start(c, expand=True)
        hbox3.pack_start(v, expand=True)
        hbox3.pack_start(b, expand=True)
        hbox3.pack_start(n,  expand=True)
        hbox3.pack_start(m, expand=True)
        hbox3.pack_start(delete,expand=True)
        hbox4.pack_start(shift, expand=True)
        hbox4.pack_start(hash, expand=True)
        hbox4.pack_start(At, expand=True)
        hbox4.pack_start(space, expand=True)
        hbox4.pack_start(stop, expand=True)
        hbox4.pack_start(comma, expand=True)
        hbox4.pack_start(numbers, expand=True)
        vbox1.pack_start(hbox1, expand=False)
        vbox1.pack_start(hbox2, expand=False)
        vbox1.pack_start(hbox3, expand=False)
        vbox1.pack_start(hbox4, expand=False)
        vbox1.hide_all()
        
    def TypeLetter(self, widget,  letter):
        #get the position of the current cursor
        pos = self.tweetText.get_position()
        #get the current text string
        text = self.tweetText.get_text()
        #if passed special delete eye catcher we are actually deleteing characters
        if (letter =="*delete*"):
            
            self.tweetText.set_text(text[0:pos-1]+text[pos:len(text)])
            self.setCursorAt(pos-1);
        else:
            #normal entry of text at the selected pos
            self.tweetText.set_text(text[0:pos]+letter+text[pos:len(text)])
            self.setCursorAt(pos+1);
        
    def show_uppercase_keyboard(self, widget):
        print "shift to uppercase"
        self.set_keyboard_uppercase()
        
        self.show_portrait_keyboard()    
    
    def show_lowercase_keyboard(self, widget):
        print "shift to lowercase"
        self.define_portrait_keyboard()
        self.show_portrait_keyboard()
    def show_number_keyboard(self, widget):
        print "shift to lowercase"
        self.define_number_keyboard()
        self.show_portrait_keyboard()
        
    def set_keyboard_uppercase(self):
        #set the keyboard to do uppercase letters
        print "setting keyboard to upper case"
        vbox1 = self.builder.get_object("qwerty1")
        hbox1 = gtk.HBox(homogeneous=True)
        hbox2 = gtk.HBox(homogeneous=True)
        hbox3 = gtk.HBox(homogeneous=True)
        hbox4 = gtk.HBox()
        buttons = vbox1.get_children()
        for button in buttons:
            button.destroy()
            
        q = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        q.set_title('Q')
        q.connect("clicked", self.TypeLetter, "Q")
        w = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        w.set_title('W')
        w.connect("clicked", self.TypeLetter, "W")   
        e = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        e.set_title('E')
        e.connect("clicked", self.TypeLetter, "E")   
        r = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        r.set_title('R')
        r.connect("clicked", self.TypeLetter, "R")   
        t = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        t.set_title('T')
        t.connect("clicked", self.TypeLetter, "T")   
        y = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        y.set_title('Y')
        y.connect("clicked", self.TypeLetter, "Y")   
        u = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        u.set_title('U')
        u.connect("clicked", self.TypeLetter, "U")   
        i = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        i.set_title('I')
        i.connect("clicked", self.TypeLetter, "I")   
        o = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        o.set_title('O')
        o.connect("clicked", self.TypeLetter, "O")   
        p = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        p.set_title('P')
        p.connect("clicked", self.TypeLetter, "P")   
        
        
        a = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        a.set_title('A')
        a.connect("clicked", self.TypeLetter, "A")   
        s = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        s.set_title('S')
        s.connect("clicked", self.TypeLetter, "S")   
        d = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        d.set_title('D')
        d.connect("clicked", self.TypeLetter, "D")   
        f = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        f.set_title('F')
        f.connect("clicked", self.TypeLetter, "F")   
        g = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        g.set_title('G')
        g.connect("clicked", self.TypeLetter, "G")   
        h = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        h.set_title('H')
        h.connect("clicked", self.TypeLetter, "H")   
        j = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        j.set_title('J')
        j.connect("clicked", self.TypeLetter, "J")   
        k = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        k.set_title('K')
        k.connect("clicked", self.TypeLetter, "K")   
        l = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        l.set_title('L')
        l.connect("clicked", self.TypeLetter, "L")   
        z = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        z.set_title('Z')
        z.connect("clicked", self.TypeLetter, "Z")   
        x = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        x.set_title('X')
        x.connect("clicked", self.TypeLetter, "X")   
        c = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        c.set_title('C')
        c.connect("clicked", self.TypeLetter, "C")   
        v = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        v.set_title('V')
        v.connect("clicked", self.TypeLetter, "V")   
        b = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        b.set_title('B')
        b.connect("clicked", self.TypeLetter, "B")   
        n = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        n.set_title('N')
        n.connect("clicked", self.TypeLetter, "N")   
        m = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        m.set_title('M')
        m.connect("clicked", self.TypeLetter, "M")   
        space = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        space.set_title('Space')
        space.connect("clicked", self.TypeLetter, " ")
        shift = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        shift.set_title('Shift')
        shift.connect("clicked", self.show_lowercase_keyboard)   
        delete = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        delete.set_title('Del')
        delete.connect("clicked", self.TypeLetter, "*delete*") 
        At = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        At.set_title('@')
        At.connect("clicked", self.TypeLetter, "@")
        hash= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        hash.set_title('#')
        hash.connect("clicked", self.TypeLetter, "#")
        stop= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        stop.set_title('.')
        stop.connect("clicked", self.TypeLetter, ".")
        comma= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        comma.set_title(',')
        comma.connect("clicked", self.TypeLetter, ",")
        numbers= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        numbers.set_title('123')
        numbers.connect("clicked", self.show_number_keyboard)
        hbox1.pack_start(q, expand=True)
        hbox1.pack_start(w, expand=True)
        hbox1.pack_start(e, expand=True)
        hbox1.pack_start(r, expand=True)
        hbox1.pack_start(t, expand=True)
        hbox1.pack_start(y, expand=True)
        hbox1.pack_start(u, expand=True)
        hbox1.pack_start(i, expand=True)
        hbox1.pack_start(o, expand=True)
        hbox1.pack_start(p, expand=True)
        hbox2.pack_start(a, expand=True)
        hbox2.pack_start(s, expand=True)
        hbox2.pack_start(d, expand=True)
        hbox2.pack_start(f, expand=True)
        hbox2.pack_start(g, expand=True)
        hbox2.pack_start(h, expand=True)
        hbox2.pack_start(j, expand=True)
        hbox2.pack_start(k, expand=True)
        hbox2.pack_start(l, expand=True)
        
        hbox3.pack_start(z, expand=True)
        hbox3.pack_start(x, expand=True)
        hbox3.pack_start(c, expand=True)
        hbox3.pack_start(v, expand=True)
        hbox3.pack_start(b, expand=True)
        hbox3.pack_start(n,  expand=True)
        hbox3.pack_start(m, expand=True)
        hbox3.pack_start(delete,expand=True)
        hbox4.pack_start(shift, expand=True)
        hbox4.pack_start(hash, expand=True)
        hbox4.pack_start(At, expand=True)
        hbox4.pack_start(space, expand=True)
        hbox4.pack_start(stop, expand=True)
        hbox4.pack_start(comma, expand=True)
        hbox4.pack_start(numbers,expand=True)
        vbox1.pack_start(hbox1, expand=False)
        vbox1.pack_start(hbox2, expand=False)
        vbox1.pack_start(hbox3, expand=False)
        vbox1.pack_start(hbox4, expand=False)
        vbox1.hide_all()
        
    def define_number_keyboard(self):
        #set the keyboard to do uppercase letters
        print "setting keyboard to numbers"
        vbox1 = self.builder.get_object("qwerty1")
        hbox1 = gtk.HBox(homogeneous=True)
        hbox2 = gtk.HBox(homogeneous=True)
        hbox3 = gtk.HBox(homogeneous=True)
        hbox4 = gtk.HBox()
        buttons = vbox1.get_children()
        for button in buttons:
            button.destroy()
            
        one = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        one.set_title('1')
        one.connect("clicked", self.TypeLetter, "1")
        two = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        two.set_title('2')
        two.connect("clicked", self.TypeLetter, "2")   
        three = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        three.set_title('3')
        three.connect("clicked", self.TypeLetter, "3")   
        four = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        four.set_title('4')
        four.connect("clicked", self.TypeLetter, "4")   
        five = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        five.set_title('5')
        five.connect("clicked", self.TypeLetter, "5")   
        six = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        six.set_title('6')
        six.connect("clicked", self.TypeLetter, "6")   
        seven = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        seven.set_title('7')
        seven.connect("clicked", self.TypeLetter, "7")   
        eight = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        eight.set_title('8')
        eight.connect("clicked", self.TypeLetter, "8")   
        nine = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        nine.set_title('9')
        nine.connect("clicked", self.TypeLetter, "9")   
        zero = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        zero.set_title('0')
        zero.connect("clicked", self.TypeLetter, "0")
        colon = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        colon.set_title(':')
        colon.connect("clicked", self.TypeLetter, ":") 
        semicolon = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        semicolon.set_title(';')
        semicolon.connect("clicked", self.TypeLetter, ";") 
        apost = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        apost.set_title('\'')
        apost.connect("clicked", self.TypeLetter, "\'")
        amp = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        amp.set_title('&')
        amp.connect("clicked", self.TypeLetter, "&")  
        exclam = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        exclam.set_title('!')
        exclam.connect("clicked", self.TypeLetter, "!")
        slash = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        slash.set_title('/')
        slash.connect("clicked", self.TypeLetter, "/")
        quest = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
       
        quest.set_title('?')
        quest.connect("clicked", self.TypeLetter, "?")
        space =hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        
        space.set_title('Space')
        space.connect("clicked", self.TypeLetter, " ")
        
        delete = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        delete.set_title('Del')
        delete.connect("clicked", self.TypeLetter, "*delete*") 
        At = hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        At.set_title('@')
        At.connect("clicked", self.TypeLetter, "@")
        hash= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        hash.set_title('#')
        hash.connect("clicked", self.TypeLetter, "#")
        stop= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        stop.set_title('.')
        stop.connect("clicked", self.TypeLetter, ".")
        comma= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        comma.set_title(',')
        comma.connect("clicked", self.TypeLetter, ",")
        letters= hildon.Button(gtk.HILDON_SIZE_FINGER_HEIGHT,
                                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
        letters.set_title('Abc')
        letters.connect("clicked", self.show_lowercase_keyboard)
        hbox1.pack_start(one, expand=True)
        hbox1.pack_start(two, expand=True)
        hbox1.pack_start(three, expand=True)
        hbox1.pack_start(four, expand=True)
        hbox1.pack_start(five, expand=True)
        hbox1.pack_start(six, expand=True)
        hbox1.pack_start(seven, expand=True)
        hbox1.pack_start(eight, expand=True)
        hbox1.pack_start(nine, expand=True)
        hbox1.pack_start(zero, expand=True)
        hbox2.pack_start(colon,expand=True)
        hbox2.pack_start(semicolon,expand=True)
        hbox2.pack_start(apost,expand=True)
        hbox2.pack_start(amp,expand=True)
        hbox2.pack_start(exclam,expand=True)
        hbox2.pack_start(slash,expand=True)
        hbox2.pack_start(quest,expand=True)
        hbox3.pack_start(delete,expand=True)
        hbox4.pack_start(hash, expand=True)
        hbox4.pack_start(At, expand=True)
        hbox4.pack_start(space, expand=True)
        hbox4.pack_start(stop, expand=True)
        hbox4.pack_start(comma, expand=True)
        hbox4.pack_start(letters,expand=True)
        vbox1.pack_start(hbox1, expand=False)
        vbox1.pack_start(hbox2, expand=False)
        vbox1.pack_start(hbox3, expand=False)
        vbox1.pack_start(hbox4, expand=False)
        vbox1.hide_all()
