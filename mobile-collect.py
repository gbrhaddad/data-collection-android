# Copyright 2024 Gabriel Haddad
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import time
import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import TimeoutException
import threading

device_configs = [
    {
        "device_name": "Pixel 8 - Device 1",
        "udid": "3A111FDJH001BA",
        "chrome_driver_path": r"C:\Users\testbed\Documents\DVAE11\chromedriver-win64\chromedriver.exe"
    },
    {
        "device_name": "Pixel 8 - Device 2",
        "udid": "3A241FDJH009TX",
        "chrome_driver_path": r"C:\Users\testbed\Documents\DVAE11\chromedriver-win64\chromedriver.exe"
    },
    {
        "device_name": "Pixel 8 - Device 3",
        "udid": "3A121FDJH002TZ",
        "chrome_driver_path": r"C:\Users\testbed\Documents\DVAE11\chromedriver-win64\chromedriver.exe"
    },
    {
        "device_name": "Pixel 8 - Device 4",
        "udid": "3A241FDJH005F5",
        "chrome_driver_path": r"C:\Users\testbed\Documents\DVAE11\chromedriver-win64\chromedriver.exe"
    },
    {
        "device_name": "Pixel 8 - Device 5",
        "udid": "3A241FDJH0065V",
        "chrome_driver_path": r"C:\Users\testbed\Documents\DVAE11\chromedriver-win64\chromedriver.exe"
    }
]

vpn_started = {config["udid"]: False for config in device_configs}
recovering = {config["udid"]: False for config in device_configs}

def start_mullvad_vpn(udid):
    print(f"Starting Mullvad VPN on device {udid}")
    subprocess.run(["adb", "-s", udid, "shell", "am", "start", "-n", "net.mullvad.mullvadvpn/.ui.MainActivity"])
    time.sleep(5)
    subprocess.run(["adb", "-s", udid, "shell", "input", "tap", "540", "2100"])
    time.sleep(5)

def stop_mullvad_vpn(udid):
    print(f"Disconnecting Mullvad VPN on device {udid}")
    time.sleep(5)
    subprocess.run(["adb", "-s", udid, "shell", "input", "tap", "540", "2100"])
    time.sleep(5)


def restart_mullvad_vpn(udid):
    print(f"Starting Mullvad VPN on device {udid}")
    subprocess.run(["adb", "-s", udid, "shell", "am", "start", "-n", "net.mullvad.mullvadvpn/.ui.MainActivity"])
    time.sleep(7)
    subprocess.run(["adb", "-s", udid, "shell", "input", "tap", "540", "2100"])
    time.sleep(5)    
    subprocess.run(["adb", "-s", udid, "shell", "input", "tap", "540", "2100"])


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_last_completed_iteration(base_dir, total_iterations, device_index):
    for sample in range(1, total_iterations + 1):
        for idx in range(1, 51):
            pcap_file = os.path.join(base_dir, f"URL_{idx}_Sample_{sample}_D_{device_index}.pcap")
            png_file = os.path.join(base_dir, f"URL_{idx}_Sample_{sample}_D_{device_index}.png")
            if not (os.path.exists(pcap_file) and os.path.exists(png_file)):
                return sample, idx
    return 1, 1

def check_device_completion(base_dir, total_iterations, device_index):
    for sample in range(1, total_iterations + 1):
        for idx in range(1, 51):
            pcap_file = os.path.join(base_dir, f"URL_{idx}_Sample_{sample}_D_{device_index}.pcap")
            png_file = os.path.join(base_dir, f"URL_{idx}_Sample_{sample}_D_{device_index}.png")
            if not (os.path.exists(pcap_file) and os.path.exists(png_file)):
                return False
    return True

def open_url_with_timeout(driver, url, timeout=15):
    driver.set_page_load_timeout(timeout)
    try:
        driver.get(url)
        time.sleep(2)
        print(f"Successfully opened URL: {url}")
        return True
    except TimeoutException:
        print(f"Failed to open URL: {url} within {timeout} seconds.")
        return False

def check_file_sizes(local_pcap_path, local_screenshot_path):
    try:
        pcap_size = os.path.getsize(local_pcap_path)
        screenshot_size = os.path.getsize(local_screenshot_path)
        if pcap_size > 1024 * 10 and screenshot_size > 1024 * 110:
            print(f"PCAP and PNG files are valid: {local_pcap_path}, {local_screenshot_path}")
            return True
        else:
            print(f"PCAP or PNG file is too small: PCAP ({pcap_size} bytes), PNG ({screenshot_size} bytes)")
            return False
            
    except Exception as e:
        print(f"Error checking file sizes: {e}")
        return False

