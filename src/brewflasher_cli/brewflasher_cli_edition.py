#!/usr/bin/env python3
import subprocess
import sys
from time import sleep
from shutil import which

import click
import esptool
import serial
from serial import SerialException

from brewflasher_cli.brewflasher_com_integration import FirmwareList, Firmware
from brewflasher_cli import serial_integration

__version__ = "0.1.1"
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]


def obtain_user_confirmation(prompt: str):
    confirmation = input(f"{prompt} (y/n): ").strip().lower()
    if confirmation not in ["y", "yes"]:
        print("Acknowledged. Exiting.")
        sys.exit(0)


@click.command()
@click.version_option(__version__)
@click.option('--firmware', '-f', default=None, help='Firmware ID to skip firmware selection')
@click.option('--serial-port', '-p', default=None, help='Serial port to skip device detection')
@click.option('--baud', '-b', default=None, help='Baud rate to flash at',
              type=click.Choice([str(x) for x in __supported_baud_rates__]))
@click.option('--erase-flash', '-e', is_flag=True, default=None, help='Erase flash memory before installing firmware')
@click.option('--dont-erase-flash', '-n', is_flag=True, default=None, help='Don\'t erase flash memory before installing firmware')
def main(firmware, serial_port, baud, erase_flash, dont_erase_flash):
    if erase_flash and dont_erase_flash:
        print("You can't specify both --erase-flash and --dont-erase-flash. Exiting.")
        sys.exit(1)

    # Initialize the firmware list
    print("Loading firmware list from BrewFlasher.com...")
    firmware_list = FirmwareList()
    if not firmware_list.load_from_website(load_esptool_only=False):
        print("Failed to load data from the website.")
        return

    if firmware is None:
        # If the user didn't specify a firmware, prompt them to select one
        selected_firmware, device_family = select_firmware(firmware_list)
    else:
        # If the user specified a firmware, find it in the list and set both selected_firmware and device_family
        selected_firmware = None
        device_family = None
        for project_id in firmware_list.Projects:
            for family_id in firmware_list.Projects[project_id].device_families:
                for this_firmware in firmware_list.Projects[project_id].device_families[family_id].firmware:
                    if this_firmware.id == int(firmware):
                        selected_firmware = this_firmware
                        device_family = firmware_list.Projects[project_id].device_families[family_id]

        if selected_firmware is None or device_family is None:
            print("Failed to find selected firmware. Exiting.")
            sys.exit(1)

    if device_family.flash_method == "avrdude":
        if not check_for_avrdude():
            print("avrdude is not on the path, which means that BrewFlasher cannot flash Arduino-based chips.")
            # TODO - Add OS-specific instructions for resolving this here
            print("Please check the avrdude documentation (https://github.com/avrdudes/avrdude/) for your operating system and install it.")
            print("Exiting.")
            sys.exit(1)
        erase_flash_flag = True  # Avrdude currently always erases flash
        selected_baud_rate = 115200
    else:
        # We only need to set selected_baud_rate & erase_flash if we're flashing with esptool

        if baud is None:
            selected_baud_rate = select_baud_rate()
        else:
            selected_baud_rate = baud

        # If the user set whether to erase the flash on the command line, respect his/her selection
        if erase_flash is None and dont_erase_flash is None:
            confirmation = input(f"Do you want to erase the flash on the device completely before writing the firmware (y/n): ").strip().lower()

            if confirmation not in ["y", "yes"]:
                erase_flash_flag = False
                print("Flash will not be erased before writing firmware")
            else:
                erase_flash_flag = True
                print("Flash WILL be erased before writing firmware")
        else:
            if erase_flash is not None:
                erase_flash_flag = erase_flash
            elif dont_erase_flash is not None:
                erase_flash_flag = not dont_erase_flash
            else:
                print("This should never happen. Please report this error to the BrewFlasher developers. (erase_flash_flag)")
                sys.exit(1)

    if erase_flash_flag:  # Set the text for the confirmation prompt below
        erase_flash_text = "erasing flash first"
    else:
        erase_flash_text = "not erasing flash first"

    # Confirm firmware selection
    print(f"\nYou've selected the following firmware:\n{selected_firmware}\n")
    obtain_user_confirmation(f"Do you want to flash this firmware at {selected_baud_rate}bps, {erase_flash_text}?")

    # Device Detection Steps
    if serial_port is None:
        selected_device = detect_new_devices()
    else:
        selected_device = serial_port

    if selected_device:
        print(f"You've selected device: {selected_device}")
    else:
        print("No device selected. Exiting.")
        sys.exit(0)

    obtain_user_confirmation(f"Do you want to flash device {selected_device} with {selected_firmware}?")

    flash_firmware_using_whatever_is_appropriate(selected_firmware, selected_baud_rate, selected_device, erase_flash_flag)
    selected_firmware.remove_downloaded_firmware()  # Clean up the downloaded firmware files
    print("Done! Exiting.")
    sys.exit(0)


