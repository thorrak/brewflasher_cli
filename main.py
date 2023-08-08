import brewflasher_com_integration


def main():
    firmware_list = brewflasher_com_integration.FirmwareList()
    firmware_list.load_from_website()

    # Step 1: Select Project
    projects = firmware_list.get_project_list()
    print("Select a Project:")
    for idx, project in enumerate(projects, start=1):
        print(f"{idx}. {project}")

    project_idx = int(input("Enter the number of your choice: ")) - 1
    selected_project = projects[project_idx]
    project_id = firmware_list.get_project_id(selected_project)

    # Step 2: Select DeviceFamily based on Project
    device_families = firmware_list.get_device_family_list(selected_project_id=project_id)
    print("\nSelect a Device Family:")
    for idx, device_family in enumerate(device_families, start=1):
        print(f"{idx}. {device_family}")

    device_family_idx = int(input("Enter the number of your choice: ")) - 1
    selected_device_family = device_families[device_family_idx]
    device_family_id = firmware_list.get_device_family_id(project_id, selected_device_family)

    # Step 3: Select Firmware based on Project and DeviceFamily
    firmwares = firmware_list.get_firmware_list(selected_project_id=project_id, selected_family_id=device_family_id)
    print("\nSelect a Firmware:")
    for idx, firmware in enumerate(firmwares, start=1):
        print(f"{idx}. {firmware}")

    firmware_idx = int(input("Enter the number of your choice: ")) - 1
    selected_firmware = firmwares[firmware_idx]

    print(
        f"\nYou have selected:\nProject: {selected_project}\nDevice Family: {selected_device_family}\nFirmware: {selected_firmware}")

    # Step 4: Confirmation
    confirmation = input("\nDo you want to flash the selected firmware? (yes or y to confirm): ")
    if confirmation.lower() in ["y", "yes"]:
        print("Flashing firmware...")
        # Here, you would include the logic to actually flash the firmware if that was a functionality you desired.
    else:
        print("Flashing aborted by the user.")
        exit()


if __name__ == "__main__":
    main()
