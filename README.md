# About
A series of Python scripts experimenting with alternative tools for tuning 
Software Defined Radio (SDR) through [gqrx](https://www.gqrx.dk/)

## MIDI Keyboard Tuner
Coorelates a top and bottom tuning frequency with a high and low midi key, dividing the frequencies evenly among the keys in between. This allows you to tune the radio with a midi controller.

## LFO Tuner
Uses a low frequency oscillator to tune the radio frequency in a constantly changing manner. Adjusting the frequency of the LFO affects how fast the tuner moves up and down. Adjusting the LFO depth affects how far up and down the frequencies go. 

## GPIO Encoder Tuner 
For Raspberry Pi. Reads an encoder from GPIO pins to tune the radio. 