def select_firmware(firmware_list):
    # Prompt user to select a Project
    projects = firmware_list.get_project_list()
    print("\nSelect a Project:")
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project}")

    project_choice = int(input("\nEnter the number of your choice: ")) - 1
    selected_project_id = firmware_list.get_project_id(projects[project_choice])

    # Prompt user to select a DeviceFamily
    device_families = firmware_list.get_device_family_list(selected_project_id)
    print("\nSelect a Device Family:")
    for idx, family in enumerate(device_families, 1):
        print(f"{idx}. {family}")

    family_choice = int(input("\nEnter the number of your choice: ")) - 1
    selected_family_id = firmware_list.get_device_family_id(selected_project_id, device_families[family_choice])

    selected_family = firmware_list.DeviceFamilies[selected_family_id]

    # Prompt user to select a Firmware
    firmwares = firmware_list.get_firmware_list(selected_project_id, selected_family_id)
    print("\nSelect a Firmware:")
    for idx, firmware in enumerate(firmwares, 1):
        print(f"{idx}. {firmware}")

    firmware_choice = int(input("\nEnter the number of your choice: ")) - 1
    selected_firmware = firmware_list.get_firmware(selected_project_id, selected_family_id, firmwares[firmware_choice])

    return selected_firmware, selected_family


def check_for_avrdude() -> bool:
    if which("avrdude") is not None or which("avrdude.exe") is not None:
        print("avrdude found on the path - Arduino installations can proceed.")
        return True
    else:
        print("avrdude not found on the path - Cannot flash Arduino firmware!")
        return False


def select_baud_rate() -> int:
    # Prompt user to select a baud rate
    print("\nSelect baud rate (speed) to flash at. Recommended to try 460800 first, and 115200 if that fails:")
    for idx, rate in enumerate(__supported_baud_rates__, 1):
        print(f"{idx}. {rate}")

    baud_rate_choice = int(input("\nEnter the number of your choice: ")) - 1
    selected_baud_rate = __supported_baud_rates__[baud_rate_choice]
    print(f"Selected: {selected_baud_rate}")

    return selected_baud_rate


def detect_new_devices():
    # Prompt user to disconnect the device
    input("\nPlease disconnect the device to flash (if it is connected), then press Enter...")

    # Cache the list of currently available serial devices
    serial_integration.cache_current_devices()

    # Prompt user to connect the device
    input("Please connect the device to flash, then press Enter...")

    # Compare the current list of serial devices against the cached list
    _, _, new_devices, new_devices_enriched = serial_integration.compare_current_devices_against_cache()

    if not new_devices:
        print("No new devices detected. Please reattempt detection, or specify the device using the --serial-port flag on the command line.")
        return None
    else:
        print("\nNew devices detected:")
        for idx, device in enumerate(new_devices_enriched, 1):
            print(
                f"{idx}. Device: {device['device']}, Description: {device['description']}, Known Name: {device['known_name']}")

        device_choice = int(input("\nSelect a device by its number: ")) - 1
        return new_devices_enriched[device_choice]['device']


