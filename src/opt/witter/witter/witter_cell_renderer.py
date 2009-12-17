
import gtk
import pango
import cairo
import gobject

class witterCellRender(gtk.GenericCellRenderer):
	__gproperties__ = {
			'text': (gobject.TYPE_STRING,
				'Text to be displayed',
				'Text to be displayed',
				'',
				gobject.PARAM_READWRITE
				),
			'background': (gobject.TYPE_STRING,
				'Background of the cell',
				'The background of the cell',
				'#00FF00',
				gobject.PARAM_READWRITE
				),
			'timestamp': (gobject.TYPE_STRING,
				'timestamp to be displayed',
				'timestamp to be displayed',
				'',
				gobject.PARAM_READWRITE
				),
			'replyto': (gobject.TYPE_STRING,
				'reply_to Text to be displayed',
				'reply_to Text to be displayed',
				'',
				gobject.PARAM_READWRITE
				),
			'font_size': (gobject.TYPE_INT,
				'font_size',
				'font_size',
				0,
				50,
				0,
				gobject.PARAM_READWRITE
				)
			}
	rect_height = 0
	font_size = 18
	
	def __init__(self):
		#gobject.GObject.__init__(self)
		gtk.GenericCellRenderer.__init__(self)
		self.__properties = {}
		#gtk.GenericCellRenderer.__init__(self)
	
	def on_get_size(self, widget, cell_area):
		#print "on_get_size, ", locals()
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 480)
		ctx = cairo.Context(surface)
		h = self.calculate_height(ctx, self.get_property('text') + self.get_property('replyto'), widget)
		
		rect_height = h
		if cell_area == None:
			return (0,0,758,h)
		x = cell_area.x
		y = cell_area.x
		w = cell_area.width
		
		return (x,y,w,h)

	def do_set_property(self, key, value):
		self.__properties[key] = value
	
	def do_get_property(self, key):
		return self.__properties[key]

	def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
		#get a cairo context object
		cairo_context = window.cairo_create()
		
		x= cell_area.x
		y = cell_area.y
		w= cell_area.width
		h = cell_area.height 
		
		#render out backing rectangle
		self.render_rect(cairo_context, x, y, widget.allocation.width - 8, h)
		
		pat = cairo.LinearGradient(x, y, x, y + h)
		color = gtk.gdk.color_parse("#6495ED")
		pat.add_color_stop_rgba(
							0.0,
							self.get_cairo_color(color.red),
							self.get_cairo_color(color.green),
							self.get_cairo_color(color.blue),
							1
							)
		color = gtk.gdk.color_parse("#5F9EA0")
		pat.add_color_stop_rgba(
							0.5,
							self.get_cairo_color(color.red),
							self.get_cairo_color(color.green),
							self.get_cairo_color(color.blue),
							1
							)
		color = gtk.gdk.color_parse("#6495ED")
		pat.add_color_stop_rgb(
							1.0,
							self.get_cairo_color(color.red),
							self.get_cairo_color(color.green),
							self.get_cairo_color(color.blue)
							)


		cairo_context.set_source(pat)
		cairo_context.fill()

		
		#we want to calculate the actual height to render the backing so we need the space required
		#to render the string using the specified font and font size
		cairo_context.set_source_rgba(1, 1, 1, 1)
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(self.get_property('font_size'))
		
		x_bearing, y_bearing, width, height = cairo_context.text_extents(self.get_property('text'))[:4]
		
		
		#get the text
		tweet = self.get_property('text')
		
		seg_len = self.get_seg_len_for_font_size(cairo_context,self.get_property('font_size'),(w-20))
		words = tweet.split(" ")
		line = ""
		linecount = 0
		#set the starting position for text display
		cairo_context.move_to(x+10, ((y+height)))
		for word in words:
			
			if ((len(line) + len(word) + 1) > seg_len):
				#set the position for the line of text, we start in the top quarter then drop in text heigh increments
				cairo_context.move_to(x+10, ((y+height) + ((linecount+1)*height) +2))
												
				#set the line string to the word we didn't add
				line = word
				linecount = linecount +1
			else:
				line = line + " "+word
			if ( word.startswith("@")):
				cairo_context.set_source_rgba(0, 0, 0, 1)
			elif ( word.startswith("http:")):
				cairo_context.set_source_rgba(0, 1, 1, 1)
			else:
				cairo_context.set_source_rgba(1, 1, 1, 1)
			word = word.replace("&amp;","&")
			word = word.replace("&lt;","<")
			word = word.replace("&gt;",">")
			cairo_context.show_text(word + " ")
			
		if (self.get_property('replyto') != ""):
			#process any retweet text
			
			cairo_context.set_source_rgba(1, 1, 1, 1)
			
			cairo_context.set_font_size(self.get_property('font_size') -5)
			x_bearing, y_bearing, width, height = cairo_context.text_extents(self.get_property('replyto'))[:4]
			cairo_context.move_to(x+10, ((y+height) + ((linecount+1)*height) +self.get_property('font_size') -5))
			seg_len = self.get_seg_len_for_font_size(cairo_context,self.get_property('font_size')-5,(w-20))
			retweet = self.get_property('replyto')
			retweetwords = retweet.split(" ")
			for word in retweetwords:
			
				if ((len(line) + len(word) + 1) > seg_len):
					#set the position for the line of text, we start in the top quarter then drop in text heigh increments
					cairo_context.move_to(x+10, ((y+height) + ((linecount+2)*height) +self.get_property('font_size') -5))
													
					#set the line string to the word we didn't add
					line = word
					linecount = linecount +1
				else:
					line = line + " "+word
				if ( word.startswith("@")):
					cairo_context.set_source_rgba(0, 0, 0, 1)
				elif ( word.startswith("http:")):
					cairo_context.set_source_rgba(0, 1, 1, 1)
				else:
					cairo_context.set_source_rgba(1, 1, 1, 1)
				word = word.replace("&amp;","&")
				word = word.replace("&lt;","<")
				word = word.replace("&gt;",">")
				cairo_context.show_text(word + " ")
				
			
		#if ( line != ""):
			# show the last line
		#	cairo_context.move_to(x+10, ((y+height) + ((linecount))*height) +2)
		#	cairo_context.show_text(line)	
			
		cairo_context.set_source_rgba(1, 1, 1, 1)
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(self.get_property('font_size') -5)
		ts_x_bearing, ts_y_bearing, ts_width, ts_height = cairo_context.text_extents(self.get_property('timestamp'))[:4]
		#position in the bottom right, in set by the width of the timestamp, and a little padding
		cairo_context.move_to(x+(w-(ts_width+10)), y+(h-5))
		cairo_context.show_text(self.get_property('timestamp'))

