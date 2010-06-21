#encapsulates the config options for witter
import gtk
import pygtk

class Config():
    def __init__(self):
        #thse are the defaults for the values stored in a config
        self.font_size = 18
        self.textcolour = "#FFFFFF"
        #default colours are the ones used in the hildon window buttons
        self.bg_top_color = "#6bd3ff"
        self.bg_bottom_color = "#0075b5"

        self.timelineRefreshInterval = 30
        self.mentionsRefreshInterval = 30

        self.DMsRefreshInterval = 30
        self.publicRefreshInterval = 0
        self.searchRefreshInterval = 0
        #we use the busy counter to track the number of busy threads
        #and show a progres/busy indicator whilst it's more than 0

        self.search_terms = ""


        self.bitlyusername = ""
        self.bitlyapikey = ""

        self.accountList = []