def flash_firmware_using_whatever_is_appropriate(firmware_obj: Firmware, baud:str, serial_port:str, erase_before_flash:bool) -> bool:
    # Initial checks
    if firmware_obj.family is None or firmware_obj is None:
        print("Must select the project, device family, and firmware to flash before flashing.")
        return False

    print("Verifying firmware list is up-to-date before downloading...")
    if not firmware_obj.pre_flash_web_verify(brewflasher_version=__version__, flasher="BrewFlasher CLI"):
        print("Firmware list is not up to date. Relaunch BrewFlasher and try again.")
        return False

    print("Downloading firmware...")
    if not firmware_obj.download_to_file():
        print("Error - unable to download firmware.\n")
        return False
    print("Downloaded successfully!\n")

    if firmware_obj.family.flash_method == "esptool":
        # Construct the command based on device family
        device_name = firmware_obj.family.name
        command_extension = []

        if device_name in ["ESP32", "ESP32-S2", "ESP32-C3"]:
            flash_options = {
                "ESP32": ["esp32", "0x10000"],
                "ESP32-S2": ["esp32s2", "-z", "--flash_mode", "dio", "--flash_freq", "80m", "0x10000"],
                "ESP32-C3": ["esp32c3", "-z", "--flash_mode", "dio", "--flash_freq", "80m", "0x10000"]
            }
            command_extension.extend(["--chip", flash_options[device_name][0], "--baud", str(baud),
                                      "--before", "default_reset", "--after", "hard_reset", "write_flash"])
            command_extension.extend(flash_options[device_name][1:])
            command_extension.append(firmware_obj.full_filepath("firmware"))

            if firmware_obj.download_url_partitions and firmware_obj.checksum_partitions:
                command_extension.extend(["0x8000", firmware_obj.full_filepath("partitions")])

            if firmware_obj.family.download_url_bootloader and firmware_obj.family.checksum_bootloader:
                boot_address = "0x0" if device_name == "ESP32-C3" else "0x1000"
                command_extension.extend([boot_address, firmware_obj.full_filepath("bootloader")])

        elif device_name == "ESP8266":
            command_extension.extend(["--chip", "esp8266", "write_flash", "0x00000",
                                      firmware_obj.full_filepath("firmware")])
        else:
            print("Invalid device family detected. Relaunch BrewFlasher and try again.")
            return False

        # For both ESP32 and ESP8266 we can directly flash an image to SPIFFS/LittleFS/OTAData
        if firmware_obj.download_url_spiffs and firmware_obj.checksum_spiffs and len(firmware_obj.spiffs_address) > 2:
            command_extension.append(firmware_obj.spiffs_address)
            command_extension.append(firmware_obj.full_filepath("spiffs"))

        if (firmware_obj.family.download_url_otadata and firmware_obj.family.checksum_otadata and
                len(firmware_obj.family.otadata_address) > 2):
            # We need to flash the otadata section. The location is dependent on the partition scheme
            command_extension.append(firmware_obj.family.otadata_address)
            command_extension.append(firmware_obj.full_filepath("otadata"))

        # Construct the main command
        command = ["--port", serial_port] + command_extension
        if erase_before_flash:
            command.extend(["--erase-all"])

        # There is a breaking change in esptool 3.0 that changes the flash size from detect to keep. We want to
        # support "detect" by default.
        command.extend(["-fs", "detect"])

        print(f"Esptool command: esptool.py {' '.join(command)}\n")

    elif firmware_obj.family.flash_method == "avrdude":
        command = [
            "avrdude",
            "-p", "atmega328p",
            "-c", "arduino",
            "-P", serial_port,
            "-D",  # Disable auto erase - may want to make this configurable in the future
            "-U", f"flash:w:{firmware_obj.full_filepath('firmware')}:i"
        ]

        print("Avrdude command: avrdude %s\n" % " ".join(command))

    else:
        raise ValueError("Invalid flash method detected. Update BrewFlasher and try again.")

    # Handle 1200 bps touch for certain devices
    if firmware_obj.family.use_1200_bps_touch:
        try:
            sleep(0.1)
            print("Performing 1200 bps touch")
            with serial.Serial(serial_port, baudrate=1200, timeout=5, write_timeout=0) as ser:
                sleep(1.5)
                print("...done\n")
        except SerialException as e:
            sleep(0.1)
            print("\nUnable to perform 1200bps touch.")
            print("Ensure correct serial port and try again or set device into 'flash' mode manually.")
            print("Instructions: http://www.brewflasher.com/manualflash/")
            raise e

    try:
        if firmware_obj.family.flash_method == "esptool":
            esptool.main(command)
        elif firmware_obj.family.flash_method == "avrdude":
            subprocess.run(command)
    except SerialException as e:
        sleep(0.1)
        raise e
    except Exception as e:
        sleep(0.1)
        print("Firmware flashing FAILED. esptool.py raised an error.")
        print("")
        print("Try flashing again, or try flashing with a slower speed.")
        print("")
        if firmware_obj.family.use_1200_bps_touch:
            print("")
            print("Alternatively, you may need to manually set the device into 'flash' mode.")
            print("")
            print("For instructions on how to do this, check this website:\nhttp://www.brewflasher.com/manualflash/")
        return False

    # The last line printed by esptool is "Staying in bootloader." -> some indication that the process is
    # done is needed
    print("")
    print("Firmware successfully flashed. Reset device to switch back to normal boot mode.")


if __name__ == "__main__":
    main()
