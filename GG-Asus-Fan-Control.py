#!/usr/bin/env python3
import sys
import subprocess
import time
import os
import re

# Metadata
version = "3.0.5"
author = "Gerald Hasani"
name = "GG-Asus-Fan-Control"
email = "contact@gerald-hasani.com"
github = "https://github.com/Gerald-Ha"
config_file = os.path.expanduser("~/.gg-asus-fan-control.conf")

# Temperature thresholds for the different modes
GG_MODE_THRESHOLD = 80  # Temperature in degrees Celsius for GG Mode
GAMING_MODE_THRESHOLD = 70  # Temperature in degrees Celsius for Gaming Mode

def print_ascii_art():
    CYAN = "\033[36m"
    RESET = "\033[0m"
    ascii_art = r"""
____  ____       _____
/ ___|/ ___|     |  ___|_ _ _ __
| |  _| |  _ _____| |_ / _  | '_ \
| |_| | |_| |_____|  _| (_| | | | |
\____|\____|     |_|  \__,_|_| |_|
"""
    print(f"{CYAN}{ascii_art}{RESET}")
    print()

def get_cpu_temperature():
    try:
        # Read Intel Package id 0 temperature from coretemp
        output = subprocess.getoutput("sensors | grep -i 'Package id 0'")
        if not output:
            output = subprocess.getoutput("sensors | grep -i 'Tctl'")
        if not output:
            output = subprocess.getoutput("sensors | grep -i 'Core 0'")
            
        if output:
            # Use regex to extract the first temperature value safely
            match = re.search(r'[\+\-]?\d+\.?\d*', output.split(":")[1])
            if match:
                return float(match.group())
        return None
    except Exception:
        return None

def set_fan_speed_manual(mode):
    base_path = "/sys/devices/platform/asus-nb-wmi/hwmon/"
    try:
        hwmon_dirs = [d for d in os.listdir(base_path) if d.startswith("hwmon")]
    except FileNotFoundError:
        print("ASUS WMI hwmon directory not found. Ensure the asus-nb-wmi module is loaded.")
        return

    if not hwmon_dirs:
        print("No valid hwmon directory found.")
        return

    hwmon_dir = hwmon_dirs[0]
    pwm1_enable_path = f'{base_path}{hwmon_dir}/pwm1_enable'
    pwm1_path = f'{base_path}{hwmon_dir}/pwm1'

    try:
        if mode == "full":
            # In recent kernels, pwm1_enable=0 might default to auto/normal profile.
            # We explicitly set manual mode (1) and max PWM (255) to force 100% speed.
            with open(pwm1_enable_path, 'w') as f:
                f.write('1')
            with open(pwm1_path, 'w') as f:
                f.write('255')
        elif mode == "auto":
            # Set to auto mode
            with open(pwm1_enable_path, 'w') as f:
                f.write('2')
        else:
            print("Unknown mode")
            return
    except Exception as e:
        print(f"Error setting fan speed: {e}")
        # Fallback for older kernels or specific driver behaviours
        if mode == "full":
            try:
                with open(pwm1_enable_path, 'w') as f:
                    f.write('0')
            except Exception as e2:
                print(f"Fallback error setting fan speed: {e2}")

def save_choice(choice):
    with open(config_file, "w") as file:
        file.write(choice)

def load_choice():
    try:
        with open(config_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "system"

def monitor_temperature(mode, interval=3):
    while True:
        current_temp = get_cpu_temperature()
        if current_temp is not None:
            if mode == "gaming" and current_temp >= GAMING_MODE_THRESHOLD:
                set_fan_speed_manual("full")
            elif mode == "gg" and current_temp >= GG_MODE_THRESHOLD:
                set_fan_speed_manual("full")
            else:
                set_fan_speed_manual("auto")
        time.sleep(interval)

def main():
    print_ascii_art()
    current_mode = load_choice()
    mode_display = {
        "system": "System Mode",
        "gg-mode": "GG Mode",
        "gaming-mode": "Gaming Mode"
    }
    current_mode_display = mode_display.get(current_mode, "Unknown Mode")
    print(f"Current Mode: {current_mode_display}")
    print()

    if "--service" in sys.argv:
        choice = load_choice()
        if choice == "gg-mode":
            print("GG Mode is being activated as a service.")
            monitor_temperature("gg", interval=4)
        elif choice == "gaming-mode":
            print("Gaming Mode is being activated as a service.")
            monitor_temperature("gaming", interval=4)
        else:
            set_fan_speed_manual("auto")
        return

    print("Please choose an option:")
    print()
    print("1. System Mode")
    print("2. GG Mode")
    print("3. Gaming Mode")
    print()
    choice = input("Enter the number of your choice: ")
    print()

    if choice == "1":
        save_choice("system")
        set_fan_speed_manual("auto")
        print("Fan control set to System Mode. The fan will operate automatically.")
        os.system("sudo systemctl stop gg-asus-fan-control.service")
    elif choice == "2":
        save_choice("gg-mode")
        print("GG Mode activated")
        os.system("sudo systemctl restart gg-asus-fan-control.service")
    elif choice == "3":
        save_choice("gaming-mode")
        print("Gaming Mode activated")
        os.system("sudo systemctl restart gg-asus-fan-control.service")
    else:
        print("Invalid selection. Please run the script again and choose a valid option.")

if __name__ == "__main__":
    main()
