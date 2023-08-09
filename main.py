import sys
from time import sleep

import esptool
import serial
from serial import SerialException

from brewflasher_com_integration import FirmwareList, Firmware, DeviceFamily, Project
import serial_integration
import click
import subprocess

__version__ = "0.0.1"
__supported_baud_rates__ = [9600, 57600, 74880, 115200, 230400, 460800, 921600]


def obtain_user_confirmation(prompt: str):
    confirmation = input(f"{prompt} (y/n): ").strip().lower()

    if confirmation not in ["y", "yes"]:
        print("Acknowledged. Exiting.")
        sys.exit(0)


@click.command()
@click.option('--firmware', '-f', default=None, help='Firmware ID to skip firmware selection.')
@click.option('--serial-port', '-p', default=None, help='Serial port to skip device detection.')
def main(firmware, serial_port):
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

    # Confirm firmware selection
    print(f"\nYou've selected the following firmware:\n{selected_firmware}\n")
    obtain_user_confirmation("Do you want to flash this firmware?")

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
