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
import threading
import thread
import gobject
import gtk
import time
import string
gtk.gdk.threads_init()
import urllib2

#this class is used to kick of threads that refresh feeds
class BitLy(object):

    def __init__(self, username, apikey):
       #takes in the method to call to get tweets, eg getTweets, getMentions ec
       self.username = username
       self.apikey = apikey

    def get_short_url(self, url):
        #condenses a url with bitly and returns a short form
        try:
            print url
            req_url = "http://api.bit.ly/shorten?version=2.0.1&format=json&longUrl=" + url + "&login=" + self.username + "&apiKey=" + self.apikey
            print req_url
            response = urllib2.urlopen(req_url)
            data = response.read()

            print shortUrl
            return shortUrl
        except IOError, e:
            msg = 'Error shortening url '
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
            print msg
        #if we fail for some reason - just return the unshortened url
        return url

    def get_expanded_url(self, url):
        #exands bit.ly urls back to normal form for display
        try:
            print url
            req_url = "http://api.bit.ly/expand?version=2.0.1&format=json&shortUrl=" + url + "&login=" + self.username + "&apiKey=" + self.apikey
            print req_url
            response = urllib2.urlopen(req_url)
            longUrl = response.read()
            print longUrl
            return longUrl
        except IOError, e:
            msg = 'Error shortening url '
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
            print msg
        #if we fail for some reason - just return the unshortened url
        return url
