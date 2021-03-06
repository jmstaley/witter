
import gtk
import pango
import pangocairo
import cairo
import gobject

class witterCellRender(gtk.GenericCellRenderer):
	__gproperties__ = {
			'text': (gobject.TYPE_STRING,
				'Text to be displayed',
				'Text to be displayed',
				'',
				gobject.PARAM_READWRITE	),
			'markup': (gobject.TYPE_STRING,
				'markup type',
				'markup type',
				'',
				gobject.PARAM_READWRITE),
			'backgroundt_r': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundt_b': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundt_g': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundt_p': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundb_r': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundb_b': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundb_g': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'backgroundb_p': (gobject.TYPE_INT,
				'Background of the cell',
				'The background of the cell',
				0,
				65535,
				0,
				gobject.PARAM_READWRITE),
			'timestamp': (gobject.TYPE_STRING,
				'timestamp to be displayed',
				'timestamp to be displayed',
				'',
				gobject.PARAM_READWRITE),
			'replyto': (gobject.TYPE_STRING,
				'reply_to Text to be displayed',
				'reply_to Text to be displayed',
				'',
				gobject.PARAM_READWRITE),
			'source': (gobject.TYPE_STRING,
				'source Text to be displayed',
				'source Text to be displayed',
				'',
				gobject.PARAM_READWRITE),
			'font_size': (gobject.TYPE_INT,
				'font_size',
				'font_size',
				0,
				50,
				0,
				gobject.PARAM_READWRITE)
			}
	rect_height = 0
	font_size = 16

	def __init__(self):
		print "renderer init"
		gtk.GenericCellRenderer.__init__(self)

		self.__properties = {}

	def on_get_size(self, widget, cell_area):
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 480)
		ctx = cairo.Context(surface)
		cr = pangocairo.CairoContext(ctx)
		if (self.get_property('text') == None):
			print "called to render a tweet with no text?"
			h = 50
		else:
			if (self.get_property('replyto') == None):
				h = self.calculate_height(cr, self.get_property('text'), widget)
			else:
				h = self.calculate_height(cr, self.get_property('text') + self.get_property('replyto'), widget)

		rect_height = h
		if cell_area == None:
			return (0, 0, 758, h)
		x = cell_area.x
		y = cell_area.x
		w = cell_area.width

		return (x, y, w, h)

	def do_set_property(self, key, value):
		self.__properties[key] = value

	def do_get_property(self, key):
		return self.__properties[key]

	def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
		#get a cairo context object

		cairo_context = pangocairo.CairoContext(window.cairo_create())

		x = cell_area.x
		y = cell_area.y
		w = cell_area.width
		h = cell_area.height

		#render out backing rectangle
		self.render_rect(cairo_context, x, y, widget.allocation.width - 8, h)

		pat = cairo.LinearGradient(x, y, x, y + h)
		color = gtk.gdk.Color(red=self.get_property('backgroundt_r'), green=self.get_property('backgroundt_g'), blue=self.get_property('backgroundt_b'), pixel=self.get_property('backgroundt_p'))
		## #6bd3ff
		pat.add_color_stop_rgba(
							0.0,
							self.get_cairo_color(color.red),
							self.get_cairo_color(color.green),
							self.get_cairo_color(color.blue),
							1)
		## #0075b5
		color = gtk.gdk.Color(red=self.get_property('backgroundb_r'), green=self.get_property('backgroundb_g'), blue=self.get_property('backgroundb_b'), pixel=self.get_property('backgroundb_p'))
		pat.add_color_stop_rgb(
							1.0,
							self.get_cairo_color(color.red),
							self.get_cairo_color(color.green),
							self.get_cairo_color(color.blue))


		cairo_context.set_source(pat)
		cairo_context.fill()


		#we want to calculate the actual height to render the backing so we need the space required
		#to render the string using the specified font and font size
		cairo_context.set_source_rgba(1, 1, 1, 1)
		layout = cairo_context.create_layout()
		font = pango.FontDescription("Sans")
		font.set_size(pango.SCALE * (self.get_property('font_size')))
		font.set_style(pango.STYLE_NORMAL)
		font.set_weight(pango.WEIGHT_BOLD)
		layout.set_font_description(font)
		layout.set_width(pango.SCALE * w)
		layout.set_wrap(pango.WRAP_WORD)


		#get the text as a unicode string
		tweet = unicode(self.get_property('text'))
		line = ""
		words = tweet.split(" ")
		for word in words:
			if (word.startswith("@")):
				word = "<span foreground=\"black\">" + word + "</span>"
			if (word.startswith("http:")):
				word = "<span foreground=\"blue\">" + word + "</span>"
			line = line + " " + word

		#set the starting position for text display
		cairo_context.move_to(x + 10, ((y + 10)))


		layout.set_markup(line)
			#layouts start again from begining not where you left off with last word
		inkRect, logicalRect = layout.get_pixel_extents()
		tweet_x, tweet_y, tweet_w, tweet_h = logicalRect

		cairo_context.show_layout(layout)
		if ((self.get_property('replyto') != "") & (self.get_property('replyto') != None)):
			#process any retweet text
			layout = cairo_context.create_layout()
			cairo_context.set_source_rgba(1, 1, 1, 1)
			font = pango.FontDescription("Sans")
			font.set_size(pango.SCALE * (self.get_property('font_size') - 2))
			font.set_style(pango.STYLE_NORMAL)
			font.set_weight(pango.WEIGHT_BOLD)
			layout.set_font_description(font)
			layout.set_wrap(pango.WRAP_WORD)
			layout.set_width(pango.SCALE * w)
			#set position under the main tweet text
			cairo_context.move_to(x + 10, ((y + tweet_h + 10)))
			layout.set_text(self.get_property('replyto'))
			#layouts start again from begining not where you left off with last word
			cairo_context.show_layout(layout)

		cairo_context.set_source_rgba(1, 1, 1, 1)
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(12)
		ts_x_bearing, ts_y_bearing, ts_width, ts_height = cairo_context.text_extents("From " + str(self.get_property('source')) + " at " + str(self.get_property('timestamp')))[:4]
		#position in the bottom right, in set by the width of the timestamp, and a little padding
		cairo_context.move_to(x + (w - (ts_width + 10)), y + (h - 5))
		cairo_context.show_text("From " + str(self.get_property('source')) + " at " + str(self.get_property('timestamp')))

	def render_rect(self, cr, x, y, w, h):
		'''
		create a rectangle with rounded corners
		'''

		x0 = x
		y0 = y
		rect_width = w
		rect_height = h

		radius = 10

		#draw the first half with rounded corners
		x1 = x0 + rect_width
		y1 = y0 + rect_height
		cr.move_to(x0, y0 + radius)
		cr.curve_to(x0, y0 + radius, x0, y0, x0 + radius, y0)
		cr.line_to(x1 - radius, y0)
		cr.curve_to(x1 - radius, y0, x1, y0, x1, y0 + radius)
		cr.line_to(x1, y1 - radius)
		cr.curve_to(x1, y1 - radius, x1, y1, x1 - radius, y1)

		cr.line_to(x0 + radius, y1)
		cr.curve_to(x0 + radius, y1, x0, y1, x0, y1 - radius - 1)
		cr.close_path()
		#draw the second half


	def calculate_height(self, cairo_context, text, widget):
		#we want to calculate the actual height to render the backing so we need the space required
		#to render the string using the specified font and font size


		layout = cairo_context.create_layout()
		font = pango.FontDescription("Sans")
		font.set_size(pango.SCALE * (self.get_property('font_size')))
		font.set_style(pango.STYLE_NORMAL)
		font.set_weight(pango.WEIGHT_BOLD)
		layout.set_font_description(font)
		layout.set_width(pango.SCALE * 780)
		layout.set_wrap(pango.WRAP_WORD)
		layout.set_text(text)

		inkRect, logicalRect = layout.get_pixel_extents()
		tweet_x, tweet_y, width, tweet_h = logicalRect

		return tweet_h + 20

	def get_cairo_color(self, color):
		ncolor = color / 65535.0
		return ncolor


	def on_activate(self, event, widget, path, background_area, cell_area, flags):

		pass

	def on_start_editing(self, event, widget, path, background_area, cell_area, flags):

		pass

	def get_seg_len_for_font_size(self, cairo_context, font_size, w):
		#figure out the rendered width of a single char at this font_size
		# work out how many chars would fill our width
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(font_size)
		#we want an average that will work for a normal sentence makeup, so the width of upper/lower narrow/wide and space chars is used
		x_bearing, y_bearing, width, height = cairo_context.text_extents("IiiE: ")[:4]
		chars_per_line = int(w / width) + 1
		return chars_per_line * 3


gobject.type_register(witterCellRender)
