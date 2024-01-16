import socket
import tkinter as tk
from tkinter import simpledialog
from threading import Thread
import mido
import rtmidi

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
    
class MIDINoteSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        # Open the MIDI input port
        self.inport = mido.open_input(mido.get_input_names()[0])  # Assuming the first MIDI device
        self.first_note = None
        self.last_note = None
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="Press a key for the first MIDI note.").pack()

    def handle_midi_input(self):
        for msg in self.inport.iter_pending():
            if msg.type == 'note_on':
                if self.first_note is None:
                    self.first_note = msg.note
                    self.label.config(text="Press a key for the last MIDI note.")
                elif self.last_note is None:
                    self.last_note = msg.note
                    self.ok_button.config(state=tk.NORMAL)

    def apply(self):
        self.result = (self.first_note, self.last_note)

    def open(self):
        self.ok_button = self.buttonbox().children['ok']
        self.ok_button.config(state=tk.DISABLED)
        self.label = self.dialog_frame.winfo_children()[0]
        self.after(100, self.check_midi)  # Check for MIDI input every 100ms
        return super().open()

    def check_midi(self):
        self.handle_midi_input()
        self.after(100, self.check_midi)  # Continue checking for MIDI input

    def close(self):
        self.inport.close()
        super().close()


class FrequencyMIDISettingsDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Start Frequency (Hz):").grid(row=0)
        tk.Label(master, text="End Frequency (Hz):").grid(row=1)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)

        return self.e1  # initial focus

    def apply(self):
        self.result = (float(self.e1.get()), float(self.e2.get()))
    
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

def run_gui(root):
    def update_frequency(val):
        frequency = float(val)
        gqrx.set_frequency(frequency)
        print(f"Frequency set to: {frequency} Hz")

    def open_settings_dialog():
        dialog = FrequencyMIDISettingsDialog(root)
        if dialog.result:
            start_freq, end_freq, first_note, last_note = dialog.result
            frequencies = calculate_frequencies(start_freq, end_freq, last_note - first_note + 1)
            midi_thread = Thread(target=handle_midi_input, args=(midi_port_name, frequencies))
            midi_thread.start()

    settings_button = tk.Button(root, text="MIDI Settings", command=open_settings_dialog)
    settings_button.pack()

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

        # Ask for frequency and MIDI note settings
        dialog = FrequencyMIDISettingsDialog(root)
        if dialog.result and midi_port_name:
            start_freq, end_freq, first_note, last_note = dialog.result
            frequencies = calculate_frequencies(start_freq, end_freq, last_note - first_note + 1)

            # Launch MIDI handling in a separate thread
            midi_thread = Thread(target=handle_midi_input, args=(midi_port_name, frequencies))
            midi_thread.start()

            run_gui(root)
            midi_thread.join()
        else:
            print("No MIDI port name provided or settings dialog cancelled.")
        
        root.destroy()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if gqrx:
            gqrx.close()
            print("Gqrx controller closed.")


