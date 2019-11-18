from main.ota_updater import OTAUpdater
import utime

def download_and_install_update_if_available():
    ota_updater = OTAUpdater('https://github.com/WimRoose/esp32-dev')
    ota_updater.download_and_install_update_if_available('Los Borrachos', 'xxxxxxxxxxxx')

def start():
    while True:
        print("helloo-")
        utime.sleep(2)
    # your custom code goes here. Something like this: ...
    # from main.x import YourProject
    # project = YourProject()
    # ...

def boot():
    download_and_install_update_if_available()
    start()


boot()
