

#include <cstdlib>
#include <iostream>
#include <QtCore>

#include "image.h"


int main(int argc, char* argv[])
{
    /*Image im;
    std::string filepath = "/home/gnthibault/Documents/pointing00.fits";
    im.LoadFromFile(filepath);

    QThread workerThread;
    im.moveToThread(&workerThread);
    im.SolveStars();
    im.thread()->wait();*/
    
    QCoreApplication a(argc, argv);

    // Task parented to the application so that it
    // will be deleted by the application.
    Image *im = new Image(&a);

    // This will cause the application to exit when
    // the task signals finished.    
    QObject::connect(im, &Image::successSolve, &a, &QCoreApplication::quit);

    // This will run the task from the application event loop.
    QTimer::singleShot(0, im, &Image::run);

    return a.exec();


    //return EXIT_SUCCESS;
}
