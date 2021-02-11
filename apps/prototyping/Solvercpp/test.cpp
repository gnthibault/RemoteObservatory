

#include <cstdlib>
#include <iostream>
#include <string>

// Qt
#include <QtCore>

#include "image.h"


int main(int argc, char* argv[])
{
    if (argc != 2) {
        std::cout << "Please provide fits path" << std::endl;
        return EXIT_SUCCESS;
    }
    QCoreApplication a(argc, argv);

    // Task parented to the application so that it
    // will be deleted by the application.
    std::string fits_filepath = argv[1];
    Image *im = new Image(&a, fits_filepath);

    // This will cause the application to exit when
    // the task signals finished.    
    QObject::connect(im, &Image::successSolve, &a, &QCoreApplication::quit);

    // This will run the task from the application event loop.
    QTimer::singleShot(0, im, &Image::run);

    return a.exec();
}
