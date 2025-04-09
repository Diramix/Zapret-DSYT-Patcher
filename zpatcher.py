import os
import json
import requests
import shutil
import msvcrt
from colorama import init, Fore

init(autoreset=True)

BYPASS_URL = "https://raw.githubusercontent.com/Diramix/Zapret-DSYT-Patcher/refs/heads/main/bypass-list.json"
GENERAL_LIST_FILE = "list-general.txt"
STATE_FILE = "res\\zapret-bypass-data.json"
CHECK_UPDATES_FILE = "check_updates.bat"
CHECK_UPDATES_OLD = "check_updates.old"
CHECK_UPDATES_NEW = os.path.join("res", CHECK_UPDATES_FILE)
HOSTS_FILE = r"C:\Windows\System32\drivers\etc\hosts"
LOCAL_HOSTS_OVERWRITE = "hosts"
VERSION_FILE = os.path.join("res", "version.txt")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def load_json_file(file_path, default=None):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}


def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_bypass_list():
    try:
        response = requests.get(BYPASS_URL)
        response.raise_for_status()
        return response.json().get("list", [])
    except Exception as e:
        print(Fore.RED + f"Failed to load bypass-list.json: {e}")
        exit(1)


def update_general_list(state):
    try:
        with open(GENERAL_LIST_FILE, "r", encoding="utf-8") as f:
            current_lines = f.readlines()
    except FileNotFoundError:
        current_lines = []

    new_lines = [link + "\n" for _, filter_links in state["applied"] for link in filter_links]

    if new_lines != current_lines:
        with open(GENERAL_LIST_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(Fore.GREEN + "Updated general-list.txt with the latest filter data.")
    else:
        print(Fore.YELLOW + "No changes in general-list.txt.")


def check_for_updates(services, state):
    updated = []
    for service in services:
        service_name = service["name"]
        service_exists = any(service_name == s[0] for s in state["applied"])

        if service_exists:
            old_links = [s[1] for s in state["applied"] if s[0] == service_name][0]
            try:
                r = requests.get(service["url"])
                r.raise_for_status()
                new_links = r.text.strip().splitlines()
                if old_links != new_links:
                    state["applied"] = [s for s in state["applied"] if s[0] != service_name]
                    state["applied"].append((service_name, new_links))
                    updated.append(service_name)
            except Exception as e:
                print(Fore.RED + f"Failed to fetch {service_name}: {e}")

    if updated:
        print(Fore.GREEN + "Updated filters: " + ", ".join(updated))
        update_general_list(state)
    else:
        print(Fore.YELLOW + "No updates found.")


def ask_selection(services, show_all_default=False):
    if not services:
        return []

    print("1 - ALL")
    for i, s in enumerate(services, start=2):
        print(f"{i} - {s['name']}")

    while True:
        choice = input("Choose options (Separate with spaces, Default: ALL):").strip() or "1"
        if choice == "":
            continue

        try:
            if choice == "1":
                return services
            indexes = [int(x) - 2 for x in choice.split()]
            selected = [services[i] for i in indexes if 0 <= i < len(services)]
            if selected:
                return selected
        except:
            clear()
            print("Select what you want to configure DPI bypass for.")
            return ask_selection(services)


def hosts_overwrite():
    clear()

    try:
        with open(HOSTS_FILE, "r", encoding="utf-8") as f:
            original_hosts = f.read()

        start_tag = "# Zapret Patcher hosts overwrite"
        end_tag = "# Zapret Patcher hosts overwrite"
        
        print("Adds ip and domains to the hosts file. The hosts file was taken from https://github.com/pumPCin/AntiZapret")

        if start_tag in original_hosts and end_tag in original_hosts:
            print("1 - Revert hosts overwrite")
            choice = input("Choose action (Default: 1):").strip() or "1"

            if choice == "1":
                revert_overwrite(original_hosts, start_tag, end_tag)
            else:
                print(Fore.RED + "Invalid choice.")
                clear()
                hosts_overwrite()
        else:
            print("1 - Apply hosts overwrite")
            choice = input("Choose action (Default: 1):").strip() or "1"

            if choice == "1":
                apply_overwrite(original_hosts, start_tag, end_tag)
            else:
                clear()
                hosts_overwrite()
    except Exception as e:
        print(Fore.RED + f"Error reading hosts file: {e}")


def apply_overwrite(original_hosts, start_tag, end_tag):
    if not os.path.exists(LOCAL_HOSTS_OVERWRITE):
        print(Fore.RED + "Hosts overwrite file not found.")
        return

    try:
        # Check if the hosts overwrite block is already present
        if start_tag in original_hosts and end_tag in original_hosts:
            print(Fore.YELLOW + "Hosts overwrite is already applied.")
            return

        with open(LOCAL_HOSTS_OVERWRITE, "r", encoding="utf-8") as f:
            overwrite_data = f.read()

        new_hosts = original_hosts.strip() + f"\n{start_tag}\n{overwrite_data}\n{end_tag}\n"

        with open(HOSTS_FILE, "w", encoding="utf-8") as f:
            f.write(new_hosts)

        print(Fore.GREEN + "Hosts overwrite applied.")
    except Exception as e:
        print(Fore.RED + f"Error writing to hosts file: {e}")


def revert_overwrite(original_hosts, start_tag, end_tag):
    try:
        parts = original_hosts.split(start_tag)
        if len(parts) >= 3:
            original_hosts = parts[0] + parts[2].split(end_tag, 1)[-1]

        with open(HOSTS_FILE, "w", encoding="utf-8") as f:
            f.write(original_hosts)

        print(Fore.GREEN + "Hosts overwrite reverted.")
    except Exception as e:
        print(Fore.RED + f"Error restoring hosts file: {e}")


def add_filters(services, state):
    clear()
    available = [s for s in services if s["name"] not in [x[0] for x in state["applied"]]]
    if not available:
        print(Fore.YELLOW + "No filters available to add.")
        return False

    print("Select what you want to configure DPI bypass for.")
    selected = ask_selection(available)

    added = []
    for service in selected:
        try:
            r = requests.get(service["url"])
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            with open(GENERAL_LIST_FILE, "a", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
            state["applied"].append((service["name"], lines))
            added.append(service["name"])
        except Exception as e:
            print(Fore.RED + f"Failed to fetch {service['name']}: {e}")

    if added:
        print(Fore.GREEN + "Added: " + ", ".join(added))
        return True
    return False


def remove_filters(services, state):
    clear()
    applied_services = [s for s in services if s["name"] in [x[0] for x in state["applied"]]]
    if not applied_services:
        print(Fore.YELLOW + "No filters to remove.")
        return False

    print("Select filters to remove:")
    selected = ask_selection(applied_services)

    try:
        with open(GENERAL_LIST_FILE, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    except:
        existing_lines = []

    remove_lines = set()
    for service in selected:
        try:
            r = requests.get(service["url"])
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            remove_lines.update(lines)
        except Exception as e:
            print(Fore.RED + f"Failed to fetch {service['name']}: {e}")

    filtered_lines = [line for line in existing_lines if line.strip() not in remove_lines]

    while filtered_lines and filtered_lines[-1].strip() == "":
        filtered_lines.pop()

    with open(GENERAL_LIST_FILE, "w", encoding="utf-8") as f:
        f.writelines(line if line.endswith("\n") else line + "\n" for line in filtered_lines)

    state["applied"] = [x for x in state["applied"] if x[0] not in [s["name"] for s in selected]]

    if selected:
        print(Fore.GREEN + "Removed: " + ", ".join([s["name"] for s in selected]))
        return True
    return False


def patch_updater():
    clear()
    local_version = None

    if os.path.exists(CHECK_UPDATES_FILE):
        with open(CHECK_UPDATES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith('set "LOCAL_VERSION='):
                    local_version = line.strip()
                    break

    if os.path.exists(CHECK_UPDATES_OLD):
        print("1 - Restore original check_updates.bat")
        while True:
            choice = input("Choice: (Default: 1):") or "1"
            if choice == "1":
                os.remove(CHECK_UPDATES_FILE)
                os.rename(CHECK_UPDATES_OLD, CHECK_UPDATES_FILE)
                print(Fore.GREEN + "Original file restored.")
                break
    else:
        print("1 - Patch check_updates.bat")
        while True:
            choice = input("Choice: (Default: 1):") or "1"
            if choice == "1":
                if os.path.exists(CHECK_UPDATES_NEW):
                    if os.path.exists(CHECK_UPDATES_FILE):
                        os.rename(CHECK_UPDATES_FILE, CHECK_UPDATES_OLD)
                    shutil.copyfile(CHECK_UPDATES_NEW, CHECK_UPDATES_FILE)
                    print(Fore.GREEN + "File updated.")
                else:
                    print(Fore.RED + "New file not found.")
                break

    if local_version:
        version_data = local_version.split('=')[-1].strip(' "')
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(version_data)
        print(Fore.GREEN + f"Version {version_data} saved to version.txt")


def select_mode():
    while True:
        print("Select mode:")
        print("1 - Filter control")
        print(Fore.RED + "2 - Updater")
        print("3 - Hosts overwrite")
        section = input("Choice:").strip()
        if section == "1":
            return 1
        elif section == "2":
            return 2
        elif section == "3":
            return 3
        else:
            clear()


def main():
    clear()
    mode = select_mode()

    if mode == 1:
        services = load_bypass_list()
        state = load_json_file(STATE_FILE, {"applied": []})

        clear()
        applied_names = [x[0] for x in state["applied"]]
        all_applied = len(applied_names) == len(services)
        if state["applied"]:
            print("Detected applied filters: " + ", ".join(applied_names))
            if not all_applied:
                print("1 - Add filters")
                print("2 - Remove filters")
                print("3 - Check for filter updates")
                while True:
                    action = input("Choose actions:").strip()
                    if action in {"1", "2", "3"}:
                        break
                if action == "1":
                    add_filters(services, state)
                elif action == "2":
                    remove_filters(services, state)
                elif action == "3":
                    check_for_updates(services, state)
            else:
                print("1 - Remove filters")
                print("2 - Check for filter updates")
                while True:
                    action = input("Choose actions:").strip()
                    if action in {"1", "2"}:
                        break
                if action == "1":
                    remove_filters(services, state)
                elif action == "2":
                    check_for_updates(services, state)
        else:
            add_filters(services, state)

        save_json_file(STATE_FILE, state)
    elif mode == 2:
        patch_updater()
    elif mode == 3:
        hosts_overwrite()

if __name__ == "__main__":
    main()

# Press any key to exit
print("Press any key to exit.")
msvcrt.getch()
