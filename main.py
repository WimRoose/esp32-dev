from main.ota_updater import OTAUpdater
import utime

def download_and_install_update_if_available():
    ota_updater = OTAUpdater()
    ota_updater.download_and_install_update_if_available('Los Borrachos', 'xxxxxxxxxxxx')

def start():
    import main.main
    # your custom code goes here. Something like this: ...
    # from main.x import YourProject
    # project = YourProject()
    # ...

def boot():
    download_and_install_update_if_available()
    start()


boot()
