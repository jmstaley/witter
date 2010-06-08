class oauthDialog:
    def __init__(self, parent):
        self.builder = gtk.Builder()
        self.builder.add_from_file("/usr/share/witter/witter.ui")

        dialog = self.builder.get_object("OauthDialog")
        dialog.set_title("Twitter Credentials")
        dialog.connect("response", self.gtk_widget_hide)
        dialog.show_all()
