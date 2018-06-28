from colorcycletemplate import ColorCycleTemplate
import time
import RPi.GPIO as GPIO
import apa102
import threading

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

plus_pin = 26
minus_pin = 19
red_RGB_pin = 27
green_RGB_pin = 17
blue_RGB_pin = 4
mode_pin = 2
red_light_pin = 20
green_light_pin = 21

GPIO.setup(plus_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Plus
GPIO.setup(minus_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Minus
GPIO.setup(red_RGB_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Red RGB
GPIO.setup(green_RGB_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Green RGB
GPIO.setup(blue_RGB_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Blue RGB
GPIO.setup(mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Mode RGB
GPIO.setup(red_light_pin, GPIO.OUT) # Red led
GPIO.setup(green_light_pin, GPIO.OUT) # Green led

red_RGB = 0
green_RGB = 0
blue_RGB = 0
state = "plus"
modes = ["solid", "rainbow", "theater_chase"]
mode_number = 0
speed = 0.011

NUM_LED = 109

GPIO.output(red_light_pin, GPIO.LOW)
GPIO.output(green_light_pin, GPIO.HIGH)

#========================
#=BUTTON PRESS DETECTION=
#========================

def button_press_plus(plus_pin):
	print(plus_pin)
	if (modes[mode_number] == "rainbow") or (modes[mode_number] == "theater_chase"):
		global speed
		speed_change = 0.005
		if speed < 0.007:
			speed_change = 0.001
		if speed > 0.001:
			print("Increase speed")
			speed = speed - speed_change
	elif modes[mode_number] == "solid":
		global state
		state = "plus"
		GPIO.output(red_light_pin, GPIO.LOW)
		GPIO.output(green_light_pin, GPIO.HIGH)

def button_press_minus(minus_pin):
	print("minus")
	if (modes[mode_number] == "rainbow") or (modes[mode_number] == "theater_chase"):
		global speed
		speed_change = 0.005
		if speed < 0.006:
			speed_change = 0.001
		if speed < 0.031:
			print ("Decrease speed")
			speed = speed + speed_change
	elif modes[mode_number] == "solid":
		global state
		state = "minus"
		GPIO.output(red_light_pin, GPIO.HIGH)
		GPIO.output(green_light_pin, GPIO.LOW)

def change_solid_color(pin):
	if pin == red_RGB_pin:
		global red_RGB
		red = GPIO.input(red_RGB_pin)
		while red == False:
			print("Change red")
			red = GPIO.input(red_RGB_pin)
			red_RGB = calculate_new_color(red_RGB)
			print("Red: " + str(red_RGB))
			update_solid_color()
			time.sleep(0.2)

	if pin == green_RGB_pin:
		global green_RGB
		green = GPIO.input(green_RGB_pin)
		while green == False:
			print("Change green")
			green = GPIO.input(green_RGB_pin)
			green_RGB = calculate_new_color(green_RGB)
			print("Green: " + str(green_RGB))
			update_solid_color()
			time.sleep(0.2)

	if pin == blue_RGB_pin:
		global blue_RGB
		blue = GPIO.input(blue_RGB_pin)
		while blue == False:
			print("Change blue")#
			blue = GPIO.input(blue_RGB_pin)
			blue_RGB = calculate_new_color(blue_RGB)
			print("Blue: " + str(blue_RGB))
			update_solid_color()
			time.sleep(0.2)

def button_press_change_mode(mode_pin):
	print("Change mode")
	global mode_number
	mode_number += 1
	if mode_number == len(modes):
		mode_number = 0
	print("New mode number: " + str(mode_number))

	if modes[mode_number] == "solid":
		update_solid_color()
	elif modes[mode_number] == "rainbow":
		start_rainbow_thread()
	elif modes[mode_number] == "theater_chase":
		start_theater_chase_thread()
	else:
		print("ERROR: NO MODE FOUND")

#==========================
#=Add events for threading=
#==========================

GPIO.add_event_detect(plus_pin, GPIO.FALLING, callback = button_press_plus, bouncetime = 300)
GPIO.add_event_detect(minus_pin, GPIO.FALLING, callback = button_press_minus, bouncetime = 300)
GPIO.add_event_detect(red_RGB_pin, GPIO.FALLING, callback = change_solid_color, bouncetime = 300)
GPIO.add_event_detect(green_RGB_pin, GPIO.FALLING, callback = change_solid_color, bouncetime = 300)
GPIO.add_event_detect(blue_RGB_pin, GPIO.FALLING, callback = change_solid_color, bouncetime = 300)
GPIO.add_event_detect(mode_pin, GPIO.FALLING, callback = button_press_change_mode, bouncetime = 1000)

def start_rainbow_thread():
	print("Starting new rainbow thread")
	start_rainbow = threading.Thread(target = start_rainbow_cycle)
	start_rainbow.start()

def start_theater_chase_thread():
	print("Starting new theater chase thread")
	start_theater_chase = threading.Thread(target = start_theater_chase_cycle)
	start_theater_chase.start()

#=========
#=Classes=
#=========

class Solid(ColorCycleTemplate):
	def init(self, strip, num_led):
		for led in range(0, num_led):
			strip.set_pixel(led, red_RGB, green_RGB, blue_RGB)

	def update(self, strip, num_led, num_steps_per_cycle, current_step, current_cycle):
		return 0

class Rainbow(ColorCycleTemplate):
	def start(self):
		"""This method does the actual work."""
		try:
			strip = apa102.APA102(num_led=self.num_led,
				global_brightness=self.global_brightness,
				mosi = self.MOSI, sclk = self.SCLK,
				order=self.order) # Initialize the strip

			self.init(strip, self.num_led) # Call the subclasses init method
			strip.show()
			current_cycle = 0
			continue_loop = 1
			while modes[mode_number] == "rainbow":
				for current_step in range (self.num_steps_per_cycle):
					continue_loop = self.update(strip, self.num_led,
						self.num_steps_per_cycle,
						current_step, current_cycle)
					if modes[mode_number] == "rainbow":
						strip.show() # repaint if required
					else:
						break
					time.sleep(self.pause_value) # Pause until the next step
		except KeyboardInterrupt:
			print('Interupted...')
			self.cleanup(strip)

	def update(self, strip, num_led, num_steps_per_cycle, current_step, current_cycle):
		scale_factor  = 255 / num_led
		start_index = 255 / num_steps_per_cycle * current_step
		for i in range(num_led):
			led_index = start_index + i * scale_factor
			led_index_rounded_wrapped = int(round(led_index, 0)) % 255
			pixel_color = strip.wheel(led_index_rounded_wrapped)
			strip.set_pixel_rgb(i, pixel_color)
		time.sleep(speed)
		return 1

class TheaterChase(ColorCycleTemplate):
	def start(self):
		"""This method does the actual work."""
		try:
			strip = apa102.APA102(num_led=self.num_led,
				global_brightness=self.global_brightness,
				mosi = self.MOSI, sclk = self.SCLK,
				order=self.order) # Initialize the strip

			self.init(strip, self.num_led) # Call the subclasses init method
			strip.show()
			current_cycle = 0
			continue_loop = 1
			while modes[mode_number] == "theater_chase":
				for current_step in range (self.num_steps_per_cycle):
					continue_loop = self.update(strip, self.num_led,
						self.num_steps_per_cycle,
						current_step, current_cycle)
					if modes[mode_number] == "theater_chase":
						strip.show() # repaint if required
					else:
						break
					time.sleep(self.pause_value) # Pause until the next step
		except KeyboardInterrupt:
			print('Interupted...')
			self.cleanup(strip)

	def update(self, strip, num_led, num_steps_per_cycle, current_step, current_cycle):
		start_index = current_step % 7
		color_index = strip.wheel(int(round(255/num_steps_per_cycle * current_step, 0)))

		for pixel in range(num_led):
			if ((pixel+start_index) % 7 == 0) or ((pixel+start_index) % 7 == 1):
				strip.set_pixel_rgb(pixel, 0)
			else:
				strip.set_pixel_rgb(pixel, color_index)
		time.sleep(speed)
		return 1

#====================
#=color schemes defs=
#====================

def update_solid_color():
	global NUM_LED
	my_cycle = Solid(num_led = NUM_LED, pause_value = 0, num_steps_per_cycle = 1, num_cycles = 1)
	my_cycle.start()

def start_rainbow_cycle():
	my_cycle = Rainbow(num_led = NUM_LED, pause_value = 0, num_steps_per_cycle = 255, num_cycles = 1)
	my_cycle.start()

def start_theater_chase_cycle():
	my_cycle = TheaterChase(num_led = NUM_LED, pause_value = 0, num_steps_per_cycle = 255, num_cycles = 1)
	my_cycle.start()

#============
#=Other defs=
#============

def calculate_new_color(color_value):
	global state
	if state == "plus" and color_value < 240:
		color_value += 16
	elif state == "plus" and color_value > 236 and color_value < 256:
		color_value = 255
	elif state == "minus" and color_value > 15:
		color_value += -16
	elif state == "minus" and color_value > 0 and color_value < 16:
		color_value = 0
	return color_value

while True:
	time.sleep(2)
	print("Thread count: " + str(threading.active_count()))
	print("Current_mode: " + modes[mode_number])
	print("Current threads: ")
	for t in threading.enumerate():
		print(t)
	print(" ")
