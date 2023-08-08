import sys
import brewflasher_com_integration
import serial_integration


def obtain_user_confirmation(prompt: str):
    confirmation = input(f"{prompt} (y/n): ").strip().lower()

    if confirmation not in ["y", "yes"]:
        print("Acknowledged. Exiting.")
        sys.exit(0)


def main():
    # Initialize the firmware list
    print("Loading firmware list from BrewFlasher.com...")
    firmware_list = brewflasher_com_integration.FirmwareList()
    if not firmware_list.load_from_website():
        print("Failed to load data from the website.")
        return

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

    # Prompt user to select a Firmware
    firmwares = firmware_list.get_firmware_list(selected_project_id, selected_family_id)
    print("\nSelect a Firmware:")
    for idx, firmware in enumerate(firmwares, 1):
        print(f"{idx}. {firmware}")

    firmware_choice = int(input("\nEnter the number of your choice: ")) - 1
    selected_firmware = firmware_list.get_firmware(selected_project_id, selected_family_id, firmwares[firmware_choice])

    # Confirm firmware selection
    print(f"\nYou've selected the following firmware:\n{selected_firmware}\n")
    obtain_user_confirmation("Do you want to flash this firmware?")

    # Device Detection Steps
    selected_device = detect_new_devices()
    if selected_device:
        print(f"You've selected device: {selected_device}")
    else:
        print("No device selected. Exiting.")
        sys.exit(0)

    obtain_user_confirmation(f"Do you want to flash device {selected_device} with {selected_firmware}?")


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
