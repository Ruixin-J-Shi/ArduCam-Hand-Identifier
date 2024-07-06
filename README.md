## Project Name:

Arduino Gaming with Gesture Recognition

## Author:

Ruixin/Jack Shi & Jonathan

## Summary

This project integrates a Flask server with an Arduino to create a finger counting game/ pattern matching game. The server uses MediaPipe to process images from a webcam, detects the number of fingers/pattern shown, and communicates this information to an Arduino. The Arduino displays game feedback on an LCD screen based on the finger count/palm pattern received from the server.

## Components

- Arduino (Uno, Mega, etc.)
- ArduCAM or any compatible camera module
- LiquidCrystal LCD display (16x2 or similar)
- Computer with Python 3 and Flask
- Serial communication setup between Arduino and computer

## Hardware Setup

1. **Arduino and LCD**: Connect the LCD to the Arduino according to the LCD pin layout and Arduino model. Typically, connections involve RS, EN, D4, D5, D6, and D7 pins.
2. **Camera to Arduino**: Connect the ArduCAM to the Arduino via the SPI and I2C connections.
3. **Arduino to Computer**: Connect the Arduino to the computer using a USB cable to allow serial communication.

### Dependencies

Install the following Python libraries if not already installed:

flask
numpy
opencv-python-headless
mediapipe

## Run server:

python server.py
