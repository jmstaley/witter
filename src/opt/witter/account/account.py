# Copyright (c) 2010 Daniel Would
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
#account class representing all the objects
#for access to an account and associated runtime tweets/etc

import twitter
import oauthtwitter
import gtk
import re
import osso
import hildon
import urllib2
import urllib
import httplib
import simplejson
import bitly
import accountData
import os.path
import gobject
import sys, os, time
from stat import *
import time
import datetime
import calendar
import locale
import email.utils as eut
import pynotify
import dbus
import location


class account():


    #these are the keys for witter on twitter
    CONSUMER_KEY = 'c0glxehHLYgzDqDMLjanA'
    CONSUMER_SECRET = 'V37SuM6o7PddlqqosLpYtIqyaLj0mgnFkGGKkJjN6I'
    ACTIVE = 1
    INACTIVE = 2
    status = ""
    avatar_size = 60
    friendCount = 0
    lat=None
    long = None
    location = True
    stopLocation=False
    savedSearches =[]
    _MCE_SERVICE = 'com.nokia.mce'
    _MCE_REQUEST_PATH = '/com/nokia/mce/request'
    _MCE_REQUEST_IF = 'com.nokia.mce.request'
    _ICD_SERVICE = 'com.nokia.icd'
    _ICD_REQUEST_PATH = '/com/nokia/icd'
    _ICD_REQUEST_IF = 'com.nokia.icd.connect'
    _CONNECTION = '[ANY]'
    _ENABLE_LED = 'req_led_pattern_activate'
    _DISABLE_LED = 'req_led_pattern_deactivate'
    _VIBRATE  = 'req_vibrator_pattern_activate'
    _VIBRATE_PATTERN= 'PatternChatAndEmail'
    _LED_PATTERN = 'PatternCommunicationIM'



    def __init__(self, osso_c, accData, controller):
        pynotify.init("Witter")
        self.bus = dbus.SystemBus()
        
        locale.setlocale(locale.LC_ALL,'en_US')
        self.controller = controller
        #these store all the data associated with this accounts tweets
        # the fields are : Name,sender_id,Tweet,TweetColour,id, type, timestamp, replyTo, source, pic, formatted_tweet
        self.tweetstore = gtk.ListStore(str, str, str, str, float, str, str , str, str, gtk.gdk.Pixbuf, str,bool)
        self.filteredtweetstore = gtk.ListStore(str, str, str, str, float, str, str , str, str, gtk.gdk.Pixbuf, str,bool)
        
        #then we want the same again to store dm's, mentions & pubilc timeline separately
        self.dmstore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.mentionstore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.publicstore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.trendstore = gtk.ListStore(str, str, str, str, str, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.friendsstore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.searchstore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        self.userhistorystore = gtk.ListStore(str, str, str, str, float, str, str, str, str, gtk.gdk.Pixbuf, str,bool)
        #store of avatar, filename, access count
        self.avatars = gtk.ListStore(gtk.gdk.Pixbuf, str, int, str)
        #base url can be set to any twitter compatible site, so we can support mutliple account types
        self.accountdata = accData
        self.osso_c = osso_c
        self.api = None
        self.connect()
        self.locationSetup=False
        self.dmnotify = pynotify.Notification("Witter","You have new DMs")
        self.dmnotify.add_action("clicked","Show DMs", self.dm_callback)
        
    def updateLocation(self):    
        #start up location tracking
        loop = gobject.MainLoop()
        self.control = location.GPSDControl.get_default()
        self.device = location.GPSDevice()
        #|location.METHOD_AGNSS
        self.control.set_properties(preferred_method=location.METHOD_ACWP|location.METHOD_GNSS,
                       preferred_interval=location.INTERVAL_DEFAULT)
 
        self.control.connect("error-verbose", self.on_error, loop)
        self.device.connect("changed", self.on_changed, self.control)
        self.control.connect("gpsd-stopped", self.on_stop, loop)
 
        gobject.idle_add(self.start_location, self.control)
        self.locationSetup=True
        loop.run()

    def stop_Location(self):
        print "stop location tracking"
        self.control.stop()

    def start_Location(self):
        print "start location tracking"
        self.control.start()
        
    def connect(self):
        if self.accountdata.password:
            print "Establishing api for " + self.accountdata.servicename + " using basic auth"
            self.api = twitter.Api(username=self.accountdata.username, password=self.accountdata.password)
            self.api.SetBaseUrl(self.accountdata.baseUrl)
            self.api.SetBaseSearchUrl(self.accountdata.searchUrl)
            
        if (self.accountdata.access_token != None):
            print "Establishing api for " + self.accountdata.servicename + " using oauth"
            self.api = oauthtwitter.OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.accountdata.access_token)
        if (self.api == None):
            print "Failed to establish api for " + self.accountdata.servicename
            return False
        else:
            print "Connection working ok"
            return True


    def getProfileInfo(self, username):
        print "getting profile info"
        user = self.api.GetUser(username)
        return user
        
    def setProfileInfo(self):
        tryCount=0
        #retry in the event of an error on the assumption it's transitory
        while (tryCount<=5):
            try:
                user = self.getProfileInfo(self.accountdata.username)
                self.controller.ui.profileTweetsLabel.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">TweetCount: </span>" +str(user.GetStatusesCount()))
                self.controller.ui.profileFollowerCount.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">Followers: </span>"+str(user.GetFollowersCount()))
                self.controller.ui.profileFollowingCount.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">Following: </span>" +str(user.GetFriendsCount()))
                self.friendCount = user.GetFriendsCount()
                self.controller.ui.accountNameLabel.set_markup(self.accountdata.username)
                status = user.GetStatus()
                print "formatting tweet"
                source = self.getSourceAppname(status.GetSource())
                formattedTweet =  self.format_tweet(user.GetName(), status.GetText(), status.GetCreatedAt(), source, status.GetInReplyToScreenName())
                
                self.controller.ui.profileLastTweet.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">Last Tweet: </span>" + formattedTweet)
                
                if (user.GetStatus().GetPlace() != None):
                    self.controller.ui.profileLocation.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">Location: </span>" +user.GetStatus().GetPlace().name)
                else:
                    if (user.GetLocation() != None):
                        self.controller.ui.profileLocation.set_markup("<span weight = 'bold' foreground=\"#6bd3ff\">Location: </span>" +user.GetLocation())
                    
                avatar, loaded = self.retrieve_avatar(user.GetProfileImageUrl(), str(user.id)+".jpg")   
                avatar = avatar.scale_simple(90, 90, gtk.gdk.INTERP_BILINEAR)
                self.controller.ui.profileImage.set_from_pixbuf(avatar)  
                self.getSavedSearches()
                self.getLists()
                return
            except AttributeError, ae:
                tryCount=tryCount+1
                print "Failed to load profile info" 
                print ae
            except IOError, e:
                tryCount = tryCount+1
                print "error"
                msg = 'Error retrieving tweets '
        print "Failed to retrieve profile info after 5 attempts"
            
    def clearSearchResults(self):
        self.searchstore.clear()
            
    def getAccountData(self):
        return self.accountdata

    def getAccountType(self):
        return self.accountdata.accessType

    def getUsername(self):
        return self.accountdata.username

    def getPassword(self):
        return self.accountdata.password

    def getServicename(self):
        return self.accountdata.servicename

    def getBaseUrl(self):
        return self.accountdata.baseUrl

    def setBaseUrl(self, url):
        self.accountdata.baseUrl = url

    def setSearchUrl(self, url):
        self.accountdata.searchUrl = url
    def getSearchUrl(self):
        return self.accountdata.searchUrl
    def getAccessToken(self):
        return self.accountdata.access_token
    def setAccessToken(self, access_token):
        self.accountdata.access_token = access_token

    def setStatus(self, status):
        self.accountdata.status = status

    def setBitlyCreds(self, username, apikey):
        self.accountdata.bitlyusername = username
        self.accountdata.bitlyapikey = apikey
    def getBitlyUid(self):
        return self.accountdata.bitlyusername
    def getBitlyapikey(self):
        return self.accountdata.bitlyapikey

    def setServiceCreds(self, username, password=None, access_token=None):
        self.accountdata.username = username
        if password:
            self.accountdata.password = password
            self.accountdata.accessType = "Basic"
            self.api = twitter.Api(username=self.accountdata.username, password=self.accountdata.password)
            #override the base url for a basic auth account, allows us to use non-twitter accounts
            self.api.SetBaseUrl(self.accountdata.baseUrl)
        if access_token:
            self.accountdata.access_token = access_token
            self.accountdata.accessType = "OAuth"
            self.api = oauthtwitter.OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.accountdata.access_token)
            self.api.SetBaseUrl(self.accountdata.baseUrl)

    #accessor methods that return the entire list of data
    #stores for this account under the different types
    def getTimeline(self):
        return self.tweetstore

    def getDmsList(self):
        return self.dmstore
    def getMentionsList(self):
        return self.mentionstore
    def getPublicList(self):
        return self.publicstore
    def getFriendsList(self):
        return self.friendsstore
    def getSearchList(self):
        return self.searchstore
    def getTrendsList(self):
        return self.trendstore
    def getUserHistoryList(self):
        return self.userhistorystore

    def getTweets(self, auto=0, older=False, get_count=20, * args):
               
        if (self.api == None):
            if (self.connect() != True):
                return
            
        print "getting tweets with " + self.accountdata.username
        print "base url = " + self.accountdata.baseUrl
        print "base url of api object = " + self.api.GetBaseUrl()
        receive_count = 0
        tryCount=0
        while (tryCount <5):
            try:
                #by default we get newer tweets
                if (older == False):
                    if self.accountdata.last_id == None:
                        data = self.api.GetFriendsTimeline()
                        rtdata = self.api.GetRetweets_to_user()
                    else:
                        print "refreshing since" + str(self.accountdata.last_id)
                        data = self.api.GetFriendsTimeline(since_id=self.accountdata.last_id, count=200)
                        rtdata = self.api.GetRetweets_to_user(since_id=self.accountdata.last_id, count=200)
                else:
                    if self.accountdata.oldest_id == None:
                        data = self.api.GetFriendsTimeline(count=get_count)
                        print "fetching retweets to user"
                        rtdata = self.api.GetRetweets_to_user(count=get_count)
                    else:
                        print "refreshing retweets prior to" + str(self.accountdata.oldest_id)
                        data = self.api.GetFriendsTimeline(max_id=self.accountdata.oldest_id, count=get_count)
                        rtdata = self.api.GetRetweets_to_user(max_id=self.accountdata.oldest_id, count=get_count)
                data += rtdata
                for x in data:
                     if x != None:
                         if (self.checkStoreForTweet(long(x.id),self.tweetstore)):
                             print "Tweet already in store"
                         else:
                             if (self.accountdata.last_id != None):
                                if (x.id == self.accountdata.last_id):
                                    continue
                             if (None != x.in_reply_to_status_id):
                                print "reply to " + x.in_reply_to_screen_name
                                #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                                reply_to = "In reply to: " + x.in_reply_to_screen_name + " - " + self.get_specific_tweet(x.in_reply_to_screen_name, x.in_reply_to_status_id)
                             else:
                                reply_to = ""
        
                             reply_to = reply_to.replace("&", "&amp;")
                             #need to store id numbers for oldest/newest
                             if self.accountdata.last_id == None:
                                self.accountdata.last_id = x.id
                             else:
                                #if we have an id stored, check if this one is 'newer' if so then store it
                                if long(self.accountdata.last_id) < long(x.id):
                                    self.accountdata.last_id = x.id
        
                             #also want to track the oldest we get hold of
                             if self.accountdata.oldest_id == None:
                                self.accountdata.oldest_id = x.id
                             else:
                                if long(self.accountdata.oldest_id) > long(x.id):
                                    self.accountdata.oldest_id = x.id
                             #strip the source app name from the url
                             source = self.getSourceAppname(x.source)
                             text = self.escapeText(x.text)
                             text = self.controller.expandBitlyUrls(text)
                             if (x.GetPlace() !=None):
                                 place = x.GetPlace().name
                             else:
                                 place=None
                             
                             pic = self.set_pic_for_id(str(x.user.GetId()), x.user.GetScreenName(), x.user.GetProfileImageUrl())
                             created_at = self.parse_time(x.created_at)
                             formatted_ts = self.format_timestamp(created_at)
                             formatted_tweet = self.format_tweet(x.user.screen_name, text, formatted_ts, source, reply_to, loc=place)
                             longid= long(x.id)
                             self.tweetstore.append([ "@" + x.user.screen_name, str(x.user.GetId()), "@" + x.user.screen_name + " : " + text, "", longid, "Tweet", x.created_at, reply_to, source, pic, formatted_tweet, True])
                             
                             receive_count = receive_count + 1
    
                if (receive_count > 0):
                    note = osso.SystemNote(self.osso_c)
                    result = note.system_note_infoprint(str(receive_count) + " Tweets Received")
                return    
            except IOError, e:
                tryCount = tryCount+1
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
                    msg = msg + 'Server returned ' + str(e.code) + " : " + reason
                print "get Tweets try : " + str(tryCount)+": " +msg
                print "sleep for 1 second, then try again"
                time.sleep(1)
            except httplib.BadStatusLine:
                tryCount = tryCount+1
                msg ="Bad Status Line"
                print "Network error - BadStatusLine"
                print "sleep for 1 second, then try again"
                time.sleep(1)
        print "Failed to retrieve tweets after 5 attempts"
        if (auto == 0):
            note = osso.SystemNote(self.osso_c)
            note.system_note_dialog(msg)
        
        

    def getMentions(self, auto=0, older=False, get_count=20, * args):
        if (self.api == None):
            if (self.connect() != True):
                return
        print "getting mentions"
        receive_count = 0
        tryCount=0
        while (tryCount <5):
            try:
                #by default we get newer tweets
                if (older == False):
                    if self.accountdata.last_mention_id == None:
                        data = self.api.GetReplies()
                    else:
                        print "refreshing since" + str(self.accountdata.last_mention_id)
                        data = self.api.GetReplies(since_id=self.accountdata.last_mention_id)
                else:
                    if self.accountdata.oldest_mention_id == None:
                        data = self.api.GetReplies(count=get_count)
                    else:
                        print "refreshing prior to" + str(self.accountdata.oldest_mention_id)
                        data = self.api.GetReplies(max_id=self.accountdata.oldest_mention_id, count=get_count)
    
                for x in data:
                     if (self.checkStoreForTweet(long(x.id),self.mentionstore)):
                         print "Tweet already in store"
                     else:
                         if (self.accountdata.last_mention_id != None):
                            if (x.id == self.accountdata.last_mention_id):
                                continue
                         if (None != x.in_reply_to_status_id):
                            print "reply to " + x.in_reply_to_screen_name
                            #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                            reply_to = "In reply to: " + x.in_reply_to_screen_name + " - " + self.get_specific_tweet(x.in_reply_to_screen_name, x.in_reply_to_status_id)
                         else:
                            reply_to = ""
    
                         reply_to = reply_to.replace("&", "&amp;")
                         #need to store id numbers for oldest/newest
                         if self.accountdata.last_mention_id == None:
                            self.accountdata.last_mention_id = x.id
                         else:
                            #if we have an id stored, check if this one is 'newer' if so then store it
                            if long(self.accountdata.last_mention_id) < long(x.id):
                                self.accountdata.last_mention_id = x.id
    
                         #also want to track the oldest we get hold of
                         if self.accountdata.oldest_mention_id == None:
                            self.accountdata.oldest_mention_id = x.id
                         else:
                            if long(self.accountdata.oldest_mention_id) > long(x.id):
                                self.accountdata.oldest_mention_id = x.id
                         #strip the source app name from the url
                         source = self.getSourceAppname(x.source)
                         text = self.escapeText(x.text)
                         text = self.controller.expandBitlyUrls(text)
                         pic = self.set_pic_for_id(str(x.user.GetId()), x.user.GetScreenName(), x.user.GetProfileImageUrl())
                         created_at = self.parse_time(x.created_at)
                         formatted_ts = self.format_timestamp(created_at)
                         formatted_tweet = self.format_tweet(x.user.screen_name, text, formatted_ts, source, reply_to)
                         self.mentionstore.append([ "@" + x.user.screen_name, str(x.user.GetId()), "@" + x.user.screen_name + " : " + text, "", long(x.id), "Tweet", x.created_at, reply_to, source, pic, formatted_tweet, True])
                         receive_count = receive_count + 1
    
                if (receive_count > 0):
                    if (self.controller.emailnotifications == False):
                        note = osso.SystemNote(self.osso_c)
                        result = note.system_note_infoprint(str(receive_count) + " Mentions Received")
                    else:
                        n = pynotify.Notification("Witter","You have "+str(receive_count)+" new mentions")
                        n.set_urgency(pynotify.URGENCY_CRITICAL)
                        icon= gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
                        n.set_hint("dbus-callback-default", "uk.wouldd.witter /uk/wouldd/witter uk.wouldd.witter open_mentions")
                        n.set_icon_from_pixbuf(icon)
                        rpc = osso.Rpc(self.osso_c)
                        rpc.rpc_run(self._MCE_SERVICE, self._MCE_REQUEST_PATH,self._MCE_REQUEST_IF,self._ENABLE_LED,rpc_args=(self._LED_PATTERN,"",""),use_system_bus=True)
                        rpc.rpc_run(self._MCE_SERVICE, self._MCE_REQUEST_PATH,self._MCE_REQUEST_IF,self._VIBRATE,rpc_args=(self._VIBRATE_PATTERN,"",""),use_system_bus=True)
                        n.show()
                return
            except IOError, e:
                tryCount=tryCount+1
                print "error"
                msg = 'Error retrieving mentions '
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
                if (auto == 0):
                    note = osso.SystemNote(self.osso_c)
                    note.system_note_dialog(msg)
                print msg
            except httplib.BadStatusLine:
                tryCount=tryCount+1
                msg ="Bad Status Line"
                print "Network error - BadStatusLine"
                print "sleep for 1 second, then try again"
                time.sleep(1)
                
        if (auto == 0):
          note = osso.SystemNote(self.osso_c)
          note.system_note_dialog(msg)

                 
    def getDMs(self, auto=0, older=False, get_count=20, * args):
        if (self.api == None):
            if (self.connect() != True):
                return
        print "getting dms"
        receive_count = 0
        try:
            #by default we get newer tweets
            if (older == False):
                if self.accountdata.last_dm_id == None:
                    data = self.api.GetDirectMessages()
                else:
                    print "refreshing since" + str(self.accountdata.last_mention_id)
                    data = self.api.GetDirectMessages(since_id=self.accountdata.last_dm_id)
            else:
                if self.accountdata.oldest_dm_id == None:
                    data = self.api.GetDirectMessages(count=get_count)
                else:
                    print "refreshing prior to" + str(self.accountdata.oldest_dm_id)
                    data = self.api.GetDirectMessages(max_id=self.accountdata.oldest_dm_id, count=get_count)

            for x in data:
                 if (self.checkStoreForTweet(long(x.id),self.dmstore)):
                     print "Tweet already in store"
                 else:
                     if (self.accountdata.last_dm_id != None):
                        if (x.id == self.accountdata.last_dm_id):
                            continue

                     #need to store id numbers for oldest/newest
                     if self.accountdata.last_dm_id == None:
                        self.accountdata.last_dm_id = x.id
                     else:
                        #if we have an id stored, check if this one is 'newer' if so then store it
                        if long(self.accountdata.last_dm_id) < long(x.id):
                            self.accountdata.last_dm_id = x.id

                     #also want to track the oldest we get hold of
                     if self.accountdata.oldest_dm_id == None:
                        self.accountdata.oldest_dm_id = x.id
                     else:
                        if long(self.accountdata.oldest_dm_id) > long(x.id):
                            self.accountdata.oldest_dm_id = x.id
                     user = x.GetSenderScreenName()
                     text = self.escapeText(x.text)
                     text = self.controller.expandBitlyUrls(text)
                     pic = self.set_pic_for_id(str(x.GetSenderId()), x.GetSenderScreenName(), "")
                     created_at = self.parse_time(x.created_at)
                     formatted_ts = self.format_timestamp(created_at)
                     formatted_tweet = self.format_tweet(user, text, formatted_ts, None, None)
                     self.dmstore.append([ "@" + user, x.GetSenderId(), "@" + user + " : " + text, "", long(x.id), "Tweet", x.created_at, "", "", pic, formatted_tweet, True])
                     receive_count = receive_count + 1

            if (receive_count > 0):
                if (self.controller.emailnotifications == False):
                    note = osso.SystemNote(self.osso_c)
                    result = note.system_note_infoprint(str(receive_count) + " DMs Received")
                else:
                    n = pynotify.Notification("Witter","You have "+str(receive_count)+" new DMs")
                    icon= gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
                    n.set_icon_from_pixbuf(icon)                
                    n.set_urgency(pynotify.URGENCY_CRITICAL)
                    n.set_hint("dbus-callback-default", "uk.wouldd.witter /uk/wouldd/witter uk.wouldd.witter open_dm")
                    rpc = osso.Rpc(self.osso_c)
                    rpc.rpc_run(self._MCE_SERVICE, self._MCE_REQUEST_PATH,self._MCE_REQUEST_IF,self._ENABLE_LED,rpc_args=(self._LED_PATTERN,"",""),use_system_bus=True)
                    rpc.rpc_run(self._MCE_SERVICE, self._MCE_REQUEST_PATH,self._MCE_REQUEST_IF,self._VIBRATE,rpc_args=(self._VIBRATE_PATTERN,"",""),use_system_bus=True)

                n.show()
        except IOError, e:
            print "error"
            msg = 'Error retrieving dms '
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
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog(msg)
            print msg
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
                 
    def getFriends(self, auto=0, older=False, get_count=20, * args):
        if (self.api == None):
            if (self.connect() != True):
                return
        print "getting Friends"
        receive_count = 0
        self.friendsstore.clear()
        try:
            #by default we get newer tweets
            page=0
            followers = self.friendCount
            moreFriends=True
            while (moreFriends):
                data = self.api.GetFriends(page=page)
                
                if ((followers -100) > 0):
                    page=page+1
                else:
                    moreFriends=False
                if (data != None):
                    for x in data:
                        #it's possible to follow someone that has never updated their status
                        if (x.status != None):
                            status = x.status.text
                            tweettime = x.status.created_at
                            source = x.status.source
                        else:
                            status = ""
                            tweettime = ""
                            status = ""
                        status = self.escapeText(status)
                        source = self.getSourceAppname(source)
                        pic = self.set_pic_for_id(str(x.id), x.GetScreenName(), x.GetProfileImageUrl())
                        created_at = self.parse_time(tweettime)
                        formatted_ts = self.format_timestamp(created_at)
                        formatted_tweet = self.format_tweet(x.screen_name, status, formatted_ts, source, None)
                        self.friendsstore.append([ "@" + x.screen_name, str(x.id), "@" + x.screen_name + " : " + status, "", long(x.id), "friend", tweettime, "", source, pic, formatted_tweet, True])
                        receive_count = receive_count + 1
    
                    if (receive_count > 0):
                        note = osso.SystemNote(self.osso_c)
                        result = note.system_note_infoprint(str(receive_count) + " Friends Received")
                    #update friend/follower counts etc
                
                followers = followers - receive_count
                
        except IOError, e:
            print "error"
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
                msg = msg + 'Server returned ' + str(e.code) + " : " + reason
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog(msg)
            print msg
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
        self.setProfileInfo()
                 
    def getPublic(self, auto=0, older=False, get_count=20, * args):
        if (self.api == None):
            if (self.connect() != True):
                return
        print "getting public"
        receive_count = 0
        try:
            #by default we get newer tweets
            if (older == False):
                if self.accountdata.last_public_id == None:
                    data = self.api.GetPublicTimeline()
                else:
                    print "refreshing since" + str(self.accountdata.last_public_id)
                    data = self.api.GetPublicTimeline(since_id=self.accountdata.last_public_id)
            else:
                if self.accountdata.oldest_public_id == None:
                    data = self.api.GetPublicTimeline(count=get_count)
                else:
                    print "refreshing prior to" + str(self.accountdata.oldest_public_id)
                    data = self.api.GetPublicTimeline(max_id=self.accountdata.oldest_public_id, count=get_count)

            for x in data:
                 if (self.checkStoreForTweet(long(x.id),self.publicstore)):
                     print "Tweet already in store"
                 else:
                     if (self.accountdata.last_public_id != None):
                        if (x.id == self.accountdata.last_public_id):
                            continue
                     if (None != x.in_reply_to_status_id):
                        print "reply to " + x.in_reply_to_screen_name
                        #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                        reply_to = "In reply to: " + x.in_reply_to_screen_name + " - " + self.get_specific_tweet(x.in_reply_to_screen_name, x.in_reply_to_status_id)
                     else:
                        reply_to = ""

                     reply_to = reply_to.replace("&", "&amp;")
                     #need to store id numbers for oldest/newest
                     if self.accountdata.last_public_id == None:
                        self.accountdata.last_public_id = x.id
                     else:
                        #if we have an id stored, check if this one is 'newer' if so then store it
                        if long(self.accountdata.last_public_id) < long(x.id):
                            self.accountdata.last_public_id = x.id

                     #also want to track the oldest we get hold of
                     if self.accountdata.oldest_public_id == None:
                        self.accountdata.oldest_public_id = x.id
                     else:
                        if long(self.accountdata.oldest_public_id) > long(x.id):
                            self.accountdata.oldest_public_id = x.id
                     #strip the source app name from the url
                     source = self.getSourceAppname(x.source)
                     text = self.escapeText(x.text)
                     text = self.controller.expandBitlyUrls(text)
                     pic = self.set_pic_for_id(str(x.user.GetId()), x.user.GetScreenName(), x.user.GetProfileImageUrl())
                     created_at = self.parse_time(x.created_at)
                     formatted_ts = self.format_timestamp(created_at)
                     formatted_tweet = self.format_tweet(x.user.screen_name, text, formatted_ts, source, reply_to)
                     self.publicstore.append([ "@" + x.user.screen_name, x.user.GetId(), "@" + x.user.screen_name + " : " + text, "", long(x.id), "Tweet", x.created_at, reply_to, source, pic, formatted_tweet, True])
                     receive_count = receive_count + 1

            if (receive_count > 0):
                note = osso.SystemNote(self.osso_c)
                result = note.system_note_infoprint(str(receive_count) + " public timeline Received")

        except IOError, e:
            print "error"
            msg = 'Error retrieving public timeline '
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
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog(msg)
            print msg
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
       
    def getUserHistory(self, friend="", auto=0, older=False, get_count=20, * args):
        if (self.api == None):
            if (self.connect() != True):
                return
        print "getting User history for " + friend
        #self.userhistorystore.clear()
        receive_count = 0
        try:
            #by default we get newer tweets
            data = self.api.GetUserTimeline(id=friend)

            for x in data:
                 if (self.checkStoreForTweet(long(x.id),self.userhistorystore)):
                     print "Tweet already in store"
                 else:
                     if (None != x.in_reply_to_status_id):
                        print "reply to " + x.in_reply_to_screen_name
                        #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                        reply_to = "In reply to: " + x.in_reply_to_screen_name + " - " + self.get_specific_tweet(x.in_reply_to_screen_name, x.in_reply_to_status_id)
                     else:
                        reply_to = ""

                     reply_to = reply_to.replace("&", "&amp;")

                     #strip the source app name from the url
                     source = self.getSourceAppname(x.source)
                     text = self.escapeText(x.text)
                     text = self.controller.expandBitlyUrls(text)
                     pic = self.set_pic_for_id(str(x.user.GetId()), x.user.GetScreenName(), x.user.GetProfileImageUrl())
                     created_at = self.parse_time(x.created_at)
                     formatted_ts = self.format_timestamp(created_at)
                     formatted_tweet = self.format_tweet(x.user.screen_name, text, formatted_ts, source, reply_to)
                     self.userhistorystore.append([ "@" + x.user.screen_name, x.user.GetId(), "@" + x.user.screen_name + " : " + text, "", long(x.id), "Tweet", x.created_at, reply_to, source, pic, formatted_tweet, True])
                     receive_count = receive_count + 1

                     if (receive_count > 0):
                        note = osso.SystemNote(self.osso_c)
                        result = note.system_note_infoprint(str(receive_count) + " user timeline Received")

        except IOError, e:
            print "error"
            msg = 'Error retrieving user timeline '
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
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog(msg)
            print msg
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
        except httplib.sslerror:
            print "Network error - SslError"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")

    def getSearch(self, searchTerms="", auto=0, older=False, get_count=20, * args):
        print "performing search"
        receive_count = 0
        #if we're not getting older tweets then pay attention to whether we want to clear search results
        if older==False:
            if self.controller.search_clear:
                self.searchstore.clear()
        #when manually triggered use the current text in the entry field
        if (auto == 0):
            searchTerms = self.controller.ui.getEntryText()
        if (searchTerms == ""):
            print "nothing to search"
            return
        #split the tweet text on any comma , 

        searchTermsList = searchTerms.split(",")
        #call search on each of the terms in the search str
        for term in searchTermsList:
            term = unicode(term).encode('utf-8')
            #then we need to urlencode so that we can use twitter chars like @ without
            #causing problems
            search = urllib.urlencode({ 'q' : term })

            try:
                print "search url " + self.accountdata.searchUrl + 'search.json?' + search
                json = urllib2.urlopen(self.accountdata.searchUrl + 'search.json?' + search)

                #JSON is awesome stuff. we get given a long string of json encoded information
                #which contains all the tweets, with lots of info, we decode to a json object
                data = simplejson.loads(json.read())
                #then this line does all the hard work. Basicaly for evey top level object in the JSON
                #structure we call out getStatus method with the contents of the USER structure
                #and the values of top level values text/id/created_at

                results = data['results']
                for x in results:
                    if (self.checkStoreForTweet(long(x['id']),self.searchstore)):
                        print "Tweet already in store"
                    else:
                        reply_to = ""
                        reply_to = reply_to.replace("&", "&amp;")
                        text = self.escapeText(x['text'])
                        text = self.controller.expandBitlyUrls(text)
                        #strip the source app name from the url
                        source = self.getSourceAppname(x['source'])
                        print "search result from userid: " + str(x['from_user_id'])
                        pic = self.get_pic_for_name(str(x['from_user']))
                        created_at = self.parse_time(x['created_at'])
                        formatted_ts = self.format_timestamp(created_at)
                        formatted_tweet = self.format_tweet(x['from_user'], text, formatted_ts, source, reply_to)
                        self.searchstore.append([ "@" + x['from_user'], str(x['from_user_id']), "@" + x['from_user'] + " : " + text, "", long(x['id']), "Search", x['created_at'], reply_to, source, pic, formatted_tweet, True])
                        receive_count = receive_count + 1
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
                    msg = msg + 'Server returned ' + str(e.code) + " : " + reason
                if (auto == 0):
                    note = osso.SystemNote(self.osso_c)
                    note.system_note_dialog(msg)
            except httplib.BadStatusLine:
                print "Network error - BadStatusLine"
                if (auto == 0):
                    note = osso.SystemNote(self.osso_c)
                    note.system_note_dialog("Network error occured. Please try again")
            except httplib.sslerror:
                print "Network error - SslError"
                if (auto == 0):
                    note = osso.SystemNote(self.osso_c)
                    note.system_note_dialog("Network error occured. Please try again")

    def getLists(self, *args):
        try:
            listdata = self.api.GetLists(self.accountdata.username)
            print listdata
            lists = listdata['lists']
            for list in lists:
                print list['id']
                print list['name']
                print list['member_count']
                membersData = self.api.GetListMembers(self.accountdata.username, list['id'])
                #print listMembers
                listMembers = membersData['users']
                for user in listMembers:
                    #print user
                    print user['screen_name']
        except IOError, e:
            msg = 'Error retrieving lists and members results '
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
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            note = osso.SystemNote(self.osso_c)
            note.system_note_dialog("Network error occured. Please try again")
        
            

    def getSavedSearches(self, * args):
        print "getting saved search terms"
        #self.searchstore.clear()
        self.savedSearches = []
        #call search on each of the terms in the search str
        try:
            
            data = self.api.GetSavedSearches()

            
            print data
           
            for x in data:
                query = x['query']
                print "found saved search: " + query
                self.savedSearches.append(query)
        except IOError, e:
            msg = 'Error retrieving saved searches results '
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
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            note = osso.SystemNote(self.osso_c)
            note.system_note_dialog("Network error occured. Please try again")
        

                
    def getTrends(self, *args):

        print "getting Trending topics"
        #first clear the previous 10
        self.trendstore.clear()

        try:
            json = urllib2.urlopen(self.accountdata.searchUrl + 'trends.json')
            #JSON is awesome stuff. we get given a long string of json encoded information
            #which contains all the tweets, with lots of info, we decode to a json object
            data = simplejson.loads(json.read())
            #then this line does all the hard work. Basicaly for evey top level object in the JSON
            #structure we call out getStatus method with the contents of the USER structure
            #and the values of top level values text/id/created_at
            trends = data['trends']
            for x in trends:
                self.trendstore.append([x['name'], "", x['name'] + " :" + x['url'], "", "", "dm", "", "", "", None, x['name'] + " :" + x['url']])

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
                msg = msg + 'Server returned ' + str(e.code) + " : " + reason
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog(msg)
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
        except httplib.sslerror:
            print "Network error - SslError"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")

    def get_specific_tweet(self,username,tweet_id):
        try:
            data = self.api.GetStatus(tweet_id)
            return data.text
        except IOError, e:
            print e
            return "protected tweet"


    def getSourceAppname(self, sourceUrl):
         #need to strip the source name from the html we get given
         if (re.search("</a>", sourceUrl)):
            startChar = sourceUrl.find(">")
            endChar = sourceUrl.find("</a>")
            sourceUrl = sourceUrl[startChar + 1:endChar]
         if (re.search("&lt;/a&gt;", sourceUrl)):
            startChar = sourceUrl.find("&gt;")
            endChar = sourceUrl.find("&lt;/a&gt;")
            sourceUrl = sourceUrl[startChar + 4:endChar]
         return sourceUrl

    def newTweet(self, tweet, reply_to_name=None, reply_to_id=None):
        #The other main need of a twitter client
        #the ability to post an update
        #get the tweet text from the input box

        #see if we have just an empty string (eg eroneous button press)
        if (tweet == ""):
            return False
        if (self.controller.location & self.locationSetup):
            if self.device:
                if self.device.fix:
                    if self.device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
                        print "lat = %f, long = %f" % self.device.fix[4:6]
                        self.lat, self.long = self.device.fix[4:6]
            
        try:

            if (reply_to_name != None):
                if (re.search(reply_to_name, tweet)):
                    #this is a reply
                    print "reply to " + reply_to_name
                    if (self.controller.location):
                        print "Tweeting with location info"
                        print str(self.lat)
                        print str(self.long)
                        status = self.api.PostUpdate(tweet, reply_to_id, lat=self.lat, long=self.long)
                    else:
                        status = self.api.PostUpdate(tweet, reply_to_id)
                else:
                    if (self.controller.location):
                        print "tweeting with location info"
                        print str(self.lat)
                        print str(self.long)
                        
                        status = self.api.PostUpdate(tweet, lat=self.lat, long=self.long)
                    else:
                        status = self.api.PostUpdate(tweet)
            else:
                if (self.controller.location):
                    print "Tweeting with location info"
                    print str(lat)
                    print str(long)
                    status = self.api.PostUpdate(tweet, lat=self.lat, long=self.long)
                else:
                    status = self.api.PostUpdate(tweet)
            return True
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
                    msg = msg + 'Server returned ' + str(e.code) + " : " + reason

            note = osso.SystemNote(self.osso_c)

            result = note.system_note_infoprint(msg)
            return False
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
            return False

    def FavouriteTweet(self, widget, id, *args):
        
        try:
                
                data = self.api.CreateFavoriteForID(id)
                note = osso.SystemNote(self.osso_c)
                result = note.system_note_infoprint("Favourite Tweet set ")
        except IOError, e:
            print "error"
            msg = 'Error favouriting ' + str(id) + ' '
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
            print msg

    def FollowUser(self, widget, name, *args):
        #strip out the @ which isn't really part of the username
        name = name.replace("@", "")
        print "follow: " + name
        try:
                print "using oauth to follow"
                data = self.api.CreateFriendship(name)
                note = osso.SystemNote(self.osso_c)
                result = note.system_note_infoprint("Now following " + name)
                #fetching tweets for newly followed user to add to timeline
                data = self.api.GetUserTimeline(id=data.GetId())

                for x in data:

                    if (None != x.in_reply_to_status_id):
                        print "reply to " + x.in_reply_to_screen_name
                        #we don't want anything showing up if there is no reply_to, so all teh formatting is held here including the newline
                        reply_to = "In reply to: " + x.in_reply_to_screen_name + " - " + self.get_specific_tweet(x.in_reply_to_screen_name, x.in_reply_to_status_id)
                    else:
                        reply_to = ""

                    reply_to = reply_to.replace("&", "&amp;")

                    #strip the source app name from the url
                    source = self.getSourceAppname(x.source)
                    text = self.escapeText(x.text)
                    text = self.controller.expandBitlyUrls(text)
                    pic = self.set_pic_for_id(str(x.user.GetId()), x.user.GetScreenName(), x.user.GetProfileImageUrl())
                    created_at = self.parse_time(x.created_at)
                    formatted_ts = self.format_timestamp(created_at)
                    formatted_tweet = self.format_tweet(x.user.screen_name, text, formatted_ts, source, reply_to)
                    self.tweetstore.append([ "@" + x.user.screen_name, x.user.GetId(), "@" + x.user.screen_name + " : " + text, "", long(x.id), "Tweet", x.created_at, reply_to, source, pic, formatted_tweet, True])
                #update follower count
                self.setProfileInfo()
        except IOError, e:
            print "error"
            msg = 'Error following ' + name + ' '
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
            print msg

    def UnFollowUser(self, widget, name, *args):
        #strip out the @ which isn't really part of the username
        name = name.replace("@", "")
        print "follow: " + name
        try:
                print "using oauth to unfollow"
                data = self.api.DestroyFriendship(name)
                note = osso.SystemNote(self.osso_c)
                result = note.system_note_infoprint("No longer following " + name)
                #update following count
                self.setProfileInfo()
        except IOError, e:
            print "error"
            msg = 'Error unfollowing ' + name + ' '
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
            print msg

    def newRetweet(self, id):
        #performs a 'newstyle' retweet for the specific tweet id
        print "retweeting "+str(id)
        try:
            self.api.reTweet(long(id))
            note = osso.SystemNote(self.osso_c)
            result = note.system_note_infoprint("ReTweeted Successfully")
        
        except IOError, e:
            print "error"
            msg = 'Error rewteeting ' + str(id) + ' '
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
            print msg
        except httplib.BadStatusLine:
            print "Network error - BadStatusLine"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
        except httplib.sslerror:
            print "Network error - SslError"
            if (auto == 0):
                note = osso.SystemNote(self.osso_c)
                note.system_note_dialog("Network error occured. Please try again")
        
    def escapeText(self, text):
        #switch certain chars for escape sequences
        text = text.replace("&", "&amp;")
        return text

    def get_pic_for_name (self, name):
        item = self.avatars.get_iter_first()
        while (item != None):
            if (self.avatars.get_value(item, 3) == name):
                return self.avatars.get_value(item, 0)
            item = self.avatars.iter_next(item)
        return gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")

    def set_pic_for_id(self, id, name, url):
        return self.set_pix(id + ".jpg", url, id, name)

    def set_pix(self, filename, url, id, name):
        item = self.avatars.get_iter_first ()
        #first find out if we already loaded this avatar
        while (item != None):
            pic = (self.avatars.get_value (item, 1))

            if (pic == filename):
                #if we access a user more than 10 times, reload their avatar
                if (self.avatars.get_value(item, 2) > 10):
                    print "refreshing avatar for " + id
                    pixbuf, success = self.retrieve_avatar(url, filename)
                    if (success):
                        self.avatars.set_value(item, 0, pixbuf)
                        self.avatars.set_value(item, 2, 0)
                        self.update_all_avatars(id, pixbuf)
                    return pixbuf
                else:
                    
                    self.avatars.set_value(item, 2, (self.avatars.get_value(item, 2) + 1))
                    return self.avatars.get_value(item, 0)
            item = self.avatars.iter_next(item)
        #if we make it here we didn't have it loaded already
        if (os.path.isfile("/home/user/.witterPics/" + self.accountdata.servicename + "/" + filename)):
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file("/home/user/.witterPics/" + self.accountdata.servicename + "/" + filename)
            except gobject.GError:
                #failed to load file, delete it, and go fetch a new one
                print "corrupted avatar file found, deleting it"
                os.remove("/home/user/.witterPics/" + self.accountdata.servicename + "/" + filename)
                print "bad file deleted, returning default icon"
                pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
            pixbuf = pixbuf.scale_simple(self.avatar_size, self.avatar_size, gtk.gdk.INTERP_BILINEAR)
            self.avatars.append([pixbuf, filename, 1, name])
            
            return pixbuf
        else:
            try:
                pixbuf, success = self.retrieve_avatar(url, filename)
                if (success == True):
                    self.avatars.append([pixbuf, filename, 1, name])
                    self.update_all_avatars(id, pixbuf)
                else:
                    print "assiging temp pixbuf"
            except IOError, e:
                print "io error"
                print e
                print "failed to find avatar for user: " + filename
                pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
        return pixbuf

    def retrieve_avatar(self, url, filename):
        try:
            if (os.path.isdir("/home/user/.witterPics") != True):
                os.mkdir("/home/user/.witterPics")
            if (os.path.isdir("/home/user/.witterPics/" + self.accountdata.servicename) != True):
                os.mkdir("/home/user/.witterPics/" + self.accountdata.servicename)

            webFile = urllib.urlopen(url)
            
            localFile = open("/home/user/.witterPics/" + self.accountdata.servicename + "/" + filename, 'w')
            localFile.write(webFile.read())
            webFile.close()
            localFile.close()
            pixbuf = gtk.gdk.pixbuf_new_from_file("/home/user/.witterPics/" + self.accountdata.servicename + "/" + filename)
            pixbuf = pixbuf.scale_simple(self.avatar_size, self.avatar_size, gtk.gdk.INTERP_BILINEAR)
        except IOError, e:
            print e
            print "failed to retreive picture for " + url + " : " + filename
            pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
            return pixbuf, False
        except UnicodeError, e2:
            print e2
            print "failed to retreive picture for " + url + " : " + filename
            pixbuf = gtk.gdk.pixbuf_new_from_file("/opt/witter/icons/default/tweet.png")
            return pixbuf, False
        return pixbuf, True

    def format_tweet(self, user, tweet, time, source, reply_to, loc=None):
        tweet = tweet.replace("&amp;", "&")
        tweet = gobject.markup_escape_text(tweet)
        if (source != None):
            source = gobject.markup_escape_text(source)
        line = " <span weight = 'bold' foreground=\"#6bd3ff\">" + user + " : </span> "

        words = tweet.split(" ")
        for word in words:
            if (word.startswith("@")):
                if (word.endswith(".") | word.endswith(":")):
                    word = " <span foreground = \"#0075b5\">" + word[0:len(word)-1] + "</span>" + word[len(word)-1:len(word)]
                else:
                    word = " <span foreground = \"#0075b5\">" + word + "</span>"
            if (word.startswith("http:") | word.startswith("www")):
                word = "<span foreground=\"#0075b5\">" + word + "</span>"
            if (word.startswith("witter") | word.startswith("Witter") | word.startswith("#witter") | word.startswith("#Witter")):
                word = "<span foreground=\"yellow\">" + word + "</span>"
            line = line + " " + word

        if (reply_to != None):
            if (reply_to != ""):
                line = line + "\n<span size='small'> " + reply_to + "</span>"
        if (source != None):
            if (source.startswith("Witter")):
                source = "<span foreground=\"yellow\">" + source + "</span>"
            if loc:
                line = line + "\n<span weight='light' size='x-small'>" + time + " from " + source + " in " + loc + "</span>"
            else:
                line = line + "\n<span weight='light' size='x-small'>" + time + " from " + source + "</span>"
        else:
            line = line + "\n<span weight='light' size='x-small'>" + time + "</span>"
        return line

    def get_age(self, filename):
        now = time.time()
        try:
            st = os.stat(filename)

        except os.error, msg:
            sys.stderr.write("can't stat %r: %r\n" % (filename, msg))
            status = 1
            st = ()
            return 10
        if st:
            anytime = st[ST_MTIME]
            fileage = time.strftime('%a %d %b/%Y %H:%M', time.localtime(anytime))

            print "file ages is " + str(fileage)
        return fileage


    def update_all_avatars(self, id, pixbuf):
        print "updating all stored images for " + id
        self.update_avatars(id, pixbuf, self.tweetstore)
        self.update_avatars(id, pixbuf, self.mentionstore)
        self.update_avatars(id, pixbuf, self.dmstore)
        self.update_avatars(id, pixbuf, self.publicstore)
        self.update_avatars(id, pixbuf, self.friendsstore)
        self.update_avatars(id, pixbuf, self.searchstore)
    def update_avatars(self, id, pixbuf, store):
        #updates all instances of tweets from the specified id with the pixbuf
        item = store.get_iter_first()
        while item != None:
            if (store.get_value(item, 1) == id):
                print ("Found pixbuf to update")
                store.set_value(item, 9, pixbuf)
            item = store.iter_next(item)

    def parse_time(self, timestr):
        #parses a time string from twitter into a date object
        #timestr = "Wed Apr 07 09:45:28 +0000 2010"
        try:
            if (timestr.find("+") == -1):
                #negative offset from UTC
                strippedDate = timestr[0: timestr.find("-")] + "+0000" + timestr[timestr.find("-") + 5: len(timestr)]
                hoursOffset = int(timestr[timestr.find("-") + 1:timestr.find("-") + 3])
                print "offset hours = -" + str(hoursOffset)
                minus = True
            else:
                #positive offset from UTC
                strippedDate = timestr[0: timestr.find("+")] + "+0000" + timestr[timestr.find("+") + 5: len(timestr)]
                hoursOffset = int(timestr[timestr.find("+") + 1:timestr.find("+") + 3])
                print "offset hours = +" + str(hoursOffset)
                minus = False
        except ValueError:
            print "error parsing timestamp: " +timestr
            return datetime.datetime.today()   
        try:


            msgDate = datetime.datetime.strptime(strippedDate, "%a %b %d %H:%M:%S +0000 %Y")
        except ValueError:
            try:
                print "trying timestamp format Mon, Jan 01 2010 00:00:00 +0000"
                msgDate = datetime.datetime.strptime(strippedDate, "%a, %d %b %Y %H:%M:%S +0000")
            except ValueError:
                try:
                    print "trying third format"
                    msgDate = datetime.datetime.strptime(strippedDate, "%a %b %d %H:%M:%S +0000 %Y")
                except ValueError, e:
                    print e 
                    print "returning datestamp for now failed to parse >" + timestr + "< stripped to: >" +strippedDate+"<"
                    print "expected something in the form >Thu Aug 26 12:00:00 +0000 2010<"
                    return datetime.datetime.today()

        timestamp = msgDate.time()
        print timestamp.tzinfo
        t = time.time()

        # we want something like '2007-10-18 14:00+0100'
        if time.localtime(t).tm_isdst and time.daylight:
            tz = time.altzone
        else:
            tz = time.timezone
        if (minus):
            td = datetime.timedelta(hours=0 - hoursOffset, seconds=tz)
        else:
            td = datetime.timedelta(hours=hoursOffset, seconds=tz)
        
        timestamp = msgDate - td
        mytz = "%+4.4d" % (tz / -(60 * 60) * 100) # time.timezone counts westwards!
        print timestamp

        dt = msgDate
        return timestamp
    
    def format_timestamp(self,timestamp):
        return timestamp.strftime('%a, %b %d %Y %H:%M:%S')  # %Z (timezone) would be empty


    def mentions_callback(self, args):
        print "mentions callback"
        self.controller.ui.switchViewTo(self.controller.ui.treeview,"mentions")

    def dm_callback(self, args):
        print "dms callback"
        self.controller.ui.switchViewTo(self.controller.ui.treeview,"direct")

    def checkStoreForTweet(self, id, store):
        #check if this id is already in our stores, if so return True
        item = store.get_iter_first()
        while item != None:
            entryId = store.get_value(item, 4)
            if (long(entryId) == id):
                return True
            item = store.iter_next(item)
        return False  
    
    def filterTweets(self, sourceList, filter):   
        temptweetstore = sourceList
        item = temptweetstore.get_iter_first()
        
        while item != None:
            tweet = sourceList.get_value(item, 2)
            tweet = tweet.lower()
            filter = filter.lower()
            if (tweet.find(filter) != -1):
                print "filtering " + tweet
                temptweetstore.set_value(item,11,False)
            item = temptweetstore.iter_next(item)
        return temptweetstore
    
    def unfilterTweets(self, sourceList, filter):   
        temptweetstore = sourceList
        item = temptweetstore.get_iter_first()
        
        while item != None:
            tweet = sourceList.get_value(item, 2)
            if (tweet.find(filter) != -1):
                print "filtering " + tweet
                temptweetstore.set_value(item,11,True)
            item = temptweetstore.iter_next(item)
        return temptweetstore
    
    def unfilterAllTweets(self, sourceList):   
        temptweetstore = sourceList
        item = temptweetstore.get_iter_first()
        
        while item != None:
            tweet = sourceList.get_value(item, 2)
            temptweetstore.set_value(item,11,True)
            item = temptweetstore.iter_next(item)
        return temptweetstore
    
    def on_error(self,control, error, data):
        print "location error: %d... quitting" % error
        data.quit()
 
    def on_changed(self,device, data):
        if self.stopLocation:
            #stoppping location tracking
            data.stop()
            self.stopLocation = False
        if not device:
            return
        if device.fix:
            if device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
                self.lat, self.long = device.fix[4:6]
    
    def on_stop(self,control, data):
        print "quitting"
        data.quit()
 
    def start_location(self,data):
        data.start()
        return False
    
    
        