#	def render_rect(self, cr, x, y, w, h):
		#render a rectangle
#		cr.rectangle(x,y,w,h)
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
		cr.curve_to(x0, y0+radius, x0, y0, x0 + radius, y0)
		cr.line_to(x1 -radius, y0)
		cr.curve_to(x1-radius, y0, x1, y0, x1, y0 + radius)
		cr.line_to(x1, y1-radius)
		cr.curve_to(x1, y1-radius, x1, y1, x1 -radius, y1)
		
		cr.line_to(x0 +radius, y1)
		cr.curve_to(x0+radius, y1, x0, y1, x0, y1-radius -1)
		cr.close_path()
		#draw the second half
		
	
	def calculate_height(self, cairo_context, text, widget):
		#we want to calculate the actual height to render the backing so we need the space required
		#to render the string using the specified font and font size
		
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(self.get_property('font_size'))
		
		x_bearing, y_bearing, width, height = cairo_context.text_extents(text)[:4]
		#figure out how many times we need to split the string to fit on the screen
		divide_text = width / (widget.allocation.width - 8)
		#round the value to an int and plus 1
		divide_text = int(divide_text) + 1
		#the rectangle height is the height of one line of text plus spacing * the number of lines needed
		rect_height = divide_text * (height +4)
		rect_height = rect_height + (2*height)
		return rect_height
	
	def get_cairo_color(self, color):
		ncolor = color/65535.0
		return ncolor
		

	def on_activate(self, event, widget, path, background_area, cell_area, flags):
		
		pass

	def on_start_editing(self, event, widget, path, background_area, cell_area, flags):
		
		pass

	def get_seg_len_for_font_size(self,cairo_context, font_size, w):
		#figure out the rendered width of a single char at this font_size
		# work out how many chars would fill our width
		cairo_context.select_font_face("Georgia",
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
		cairo_context.set_font_size(font_size)
		#we want an average that will work for a normal sentence makeup, so the width of upper/lower narrow/wide and space chars is used
		x_bearing, y_bearing, width, height = cairo_context.text_extents("IiiE: ")[:4]
		chars_per_line = int(w/width) +1
		return chars_per_line*3
		
		
gobject.type_register(witterCellRender)