def run_script_on_device(config, device_index):
    global vpn_started, recovering
    udid = config["udid"]
    chrome_driver_path = config["chrome_driver_path"]

    output_base_dir = 'C:/Users/testbed/Documents/DVAE21/nl-ams-wg-002'  
    create_directory(output_base_dir)

    total_iterations = 20

    if check_device_completion(output_base_dir, total_iterations, device_index):
        print(f"Device {udid} is complete, skipping")
        return

    last_sample, last_url = get_last_completed_iteration(output_base_dir, total_iterations, device_index)
    print(f"Resuming from sample {last_sample}, URL row {last_url} on device {udid}")

    if not vpn_started[udid]:
        start_mullvad_vpn(udid)
        vpn_started[udid] = True

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = config["device_name"]
    options.udid = udid
    options.browser_name = "Chrome"
    options.chromedriver_executable = chrome_driver_path
    options.no_reset = False

    driver = webdriver.Remote(
        command_executor="http://127.0.0.1:4723",
        options=options
    )

    txt_file = 'URLs.txt'
    toggle=0
    for repeat in range(last_sample, total_iterations + 1):
        print(f"Starting iteration {repeat}/{total_iterations} on device {udid}")
        with open(txt_file, mode='r') as file:
            for idx, line in enumerate(file, start=1):
                if repeat == last_sample and idx < last_url:
                    continue

                url = line.strip()

                while True:  
                    try:
                        
                        subprocess.run(
                            ["adb", "-s", udid, "shell", "su", "-c", "rm -rf /data/data/com.android.chrome/cache/*"]
                        )
                        time.sleep(5)

                        pcap_filename = f"URL_{idx}_Sample_{repeat}_D_{device_index}.pcap"
                        screenshot_filename = f"URL_{idx}_Sample_{repeat}_D_{device_index}.png"
                        remote_pcap_path = f"/sdcard/{pcap_filename}"
                        local_pcap_path = os.path.join(output_base_dir, pcap_filename)
                        local_screenshot_path = os.path.join(output_base_dir, screenshot_filename)

                        tcpdump_proc = subprocess.Popen([ 
                            "adb",  "-s", udid, "shell", "su", "-c",
                            f"tcpdump -i any port 51820 -s 64 -w {remote_pcap_path}"
                        ])
                        time.sleep(5)
                        print(f"Started tcpdump for {url} on device {udid}")

                        if not open_url_with_timeout(driver, url, timeout=15):
                            print(f"Error: Timeout while opening {url} on device {udid}, restarting Chrome")
                            subprocess.run(["adb", "-s", udid, "shell", "su", "-c", "pkill tcpdump"])
                            time.sleep(5)
                            driver.quit()
                            recovering[udid] = True
                            run_script_on_device(config, device_index)
                            return

                        print(f"Taking screenshot for URL: {url} (Iteration {repeat}/{total_iterations}) on device {udid}")
                        driver.get_screenshot_as_file(local_screenshot_path)
                        print(f"Screenshot saved to {local_screenshot_path}")
                        time.sleep(20)

                        print(f"Stopping tcpdump for URL: {url} (Iteration {repeat}/{total_iterations}) on device {udid}")
                        subprocess.run(["adb", "-s", udid, "shell", "su", "-c", "pkill tcpdump"])
                        time.sleep(5)

                        subprocess.run(["adb", "-s", udid, "pull", remote_pcap_path, local_pcap_path])
                        print(f"PCAP saved to {local_pcap_path}")
                        subprocess.run(["adb", "-s", udid, "shell", "su", "-c", f"rm {remote_pcap_path}"])
                        time.sleep(5)

                        if not check_file_sizes(local_pcap_path, local_screenshot_path):
                            print(f"Files did not pass validation. Retrying URL {url} on device {udid}")
                            start_mullvad_vpn(udid)
                            continue  
                            
                        toggle+=1
                          

                        if toggle==10: 
                            restart_mullvad_vpn(udid)
                            time.sleep(2)                            
                            toggle=0
                        break    


                    except Exception as e:
                        print(f"Error on device {udid}: {e}. Restarting Chrome")
                       
                        driver.quit()
                        recovering[udid] = True
                        run_script_on_device(config, device_index)
                        return

    print(f"Finished iterations for device {udid}. Disconnecting VPN")
    stop_mullvad_vpn(udid)
    driver.quit()

threads = []
for config in device_configs:
    device_index = device_configs.index(config) + 1
    thread = threading.Thread(target=run_script_on_device, args=(config, device_index))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

print("All devices have completed their tasks")
