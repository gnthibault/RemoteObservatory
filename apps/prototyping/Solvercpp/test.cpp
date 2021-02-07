

#include <cstdlib>
#include <iostream>
#include "image.h"


int main(int argc, char* argv[])
{
    Image im;
    std::string filepath = "/home/gnthibault/pointing00.fits";
    im.LoadFromFile(filepath);
    std::cout << "It works";
    return EXIT_SUCCESS;
}
