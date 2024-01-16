import RPi.GPIO as GPIO
import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import time

# Initialize SDR
sdr = SoapySDR.Device({})
sdr.setSampleRate(SOAPY_SDR_RX, 0, 2.5e6)
sdr.setFrequency(SOAPY_SDR_RX, 0, 100e6)  # Initial frequency

# GPIO setup for the encoder
clk = 17
dt = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
clkLastState = GPIO.input(clk)

try:
    while True:
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
        if clkState != clkLastState:
            if dtState != clkState:
                # Increase frequency
                current_freq = sdr.getFrequency(SOAPY_SDR_RX, 0)
                sdr.setFrequency(SOAPY_SDR_RX, 0, current_freq + 1e6)
                print(current_freq)
            else:
                # Decrease frequency
                current_freq = sdr.getFrequency(SOAPY_SDR_RX, 0)
                sdr.setFrequency(SOAPY_SDR_RX, 0, current_freq - 1e6)
                print(current_freq)
            clkLastState = clkState
        time.sleep(0.01)
finally:
    GPIO.cleanup()
