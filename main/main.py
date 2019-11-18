from main.ota_updater import OTAUpdater


def download_and_install_update_if_available():
    ota_updater = OTAUpdater('https://Wim_Roose@bitbucket.org/Wim_Roose/esp32-dev.git')
    ota_updater.download_and_install_update_if_available('Los Borrachos', 'xxxxxxxxxxxx')

def start():
	print("helloo")
	pass
    # your custom code goes here. Something like this: ...
    # from main.x import YourProject
    # project = YourProject()
    # ...

def boot():
    download_and_install_update_if_available()
    start()


boot()
