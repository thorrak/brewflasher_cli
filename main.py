import sys
from time import sleep

import esptool
import serial
from serial import SerialException

from brewflasher_com_integration import FirmwareList, Firmware, DeviceFamily, Project
import serial_integration
import click

__version__ = "0.0.1"
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]


def obtain_user_confirmation(prompt: str):
    confirmation = input(f"{prompt} (y/n): ").strip().lower()

    if confirmation not in ["y", "yes"]:
        print("Acknowledged. Exiting.")
        sys.exit(0)


@click.command()
@click.option('--firmware', '-f', default=None, help='Firmware ID to skip firmware selection')
@click.option('--serial-port', '-p', default=None, help='Serial port to skip device detection')
@click.option('--baud', '-b', default=None, help='Baud rate to flash at',
              type=click.Choice([str(x) for x in __supported_baud_rates__]))
@click.option('--erase-flash', '-e', is_flag=True, default=None, help='Erase flash memory before installing firmware')
def main(firmware, serial_port, baud, erase_flash):
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

    if baud is None:
        selected_baud_rate = select_baud_rate()
    else:
        selected_baud_rate = baud

    # If the user set whether to erase the flash on the command line, respect his/her selection
    if erase_flash is None:
        confirmation = input(f"Do you want to erase the flash on the device completely before writing the firmware (y/n): ").strip().lower()

        if confirmation not in ["y", "yes"]:
            erase_flash_flag = False
            print("Flash will not be erased before writing firmware")
        else:
            erase_flash_flag = True
            print("Flash WILL be erased before writing firmware")
    else:
        erase_flash_flag = erase_flash

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
    from shutil import which

    if which("avrdude") is not None:
        print("avrdude found on the path - Arduino installations can proceed.")
        return True
    else:
        print("avrdude not found on the path - Cannot flash Arduino firmware!")
        return False

    # # Test if avrdude is available. If not, the user will need to install it.
    # try:
    #     rettext = subprocess.check_output(["dpkg", "-s", "avrdude"]).decode(encoding='cp437')
    #     install_check = rettext.find("installed")
    #
    #     if install_check == -1:
    #         # The package status isn't 'installed'
    #         print("Warning - Package 'avrdude' not installed. Arduino installations will fail! Click <a href=\"http://www.fermentrack.com/help/avrdude/\">here</a> to learn how to resolve this issue.")
    #         return False
    #     else:
    #         return True
    # except:
    #     print("Unable to check for installed 'avrdude' package - Arduino installations may fail!")
    #     return False


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
    input("\nPlease disconnect the device (if it is connected), then press Enter...")

    # Cache the list of currently available serial devices
    serial_integration.cache_current_devices()

    # Prompt user to connect the device
    input("Please connect the device, then press Enter...")

    # Compare the current list of serial devices against the cached list
    _, _, new_devices, new_devices_enriched = serial_integration.compare_current_devices_against_cache()

    if not new_devices:
        print("No new devices detected.")
        return None
    else:
        print("\nNew devices detected:")
        for idx, device in enumerate(new_devices_enriched, 1):
            print(
                f"{idx}. Device: {device['device']}, Description: {device['description']}, Known Name: {device['known_name']}")

        device_choice = int(input("\nSelect a device by its number: ")) - 1
        return new_devices_enriched[device_choice]['device']


if __name__ == "__main__":
    main()
