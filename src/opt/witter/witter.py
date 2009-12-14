#!/usr/bin/env python2.5
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
# Name        : witter.py
# Author      : Daniel Would
# Version     : 0.1
# Description : Witter
# ============================================================================

#This is the bunch of things I wound up importing
#I think I need them all.. 
import gtk
import pygtk
import hildon
import urllib2
import urllib
import mimetools, mimetypes
import base64
import urlparse
import simplejson
import socket
import re
import string
import osso
import os
import webbrowser
import ConfigParser
import pycurl


import random
import witter
import time

gtk.gdk.threads_init()



#Initially I found I'd hang the whole interface if I was having network probs
#because by default there is an unlimited wait on connect so I set
#the timeout to 10 seconds afterwhich you get back a timeout error
# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

#the main witter application
class Witter():
    #first an init method to set everything up    
    def __init__(self):
	#defaults for auto-refresh
	self.timelineRefreshInterval = 30
	self.mentionsRefreshInterval = 30
	
	self.DMsRefreshInterval = 30
	self.publicRefreshInterval = 0
	self.searchRefreshInterval = 0
	self.search_terms = ""
	self.refreshtask = None
	self.dmresfresh = None
	self.mentionrefresh = None
	self.publicrefresh = None
	self.searchrefresh = None
	self.username = "UserName"
	self.password = ""
	
	#make the hildon program
        self.program = hildon.Program()
        self.program.__init__()

        self.osso_c = osso.Context("witter","0.1.1", False) 
        # set name of application: this shows in titlebar
        gtk.set_application_name("Witter")
        self.twitterUrlRoot = "http://twitter.com/"
        self.twitterSearchUrlRoot = "http://search.twitter.com/"
        self.twitterName = "Witter"
        self.identicaUrlRoot = "http://identi.ca/api/"
        self.identicaSearchUrlRoot = "http://identi.ca/api/"
        self.identicaName = "Witti.ca"
        self.serviceUrlRoot = self.twitterUrlRoot
        self.searchServiceUrlRoot = self.twitterSearchUrlRoot
        self.serviceName = self.twitterName
	 #used to store the id of message if we're going to do a reply_to
        self.reply_to=None
        self.reply_to_name=None
	self.retweetname=None
	self.retweetid=None
        #Set the Glade file
       # self.gladefile = "/usr/share/witter/witter.glade"  
        #self.wTree = gtk.glade.XML(self.gladefile) 
        self.builder = gtk.Builder()
        self.builder.add_from_file("/usr/share/witter/witter.ui") 
        #map all the signals
        dic = { 
            "newTweet" : self.enterPressed,
            "getTweets" : self.updateSelectedView,
            "storecreds" : self.store_creds,
            "on_timeline_clicked" : self.switchView,
            "on_mentions_clicked" : self.switchView,
            "on_direct_messages_clicked" : self.switchView,
            "on_search_clicked" : self.switchView,
            "on_trend_clicked" : self.switchView,
            "on_insert_clicked" : self.twitPic,
            "on_friends_clicked" : self.switchView,
	    "setProps" : self.setProps,
	    "nosetProps" : self.dontsetProps,
        }
        self.builder.connect_signals(dic)
        #self.wTree.signal_autoconnect( dic )
	
	#fix the buttons to get the style right 
        refreshButton = self.builder.get_object("Refresh")
	tweetButton = self.builder.get_object("Tweet")
	timelineButton = self.builder.get_object("timeline")
	mentionsButton = self.builder.get_object("mentions")
	dmsButton = self.builder.get_object("direct messages")
	searchButton = self.builder.get_object("search")
	friendsButton = self.builder.get_object("friends")
	okButton = self.builder.get_object("Ok")
	cancelButton = self.builder.get_object("Cancel")
	propscancelButton = self.builder.get_object("props-cancel")
	refreshstoreButton = self.builder.get_object("refresh_store")
	refreshButton.set_name("HildonButton-finger")
	tweetButton.set_name("HildonButton-finger")
	timelineButton.set_name("HildonButton-finger")
	mentionsButton.set_name("HildonButton-finger")
	dmsButton.set_name("HildonButton-finger")
	searchButton.set_name("HildonButton-finger")
	friendsButton.set_name("HildonButton-finger")
	okButton.set_name("HildonButton-finger")
	cancelButton.set_name("HildonButton-finger")
	propscancelButton.set_name("HildonButton-finger")
	refreshstoreButton.set_name("HildonButton-finger")
	
	self.textcolour="#FFFFFF"
        #
        #go read config file
        #
        self.readConfig()
        #being lazy this just uses basic auth and I am not doing anything
        #yet to store uid/pwd so for the moment just put info here
        
        
        #at one point I had the text different colours
        #I may do again
        self.namecolour = self.textcolour
        self.tweetcolour = self.textcolour
        
        self.defaultwidth = 790
        #default to colours above, but check if we're on fremantle and change
        #to appropriate colours if we are
        self.checkVersion()
        #This being a hildon app we start with a hildon.Window
        self.window = hildon.StackableWindow()

        #connect the delete event for closing the window
        self.window.connect("delete_event", self.quit)
        #we default to the timeline view
        self.window.set_title(self.serviceName +" - timeline")
        #add window to self  
        self.program.add_window(self.window)
        #reparent the vbox1 from glade to self.window
        # self.vbox = self.wTree.get_widget("vbox1")
        self.vbox = self.builder.get_object("vbox1")
        #pannedWindow = hildon.PannableArea()
	pannedWindow = self.builder.get_object("pannableArea")
        # hildon.hildon_pannable_area_new_full(mode, enabled, vel_min, vel_max, decel, sps)

        #self.scrolled_window = self.wTree.get_widget("scrolled_window")
        self.vbox.reparent(self.window)
        #self.vbox.pack_end(pannedWindow)
        
        self.urlmenu = self.build_right_click_menu()
        # create a menu object by calling a method to deine it
        self.menu = self.create_m5_menu(self)
        # add the menu to the window
        self.window.set_app_menu(self.menu)
        #
        
        
        self.last_id=None
        self.last_dm_id=None
        self.last_mention_id=None
        self.last_public_id=None
        
        #self.urlmenu = gtk.Menu()
        # define a liststore we use this to store our tweets and some associated data
        # the fields are : Name,nameColour,Tweet+Timestamp,TweetColour,id, type
        self.liststore = gtk.ListStore(str, str, str, str, str, str)
        #then we want the same again to store dm's, mentions & pubilc timeline separately
        self.dmliststore = gtk.ListStore(str, str, str, str, str, str)
        self.mentionliststore = gtk.ListStore(str, str, str, str, str, str)
        self.publicliststore= gtk.ListStore(str, str, str, str, str, str)
        self.trendliststore= gtk.ListStore(str, str, str, str)
        self.friendsliststore = gtk.ListStore(str,str,str,str,str,str)
        self.searchliststore = gtk.ListStore(str,str,str,str,str,str)
        #we want auto-complete of @references 
        #self.tweetText = self.wTree.get_widget("TweetText")
        self.tweetText = self.builder.get_object("TweetText")
	self.tweetText.connect("changed", self.CharsRemaining)
        tweetComplete = gtk.EntryCompletion()
        tweetComplete.set_model(self.friendsliststore)
        tweetComplete.set_text_column(0)
        tweetComplete.set_inline_completion(True)
        tweetComplete.set_minimum_key_length(2)
        self.tweetText.set_completion(tweetComplete)
        
        # create the TreeView using treestore this is the object which displays the
        # info stored in the liststore
        self.treeview = gtk.TreeView(self.liststore)
	#self.treeview = hildon.hildon_gtk_tree_view_new(self.liststore)
        self.treeview.set_model(self.liststore)
        # create the TreeViewColumn to display the data, I decided on two colums
        # one for name and the other for the tweet
        #self.tvcname = gtk.TreeViewColumn('Name')
        #cell = witter.witter_cell_renderer.witterCellRender()
	cell = gtk.CellRendererText()
        cell.set_property('background',"#6495ED")
	
	self.tvctweet = gtk.TreeViewColumn('Pango Markup', cell, markup=2)

        #self.tvctweet = gtk.TreeViewColumn('Tweet')
        # add the two tree view columns to the treeview
        #self.treeview.append_column(self.tvcname)
        self.treeview.append_column(self.tvctweet)
        # we need a CellRendererText to render the data
        
        # add the cell renderer to the columns
        #self.tvcname.pack_start(cell, True)
        #self.tvctweet.pack_start(cell,True)
        # set the cell "text" attribute to column 0 - retrieve text
        # from that column in liststore and treat it as the text to render
        # in this case it's the name of a tweeter
        #self.tvcname.add_attribute(self.cell, 'text', 0)
        # we then use the second field of our liststore to hold the colour for
        # the 'name' text
        #self.tvcname.add_attribute(self.cell, 'foreground', 1)
        # next we add a mapping to the tweet column, again the third field
        # in our list store is the tweet text
        self.tvctweet.add_attribute(cell, 'text',2)
        # and the fourth is the colour of the tweet text 
        #self.tvctweet.add_attribute(cell, 'foreground', 3)
        # we start up non-fullscreen, and we want the tweets to appear without
        # scrolling left-right (well I wanted that) so I set a wrap width for
        # the text being rendered
        cell.set_property('wrap-width', self.defaultwidth)
        # make it searchable (I found this in an example and thought I might use it
        # but currently I make no use of this setting
        self.treeview.set_search_column(2)
        self.treeview.set_rules_hint(True)
       
        self.treeview.set_property('enable-grid-lines',True)
        # Allow sorting on the column. This is cool because no matter what order
        # we load tweets in, we always get a view which is sorted by the tweet id which
        # always increments, so we get them in order
        
        self.liststore.set_sort_column_id(4,gtk.SORT_DESCENDING)
        self.dmliststore.set_sort_column_id(4,gtk.SORT_DESCENDING)
        self.mentionliststore.set_sort_column_id(4,gtk.SORT_DESCENDING)
        self.publicliststore.set_sort_column_id(4,gtk.SORT_DESCENDING)
        self.searchliststore.set_sort_column_id(4,gtk.SORT_DESCENDING)
        #want to order the friends list by name
        self.friendsliststore.set_sort_column_id(0,gtk.SORT_ASCENDING)
        # I don't want to accidentally be dragging and dropping rows out of order
        self.treeview.set_reorderable(False)
        #with all that done I add the treeview to the scrolled window
        pannedWindow.add_with_viewport(self.treeview)
        #self.treeview.connect("button-press-event", self.build_menu, None);
        selection = self.treeview.get_selection()
        selection.connect('changed', self.build_menu)

        # self.treeview.connect("changed", self.build_menu, None);
        self.treeview.tap_and_hold_setup(self.urlmenu, callback=gtk.tap_and_hold_menu_position_top)
	#init the configDialog
	self.configDialog = None
        if (re.search("UserName",self.username)):
	       self.promptForCredentials() 
	#call the refresh thread
	self.gettingTweets = False
	self.start_refresh_threads()
	       
        
    def quit(self, *args):
        #this is our end method called when window is closed
        print "Stop Wittering"
	print "shutting down refresh loop"
	self.writeConfig()
	self.end_refresh_threads()
	
        gtk.main_quit()
       
    def create_menu(self, widget):
        #a fairly standard menu create
        #I put in the same options as I have buttons
        # and linked to the same methods
        menu = gtk.Menu()
  
        menuItemGetTweets = gtk.MenuItem("Get Tweets")
        menuItemGetTweets.connect("activate", self.getTweets )
        menuItemTweet = gtk.MenuItem("Tweet")
        menuItemTweet.connect("activate",self.newTweet)
        menuItemTwitPic = gtk.MenuItem("TwitPic")
        menuItemTwitPic.connect("activate", self.selectImage)
        menuItemTrends = gtk.MenuItem("Trends")
        menuItemTrends.connect("activate", self.switchViewTo, "trends")
        menuItemPublic = gtk.MenuItem("Public")
        menuItemPublic.connect("activate", self.switchViewTo, "public")
        menuItemCreds = gtk.MenuItem("Set UID/PWD")
        menuItemCreds.connect("activate",self.promptForCredentials)
        menuItemInvert = gtk.MenuItem("Invert Text")
        menuItemInvert.connect("activate",self.flipTextColour)
        menuItemSeparator = gtk.SeparatorMenuItem()
        menuItemExit = gtk.MenuItem("Exit")
        menuItemExit.connect("activate", self.quit);
                
        menu.append(menuItemGetTweets)
        menu.append(menuItemTweet)
        menu.append(menuItemTwitPic)
        menu.append(menuItemTrends)
        menu.append(menuItemPublic)
        menu.append(menuItemSeparator)
        menu.append(menuItemCreds)
        menu.append(menuItemExit)
        
        menuItemFile = gtk.MenuItem("File")
        menuItemFile.set_submenu(menu)
        return menu

 
    def create_m5_menu(self, widget):
        #a fairly standard menu create
        #I put in the same options as I have buttons
        # and linked to the same methods
        menu = hildon.AppMenu()

        GetTweets = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        command_id = "Get Tweets"
        GetTweets.set_label(command_id)
        # Attach callback to clicked signal
        GetTweets.connect("clicked", self.getTweets)
        GetTweets.show()
        menu.append(GetTweets)
        Tweets = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Tweets.set_label("Tweet")
        # Attach callback to clicked signal
        Tweets.connect("clicked", self.newTweet)
        Tweets.show()
        menu.append(Tweets)
        
        TwitPic = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        TwitPic.set_label("TwitPic!")
        # Attach callback to clicked signal
        TwitPic.connect("clicked", self.selectImage)
        TwitPic.show()
        menu.append(TwitPic)
        
        Trends = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Trends.set_label("Trends")
        # Attach callback to clicked signal
        Trends.connect("clicked", self.switchViewTo, "trends")
        Trends.show()
        menu.append(Trends)
        
        Public = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Public.set_label("Public")
        # Attach callback to clicked signal
        Public.connect("clicked", self.switchViewTo, "public")
        Public.show()
        menu.append(Public)
        
        Creds = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Creds.set_label("Set UID/PWD")
        # Attach callback to clicked signal
        Creds.connect("clicked", self.promptForCredentials)
        Creds.show()
        menu.append(Creds)
        
        Service = hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Service.set_label("Toggle ServiceType")
        # Attach callback to clicked signal
        Service.connect("clicked", self.switchService)
        Service.show()
        menu.append(Service)
	
	Properties= hildon.GtkButton(gtk.HILDON_SIZE_AUTO)
        Properties.set_label("Properties")
        # Attach callback to clicked signal
        Properties.connect("clicked", self.configProperties)
        Properties.show()
        menu.append(Properties)
	
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
 
    def run(self):     
        #this is the main execution method
        # we set things visible, connect a couple of event hooks to methods
        # specifically to handle switching in and our of fullscreen
        self.window.show_all()
        self.window.connect("key-press-event", self.on_key_press)
        self.window.connect("window-state-event", self.on_window_state_change)
	
        #this starts everything up
        gtk.main() 
	
        
    def updateSelectedView(self, *args):
        #call the get method for whichever liststore we're viewing
        if (self.treeview.get_model() == self.liststore):
            self.getTweets()
        elif (self.treeview.get_model() == self.dmliststore):
            self.getDMs()
        elif (self.treeview.get_model() == self.mentionliststore):
            self.getMentions()
        elif (self.treeview.get_model() == self.publicliststore):
            self.getPublic()
        elif (self.treeview.get_model() == self.trendliststore):
            self.getTrends()
        elif (self.treeview.get_model() == self.friendsliststore):
            self.getFriends()
        elif (self.treeview.get_model() == self.searchliststore):
            self.getSearch()
            
    def getTweets(self, auto=0, *args):
	self.gettingTweets = True
        print "getting tweets"
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.serviceUrlRoot+'statuses/friends_timeline.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        #switch on whether this is an refresh or a first download
        try:
    
            if self.last_id == None:
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/friends_timeline.json')
            else:
                #basically the twitter API will respond with just tweets newer than the ID we send
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/friends_timeline.json?since_id='+str(self.last_id)+'L')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
	    [self.getStatus(x['user'],x['text'], x['id'], x['created_at'],x['in_reply_to_screen_name'], x['in_reply_to_status_id'], "tweet") for x in data]
	    #hildon.hildon_banner_show_information(self.window,"","Tweets Received")
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("Tweets Received")
	    self.gettingTweets = False
        except IOError, e:
	    print "error"
            msg = 'Error retrieving tweets '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
	    if (auto==0):
		    note = osso.SystemNote(self.osso_c)
		    note.system_note_dialog(msg, type='notice')

	    self.gettingTweets = False

          
        
    def getDMs(self, auto=0, *args):
	self.gettingTweets = True
        print "getting DMs"
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.serviceUrlRoot+'direct_messages.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        try:
            #switch on whether this is an refresh or a first download
            if self.last_dm_id == None:
                json = urllib2.urlopen(self.serviceUrlRoot+'direct_messages.json')
            else:
                json = urllib2.urlopen(self.serviceUrlRoot+'direct_messages.json?since_id='+str(self.last_dm_id)+'L')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            [self.getStatus(x['sender'],x['text'], x['id'], x['created_at'],None, None, "dm") for x in data]
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("DMs Received")
	    self.gettingTweets = False
        except IOError, e:
            msg = 'Error retrieving DMs '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
	    if (auto==0):
		    note = osso.SystemNote(self.osso_c)
		    note.system_note_dialog(msg, type='notice')
	    self.gettingTweets = False



    def getMentions(self, auto=0,*args):
	self.gettingTweets = True
        print "getting Mentions"
        
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.serviceUrlRoot+'statuses/mentions.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        try:
            #switch on whether this is an refresh or a first download
            if self.last_mention_id == None:
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/mentions.json')
            else:
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/mentions.json?since_id='+str(self.last_mention_id)+'L')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            [self.getStatus(x['user'],x['text'], x['id'], x['created_at'],x['in_reply_to_screen_name'], x['in_reply_to_status_id'], "mention") for x in data]
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("Mentions Received")
	    self.gettingTweets = False
        except IOError, e:
            msg = 'Error retrieving Mentions '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
	    if (auto==0):
		    note = osso.SystemNote(self.osso_c)
		    note.system_note_dialog(msg, type='notice')
	    self.gettingTweets = False

        
    def getPublic(self, auto=0,*args):
	self.gettingTweets = True
        print "getting Public timeline"
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.serviceUrlRoot+'statuses/public_timeline.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        try:
            #switch on whether this is an refresh or a first download
            if self.last_public_id == None:
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/public_timeline.json')
            else:
                json = urllib2.urlopen(self.serviceUrlRoot+'statuses/public_timeline.json?since_id='+str(self.last_public_id)+'L')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            [self.getStatus(x['user'],x['text'], x['id'], x['created_at'],x['in_reply_to_screen_name'], x['in_reply_to_status_id'], "public") for x in data]
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("Public timeline Received")
	    self.gettingTweets = False
        except IOError, e:
            msg = 'Error retrieving Public timeline '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
	    if(auto==0):	
		    note = osso.SystemNote(self.osso_c)
		    note.system_note_dialog(msg, type='notice')
	    self.gettingTweets = False

            
    def getSearch(self, auto=0,*args):
        print "performing search"
	#clear any previous stuff, currenlty we'll just get one page of search results
        self.searchliststore.clear()
        #overloading the tweet text input as the search criteria
        searchterm = self.builder.get_object("TweetText").get_text()
        if (auto==1):
		#auto search performed frrom the saved search
		searchterm = self.search_terms
		
        #see if we have just an empty string (eg eroneous button press)
        if (searchterm == ""):
            print "nothing to search"
            return
        
        
        #split the tweet text on any comma , 
	
	searchTerms = searchterm.split(",")
	#call search on each of the terms in the search str
	for term in searchTerms:
		term = unicode(term).encode('utf-8')
		#then we need to urlencode so that we can use twitter chars like @ without
		#causing problems
		search = urllib.urlencode({ 'q' : term })
		
		#Now for the main logic...fetching tweets
		#at the moment I'm just using basic auth. 
		#urllib2 provides all the HTTP handling stuff
		auth_handler = urllib2.HTTPBasicAuthHandler()
		#realm here is important. or at least it seemed to be
		#this info is on the login box if you go to the url in a browser
		auth_handler.add_password(realm='Twitter API',
				  uri=self.searchServiceUrlRoot+'/search.json',
				  user=self.username,
				  passwd=self.password)
		#we create an 'opener' object with our auth_handler
		opener = urllib2.build_opener(auth_handler)
		# ...and install it globally so it can be used with urlopen.
		urllib2.install_opener(opener)
		
		try:
		    json = urllib2.urlopen(self.searchServiceUrlRoot+'search.json?'+search)
		    
		    #JSON is awesome stuff. we get given a long string of json encoded information
		    #which contains all the tweets, with lots of info, we decode to a json object
		    data = simplejson.loads(json.read())
		    #then this line does all the hard work. Basicaly for evey top level object in the JSON
		    #structure we call out getStatus method with the contents of the USER structure
		    #and the values of top level values text/id/created_at
	  
		    results = data['results']
		    [self.getStatus(x['from_user'],x['text'], x['id'], x['created_at'],None, None, "search") for x in results]
		    note = osso.SystemNote(self.osso_c)

		    result = note.system_note_infoprint("Search results Received for : " + term)
		except IOError, e:
		    msg = 'Error retrieving search results '
		    if hasattr(e, 'reason'):
			    msg = msg + str(e.reason)
			    
		    if hasattr(e, 'code'):
			if (e.code == 401):
			    reason = "Not authorised: check uid/pwd"
			elif(e.code == 503):
			    reason = "Service unavailable"
			else:
			    reason = ""
			msg = msg +'Server returned ' + str(e.code) + " : " + reason
			
		    note = osso.SystemNote(self.osso_c)
		    note.system_note_dialog(msg, type='notice')


            
    def getTrends(self, *args):
        print "getting Trending topics"
        #first clear the previous 10
        self.trendliststore.clear()
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.searchServiceUrlRoot+'trends.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        
        try:
            json = urllib2.urlopen(self.searchServiceUrlRoot+'trends.json')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            trends = data['trends']
            [self.getTrend(x['name'], x['url']) for x in trends]
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("Trends Received")
        except IOError, e:
            msg = 'Error retrieving trends '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
		
	    note = osso.SystemNote(self.osso_c)
	    note.system_note_dialog(msg, type='notice')

            
    def getTrend(self, name, url):
        
        self.trendliststore.append([name, self.namecolour,"<span foreground=\"blue\">"+name+"</span> :"+url,self.tweetcolour])
        
        
    def getFriends(self, *args):
        print "getting Friends"
        #first clear the previous 10
        self.friendsliststore.clear()
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri=self.serviceUrlRoot+'statuses/friends.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        
        try:
            json = urllib2.urlopen(self.serviceUrlRoot+'statuses/friends.json')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            
            for x in data:
                #if we follow someone with no status then you get a key error on status
                try:
                    self.getStatus(x['screen_name'],x['status'], x['id'], x['created_at'],None,None, "friend") 
                except KeyError:
                    print  x
	    note = osso.SystemNote(self.osso_c)

	    result = note.system_note_infoprint("Friends Received")
        except IOError, e:
            msg = 'Error retrieving friends '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
		
	    note = hildon.hildon_note_new_information(self.window, msg)
            note.run()
	    note.destroy()


        
    def getStatus(self, user,data, id, created_at, in_reply_to_screen_name, in_reply_to_id, type):
        #at this point user is another JSON structure of lots more values of which we are currently
        #only interested in screen_name
        #append to our list store the values from the JSON data we've been passed for a tweet
        # the funny #NXNXNX type values are colours I chose a slightly blue for the name
        # and black for the tweet. At some point I intend to do some alternating colours for
        # cell backgrounds to make the display clearer
        if (re.search("tweet", type)):
            if (None != in_reply_to_id):
                print "reply to "+in_reply_to_screen_name
                #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                reply_to = "\n<span size=\"xx-small\">In reply to: "+in_reply_to_screen_name+" - " + self.get_specific_tweet(in_reply_to_screen_name, in_reply_to_id)+"</span>"
            else:
                reply_to=""
            data = data.replace("&","&amp;")
            reply_to = reply_to.replace("&","&amp;")
            self.liststore.append([ "@"+user['screen_name'],self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user['screen_name']+"</b></span> : "+data+"\n<span size=\"xx-small\">posted on: "+created_at+"</span>"+reply_to,self.tweetcolour, id, type])
            #now we process the id, this is so we can do a refresh with just the posts since the latest one we have
            #if we haven't stored the most recent id then store this one
            if self.last_id == None:
                self.last_id=id
            else:
                #if we have an id stored, check if this one is 'newer' if so then store it
                if long(self.last_id) < long(id):
                    self.last_id=id
        elif (re.search("dm", type)):
            data = data.replace("&","&amp;")
            self.dmliststore.append([ "@"+user['screen_name'],self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user['screen_name']+"</b></span> : "+data+"\n<span size=\"xx-small\">posted on: "+created_at+"</span>",self.tweetcolour, id, type])
            if self.last_dm_id == None:
                self.last_dm_id=id
            else:
                #if we have an id stored, check if this one is 'newer' if so then store it
                if long(self.last_dm_id) < long(id):
                    self.last_dm_id=id
        elif (re.search("mention", type)):
            if (None != in_reply_to_id):
                print "reply to "+in_reply_to_screen_name
                #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                reply_to = "\n<span size=\"xx-small\">In reply to: "+in_reply_to_screen_name+" - " + self.get_specific_tweet(in_reply_to_screen_name, in_reply_to_id)+"</span>"
            else:
                reply_to=""
            data = data.replace("&","&amp;")
            reply_to = reply_to.replace("&","&amp;")
            self.mentionliststore.append([ "@"+user['screen_name'],self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user['screen_name']+"</b></span> : "+data+"\n<span size=\"xx-small\">posted on: "+created_at+"</span>"+reply_to,self.tweetcolour, id, type])
            if self.last_mention_id == None:
                self.last_mention_id=id
            else:
                #if we have an id stored, check if this one is 'newer' if so then store it
                if long(self.last_mention_id) < long(id):
                    self.last_mention_id=id
        elif (re.search("public", type)):
            if (None != in_reply_to_id):
                print "reply to "+in_reply_to_screen_name
                #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                reply_to = "\n<span size=\"xx-small\">In reply to: "+in_reply_to_screen_name+" - " + self.get_specific_tweet(in_reply_to_screen_name, in_reply_to_id)+"</span>"
            else:
                reply_to=""
            data = data.replace("&","&amp;")
            reply_to = reply_to.replace("&","&amp;")
            self.publicliststore.append([ "@"+user['screen_name'],self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user['screen_name']+"</b></span> : "+data+"\n<span size=\"xx-small\">posted on: "+created_at+"</span>"+reply_to,self.tweetcolour, id, type])
            if self.last_public_id == None:
                self.last_public_id=id
            else:
                #if we have an id stored, check if this one is 'newer' if so then store it
                if long(self.last_public_id) < long(id):
                    self.last_public_id=id
        elif (re.search("friend", type)):
            text_data = data['text'].replace("&","&amp;")
            self.friendsliststore.append([ "@"+user,self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user+"</b></span> : "+text_data+"\n<span size=\"xx-small\">posted on: "+data['created_at']+"</span>",self.tweetcolour, id, type])
        elif (re.search("search", type)):
            
            data = data.replace("&","&amp;")
            
            self.searchliststore.append([ "@"+user,self.namecolour,"<span foreground=\"#0000FF\"><b>@"+user+"</b></span> : "+data+"\n<span size=\"xx-small\">posted on: "+created_at+"</span>",self.tweetcolour, id, type])
            
                
    def enterPressed(self,widget,*args):
	    #in most views we want to call newTweet, but in search call the getSearch
	    if (self.treeview.get_model() == self.searchliststore):
		self.getSearch()
	    else:
		self.newTweet(self,widget,*args)
	    
    def newTweet(self, widget, *args):
        #The other main need of a twitter client
        #the ability to post an update
        #get the tweet text from the input box
        tweet = self.builder.get_object("TweetText").get_text()
        
        #see if we have just an empty string (eg eroneous button press)
        if (tweet == ""):
            return
        #first we need to encode for utf-8
        tweet = unicode(tweet).encode('utf-8')
                
        if (self.reply_to_name != None):
            if (re.search(self.reply_to_name,tweet)):
                #the tweet text is still a reply to this person
                print "adding reply to information"
                 #we get the text in the input box then we construct the outbound tweet
                
                #then we need to urlencode so that we can use twitter chars like @ without
                #causing problems
                
                post = urllib.urlencode({ 'status' : tweet, 'in_reply_to_status_id' : self.reply_to })
                        
            else:
                #since setting the reply to id the user has removed the reference to the person
                self.reply_to_name = None
                self.reply_to = None
                post = urllib.urlencode({ 'status' : tweet })
        else:
            post = urllib.urlencode({ 'status' : tweet })     
            
       
        #build the request with the url and our post data
        req = urllib2.Request('http://twitter.com/statuses/update.json', post)
        #setup the auth stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm='Twitter API',
                              uri='http://twitter.com/statuses/update.json',
                              user=self.username,
                              passwd=self.password)
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
	try:
		urllib2.install_opener(opener)
		json = urllib2.urlopen(req)
		#opener.close()
		data = simplejson.loads(json.read())
		#message sent, I'm assuming a failure to send would not continue
		#in this method? so it's safe to remove the tweet line
		# what I don't want is to lose the tweet I typed if we didn't
		# sucessfully send it to twitter. that would be annoying (I'm looking
		# at you Mauku)
		self.builder.get_object("TweetText").set_text("")
		hildon.hildon_banner_show_information(self.window,"","Tweet Successful")
		self.reply_to_name = None
		self.reply_to = None
		#last thing to do is refresh main feed
		self.getTweets()
	except IOError, e:
            msg = 'Error posting tweet '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
		
	    note = hildon.hildon_note_new_information(self.window, msg)
            note.run()
	    note.destroy()
        
	
	
        
    def get_specific_tweet(self, screen_name, tweet_id):
        #this method gets an identified tweet from id and screenname
        #Now for the main logic...fetching tweets
        #at the moment I'm just using basic auth. 
        #urllib2 provides all the HTTP handling stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri='http://twitter.com/statuses/show/'+str(tweet_id)+'L.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        
        try:
            
            json = urllib2.urlopen('http://twitter.com/statuses/show/'+str(tweet_id)+'L.json')
            
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            return data['text']
        except IOError, e:
            return "protected tweet"
                
                
    def on_window_state_change(self, widget, event, *args): 
        #this just sets a flag to keep track of what state we're in
       if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN: 
            self.window_in_fullscreen = True 
       else: 
            self.window_in_fullscreen = False 

    def on_key_press(self, widget, event, *args): 
        #this picks up the press of the full screen key and toggles
        #from one mode to the other
       if event.keyval == gtk.keysyms.F6: 
             # The "Full screen" hardware key has been pressed 
             if self.window_in_fullscreen: 
                 self.window.unfullscreen () 
                 #when we toggle off fullscreen set the cell render wrap
                 #to 500
                 self.cell.set_property('wrap-width',self.defaultwidth)
             else: 
                self.window.fullscreen () 
                #when we toggle into fullscreen set the cell render wrap
                #wider
                self.cell.set_property('wrap-width', 630)
                
    def build_right_click_menu(self, *args):
        #build the layout for the right click menu
        urlmenu = gtk.Menu()
        urlmenu.set_title("hildon-context-sensitive-menu")
        self.menuItemURL = gtk.MenuItem("URL actions")
        
        urlmenu.append(self.menuItemURL)
        self.menuItemURL.show()
        #regardless we should provide the option to follow/unfollow/reply to/dm user?
        self.menuItemUserAction = gtk.MenuItem("User Actions")
        
        urlmenu.append(self.menuItemUserAction)
        self.menuItemUserAction.show()
        #unfollow
        self.menuItemReplyTo = gtk.MenuItem("Reply To")
        urlmenu.append(self.menuItemReplyTo)
        self.menuItemReplyTo.show()
	menuItemSeparator = gtk.SeparatorMenuItem()
	urlmenu.append(menuItemSeparator)
        self.menuItemReTweet = gtk.MenuItem("ReTweet")
        urlmenu.append(self.menuItemReTweet)
	self.menuItemReplyTo.connect("activate", self.replyTo)
	self.menuItemReTweet.connect("activate", self.reTweet)
        self.menuItemReTweet.show()
        return urlmenu 
         
    def build_menu(self, widget, *args):
        #a fairly standard menu create
        #I put in the same options as I have buttons
        # and linked to the same methods
        self.menuItemURL.remove_submenu()
        self.menuItemUserAction.remove_submenu()
               
        treeselection = self.treeview.get_selection()
        select1, select2 = treeselection.get_selected_rows()
        #entry1, entry2 = self.treeview.get_selection().get_selected()
        #we might one day have more than on element selected, for now we get 1 row
        try:
            if select2 != None:
                for item in select2[0]:
                    #we want to access field 3 which has or Tweet in it
                    entry = select1.get_value(select1.get_iter(item), 2)
                    #and we might as well list the person who provided the url
                    name = select1.get_value(select1.get_iter(item), 0)
                    id = select1.get_value(select1.get_iter(item), 4)
                    
                if re.search("http", entry): 
                    #convert the string to chunks deliniated on space (we assume the url 
                    #has spaces around it 
                    L = string.split(entry)
                    for word in L :
                        #find the 'word' which is our url
                        if re.search("http", word):
                            url=word
                            menuUrls = gtk.Menu()
                            menuItemLaunchURL = gtk.MenuItem(url)
                            menuItemLaunchURL.connect("activate", self.openBrowser, url )
                            menuUrls.append(menuItemLaunchURL)
                            menuUrls.show()
                            self.menuItemURL.set_submenu(menuUrls)
                            
                    
                menuUserAct = gtk.Menu()        
                menuItemFollowUser = gtk.MenuItem("Follow: "+name)                 
                menuItemFollowUser.connect("activate", self.FollowUser, name)
                menuItemUnFollowUser = gtk.MenuItem("Unfollow: "+name)
                menuItemUnFollowUser.connect("activate", self.UnFollowUser, name)
                menuUserAct.append(menuItemFollowUser)
                menuUserAct.append(menuItemUnFollowUser)
                menuUserAct.show()
                self.menuItemUserAction.set_submenu(menuUserAct)
		self.reply_to = id
		self.reply_to_name= name
                self.retweetname = name
		self.retweetid = id
		
        except IndexError:
            print "nothing selected"
           
     
      
        self.urlmenu.show_all()
        
    
    
    def FollowUser(self, widget, name, *args  ):
        print "follow: " + name
        
        post = urllib.urlencode({ 'screen_name' : name })
                
        #build the request with the url and our post data
        req = urllib2.Request('http://twitter.com/friendships/create.json', post)
        
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        
        auth_handler.add_password(realm='Twitter API',
                          uri='http://twitter.com/friendships/create.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        #switch on whether this is an refresh or a first download
       
        json = urllib2.urlopen(req)
        #JSON is awesome stuff. we get given a long string of json encoded information
        #which contains all the tweets, with lots of info, we decode to a json object
        data = simplejson.loads(json.read())
        print data
        
    def UnFollowUser(self, widget, name, *args ):
        print "unfollow : " + name
        post = urllib.urlencode({ 'screen_name' : name })
                
        #build the request with the url and our post data
        req = urllib2.Request('http://twitter.com/friendships/destroy.json', post)
        
        auth_handler = urllib2.HTTPBasicAuthHandler()
        #realm here is important. or at least it seemed to be
        #this info is on the login box if you go to the url in a browser
        auth_handler.add_password(realm='Twitter API',
                          uri='http://twitter.com/friendships/destroy.json',
                          user=self.username,
                          passwd=self.password)
        #we create an 'opener' object with our auth_handler
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)
        #switch on whether this is an refresh or a first download
       
        json = urllib2.urlopen(req)
        #JSON is awesome stuff. we get given a long string of json encoded information
        #which contains all the tweets, with lots of info, we decode to a json object
        data = simplejson.loads(json.read())
        print data
    
    def replyTo(self, widget, *args):
        print "reply to : " + self.reply_to_name + " message_id " + self.reply_to
        self.tweetText.set_text(self.reply_to_name)
        
    
    def reTweet(self, widget,  *args):
        print "reTweet : " + self.retweetname + " message_id " +self.retweetid
        
	post = urllib.urlencode({ })
        #build the request with the url and our post data
        req = urllib2.Request('http://api.twitter.com/1/statuses/retweet/'+str(self.retweetid)+'L.json', post)
        #setup the auth stuff
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm='Twitter API',
                              uri='http://api.twitter.com/1/statuses/retweet/'+str(self.retweetid)+'L.json',
                              user=self.username,
                              passwd=self.password)
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
	try:
		urllib2.install_opener(opener)
		json = urllib2.urlopen(req)
		hildon.hildon_banner_show_information(self.window,"","ReTweet Successful")
	except IOError, e:
	    msg = 'Error posting tweet '
	    if hasattr(e, 'reason'):
		    msg = msg + str(e.reason)
		    
            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
		elif(e.code == 503):
		    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg +'Server returned ' + str(e.code) + " : " + reason
		
	    note = hildon.hildon_note_new_information(self.window, msg)
            note.run()
	    note.destroy()
	
    def openBrowser(self, widget, url, *args):      
        #open a url in a browser
        context = osso.Context("Witter", "1.0",False)
        if (self.maemo_ver==5):
            webbrowser.open_new(url)
        else:
            webbrowser.open(url, context=context)
        print "We tried to open a browser"
        
    def checkVersion(self):
        #we want to see if we're on fremantle or not as the default colour
        #scheme has changed
        #look for /etc/maemo_version
        print "checking for /proc/component_version"
        try:
            f = open('/proc/component_version', 'r')
            read_data = f.read()
            if (re.search("RX-51", read_data)):
                print "found n900"
                self.textcolour="#FFFFFF"
                self.tweetcolour= "#FFFFFF"
                self.namecolour="#FE00B8"
                self.defaultwidth=790
                self.maemo_ver=5
            else:
		self.textcolour="#000000"
                print "found"+ read_data
                self.maemo_ver=4
        except IOError:
            #couldn't find the file 
            print "Assuming pre-maemo5"
            self.maemo_ver=4
    
    def readConfig(self):
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(open('/home/user/.witter'))
	    try:
		user = config.get("credentials", "username");
		self.username=base64.b64decode(user)
		password = config.get("credentials", "password");
		self.password=base64.b64decode(password)
         
                self.textcolour=config.get("UI","textcolour")
            except ConfigParser.NoSectionError:
                print "no text colour setting"
            try:
                serviceType =config.get("Service","type")
                if (serviceType == "twitter"):
                    self.serviceUrlRoot=self.twitterUrlRoot
                    self.searchServiceUrlRoot=self.twitterSearchUrlRoot
                    self.serviceName=self.twitterName
                elif ("identi.ca" == serviceType):
                    self.serviceUrlRoot=self.identicaUrlRoot
                    self.searchServiceUrlRoot=self.identicaSearchUrlRoot
                    self.serviceName=self.identicaName
            except ConfigParser.NoSectionError:
                print "no service setting"
	    try:
		    self.timelineRefreshInterval = int(config.get("refresh_interval", "timeline"))
		    self.mentionsRefreshInterval = int(config.get("refresh_interval","mentions"))
		    self.DMsRefreshInterval = int(config.get("refresh_interval","dm"))
		    self.publicRefreshInterval = int(config.get("refresh_interval","public"))
		    self.searchRefreshInterval = int(config.get("refresh_interval","search"))
	    except ConfigParser.NoSectionError:
		print "No refresh_interval section"
	    except ConfigParser.NoOptionError:
		print "unknown option"
	    try:
		    self.search_terms = config.get("search","search_terms")
	    except ConfigParser.NoSectionError:
		print "No refresh_interval section"
		
        except IOError:
            #couldn't find the file set uid so we can prompt
	    #for creds
            self.username = "UserName"
            self.password = ""
            print "No config file, prompt for uid/pwd"
            
    def switchService(self, *args):
        if (self.serviceUrlRoot == self.twitterUrlRoot):
            self.serviceUrlRoot = self.identicaUrlRoot
            self.serviceName = self.identicaName
            self.searchServiceUrlRoot = self.identicaSearchUrlRoot
            self.window.set_title("Witter - now using identi.ca")
        else:
            self.serviceUrlRoot = self.twitterUrlRoot
            self.serviceName = self.twitterName
            self.searchServiceUrlRoot = self.twitterSearchUrlRoot
            self.window.set_title("Witter - now using twitter")         
    
    def writeConfig(self):
	try:
		f = open('/home/user/.witter','w')
		f.write("[credentials]\n")
		f.write("username = "+base64.b64encode(self.username)+"\n")
		f.write("password = "+base64.b64encode(self.password)+"\n")    
		f.write("[UI]\n")
		f.write("textcolour = "+self.textcolour+"\n")
		f.write("[refresh_interval]\n")
		f.write("timeline="+str(self.timelineRefreshInterval)+"\n")
		f.write("mentions="+str(self.mentionsRefreshInterval)+"\n")
		f.write("dm="+str(self.DMsRefreshInterval)+"\n")
		f.write("public="+str(self.publicRefreshInterval)+"\n")
		f.write("search="+str(self.searchRefreshInterval)+"\n")
		f.write("[search]\n")
		f.write("search_terms="+self.search_terms+"\n")
	except IOError, e:
		print "failed to write config file"
		
    def promptForCredentials(self, *args):
        #dialog = self.wTree.get_widget("CredentialsDialog")
        dialog = self.builder.get_object("CredentialsDialog")
        dialog.set_title("Twitter Credentials")
        dialog.connect("response", self.gtk_widget_hide)
        dialog.show_all()
        
    def  store_creds(self, widget, *args):
        print "store_creds called"
        
        #store the values set
        self.username = self.builder.get_object("UserName").get_text()
        self.password = self.builder.get_object("Password").get_text()
        self.writeConfig()

    def  gtk_widget_hide(self, widget, *args):
        widget.hide_all()
        #widget.destroy()
	
    def reparent_loc(self, widget, newParent):
        widget.reparent(newParent)
        
    def switchViewTo(self, widget, type ):
	if (self.treeview.get_model() == self.searchliststore):
	    #switching out of search view, save search terms and reset text box
	    self.search_terms = self.tweetText.get_text()
	    self.tweetText.set_text("")
        if (re.search("timeline",type)):
            self.treeview.set_model(self.liststore)
            self.window.set_title(self.serviceName +" - timeline")
        elif (re.search("direct", type)):
            self.treeview.set_model(self.dmliststore)
            self.window.set_title(self.serviceName +" - direct messages")
        elif (re.search("mentions", type)):
            self.treeview.set_model(self.mentionliststore)
            self.window.set_title(self.serviceName +" - mentions")
        elif (re.search("public", type)):
            self.treeview.set_model(self.publicliststore)
            self.window.set_title(self.serviceName +" - public")
        elif (re.search("trends", type)):
            self.treeview.set_model(self.trendliststore) 
            self.window.set_title(self.serviceName +" - trends")
        elif (re.search("friends", type)):
            self.treeview.set_model(self.friendsliststore)
            self.window.set_title(self.serviceName +" - friends")
        elif (re.search("search", type)):
	    self.tweetText.set_text(self.search_terms)
            self.treeview.set_model(self.searchliststore)  
            self.window.set_title(self.serviceName +" - search")  
            
    def switchView(self, widget):
        #switches the active liststore to display what the user wants
        print widget
        type = widget.get_label()
        print type
        self.switchViewTo(widget,type)
        

    def selectImage(self, widget):
        #bring up a file choser to let people select images
        #imageChose = self.wTree.get_widget("filechooserdialog1")
        imageChose = self.builder.get_object("filechooserdialog1")
                
        filter = gtk.FileFilter()
        filter.set_name("*.jpg")
        filter.add_pattern("*.jpg")
        imageChose.remove_filter(filter)
        imageChose.add_filter(filter)
        imageChose.set_filter(filter)
        imageChose.show()
        
    def alreadyRetrieved(self, liststore, *args):
        #method to check if we have already stored this tweet
        
        #iterate over values and
        item = liststore.get_iter_first ()

        while True:

            value = model.get_value(item, 0)
        
            item = model.iter_next(item)
        
            if item is None:
        
                break


        
    def flipTextColour(self, *args):
        #until I figure out how to obey theme colours, let the user
        #flip the colours in use.
        if (re.search("#000000", self.textcolour)):
            self.textcolour = "#FFFFFF"
            
        else:
            self.textcolour = "#000000"
        #reset all the values in the current list stores
        item = self.liststore.get_iter_first ()

        while ( item != None ):
            self.liststore.set_value(item,1,self.textcolour)
            self.liststore.set_value(item,3,self.textcolour)
            item = self.liststore.iter_next(item)
        
        item = self.dmliststore.get_iter_first ()

        while ( item != None ):
            self.dmliststore.set_value(item,1,self.textcolour)
            self.dmliststore.set_value(item,3,self.textcolour)
            item = self.dmliststore.iter_next(item)
        item = self.friendsliststore.get_iter_first ()

        while ( item != None ):
            self.friendsliststore.set_value(item,1,self.textcolour)
            self.friendsliststore.set_value(item,3,self.textcolour)
            item = self.friendsliststore.iter_next(item)
        
        item = self.mentionliststore.get_iter_first ()

        while ( item != None ):
            self.mentionliststore.set_value(item,1,self.textcolour)
            self.mentionliststore.set_value(item,3,self.textcolour)
            item = self.mentionliststore.iter_next(item)
        item = self.publicliststore.get_iter_first ()

        while ( item != None ):
            self.publicliststore.set_value(item,1,self.textcolour)
            self.publicliststore.set_value(item,3,self.textcolour)
            item = self.publicliststore.iter_next(item)
        
        item = self.searchliststore.get_iter_first ()

        while ( item != None ):
            self.searchliststore.set_value(item,1,self.textcolour)
            self.searchliststore.set_value(item,3,self.textcolour)
            item = self.searchliststore.iter_next(item)
            
        item = self.trendliststore.get_iter_first ()

        while ( item != None ):
            self.trendliststore.set_value(item,1,self.textcolour)
            self.trendliststore.set_value(item,3,self.textcolour)
            item = self.trendliststore.iter_next(item)
      
    def twitPic(self, widget, *args):
        print "twitPic"
        #dialog = self.wTree.get_widget("filechooserdialog1")
        dialog = self.builder.get_object("filechooserdialog1")
        file = dialog.get_filename()
        
        try:
            fin = open(file, "rb")
            jpgImage = fin.read()
            #tweet = self.wTree.get_widget("TweetText").get_text()
            tweet = self.builder.get_object("TweetText").get_text()
            #see if we have just an empty string (eg eroneous button press)
            if (tweet == ""):
                print "No tweet to go with image"
                return
            
            # upload binary file with pycurl by http post
            c = pycurl.Curl()
            c.setopt(c.POST, 1)
            c.setopt(c.URL, "http://twitpic.com/api/uploadAndPost")
            c.setopt(c.HTTPPOST, [("media", (c.FORM_FILE, file)), 
                                  ("username",self.username), 
                                  ("password",self.password),
                                  ("message",tweet)])
            #c.setopt(c.VERBOSE, 1)
            c.perform()
            c.close()
            print "posted TwitPic"

            
            #message sent, I'm assuming a failure to send would not continue
            #in this method? so it's safe to remove the tweet line
            # what I don't want is to lose the tweet I typed if we didn't
            # sucessfully send it to twitter. that would be annoying (I'm looking
            # at you Mauku)
            #self.wTree.get_widget("TweetText").set_text("")
            self.builder.get_object("TweetText").set_text("")
        except IOError:
            print "couldn't read file"
        print file
    
    def CharsRemaining(self, widget):
	     tweet = self.builder.get_object("TweetText").get_text()
	     counter = self.builder.get_object("Counter")
	     counter.set_text((str(140-len(tweet))))
    
     
    def about(self,widget, *args):
		dlg = gtk.AboutDialog()
		dlg.set_version("0.1.1")
		dlg.set_name("Witter")
		dlg.set_authors(["Daniel Would"])
		dlg.set_website("Homepage : http://danielwould.wordpress.com/witter/\nBugtracker : http://garage.maemo.org/projects/witter")
		def close(w, res):
			if res == gtk.RESPONSE_CANCEL:
				w.hide()
		dlg.connect("response", close)
		dlg.show()
	
    def configProperties(self, widget, *args):
	    #dialog = self.wTree.get_widget("CredentialsDialog")
	    if (self.configDialog == None):
		self.configDialog = self.builder.get_object("setRefreshDialog")
		self.configDialog.set_title("Witter Properties")
		self.configDialog.connect("response", self.dontsetProps)
	    
		self.timelineNumberEd = self.builder.get_object("timeline-NumberEditor")
		self.mentionsNumberEd = self.builder.get_object("mentions-NumberEditor")
		self.DMNumberEd = self.builder.get_object("DM-NumberEditor")
		self.publicNumberEd = self.builder.get_object("public-NumberEditor")
		self.searchNumberEd = self.builder.get_object("search-NumberEditor")
	    
	    self.timelineNumberEd.set_value(self.timelineRefreshInterval)
	    self.mentionsNumberEd.set_value(self.mentionsRefreshInterval)
	    self.DMNumberEd.set_value(self.DMsRefreshInterval)
	    self.publicNumberEd.set_value(self.publicRefreshInterval)
	    self.searchNumberEd.set_value(self.searchRefreshInterval)
            self.configDialog.show_all()

    def dontsetProps(self,widget, *args):
	    print "cancelledOperation"
	    self.configDialog.hide_all()
	    
    def setProps(self, widget, *args):
	    #set all the refresh inteval values
	    self.timelineRefreshInterval = self.timelineNumberEd.get_value()
	    self.mentionsRefreshInterval = self.mentionsNumberEd.get_value()
	    self.DMsRefreshInterval = self.DMNumberEd.get_value()
	    self.publicRefreshInterval = self.publicNumberEd.get_value()
	    self.searchRefreshInterval = self.searchNumberEd.get_value()
	    #stop and start the threads to pick up the new values
	    self.end_refresh_threads()
	    self.start_refresh_threads()
	    self.configDialog.hide_all()
	    
    def end_refresh_threads(self):
	    #end all the refresh threads
	    if (self.refreshtask != None):
		self.refreshtask.stop()
	    if (self.dmrefresh != None):
		self.dmrefresh.stop()
	    if (self.mentionrefresh != None):
		self.mentionrefresh.stop()
	    if (self.publicrefresh != None):
		self.publicrefresh.stop()
	    if (self.searchrefresh != None):
		self.searchrefresh.stop()
	

    def start_refresh_threads(self):
	    #we store the refresh interval in minutes, but pass it through as a value in seconds
	    #this method launches a thread for each of the views we want to have auto-refreshed
	    if (self.timelineRefreshInterval != 0):
		    self.refreshtask = witter.RefreshTask(self.getTweetsWrapper, self.showBusy)
		    self.refreshtask.start(self.timelineRefreshInterval*60, self)
	    if (self.DMsRefreshInterval != 0):
		    self.dmrefresh = witter.RefreshTask(self.getDMsWrapper, self.showBusy)
		    self.dmrefresh.start(self.DMsRefreshInterval*60, self)
	    if (self.mentionsRefreshInterval != 0):
		    self.mentionrefresh = witter.RefreshTask(self.getMentionsWrapper, self.showBusy)
		    self.mentionrefresh.start(self.mentionsRefreshInterval*60, self)
	    if (self.publicRefreshInterval != 0) :
		    self.publicrefresh = witter.RefreshTask(self.getPublicWrapper, self.showBusy)
		    self.publicrefresh.start(self.publicRefreshInterval*60, self)
	    if (self.searchRefreshInterval != 0) :
		    self.searchrefresh = witter.RefreshTask(self.getSearchWrapper, self.showBusy)
		    self.searchrefresh.start(self.searchRefreshInterval*60, self)
	    print "end refresh setup"
	    
    def getTweetsWrapper(self, *args):
	    
	    self.getTweets(auto=1)
	    
	    return "done"
	    
    def getDMsWrapper(self, *args):
	    #we want to randomise the streams so they don't clash
	    #time.sleep(random.randint(1, 30))
	    #if (self.gettingTweets == False):
	    self.getDMs(auto=1)
	  
	    return "done"
	    
    def getMentionsWrapper(self, *args):
	    #we want to randomise the streams so they don't clash
	    #time.sleep(random.randint(1, 30))
	    #if (self.gettingTweets == False):
	    self.getMentions(auto=1)
	    
	    return "done"

    def getPublicWrapper(self, *args):
	    #we want to randomise the streams so they don't clash
	    #time.sleep(random.randint(1, 30))
	    #if (self.gettingTweets == False):
	    self.getPublic(auto=1)
	    return "done"
		
    def getSearchWrapper(self, *args):
	    
	    self.getSearch(auto=1)
	    
	    return "done"

    def showBusy(self, *args):
	    print "running"
	    return "still running"
	    
	    
if __name__ == "__main__":  
    #this is just what initialises the app and calls run
    app = Witter() 
   
    app.run()         
   
   
