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


   def __init__(self, callback, loop_callback, complete_callback=None):
       #takes in the method to call to get tweets, eg getTweets, getMentions ec
       self.callback = callback
       #and the call back to give updates on progress
       self.loop_callback = loop_callback
       #and something to tell when we're finished
       self.complete_callback = complete_callback
       self._stopped = False

   def _start(self, sleep,*args ):
       #loop forever, or until someone calls stop on this thread
	while (self._stopped != True):
		count = 0;
		self.callback(*args)
		#sleep and check, wake up every 10 seconds and check if we've been told to end
		while ((count != (sleep/10)) & (self._stopped !=True)):
			time.sleep(10)
			count = count +1;
		
#not yet used, this was from an example I found, I may use it to show some kind of 'busy updating' indicator
#but I've not figured out how to yet
   def _loop(self, args):
       print "looping"
       self.loop_callback(*args)

   def start(self, *args, **kwargs):
       threading.Thread(target=self._start, args=args, kwargs=kwargs).start()

   def stop(self):
       print "stopping thread"
       self._stopped = True
