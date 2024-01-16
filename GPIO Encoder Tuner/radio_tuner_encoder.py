import socket
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import RPi.GPIO as GPIO
import time

# GPIO setup for the encoder
clk = 17
dt = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
clkLastState = GPIO.input(clk)

def test_gqrx_connection(host='localhost', port=7356):
    try:
        # Create a socket and connect to Gqrx
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        # Send a command to get the frequency
        s.sendall(b'f\n')
        frequency = s.recv(1024).decode('utf-8').strip()

        s.close()
        return f'Connected successfully! Current frequency: {frequency} Hz'
    except Exception as e:
        return f'Failed to connect: {e}'

    
class GqrxController:
    def __init__(self, host='localhost', port=7356):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def send_command(self, cmd):
        self.sock.sendall((cmd + '\n').encode('utf-8'))
        response = self.sock.recv(1024).decode('utf-8').strip()
        return response

    def get_frequency(self):
        return float(self.send_command('f'))

    def set_frequency(self, freq):
        self.send_command(f'F {freq}')
        return self.get_frequency()

    def close(self):
        self.sock.close()

def run_gui():
    def update_frequency(val):
        frequency = float(val)
        gqrx.set_frequency(frequency)
        print(f"Frequency set to: {frequency} Hz")

    root = tk.Tk()
    root.title("Gqrx Controller")

    freq_slider = tk.Scale(root, from_=2.399e9, to=2.403e9, resolution=1e6,
                           orient=tk.HORIZONTAL, length=400,
                           label="Frequency:", command=update_frequency)
    freq_slider.set(gqrx.get_frequency())
    freq_slider.pack()

    root.mainloop()

def handle_encoder_input():
    global clkLastState
    clkState = GPIO.input(clk)
    dtState = GPIO.input(dt)
    try:
        if clkState != clkLastState:
            if dtState != clkState:
                # Increase frequency
                current_freq = gqrx.get_frequency()
                gqrx.set_frequency(current_freq + 1e6)
                print(current_freq)
            else:
                # Decrease frequency
                current_freq = gqrx.get_frequency()
                gqrx.set_frequency(current_freq - 1e6)
                print(current_freq)
            clkLastState = clkState
        time.sleep(0.01)
    except Exception as e:
        print(f"Failed to handle encoder input: {e}")

if __name__ == '__main__':
    try:
        gqrx = GqrxController()



        encoder_thread = Thread(target=handle_encoder_input)
        encoder_thread.start()

        run_gui()
        encoder_thread.join()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if gqrx:
            gqrx.close()
            print("Gqrx controller closed.")


