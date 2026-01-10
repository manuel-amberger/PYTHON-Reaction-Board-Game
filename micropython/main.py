import time
import random
from machine import Pin
from machine import PWM
import neopixel


# Pin definitions
player_1_btn = Pin(14, Pin.IN, Pin.PULL_DOWN)       # Player 1 button 
player_2_btn = Pin(15, Pin.IN, Pin.PULL_DOWN)       # Player 2 button
start_btn = Pin(17, Pin.IN, Pin.PULL_DOWN)          # Start button
mode_switch = Pin(16, Pin.IN, Pin.PULL_DOWN)        # Mode switch
player_1_yellow_led = Pin(1, Pin.OUT)               # Player 1 yellow LED
player_2_yellow_led = Pin(2, Pin.OUT)               # Player 2 yellow LED
buzzer = PWM(Pin(6))                                # Buzzer


# Global variables
buzzer_flag = True                                  # Buzzer flag
game_started = False                                # Game started flag


# Interrupt handlers
# Mode switch interrupt handler
mode_switch_interrupt_flag = False                  # Mode switch switched flag

def mode_switch_switched(pin):                      # Handler
    global mode_switch_interrupt_flag
    mode_switch_interrupt_flag = True

mode_switch.irq(trigger=Pin.IRQ_RISING, handler=mode_switch_switched)         # Mode switch interrupt

# Players interrupt handler
player1_pressed = False                             # Player 1 button pressed flag
player2_pressed = False                             # Player 2 button pressed flag

def player1_btn_pressed(pin):                       # Handler 
    global player1_pressed
    player1_pressed = True

def player2_btn_pressed(pin):                       # Handler
    global player2_pressed
    player2_pressed = True

player_1_btn.irq(trigger=Pin.IRQ_RISING, handler=player1_btn_pressed)         # Player 1 button interrupt
player_2_btn.irq(trigger=Pin.IRQ_RISING, handler=player2_btn_pressed)         # Player 2 button interrupt


# Matrix definitions
WIDTH = 8                                           # Matrix width
HEIGHT = 8                                          # Matrix height 
NUM_PIXELS = WIDTH * HEIGHT                         # Total pixels

np = neopixel.NeoPixel(Pin(0), NUM_PIXELS)          # Matrix data pin

# Matrix colors
PIXELS_COLOR_GREEN = (0, 255, 0)                    # Matrix Green
PIXELS_COLOR_RED = (255, 0, 0)                      # Matrix Red
PIXELS_COLOR_YELLOW = (255, 150, 0)                 # Matrix Yellow
PIXELS_OFF = (0, 0, 0)                              # Matrix Off

# Matrix functions
def set_matrix_color(color):                        # Function: Set color on full matrix
    for i in range(NUM_PIXELS):
        np[i] = color
    np.write()

def set_matrix_pixel(x, y, color):                  # Function: Set pixel at (x,y) to color
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        np[y*WIDTH +x] = color

def clear_matrix():                                 # Function: Clear matrix
    for i in range(NUM_PIXELS):
        np[i] = PIXELS_OFF
    np.write()

def set_half(color, side):                          # Function: Set half matrix to color
    for y in range(HEIGHT):
        for x in range (WIDTH):
            index = y * WIDTH + x
            if side == 'left' and x < 4:
                np[index] = color
            elif side == 'right' and x >= 4:
                np[index] = color
            else:
                np[index] = PIXELS_OFF
    np.write()

def show_reaction_bar(reaction_time_ms):            # Function: Show reaction time bar
    max_time = 2000
    columns_to_light = int((reaction_time_ms / max_time) * 8)
    if columns_to_light > 8:
        columns_to_light = 8

    clear_matrix()

    for x in range(columns_to_light):
        for y in range(8):
            if reaction_time_ms < 500:
                color = PIXELS_COLOR_GREEN
            elif reaction_time_ms < 1000:
                color = PIXELS_COLOR_YELLOW
            else:
                color = PIXELS_COLOR_RED

            set_matrix_pixel(x, y, color)
    np.write()


# Waiting screen animation
color = PIXELS_COLOR_GREEN
col = 0
direction = 1

