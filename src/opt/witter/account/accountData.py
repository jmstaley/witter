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
class accountdata():
    ACTIVE = 1
    INACTIVE = 2

    def __init__(self):
        #base url can be set to any twitter compatible site, so we can support mutliple account types
        self.servicename = "Twitter"
        self.baseUrl = "https://twitter.com/"
        self.searchUrl = "https://search.twitter.com/"
        self.username = ""
        self.password = None
        self.accessType = "Basic"
        #override the base url for a basic auth account, allows us to use non-twitter accounts

        self.access_token = None

        self.bitlyusername = None
        self.bitlyapikey = None

        self.last_id = None
        self.oldest_id = None
        self.last_dm_id = None
        self.oldest_dm_id = None
        self.last_mention_id = None
        self.oldest_mention_id = None
        self.last_public_id = None
        self.oldest_public_id = None
        self.last_friend_history_id = None
        self.oldest_friend_history_id = None
        self.status = self.INACTIVE
