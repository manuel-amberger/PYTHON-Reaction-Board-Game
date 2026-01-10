import time
import random
from gpiozero import Button, LED, PWMOutputDevice
import board
import neopixel


# Pin definitions
player_1_btn = Button(23, pull_up=False)     # Player 1 button
player_2_btn = Button(24, pull_up=False)     # Player 2 button
start_btn = Button(25, pull_up=False)        # Start button
mode_switch = Button(16, pull_up=False)      # Mode switch
player_1_yellow_led = LED(27)                # Player 1 yellow LED
player_2_yellow_led = LED(22)                # Player 2 yellow LED
buzzer = PWMOutputDevice(6)                  # Buzzer (PWM)


# Global variables
buzzer_flag = True                           # Buzzer flag
game_started = False                         # Game started flag


# Interrupt handlers
# Mode switch interrupt handler
mode_switch_interrupt_flag = False           # Mode switch interrupt flag

def mode_switch_switched():
    global mode_switch_interrupt_flag
    mode_switch_interrupt_flag = True

mode_switch.when_pressed = mode_switch_switched

# Players interrupt handlers
player1_pressed = False                      # Player 1 button pressed flag
player2_pressed = False                      # Player 2 button pressed flag

def player1_btn_pressed():
    global player1_pressed
    player1_pressed = True

def player2_btn_pressed():
    global player2_pressed
    player2_pressed = True

player_1_btn.when_pressed = player1_btn_pressed
player_2_btn.when_pressed = player2_btn_pressed


# matrix definitions
WIDTH = 8
HEIGHT = 8
NUM_PIXELS = WIDTH * HEIGHT

np = neopixel.NeoPixel(board.D5, NUM_PIXELS, brightness=0.5, auto_write=False)

# Matrix colors
PIXELS_COLOR_GREEN = (0, 255, 0)
PIXELS_COLOR_RED = (255, 0, 0)
PIXELS_COLOR_YELLOW = (255, 150, 0)
PIXELS_OFF = (0, 0, 0)

# Matrix functions
def set_matrix_color(color):
    for i in range(NUM_PIXELS):
        np[i] = color
    np.show()

def set_matrix_pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        np[y * WIDTH + x] = color

def clear_matrix():
    for i in range(NUM_PIXELS):
        np[i] = PIXELS_OFF
    np.show()

def set_half(color, side):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            index = y * WIDTH + x
            if side == 'left' and x < 4:
                np[index] = color
            elif side == 'right' and x >= 4:
                np[index] = color
            else:
                np[index] = PIXELS_OFF
    np.show()

def show_reaction_bar(reaction_time_ms):
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
    np.show()

# Waiting screen animation
color = PIXELS_COLOR_GREEN
col = 0
direction = 1

def draw_vertical_bar(column, color):
    for y in range(HEIGHT):
        set_matrix_pixel(column, y, color)
    np.show()

def animate_bar_step(column, color):
    time.sleep(0.15)
    clear_matrix()
    draw_vertical_bar(column, color)


# Buzzer sounds
def play_tone(freq, duration=0.15):
    if buzzer_flag:
        buzzer.frequency = freq
        buzzer.value = 0.5
        time.sleep(duration)
        buzzer.value = 0

def sound_mode_switch():
    play_tone(700, 0.1)
    play_tone(900, 0.1)

def sound_start_press():
    for f in [600, 800, 1000]:
        play_tone(f, 0.1)

def sound_win():
    for f in [800, 1000, 1200, 1500]:
        play_tone(f, 0.1)

def sound_too_early():
    for f in [1000, 700, 400]:
        play_tone(f, 0.15)


# Main loop
while True:

    # Koop - Mode
    if mode_switch.value == 1:

        sound_mode_switch()

        while not mode_switch_interrupt_flag:
            animate_bar_step(col, color)

            if start_btn.is_pressed:
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
    else:

        sound_mode_switch()

        while not mode_switch_interrupt_flag:
            animate_bar_step(col, color)

            if start_btn.is_pressed:
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
                start_time = time.time()

            if player1_pressed:
                if game_started:
                    reaction_time = (time.time() - start_time) * 1000

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