def draw_vertical_bar(column, color):               # Function: Draw vertical bar
    for y in range(HEIGHT):
        set_matrix_pixel(column, y, color)
    np.write()

def animate_bar_step(column, color):                # Function: Animate bar step
    time.sleep(0.15)
    clear_matrix()
    draw_vertical_bar(column, color)


# Buzzer sounds
def play_tone(freq, duration=0.15, duty=20000):     # Function: Play tone
    if buzzer_flag:
        buzzer.freq(freq)
        buzzer.duty_u16(duty)
        time.sleep(duration)
        buzzer.duty_u16(0)

def sound_mode_switch():                            # Sound: Mode switch
    play_tone(700, 0.1)
    play_tone(900, 0.1)

def sound_start_press():                            # Sound: Start button pressed
    for f in [600, 800, 1000]:
        play_tone(f, 0.1)

def sound_win():                                    # Sound: Win
    for f in [800, 1000, 1200, 1500]:
        play_tone(f, 0.1)

def sound_too_early():                              # Sound: Too early
    for f in [1000, 700, 400]:
        play_tone(f, 0.15)



# main loop
while True:

    # Koop - Mode
    if mode_switch.value() == 1:

        sound_mode_switch()

        while not mode_switch_interrupt_flag:
            animate_bar_step(col, color)

            if start_btn.value() == 1:
                sound_start_press()

                delay = random.randint(2000, 5000)

                set_matrix_color(PIXELS_COLOR_RED)
                time.sleep(delay / 1000)
                game_started = True
                set_matrix_color(PIXELS_COLOR_GREEN)
            
            clear_matrix()
                
            if game_started:
                if player1_pressed:
                    sound_win()

                    for i in range(5):
                        set_half(PIXELS_COLOR_GREEN, 'left')
                        time.sleep(0.5)
                        clear_matrix()

                    player1_pressed = False
                    player2_pressed = False
                    game_started = False
                    break

                if player2_pressed:
                    sound_win()

                    for i in range(5):
                        set_half(PIXELS_COLOR_GREEN, 'right')
                        time.sleep(0.5)
                        clear_matrix()

                    player1_pressed = False
                    player2_pressed = False
                    game_started = False
                    break

            else:
                if player1_pressed:
                    sound_too_early()

                    for i in range(3):
                        player_1_yellow_led.on()
                        time.sleep(0.5)
                        player_1_yellow_led.off()

                    player1_pressed = False
                    player2_pressed = False
                    game_started = False

                if player2_pressed:
                    sound_too_early()

                    for i in range(3):
                        player_2_yellow_led.on()
                        time.sleep(0.5)
                        player_2_yellow_led.off()
                        
                    player1_pressed = False
                    player2_pressed = False
                    game_started = False

            col += direction
            if col == 7:
                direction = -1
            elif col == 0:
                direction = 1
        
            time.sleep(0.1)

        mode_switch_interrupt_flag = False

    # Single Player - Mode
    elif mode_switch.value() == 0:

        sound_mode_switch()

        while not mode_switch_interrupt_flag:
            animate_bar_step(col, color)

            if start_btn.value() == 1:
                sound_start_press()

                for i in range(3):
                    set_half(PIXELS_COLOR_GREEN, 'left')
                    time.sleep(0.5)
                    clear_matrix()

                delay = random.randint(2000, 5000)

                set_matrix_color(PIXELS_COLOR_RED)
                time.sleep(delay / 1000)
                set_matrix_color(PIXELS_COLOR_GREEN)
                game_started = True
                start_time = time.ticks_ms()

            if player1_pressed:
                if game_started:
                    reaction_time = time.ticks_diff(time.ticks_ms(), start_time)

                    sound_win()

                    show_reaction_bar(reaction_time)
                    time.sleep(4)

                else:
                    sound_too_early()

                    for i in range(3):
                        player_1_yellow_led.on()
                        time.sleep(0.5)
                        player_1_yellow_led.off()

            player1_pressed = False
            game_started = False
            clear_matrix()

            col += direction
            if col == 7:
                direction = -1
            elif col == 0:
                direction = 1

            time.sleep(0.1)

        mode_switch_interrupt_flag = False