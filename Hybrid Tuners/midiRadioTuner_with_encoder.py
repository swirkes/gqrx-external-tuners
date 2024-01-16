import socket
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import mido
import rtmidi
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

def calculate_frequencies(start_freq, end_freq, num_keys):
    step = (end_freq - start_freq) / (num_keys - 1)
    return [start_freq + i * step for i in range(num_keys)]

def midi_to_frequency(note_number, frequencies):
    if 21 <= note_number <= 108:
        return frequencies[note_number - 21]
    return None

def handle_midi_input(port_name, frequencies):
    try:
        with mido.open_input(port_name) as inport:
            for msg in inport:
                if msg.type == 'note_on':
                    frequency = midi_to_frequency(msg.note, frequencies)
                    if frequency:
                        print(f"Setting frequency to {frequency} Hz")
                        gqrx.set_frequency(frequency)
    except Exception as e:
        print(f"Failed to open MIDI port {port_name}: {e}")

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


        # List available MIDI ports
        print("Available MIDI ports:")
        for port in mido.get_input_names():
            print(f"- {port}")

        # Ask for MIDI port name
        root = tk.Tk()  # Temporary Tkinter instance for the dialog
        root.withdraw()  # Hide the main window
        midi_port_name = simpledialog.askstring("MIDI Port", "Enter MIDI port name:", parent=root)
        root.destroy()

        # Launch MIDI handling in a separate thread
        if midi_port_name:
            frequencies = calculate_frequencies(7.000e6, 8.481e6, 88)
            midi_thread = Thread(target=handle_midi_input, args=(midi_port_name, frequencies))
            midi_thread.start()

            encoder_thread = Thread(target=handle_encoder_input)
            encoder_thread.start()

            run_gui()
            midi_thread.join()
            encoder_thread.join()
        else:
            print("No MIDI port name provided.")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if gqrx:
            gqrx.close()
            print("Gqrx controller closed.")


