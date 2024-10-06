import random, time
from machine import Pin, freq, Timer
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.config import Config
from lib.hydra.beeper import Beeper
from font import vga1_8x16 as small_font
from font import vga2_16x32 as big_font
import neopixel


freq(240_000_000)
led = neopixel.NeoPixel(Pin(21), 1, bpp=3)

tft = Display(use_tiny_buf=True)

blight = tft.backlight
blight.freq(1000)
blight.duty_u16(40000)

kb = UserInput()
beep = Beeper()

numbers = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."}

config = Config()
ui_color = config.palette[8]
bg_color = config.palette[2]


def start_timer(time_qty, units):
    time_started = time.time()
    time_amount = float(time_qty)
    seconds_to_count = 0
    if units == "seconds":
        seconds_to_count = time_amount
    elif units == "minutes":
        seconds_to_count = time_amount * 60
    elif units == "hours":
        seconds_to_count = time_amount * 60 * 60

    display = ""
    prev_display = ""
    time_left = seconds_to_count

    display_x = random.randint(4, 240 - len("00:00:00")*16 - 16)
    display_y = random.randint(4, 135 - 32 - 4)
    updated = False

    dim_timer = time.time()
    dim_countdown = 30

    prev_pressed_keys = []
    pressed_keys = []

    while time_left > 0:
        prev_display = display

        time_so_far = time.time() - time_started
        time_left = seconds_to_count - time_so_far

        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        seconds = int(time_left % 60)

        # update display position every 10 seconds
        if seconds % 10 == 5 and not updated:
            display_x = random.randint(4, 240 - len("00:00:00")*16 - 4)
            display_y = random.randint(4, 135 - 32 - 4)
            updated = True

        # reset 10 second timer triggered flag
        if seconds % 10 == 0 and updated:
            updated = False

        display = ""

        # dim display
        if (time.time() - dim_timer) > dim_countdown:
            blight.duty_u16(22000)

        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "ESC" in pressed_keys and "ESC" not in prev_pressed_keys:
                return
            blight.duty_u16(40000)
            dim_countdown = 30
            dim_timer = time.time()

        prev_pressed_keys = pressed_keys

        if hours > 0:
            display += f"{int(hours)}:"
        display += f"{minutes:02}:"
        display += f"{seconds:02}"

        if display != prev_display and time_left > 0:
            tft.fill(bg_color)
            tft.text(display, display_x, display_y, ui_color, font=big_font)
            tft.show()

    blight.duty_u16(40000)
    tft.fill(bg_color)
    tft.text("00:00", 120 - len(display)*16//2, 70 - 16, ui_color, font=big_font)
    tft.text("< any key >", 120 - len(display)*16//2, 118, ui_color, font=small_font)
    tft.show()

    timer = Timer(1, mode=Timer.PERIODIC, period=1000, callback = lambda t: alarm())

    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            timer.deinit()
            return

        prev_pressed_keys = pressed_keys

def alarm():
    led.fill((255,255,255)); led.write() # set led
    beep.play(("C3","C4","C5","C6"), 50, 10)
    led.fill((0,0,0)); led.write() # set led

def main():
    pressed_keys = kb.get_pressed_keys()
    prev_pressed_keys = pressed_keys
    current_units = "minutes"
    time_value = "0"

    redraw = True

    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "h" in pressed_keys and "h" not in prev_pressed_keys and current_units != "hours":
                current_units = "hours"
            elif 'm' in pressed_keys and 'm' not in prev_pressed_keys and current_units != "minutes":
                current_units = "minutes"
            elif 's' in pressed_keys and 's' not in prev_pressed_keys and current_units != "seconds":
                current_units = "seconds"
            elif ',' in pressed_keys and ',' not in prev_pressed_keys: # left
                if current_units == "minutes":
                    current_units = "seconds"
                elif current_units == "hours":
                    current_units = "minutes"
            elif '/' in pressed_keys and '/' not in prev_pressed_keys: # right
                if current_units == "seconds":
                    current_units = "minutes"
                elif current_units == "minutes":
                    current_units = "hours"
            elif "ENT" in pressed_keys and "ENT" not in prev_pressed_keys and time_value != "0":
                start_timer(time_value, current_units)
                time_value = "0"
                current_units = "minutes"
                redraw = True
            elif "BSPC" in pressed_keys and "BSPC" not in prev_pressed_keys:
                time_value = time_value[:-1] if len(time_value) > 1 else "0"
            else:
                for key in pressed_keys:
                    if (len(key) == 1
                    and key not in prev_pressed_keys
                    and key in numbers):
                        if key == "." and "." in time_value:
                            # max 1 decimal point
                            pass
                        elif key == "0" and time_value == "0":
                            # can't keep adding if the first digit it zeros
                            pass
                        else:
                            time_value += key

            if time_value != "0":
                # remove leading 0s
                time_value = time_value.lstrip("0")
                if time_value[0] == ".":
                    time_value = "0" + time_value
            redraw = True


        if redraw:
            tft.fill(bg_color)

            tft.text(time_value, 120- len(time_value)*16//2, 70 - 16 - 10, ui_color, font=big_font)
            tft.text(current_units, 120 - len(current_units)*8//2, 70 + 24 - 10, ui_color, font=small_font)

            select = ""
            if current_units == "seconds":
                select += "[ s ] "
            else:
                select += "  s   "
            if current_units == "minutes":
                select += "[ m ] "
            else:
                select += "  m   "
            if current_units == "hours":
                select += "[ h ]"
            else:
                select += "  h  "
            tft.text(select, 120 - len(select)*8//2, 118, ui_color, font=small_font)

            tft.show()
            redraw = False

        prev_pressed_keys = pressed_keys

main()
