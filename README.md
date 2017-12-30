# RemoteObservatory
Another astronomical observatory manager

## Install
sudo apt-add-repository ppa:mutlaqja/ppa
sudo apt-get update
sudo apt-get install libcfitsio-dev libnova-dev swig indi-full kstars-bleeding
pip install requests pyindi-client requests-cache watchdog astropy

## Web service

For now, RemoteObservatory only uses WUG, so, ensure that you have a json file containing your wug key in your home directory inside a .wug.json file


