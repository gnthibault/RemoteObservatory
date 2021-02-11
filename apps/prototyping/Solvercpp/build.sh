# sudo apt-get install cimg-dev libstellarsolver-dev libqt5core5a qtdeclarative5-dev qtbase5-dev qt5-default qtcreator
#g++ ./image.cpp ./test.cpp -fPIC -I/usr/include/x86_64-linux-gnu/qt5/ -I/usr/include/x86_64-linux-gnu/qt5/QtCore -I/usr/include/libstellarsolver/ -L/usr/lib -L/usr/lib/x86_64-linux-gnu -pthread -lQt5Core -lcfitsio -lstellarsolver -o ./test
qmake Solvercpp.pro
make

#Eventually launch with LD_LIBRARY_PATH=/opt/anaconda3/lib/ ./Solvercpp 
