

#include <cstdlib>
#include <iostream>
#include "image.h"


int main(int argc, char* argv[])
{
    Image im;
    std::string filepath = "/home/gnthibault/Documents/pointing00.fits";
    im.LoadFromFile(filepath);
    return EXIT_SUCCESS;
}
