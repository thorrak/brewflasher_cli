# BrewFlasher CLI Edition

BrewFlasher CLI edition is a command-line port of the [BrewFlasher](https://www.brewflasher.com) firmware flashing 
application. It is designed to allow flashing brewing-related firmware from command line environments -- such as a
Raspberry Pi. It also adds support for Arduino-based brewing-related firmware (similar to that provided 
in [Fermentrack's](http://www.fermentrack.com/) firmware flashing workflow).

## Choosing the right BrewFlasher Edition

There are currently three editions of BrewFlasher to choose from:

- **BrewFlasher Desktop** - Designed to be run from Windows or MacOS, this allows you to flash an ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from your _desktop or laptop_. It is a downloadable application with a GUI interface, and is the easiest way to flash these architectures. It is accessible [here](https://www.brewflasher.com).
- **BrewFlasher Web Edition** - Designed to be run from a web browser, this allows you to flash an ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from your _desktop or laptop_. It is a web application, and is the easiest way to flash these architectures when you would prefer not to download a full Desktop application. It is accessible [here](https://web.brewflasher.com).
- **BrewFlasher CLI Edition** - Designed to be run from a command line, this allows you to flash an Arduino (Atmel), ESP8266, ESP32, ESP32-S2, or ESP32-C3-based microcontroller from a _command line environment_ such as a Raspberry Pi. If you are looking to flash an Arduino-based controller, this is the easiest way to do so.


## Installation

BrewFlasher CLI is available on PyPi and can be installed using pip:

    pip install brewflasher_cli


## Usage

Once installed, you can run the application using the following command:

    brewflasher

The script will prompt you for the information it needs to complete the flashing process. If you already know some of
the options you want to specify, you can pass them in as command line arguments. For example, if you want to flash a
device using the serial port `/dev/ttyUSB0` at the speed `460800` bps without erasing the flash before installing, you 
can run the following command:

    brewflasher --serial-port /dev/ttyUSB0 --baud 460800 --dont-erase-flash

A full list of command line options can be seen by running `brewflasher --help`


## Uninstallation

If you want to uninstall BrewFlasher CLI, you can do so using the following command:

    pip uninstall brewflasher_cli

## Building from source

If you want to build BrewFlasher CLI from source, you can do so using the following commands in the root directory of
this package:

    python3 -m build
    pip install .

Make sure that you have run `pip uninstall brewflasher_cli` first or you risk having the PyPi version of BrewFlasher CLI
installed alongside your local version.
