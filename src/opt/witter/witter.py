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
# Name        : witter.py
# Author      : Daniel Would
# Version     : 0.3.4
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
import dbus
import dbus.glib
import os
import webbrowser
import ConfigParser
import pycurl
import oauthtwitter
import twitter
import bitly
import random
import witter
import time
import pickle
import gobject
import cProfile
import dbus
import dbus.glib
import conic 
#import witter components
import ui
import account


gtk.gdk.threads_init()



#Initially I found I'd hang the whole interface if I was having network probs
#because by default there is an unlimited wait on connect so I set
#the timeout to 10 seconds afterwhich you get back a timeout error
# timeout in seconds
timeout = 20
socket.setdefaulttimeout(timeout)

#the main witter application
class Witter():
    #first an init method to set everything up    
    def __init__(self):
        #version of witter
        self.version = "0.3.7"
        #object holding witter config
        self.config = None
        #defaults for auto-refresh

        self.timelineRefreshInterval = 30
        self.mentionsRefreshInterval = 30

        self.DMsRefreshInterval = 30
        self.publicRefreshInterval = 0
        self.searchRefreshInterval = 0
        self.font_size = 18
        #we use the busy counter to track the number of busy threads
        #and show a progres/busy indicator whilst it's more than 0

        self.search_terms = ""
        self.refreshtask = None
        self.dmrefresh = None
        self.mentionrefresh = None
        self.publicrefresh = None
        self.searchrefresh = None
        self.search_clear = False
        self.filterList = []
        self.username = "UserName"
        self.password = ""
        self.bitlyusername = ""
        self.bitlyapikey = ""
        self.access_token = ""
        self.user = ""
        self.CONSUMER_KEY = 'c0glxehHLYgzDqDMLjanA'
        self.CONSUMER_SECRET = 'V37SuM6o7PddlqqosLpYtIqyaLj0mgnFkGGKkJjN6I'
        self.textcolour = "#FFFFFF"

        #make the hildon program
        self.program = hildon.Program()
        self.program.__init__()

        self.osso_c = osso.Context("witter", self.version, False)
        self.osso_rpc = osso.Rpc(self.osso_c)
        self.osso_rpc.set_rpc_callback("uk.wouldd.witter", "/uk/wouldd/witter", "uk.wouldd.witter", self.cb_switch_view, self.osso_c)
        # set name of application: this shows in titlebar
        
        system_bus = dbus.Bus.get_system()
        system_bus.add_signal_receiver(self._on_orientation_signal, \
                 signal_name='sig_device_orientation_ind', \
                 dbus_interface='com.nokia.mce.signal', \
                 path='/com/nokia/mce/signal')

        self.twitterUrlRoot = "https://twitter.com/"
        self.twitterSearchUrlRoot = "https://search.twitter.com/"
        self.twitterName = "Witter"

        self.serviceUrlRoot = self.twitterUrlRoot
        self.searchServiceUrlRoot = self.twitterSearchUrlRoot
        self.serviceName = self.twitterName

    	 #used to store the id of message if we're going to do a reply_to
        self.reply_to = ""
        self.reply_to_name = ""
        self.reply_all = ""
        self.retweetname = ""
        self.retweetid = ""
        self.retweettext = ""
        self.selectedUser = ""
        self.theme = "default"
        self.gestures = True
        self.location = False
        self.emailnotifications = True
        self.orientation = 'Landscape'
        #
        #go read config file
        #
        self.readConfig()
        if (self.config == None):
            self.config = self.createConfig()

        # self.treeview.connect("changed", self.build_menu, None);
        #self.treeview.tap_and_hold_setup(self.urlmenu, callback=gtk.tap_and_hold_menu_position_top)
    	#init the configDialog

        self.configDialog = None
        #iterate through any accounts in the config and set the last stored active
        #account at the current active acount
        self.accounts = []
        for acc in self.config.accountList:
            if (acc.status == acc.ACTIVE):
                self.activeAccount = account.account(self.osso_c, acc, self)
                self.accounts.append(self.activeAccount)
            else:
                additional_acc = account.account(self.osso_c, acc, self)
                self.accounts.append(additional_acc)

        #reload any cached tweets
        self.activeAccount.tweetstore = self.reload_timeline_data('/home/user/.wittertl',self.activeAccount.getTimeline())
        self.activeAccount.mentionstore = self.reload_timeline_data('/home/user/.wittermen',self.activeAccount.getMentionsList())
        self.activeAccount.dmstore = self.reload_timeline_data('/home/user/.witterdm',self.activeAccount.getDmsList())
        

        #call the refresh thread

        #pass the witter ui a reference to this object for callbacks
        self.ui = ui.WitterUI(self)
        #self.ui.setActiveListStore(self.activeAccount.getTimeline(),4)
        self.ui.theme = self.theme
        self.ui.load_theme_icons()
        self.ui.select_ui_theme(self.theme)
        self.ui.gesture_enabled = self.gestures
        self.ui.orientation = self.orientation
        
        self.gettingTweets = False
        if (self.activeAccount.getUsername() != "Username"):
            self.start_refresh_threads()
        #
        #need to load all account references, and set the active account
        #
        from portrait import FremantleRotation
        if ((self.orientation == 'Landscape') | (self.orientation == 'landscape')):
            print "setting never rotate"
            mymode = FremantleRotation.NEVER
        elif ((self.orientation == 'Portrait') | (self.orientation == 'portrait')):
            print "setting always rotated"
            mymode =FremantleRotation.ALWAYS
        elif ((self.orientation == 'Automatic') | (self.orientation == 'automatic')):
            print "setting automatic"
            mymode =FremantleRotation.AUTOMATIC
        
        self.rotation = FremantleRotation("Witter", self.ui.window, mode=mymode)
        self.profileUpdateThread = witter.RefreshTask(self.setProfile, 0, None)
        self.profileUpdateThread.refresh()
        

    def quit(self, *args):
        #this is our end method called when window is closed
        print "Stop Wittering"
    	print "shutting down refresh loop"
    	self.writeConfig()
    	self.end_refresh_threads()

        gtk.main_quit()

    def run(self):

        #this starts everything up
        gtk.main()


    def updateSelectedView(self, *args):
        #call the get method for whichever liststore we're viewing
        print "refreshing view"
        print str(self.ui.getCurrentView())
        curView = self.ui.getCurrentView()
        if (curView == self.ui.TIMELINE_VIEW):

            #self.getTweets()
    	    refreshtask = witter.RefreshTask(self.getTweetsWrapper, 0, None)
    	    refreshtask.refresh()
        elif (curView == self.ui.DM_VIEW):
            refreshtask = witter.RefreshTask(self.getDMsWrapper, 0, None)
            refreshtask.refresh()
        elif (curView == self.ui.MENTIONS_VIEW):

    	    refreshtask = witter.RefreshTask(self.getMentionsWrapper, 0, None)
    	    refreshtask.refresh()
        elif (curView == self.ui.PUBLIC_VIEW):
            refreshtask = witter.RefreshTask(self.getPublicWrapper, 0, None)
            refreshtask.refresh()
        elif (curView == self.ui.TRENDS_VIEW):
            refreshtask = witter.RefreshTask(self.getTrendsWrapper, 0, None)
            refreshtask.refresh()
        elif (curView == self.ui.FRIENDS_VIEW):
            refreshtask = witter.RefreshTask(self.getFriendsWrapper, 0, None)
            refreshtask.refresh()
        elif (curView == self.ui.SEARCH_VIEW):
            refreshtask = witter.RefreshTask(self.getSearchWrapper, 0, None)
            refreshtask.refresh()
        elif (curView == self.ui.USERHIST_VIEW):
            refreshtask = witter.RefreshTask(self.getUserHistWrapper, 0, None)
            refreshtask.refresh()

	self.ui.hideBottomBar()
	#self.builder.get_object("hbox2").hide_all()

    def enterPressed(self, widget, tweetBox, *args):
        self.ui.showBusy(1)
        print "sending tweet"
        tweetBuf = tweetBox.get_buffer()
        tweet = tweetBuf.get_text(tweetBuf.get_start_iter(),tweetBuf.get_end_iter())
        result = self.activeAccount.newTweet(tweet, reply_to_name=self.reply_to_name, reply_to_id=self.reply_to)
        print "Tweet Sent"
        if (result == True):
            print "Tweet successful"
            hildon.hildon_banner_show_information(self.ui.window, "", "Tweet Successful")
            #tweet successful, clear tweet text
            tweetBuf.set_text("")
    	    #if we were in the search view, we want to restore the search terms after a tweet
            if (self.ui.getCurrentView == self.ui.SEARCH_VIEW):
    		    self.ui.setTweetText(self.search_terms)
        else:
            print "Tweet Failed"
            hildon.hildon_banner_show_information(self.ui.window, "", "Tweet Failed")
        self.ui.showBusy(-1)
        profileUpdateThread = witter.RefreshTask(self.setProfile, 0, None)
        profileUpdateThread.refresh()


    def FollowTweetAuthor(self, widget):
        #TODO : put this on a thread
        self.activeAcount.FollowUser(widget, self.reply_to_name)
        refreshtask = witter.RefreshTask(self.followUserWrapper, 0, None)
        refreshtask.refresh()


    def UnFollowTweetAuthor(self, widget):
        self.activeAccount.UnFollowUser(widget, self.reply_to_name)


    def replyTo(self, widget, *args):
        self.ui.hideActionButtons()
        self.ui.showBottomBar()
    	if (self.ui.getCurrentView() == self.ui.SEARCH_VIEW):
    		#we want to store the search terms, replace them with tweet text
    		#so we can restore the search terms afterwards
    		self.search_terms = self.ui.getEntryText()
        self.ui.setTweetText(self.reply_to_name + " ")
    	self.ui.setCursorAt(len(self.reply_to_name) + 1);

    def replyAll(self, widget, *args):
        self.ui.hideActionButtons()
        self.ui.showBottomBar()
        if (self.ui.getCurrentView() == self.ui.SEARCH_VIEW):
            #we want to store the search terms, replace them with tweet text
            #so we can restore the search terms afterwards
            self.search_terms = self.ui.getEntryText()
        self.ui.setTweetText(self.reply_all + " ")
        self.ui.setCursorAt(len(self.reply_all) + 1);


    def directMessage(self, widget, *args):
        self.ui.hideActionButtons()
        self.ui.showBottomBar()
        name = self.reply_to_name.replace("@", "")
        if (self.ui.getCurrentView() == self.ui.SEARCH_VIEW):
            #we want to store the search terms, replace them with tweet text
            #so we can restore the search terms afterwards
            self.search_terms = self.ui.getEntryText()

        self.ui.setTweetText("d " + name + " ")
        self.ui.setCursorAt(len(self.reply_to_name) + 3);

    def reTweet(self, widget, *args):
        self.ui.hideActionButtons()
        self.ui.showBottomBar()
        #if we expanded a url domain, we want it dropped from the retweet.
        words = self.retweettext.split(" ")
        for index, word in enumerate(words):
            if (re.search("http://bit.ly", word)):
                if (words[index + 1].startswith("(")):
                    words[index + 1] = ""

        retweet = ' '.join(words)

        self.ui.setTweetText("RT " + retweet)
        self.ui.setCursorAt(0)

    def reTweetNew(self,widget,*args):
        self.ui.hideActionButtons()
        self.ui.showBottomBar()
        self.activeAccount.newRetweet(self.retweetid)

    def openBrowser(self, widget, url, *args):
        #open a url in a browser

        print "opening browser - maemo5 style"
        #webbrowser.open_new(url)
        self.osso_rpc.rpc_run_with_defaults("osso_browser", "open_new_window", (url,))

        print "We tried to open a browser"
        
    def FavouriteTweet(self, widget, id, *args):
        #open a url in a browser

        print "Favourite the tweet"
        #webbrowser.open_new(url)
        self.activeAccount.FavouriteTweet(self,long(id))
        print "tweet set as favourite"

    def Translate(self, widget, text, *args):
        #open a url in a browser

        url = "http://translate.google.com/#auto|en|"
        translateText = urllib.quote(text)
        self.openBrowser(widget, url + translateText)

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
                self.textcolour = "#FFFFFF"
                self.tweetcolour = "#FFFFFF"
                self.namecolour = "#FE00B8"
                self.defaultwidth = 790
                self.maemo_ver = 5
            else:
		self.textcolour = "#000000"
                print "found" + read_data
                self.maemo_ver = 4
        except IOError:
            #couldn't find the file 
            print "Assuming pre-maemo5"
            self.maemo_ver = 4

    def readConfig(self):
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(open('/home/user/.witter'))
            try:
                user = config.get("credentials", "username");
                self.username = base64.b64decode(user)
                password = config.get("credentials", "password");
                self.password = base64.b64decode(password)
                user2 = config.get("credentials", "bitlyusername");
                self.bitlyusername = base64.b64decode(user2)
                password2 = config.get("credentials", "bitlyapikey");
                self.bitlyapikey = base64.b64decode(password2)
            except ConfigParser.NoSectionError:
                print "no text colour setting"
            except ConfigParser.NoOptionError:
                print "missing option in config"
            try:
                #self.access_token = config.get("credentials", "access_token")
                topCol = config.get("UI", "bg_top")
                
                self.bg_top_color = gtk.gdk.color_parse(topCol)
                bottomCol = config.get("UI", "bg_bottom")
                
                self.bg_bottom_color = gtk.gdk.color_parse(bottomCol)
                self.font_size = int(config.get("UI", "font_size"))
                self.theme = config.get("UI", "theme")
                gestures = config.get("UI","gestures_enabled")
                
                emailnotifications = config.get("UI","notifications_enabled")
                if (gestures == "True"):
                    self.gestures = True
                    print "gestures enabled"
                else:
                    self.gestures = False
                    print "gestures disabled"
                     
                if (emailnotifications == "True"):
                    self.emailnotifications = True
                else:
                    self.emailnotifications = False
                self.orientation = config.get("UI","orientation")    
            except ConfigParser.NoSectionError:
                print "no text colour setting"
            except ConfigParser.NoOptionError:
                print "missing option in config"
            try:
                loc = config.get("General","location")
                if (loc == "True"):
                    self.location = True
                    print "tweet with location enabled"
                else:
                    self.location = False
                    print "tweet with location disabled"
            except ConfigParser.NoSectionError:
                print "no location setting"
            except ConfigParser.NoOptionError:
                print "missing location option in config"
                   
            try:
                serviceType = config.get("Service", "type")
                if (serviceType == "twitter"):
                    self.serviceUrlRoot = self.twitterUrlRoot
                    self.searchServiceUrlRoot = self.twitterSearchUrlRoot
                    self.serviceName = self.twitterName
                elif ("identi.ca" == serviceType):
                    self.serviceUrlRoot = self.identicaUrlRoot
                    self.searchServiceUrlRoot = self.identicaSearchUrlRoot
                    self.serviceName = self.identicaName
            except ConfigParser.NoSectionError:
                print "no service setting"
    	    try:
    		    self.timelineRefreshInterval = int(config.get("refresh_interval", "timeline"))
    		    self.mentionsRefreshInterval = int(config.get("refresh_interval", "mentions"))
    		    self.DMsRefreshInterval = int(config.get("refresh_interval", "dm"))
    		    self.publicRefreshInterval = int(config.get("refresh_interval", "public"))
    		    self.searchRefreshInterval = int(config.get("refresh_interval", "search"))
    	    except ConfigParser.NoSectionError:
    		    print "No refresh_interval section"
    	    except ConfigParser.NoOptionError:
    		    print "unknown option"
    	    try:
                self.search_terms = config.get("search", "search_terms")
                search_clear = config.get("search", "search_clear")
                if (search_clear == "True"):
                    self.search_clear = True
                    print "clear search results on new search enabled"
                else:
                    self.search_clear= False
                    print "clear search results on new search disabled"
    	    except ConfigParser.NoSectionError:
    		    print "No refresh_interval section"
            except ConfigParser.NoOptionError:
                print "unknown option"
            try:
                counter=0
                while True:
                    self.filterList.append(config.get("filters", "filter"+str(counter)))
                    counter = counter+1
                
                
            except ConfigParser.NoSectionError:
                print "No filters section"
            except ConfigParser.NoOptionError:
                print "unknown option"
            try:
                f = open('/home/user/.witteroauth')
                self.access_token = pickle.load(f)
            except IOError:
                print "failed to read oauth access token"
            except EOFError:
                print "end of file, probably no token"
            try:
                self.config = witter.Config()
                self.config.font_size = self.font_size
                self.config.textcolour = "#FFFFFF"
                self.bg_top_color = "#6bd3ff"
                self.config.bg_bottom_color = "#0075b5"

                self.config.timelineRefreshInterval = self.timelineRefreshInterval
                self.config.mentionsRefreshInterval = self.mentionsRefreshInterval

                self.config.DMsRefreshInterval = self.DMsRefreshInterval
                self.config.publicRefreshInterval = self.publicRefreshInterval
                self.config.searchRefreshInterval = self.searchRefreshInterval
                #we use the busy counter to track the number of busy threads
                #and show a progres/busy indicator whilst it's more than 0

                self.config.search_terms = self.search_terms

                self.config.bitlyusername = self.bitlyusername
                self.config.bitlyapikey = self.bitlyapikey
                config = ConfigParser.ConfigParser()
                config.readfp(open('/home/user/.witterUser'))

                counter = 0
                while True:
                    accData = account.accountdata()
                    accData.username = config.get("users", "username" + str(counter));
                    password = config.get("users", "password" + str(counter));
                    accData.password = base64.b64decode(password)
                    accData.servicename = config.get("users", "type" + str(counter))
                    accData.baseUrl = config.get("users", "baseurl" + str(counter))
                    accData.searchUrl = config.get("users", "serachUrl" + str(counter))
                    token = config.get("users", "oauthtoken" + str(counter))
                    if (token != "None"):
                        accData.access_token = oauthtwitter.oauth.OAuthToken.from_string(token)
                    accData.status = int(config.get("users", "status" + str(counter)))
                    try:
                        id = config.get("users", "last_id" + str(counter))
                        if (id != "None"):
                            accData.last_id = long(id)
                        dmid = config.get("users", "last_dm_id" + str(counter))
                        if (dmid != "None"):
                            accData.last_dm_id = long(dmid)
                        menid = config.get("users", "last_mention_id" + str(counter))
                        if (menid != "None"):
                            accData.last_mention_id = long(menid)
                    except ConfigParser.NoOptionError:
                        print "No stored ids from last run"
                    self.config.accountList.append(accData)

                    counter = counter + 1
            except ConfigParser.NoSectionError:
                print "No users section, failed loading user accounts"
                self.config = None
            except ConfigParser.NoOptionError:
                print "No more users to load"
            except IOError:
                print "failed to read configuration"
                self.config = None
            except EOFError, e:
                print "end of file, failed to load"
                print e
                self.config = None
            
        except IOError:
            #couldn't find the file set uid so we can prompt
	        #for creds
            self.username = "UserName"
            self.password = ""
            print "No config file, prompt for uid / pwd"


    def writeConfig(self):
        try:
            f = open('/home/user/.witter', 'w')
            f.write("[credentials]\n")
            f.write("username = " + base64.b64encode(self.username) + "\n")
            f.write("password = " + base64.b64encode(self.password) + "\n")
            f.write("bitlyusername = " + base64.b64encode(self.bitlyusername) + "\n")
            f.write("bitlyapikey = " + base64.b64encode(self.bitlyapikey) + "\n")
            f.write("[UI]\n")
            f.write("textcolour = " + self.ui.textcolour + "\n")
            f.write("bg_top = " + self.ui.bg_top_color.to_string() + "\n")
            f.write("bg_bottom = " + self.ui.bg_bottom_color.to_string() + "\n")
            f.write("font_size = " + str(self.font_size) + "\n")
            f.write("theme = " + self.ui.theme + "\n")
            f.write("orientation = " + self.ui.orientation +"\n")
            if self.ui.gesture_enabled:
                f.write("gestures_enabled = True\n")
            else:
                f.write("gestures_enabled = False\n")
            if self.emailnotifications:
                f.write("notifications_enabled = True\n")
            else:
                f.write("notifications_enabled = False\n")
            f.write("[General]\n")
            f.write("location = " + str(self.location) +"\n")
            f.write("[refresh_interval]\n")
            f.write("timeline = " + str(self.timelineRefreshInterval) + "\n")
            f.write("mentions = " + str(self.mentionsRefreshInterval) + "\n")
            f.write("dm = " + str(self.DMsRefreshInterval) + "\n")
            f.write("public = " + str(self.publicRefreshInterval) + "\n")
            f.write("search = " + str(self.searchRefreshInterval) + "\n")
            f.write("[search]\n")
            f.write("search_terms = " + self.search_terms + "\n")
            if self.search_clear:
                f.write("search_clear = True\n")
            else:
                f.write("search_clear = False\n")
            f.write("[filters]\n")
            counter=0
            for filter in self.filterList:
                f.write("filter"+str(counter)+" = " + filter+"\n")
                counter = counter+1
    	except IOError, e:
    		print "failed to write config file"
        try:
            f2 = open('/home/user/.witteroauth', 'w')
            pickle.dump(self.access_token, f2)
        except IOError, e:
            print "failed to write access token"
        try:
            f3 = open('/home/user/.witterUser', 'w')
            f3.write("[users]\n")
            counter = 0
            for account in self.config.accountList:
                f3.write("username" + str(counter) + " = " + account.username + "\n")
                f3.write("password" + str(counter) + " = " + base64.b64encode(account.password) + "\n")
                f3.write("type" + str(counter) + " = " + account.servicename + "\n")
                f3.write("baseurl" + str(counter) + " = " + account.baseUrl + "\n")
                f3.write("serachUrl" + str(counter) + " = " + account.searchUrl + "\n")
                if (account.access_token != None):
                    f3.write("oauthtoken" + str(counter) + " = " + account.access_token.to_string() + "\n")
                else:
                    f3.write("oauthtoken" + str(counter) + " = None\n")
                f3.write("status" + str(counter) + " = " + str(account.status) + "\n")
                #todo output tne last used ids for timelines, for each account
                #then restore them at start up and only ever fetch since latest
                f3.write("last_id" + str(counter) + " = " + str(account.last_id) + "\n")
                f3.write("last_dm_id" + str(counter) + " = " + str(account.last_dm_id) + "\n")
                f3.write("last_mention_id" + str(counter) + " = " + str(account.last_mention_id) + "\n")

                counter = counter + 1
            
            
            print "written config object to file"
        except IOError, e:
            print "failed to write ConfigObject"
        
        self.save_timeline_data('/home/user/.wittertl',self.activeAccount.getTimeline())
        self.save_timeline_data('/home/user/.wittermen',self.activeAccount.getMentionsList())
        self.save_timeline_data('/home/user/.witterdm',self.activeAccount.getDmsList())
       
    def save_timeline_data(self,file,store):
        try:
            f5 = open(file, 'w')
            f5.write("[tweets]\n")
            counter =0
            item = store.get_iter_first()
            #just store the top 20 tweets
            while (item != None) and (counter < 20):
                f5.write("senderName" + str(counter) + " = " + store.get_value(item,0)+"\n")
                f5.write("senderId" + str(counter) + " = " +store.get_value(item,1)+"\n")
                tweet = store.get_value(item,2)
                tweet = tweet.replace(";","&SC;")
                tweet = tweet.replace("\n","&CR;")
                f5.write("tweet" + str(counter) + " = " +tweet+"\n")
                #3 is unused now, used to be tweet colour
                f5.write("tweetId" + str(counter) + " = " +str(store.get_value(item,4))+"\n")
                f5.write("type" + str(counter)+" = " + str(store.get_value(item,5))+"\n")
                f5.write("createdAt" + str(counter) + " = " +store.get_value(item,6)+"\n")
                reply = store.get_value(item,7)
                reply = reply.replace("\n","&CR;")
                f5.write("replyTo" + str(counter) + " = " +reply+"\n")
                f5.write("source" + str(counter) + " = " +store.get_value(item,8)+"\n")
                #9 is avatar pic
                formattedTweet = store.get_value(item,10)
                formattedTweet = formattedTweet.replace("\n","&CR;")
                f5.write("formattedTweet" + str(counter) + " = " +formattedTweet+"\n")
                
                item = store.iter_next(item)
                counter= counter+1
                
        except IOError, e:
            print "failed to write timeline history file " + file
       
    def reload_timeline_data(self, file,tweetstore):
        #reloads timeline/mentions/dms from files into the current active account
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(open(file))

            counter = 0
            while True:
                senderName = config.get("tweets", "senderName" + str(counter));
                senderId = config.get("tweets", "senderId" + str(counter));
                tweet = config.get("tweets", "tweet" + str(counter));
                tweet = tweet.replace("&CR;","\n")
                tweet = tweet.replace("&SC;",";")
                tweetId = config.get("tweets", "tweetId" + str(counter));
                tweet_long_id = float(tweetId)
                createdAt = config.get("tweets", "createdAt" + str(counter));
                replyTo = config.get("tweets", "replyTo" + str(counter));
                replyTo = replyTo.replace("&CR;","\n")
                type = config.get("tweets", "type" + str(counter));
                source = config.get("tweets", "source" + str(counter));
                formattedTweet = config.get("tweets", "formattedTweet" + str(counter));
                formattedTweet = formattedTweet.replace("&CR;", "\n")
                #load avatar
                filename = senderId+".jpg"
                if (os.path.isfile("/home/user/.witterPics/" + self.activeAccount.accountdata.servicename + "/" + filename)):
                    try:
                        avatar = gtk.gdk.pixbuf_new_from_file("/home/user/.witterPics/" + self.activeAccount.accountdata.servicename + "/" + filename)
                    except gobject.GError:
                        #failed to load file, delete it, and go fetch a new one
                        print "corrupted avatar file found, deleting it"
                        os.remove("/home/user/.witterPics/" + self.activeAccount.accountdata.servicename + "/" + filename)
                        print "bad file deleted, returning default icon"
                        avatar = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
                else:
                    avatar = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
                avatar = avatar.scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
                tweetstore.append([senderName,senderId,tweet,"",tweet_long_id,type,createdAt,replyTo,source,avatar,formattedTweet, True])
                counter=counter+1
                
                
        except ConfigParser.NoSectionError:
            print "Failed to load cached timeline"
        except ConfigParser.NoOptionError:
            print "Failed to load cached timeline"
        except IOError:
            print "failed to read timeline file"
            
        except EOFError, e:
            print "end of file, failed/finished? to load cached timeline"
            print e
        return tweetstore


    def createConfig(self):
            config = witter.Config()
            config.font_size = 18
            config.textcolour = "#FFFFFF"
            self.bg_top_color = "#6bd3ff"
            config.bg_bottom_color = "#0075b5"

            config.timelineRefreshInterval = self.timelineRefreshInterval
            config.mentionsRefreshInterval = self.mentionsRefreshInterval

            config.DMsRefreshInterval = self.DMsRefreshInterval
            config.publicRefreshInterval = self.publicRefreshInterval
            config.searchRefreshInterval = self.searchRefreshInterval
            #we use the busy counter to track the number of busy threads
            #and show a progres/busy indicator whilst it's more than 0

            config.search_terms = self.search_terms

            config.bitlyusername = self.bitlyusername
            config.bitlyapikey = self.bitlyapikey
            accData = account.accountdata()
            activeAccount = account.account(self.osso_c, accData, self)
            activeAccount.setServiceCreds(self.username, password=self.password, access_token=self.access_token)
            activeAccount.setBaseUrl(self.serviceUrlRoot)
            activeAccount.setSearchUrl(self.searchServiceUrlRoot)
            activeAccount.setStatus(activeAccount.ACTIVE)
            activeAccount.setBitlyCreds(self.bitlyusername, self.bitlyapikey)

            config.accountList.append(activeAccount.getAccountData())
            return config


    def configOauth(self, widget, account, *args):
         try:
             twitter = oauthtwitter.OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET)
             
             self.request_token = twitter.getRequestToken()
             print "obtained oauth request_token"
             print "requesting auth url"
             authorization_url = twitter.getAuthorizationURL(self.request_token)
             print "authorization url is " + authorization_url
             self.osso_rpc.rpc_run_with_defaults("osso_browser", "open_new_window", (authorization_url,))
             self.auth_account = account
             #ask the ui to prompt user to go to browser etc.
             self.ui.showOauthPrompts()


         except IOError, e:
            print "error"
            msg = 'Error retrieving oauth url '
            if hasattr(e, 'reason'):
                msg = msg + str(e.reason)

            if hasattr(e, 'code'):
                if (e.code == 401):
                    reason = "Not authorised: check uid/pwd"
                elif(e.code == 503):
                    reason = "Service unavailable"
                else:
                    reason = ""
                msg = msg + 'Server returned ' + str(e.code) + " : " + reason

            note = osso.SystemNote(self.osso_c)
            note.system_note_dialog(msg)


    def getAccessToken(self, widget):
         pin = self.ui.getOauthPIN()
         twitter = oauthtwitter.OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.request_token)
         access_token = twitter.getAccessToken(pin)
         print access_token
         self.access_token = access_token
         api = oauthtwitter.OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, access_token)
         self.auth_account.access_token = access_token
         #self.activeAccount.setAccessToken(access_token)
         self.ui.builder.get_object("OauthDialog").hide_all()
         self.ui.reload_account_window(widget, self.auth_account)


    def  store_creds(self, widget, *args):
        print "store_creds called"

        #store the values set
        self.username = self.ui.builder.get_object("UserName").get_text()
        self.password = self.ui.builder.get_object("Password").get_text()
        self.writeConfig()



    def selectImage(self, widget):
        #bring up a file choser to let people select images
        #imageChose = self.wTree.get_widget("filechooserdialog1")
        imageChose = self.ui.builder.get_object("filechooserdialog1")

        filter = gtk.FileFilter()
        filter.set_name("*.jpg")
        filter.add_pattern("*.jpg")
        imageChose.remove_filter(filter)
        imageChose.add_filter(filter)
        imageChose.set_filter(filter)
        imageChose.show()


    def twitPic(self, widget, *args):
        print "twitPic"
        #dialog = self.wTree.get_widget("filechooserdialog1")
        dialog = self.ui.builder.get_object("filechooserdialog1")
        file = dialog.get_filename()

        try:
            fin = open(file, "rb")
            jpgImage = fin.read()
            #tweet = self.wTree.get_widget("TweetText").get_text()
            tweet = self.ui.getEntryText()
            #see if we have just an empty string (eg eroneous button press)
            if (tweet == ""):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("You must enter a message first")
                print "No tweet to go with image"
                return

            # upload binary file with pycurl by http post
            c = pycurl.Curl()
            c.setopt(c.POST, 1)
            c.setopt(c.URL, "http://twitpic.com/api/uploadAndPost")
            c.setopt(c.HTTPPOST, [("media", (c.FORM_FILE, file)),
                                  ("username", self.activeAccount.getUsername()),
                                  ("password", self.activeAccount.getPassword()),
                                  ("message", tweet)])
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
            self.ui.setTweetText("")
            dialog.hide()
        except IOError:
            note = osso.SystemNote(self.osso_c)
            note.system_note_dialog("Failed to load selected image")
            print "couldn't read file"
        print file



    def end_refresh_threads(self):
	    self.activeAccount.stop_Location()
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
		    self.refreshtask = witter.RefreshTask(self.getTweetsWrapper, 0 , None)
		    self.refreshtask.start(self.timelineRefreshInterval * 60, self)
        if (self.DMsRefreshInterval != 0):
		    self.dmrefresh = witter.RefreshTask(self.getDMsWrapper, 0, None)
		    self.dmrefresh.start(self.DMsRefreshInterval * 60, self)
        if (self.mentionsRefreshInterval != 0):
		    self.mentionrefresh = witter.RefreshTask(self.getMentionsWrapper, 0, None)
		    self.mentionrefresh.start(self.mentionsRefreshInterval * 60, self)
        if (self.publicRefreshInterval != 0) :
		    self.publicrefresh = witter.RefreshTask(self.getPublicWrapper, 0, None)
		    self.publicrefresh.start(self.publicRefreshInterval * 60, self)
        if (self.searchRefreshInterval != 0) :
		    self.searchrefresh = witter.RefreshTask(self.getSearchWrapper, 0, None)
		    self.searchrefresh.start(self.searchRefreshInterval * 60, self)
        self.locationUpdateThread = witter.RefreshTask(self.startLocation, 0, None)
        self.locationUpdateThread.refresh()
        
        if (self.location):    
            print "location sharing enabled"
            
            self.activeAccount.start_Location()
        else:
            print "location sharing disabled"
            while (self.activeAccount.locationSetup == False):
                print "waiting for gps thread"
                time.sleep(2)
            self.activeAccount.stop_Location()
            
        print "end refresh setup"

    def startLocation(self, get_older=False, more=0, autoval=None):
        self.activeAccount.updateLocation()
    def setProfile(self, get_older=False, more=0, autoval=None):
        self.activeAccount.setProfileInfo()   
        
    def getTweetsWrapper(self, get_older=False, more=0, autoval=None):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getTweets(auto=autoval, older=get_older, get_count=more)
        self.ui.showBusy(-1)


    def getDMsWrapper(self, get_older=False, autoval=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getDMs(auto=autoval, older=get_older, get_count=more)
        self.ui.showBusy(-1)


    def getMentionsWrapper(self, get_older=False, autoval=None, more=0, *args):

        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getMentions(auto=autoval, older=get_older, get_count=more)
        self.ui.showBusy(-1)


    def getPublicWrapper(self, get_older=False, autoval=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getPublic(auto=autoval, older=get_older, get_count=more)
        self.ui.showBusy(-1)

    def getSearchWrapper(self, get_older=False, autoval=None, searchTerms=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        if searchTerms == None:
            if (autoval == 1):
                #if we manually his search get the latest content of the search box
                searchTerms = self.ui.getEntryText()
            else:
                searchTerms = self.search_terms
        print "calling getSearch with " + searchTerms
        self.activeAccount.getSearch(auto=autoval, searchTerms=searchTerms, older=get_older, get_count=more)
        self.ui.showBusy(-1)


    def getFriendsWrapper(self, get_older=False, autoval=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getFriends()
        self.ui.showBusy(-1)


    def getUserHistWrapper(self, get_older=False, autoval=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        user = self.ui.getEntryText()
        self.ui.set_title(self.serviceName + " " + user + " - History")
        self.activeAccount.getUserHistory(friend=user, auto=autoval)
        self.ui.setTweetText("")
        self.ui.showBusy(-1)

    def followUserWrapper(self, get_older=False, more=0, autoval=None):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAcount.FollowUser(widget, self.reply_to_name)
        self.ui.showBusy(-1)
  

    def getTrendsWrapper(self, get_older=False, autoval=None, more=0, *args):
        self.ui.showBusy(1)
        self.establish_connection()
        self.activeAccount.getTrends()
        self.ui.showBusy(-1)
        return "done"

    
    def searchWrapper(self, widget, searchTerms):
        print searchTerms
        refreshtask = witter.RefreshTask(self.getSearchWrapper, 0, None, search_terms=searchTerms)
        print "refreshing search for " + refreshtask.search_terms
        refreshtask.refresh()

    def getMore(self, more, *args):
        #call the get method for whichever liststore we're viewing
        curView = self.ui.getCurrentView()
        if (curView == self.ui.TIMELINE_VIEW):
            #self.getTweets()
            refreshtask = witter.RefreshTask(self.getTweetsWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.DM_VIEW):
            refreshtask = witter.RefreshTask(self.getDMsWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.MENTIONS_VIEW):

            refreshtask = witter.RefreshTask(self.getMentionsWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.PUBLIC_VIEW):
            refreshtask = witter.RefreshTask(self.getPublicWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.TRENDS_VIEW):
            refreshtask = witter.RefreshTask(self.getTrendsWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.FRIENDS_VIEW):
            refreshtask = witter.RefreshTask(self.getFriendsWrapper, more, None)
            refreshtask.refresh()
        elif (curView == self.ui.SEARCH_VIEW):
            refreshtask = witter.RefreshTask(self.getSearchWrapper, more, None)
            refreshtask.refresh()


    def get20More(self, *args):
        self.getMore(20)

    def get50More(self, *args):
        self.getMore(50)

    def get100More(self, *args):
        self.getMore(100)

    def get200More(self, *args):
        self.getMore(200)

    def showHist(self, widget, user):
        self.ui.showBusy(1)
        self.ui.hideActionButtons()
        self.ui.hideActionButtons()
        self.ui.toggle_view_to(widget, "user")
        self.ui.setTweetText(user)

        #need to strip the @ symbol from the user before we request their history
        refreshtask = witter.RefreshTask(self.getUserHistWrapper, 0, self.ui.showBusy)
        refreshtask.refresh()

        self.ui.showBusy(-1)


    def tweetAt(self, *args):
        self.ui.hideActionButtons()
        self.ui.setTweetText(self.reply_to_name)


    def tweetAtUser(self, widget, user, *args):
        self.ui.hideActionButtons()
        self.ui.hideActionButtons()
        self.ui.setTweetText(user)


    def setBitlyuid(self, widget):
         self.bitlyusername = widget.get_text()
         self.activeAccount.setBitlyCreds(self.bitlyusername, self.bitlyapikey)

    def setBitlyapiki(self, widget):
         self.bitlyapikey = widget.get_text()
         self.activeAccount.setBitlyCreds(self.bitlyusername, self.bitlyapikey)

    def expandBitlyUrls(self, data):
        if (self.bitlyusername != ""):
                words = data.split(" ")
                for word in words:
                    if re.search("http://bit.ly", word):
                        #appears to have a bitly URL so lets lengthen it
                        try:
                            bitlyapi = bitly.Api(login=self.bitlyusername, apikey=self.bitlyapikey)

                            longurl = bitlyapi.expand(word)
                            #having gotten the long url
                            #strip out the domain name and append it to the tweet
                            #after the bit.ly url in brackets
                            enddomain = int(longurl.find("/", 7, len(longurl)))
                            print enddomain
                            longurl = longurl[7:enddomain]

                            #switch the long url in to the data


                            data = data.replace(word, word + " (" + longurl + ")")
                        except bitly.BitlyError:
                            print "bitly gave error response"
                        except KeyError:
                            print "bitly gave key error response"
        return data


    def getShortenedURL(self, widget, urlEntry):
        #pop the urlshortening window off the stack
        hildon.WindowStack.get_default().pop_1()
        print "shortening URL " + urlEntry.get_text()
        if (self.bitlyusername != ""):
            try:
                bitlyapi = bitly.Api(login=self.bitlyusername, apikey=self.bitlyapikey)
                shortUrl = bitlyapi.shorten(urlEntry.get_text())
                #switch the long url in to the data
                self.ui.appendTweetText(shortUrl)
            except bitly.BitlyError:
                print "bitly gave error response"
            except KeyError:
                print "bitly gave key error response"

    def setActiveAccount(self, accountData):
        for account in self.accounts:
            if (account.getAccountData() == accountData):
                print "switching active account to " + account.getUsername()
                self.activeAccount = account
                self.ui.setWindowTitlePrefix("Witter(" + self.activeAccount.getUsername() + ")")
                


    def addNewAccount(self, accountData):
        newAccount = account.account(self.osso_c, accountData, self)
        self.accounts.append(newAccount)

    def deleteAccount(self, accountData):
        for account in self.accounts:
            if (account.getAccountData() == accountData):
                self.accounts.remove(account)
                self.config.accountList.remove(account.getAccountData())

    def cb_switch_view(self, interface, method, args, user_data):
         if method == 'open_mentions':
            self.ui.toggleviewto("mentions")
            self.ui.window.show()
            #self.ui.window.fullscreen()
            #self.ui.window.setActiveWindow()

         if method == 'open_dm':
            self.ui.toggleviewto("direct")
            self.ui.window.show()
            #self.ui.window.fullscreen()
            
            #self.ui.window.setActiveWindow()
            
    def _on_orientation_signal(self, orientation, stand, face, x, y, z):
         
         if (self.ui.activeWindow.get_is_topmost()):
             if ((orientation == 'portrait') & (self.ui.current_orientation == 'landscape') ):
                print "switching to portrait from " + self.ui.current_orientation
                #self.ui.orientation=orientation
                #self.ui.cell.set_property('wrap-width', 400)
                
                self.ui.icon_size = 30
                self.ui.load_theme_icons()
                self.ui.width=400
                if ((self.ui.activeWin !="home") & (self.ui.activeWin != None)):
                    
                    self.ui.toggleviewto(self.ui.activeWin)
                else:
                    widgetList = self.ui.accountvbox.get_children()
                    for widget in widgetList:
                        self.ui.accountvbox.remove(widget)
                    accounthbox = self.ui.account_summary()    
                    self.ui.accountvbox.pack_start(accounthbox,expand=False)
                    self.ui.accountvbox.show_all()
                    self.activeAccount.setProfileInfo()
                self.ui.current_orientation = 'portrait'
                
             if ((orientation == 'landscape') & (self.ui.current_orientation == 'portrait')):
                print "switching to landscape from " + self.ui.current_orientation
                #self.ui.orientation=orientation
                #self.ui.cell.set_property('wrap-width', 730)
                
                self.ui.icon_size = 48
                self.ui.load_theme_icons()
                self.ui.define_ui_buttons()
                self.ui.width=720
                if ((self.ui.activeWin !="home") & (self.ui.activeWin != None)):
                    self.ui.toggleviewto(self.ui.activeWin)
                else:
                    widgetList = self.ui.accountvbox.get_children()
                    for widget in widgetList:
                        self.ui.accountvbox.remove(widget)
                    accounthbox = self.ui.account_summary()    
                    self.ui.accountvbox.pack_start(accounthbox,expand=False)
                    self.ui.accountvbox.show_all()
                    self.activeAccount.setProfileInfo()
                
                self.ui.current_orientation = 'landscape'
         else:
            print "not top most window, not rotating"
             #print "refresh current view"
             #curView = self.ui.getCurrentView()  
             #if (curView == self.ui.TIMELINE_VIEW):
             #   self.ui.switch_view_to("timeline")
             #elif (curView == self.ui.DM_VIEW):
             #   self.ui.switch_view_to("direct")
             #elif (curView == self.ui.MENTIONS_VIEW):
             #   self.ui.switch_view_to("mentions")
             #elif (curView == self.ui.PUBLIC_VIEW):
             #   self.ui.switch_view_to("public")
             #elif (curView == self.ui.TRENDS_VIEW):
             #   self.ui.switch_view_to("trends")
             #elif (curView == self.ui.FRIENDS_VIEW):
             #   self.ui.switch_view_to("friends")
             #elif (curView == self.ui.SEARCH_VIEW):
             #   self.ui.switch_view_to("search")
             #elif (curView == self.ui.USERHIST_VIEW):
             #   self.ui.switch_view_to("user")
            
    def establish_connection(self):
        magic = 0xAA55 
        connection = conic.Connection()
        connection.connect("connection-event", self.connection_cb, magic)

        # The request_connection method should be called to initialize
        # some fields of the instance
        assert(connection.request_connection(conic.CONNECT_FLAG_NONE)) 
        
    def connection_cb(self, connection, event, magic):
        print "connection_cb(%s, %s, %x)" % (connection, event, magic)
 	
        status = event.get_status()
        error = event.get_error()
        iap_id = event.get_iap_id()
        bearer = event.get_bearer_type()
 	
        if status == conic.STATUS_CONNECTED:
            print "(CONNECTED (%s, %s, %i, %i)" % \
            (iap_id, bearer, status, error)
        elif status == conic.STATUS_DISCONNECTED:
            print "(DISCONNECTED (%s, %s, %i, %i)" % \
            (iap_id, bearer, status, error)
        elif status == conic.STATUS_DISCONNECTING:
            print "(DISCONNECTING (%s, %s, %i, %i)" % \
            (iap_id, bearer, status, error) 
            
    def getVersion(self):
        return self.version

if __name__ == "__main__":
    #this is just what initialises the app and calls run
    app = Witter()

    #cProfile.run('app.run()', 'witterprof')
    app.run()

