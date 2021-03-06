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

#this class is used to kick of threads that refresh feeds
class RefreshTask(object):


   def __init__(self, callback, extraMsgs, loop_callback, search_terms=None,complete_callback=None):
       #takes in the method to call to get tweets, eg getTweets, getMentions ec
       self.callback = callback
       #and the call back to give updates on progress
       self.loop_callback = loop_callback
       #and something to tell when we're finished
       self.complete_callback = complete_callback
       self.search_terms=search_terms
       if search_terms !=None:
           print "refresh thread primed with searchterms " + search_terms
       self._stopped = False
       self.extraMsgs = extraMsgs

   def _start(self, sleep, *args):
       #loop forever, or until someone calls stop on this thread
	while (self._stopped != True):
		count = 0;
		self.callback(autoval=1)
		#set the refresh flag back to false
		self.refresh = False
		#sleep and check, wake up every 10 seconds and check if we've been told to end
		while (count != (sleep / 10)):
			time.sleep(10)
			if (self._stopped == True):
				print "killing thread"
				return
			if (self.refresh == True):
				#exit the while look
				break
			count = count + 1;

#not yet used, this was from an example I found, I may use it to show some kind of 'busy updating' indicator
#but I've not figured out how to yet
   def _loop(self, args):
       print "looping"
       self.loop_callback(*args)

   def start(self, *args, **kwargs):
       threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

   def _refresh(self, *args):
	   #just call the callback and end
       if (self.extraMsgs != 0):
           if (self.search_terms != None):
               print "refresh specific search term" +self.search_terms
               self.callback(autoval=1, get_older=True, more=self.extraMsgs, searchTerms=self.search_terms)
           else:
               self.callback(autoval=0, get_older=True, more=self.extraMsgs)
       else:
           if (self.search_terms != None):
               print "refresh specific search term" +self.search_terms
               self.callback(autoval=1, get_older=False, more=self.extraMsgs, searchTerms=self.search_terms)
           else:
               self.callback(autoval=0, get_older=False, more=self.extraMsgs)

   def refresh(self, *args, **kwargs):
	   #used to do a single refresh in background thread
	 threading.Thread(target=self._refresh, args=args, kwargs=kwargs).start()

   def stop(self):
       print "stopping thread"
       self._stopped = True
