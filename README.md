# BrewFlasher CLI Edition

BrewFlasher CLI edition is a command-line port of the [BrewFlasher](https://www.brewflasher.com) firmware flashing 
application. It is designed to allow flashing brewing-related firmware from command line environments -- such as a
Raspberry Pi. It also adds support for Arduino-based brewing-related firmware (similar to that provided 
in [Fermentrack's](http://www.fermentrack.com/) firmware flashing workflow).

## Choosing the right BrewFlasher Edition

There are currently three editions of BrewFlasher to choose from:

- BrewFlasher Desktop - Designed to be run from Windows or MacOS, this allows you to flash an ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from your _desktop or laptop_. It is a downloadable application with a GUI interface, and is the easiest way to flash these architectures.
- BrewFlasher Web Edition - Designed to be run from a web browser, this allows you to flash an ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from your _desktop or laptop_. It is a web application, and is the easiest way to flash these architectures when you would prefer not to download a full Desktop application.
- BrewFlasher CLI Edition - Designed to be run from a command line, this allows you to flash an Arduino (Atmel), ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from a _command line environment_ such as a Raspberry Pi. If you are looking to flash an Arduino-based controller, this is the easiest way to do so.


## Installation

TBD - this is a work in progress. For now, you can install BrewFlasher CLI Edition by cloning this repository and 
running `pip install -r requirements.txt` from the root directory, assuming that you have a modern Python 3 version 
available. You may want to create a venv to install the requirements into.

Eventually, I plan to freeze this with pyinstaller, or set up some other, easier way to install it (such as an install script)

## Usage

BrewFlasher CLI Edition is designed to be run from the command line. It is a Python script, so you can run it as follows:

    python3 brewflasher_cli.py

The script will prompt you for the information it needs to complete the flashing process.
