


#include <fstream>
#include <iostream>
#include <memory>
#include <cmath>
#include <fitsio.h>
#include <tuple>
#include <functional>
#include <list>
#include <set>
#include <array>
#include <string>
#include <sys/stat.h>

//Local include
#include "image.h"


//Image::Image() {
//    ResetData();
//}

//Image::~Image() {
//    ResetData();
//}

void Image::ResetData(void) {
}

bool Image::LoadFromFile(std::string& filepath)
{
    ResetData();
    int status = 0, anynullptr = 0;
    long naxes[3];

    fitsfile *fptr;  // FITS file pointer

    // Use open diskfile as it does not use extended file names which has problems opening
    // files with [ ] or ( ) in their names.
    QString fileToProcess;
    fileToProcess = "/home/gnthibault/pointing00.fits";
    if (fits_open_diskfile(&fptr, fileToProcess.toLatin1() , READONLY, &status))
    {
        std::cout<< "Unsupported type or read error loading FITS blob";
        return false;
    }
    else
        stats.size = QFile(fileToProcess).size();

    if (fits_movabs_hdu(fptr, 1, IMAGE_HDU, &status))
    {
        std::cout<<"IMG Could not locate image HDU.";
        fits_close_file(fptr, &status);
        return false;
    }

    int fitsBitPix = 0;
    if (fits_get_img_param(fptr, 3, &fitsBitPix, &(stats.ndim), naxes, &status))
    {
        std::cout<<"IMG FITS file open error (fits_get_img_param).\n";
        fits_close_file(fptr, &status);
        return false;
    }

    if (stats.ndim < 2)
    {
        std::cout<<"IMG 1D FITS images are not supported.\n";
        fits_close_file(fptr, &status);
        return false;
    }

    switch (fitsBitPix)
    {
        case BYTE_IMG:
            stats.dataType      = TBYTE;
            stats.bytesPerPixel = sizeof(uint8_t);
            break;
        case SHORT_IMG:
            // Read SHORT image as USHORT
            stats.dataType      = TUSHORT;
            stats.bytesPerPixel = sizeof(int16_t);
            break;
        case USHORT_IMG:
            stats.dataType      = TUSHORT;
            stats.bytesPerPixel = sizeof(uint16_t);
            break;
        case LONG_IMG:
            // Read LONG image as ULONG
            stats.dataType      = TULONG;
            stats.bytesPerPixel = sizeof(int32_t);
            break;
        case ULONG_IMG:
            stats.dataType      = TULONG;
            stats.bytesPerPixel = sizeof(uint32_t);
            break;
        case FLOAT_IMG:
            stats.dataType      = TFLOAT;
            stats.bytesPerPixel = sizeof(float);
            break;
        case LONGLONG_IMG:
            stats.dataType      = TLONGLONG;
            stats.bytesPerPixel = sizeof(int64_t);
            break;
        case DOUBLE_IMG:
            stats.dataType      = TDOUBLE;
            stats.bytesPerPixel = sizeof(double);
            break;
        default:
            std::cout<<"IMG Bit depth "<< fitsBitPix <<" is not supported.\n";
            fits_close_file(fptr, &status);
            return false;
    }

    if (stats.ndim < 3)
        naxes[2] = 1;

    if (naxes[0] == 0 || naxes[1] == 0)
    {
        std::cout<<"IMG Image has invalid dimensions "<<naxes[0]<<" x "<<naxes[1];
        return false;
    }

    stats.width               = static_cast<uint16_t>(naxes[0]);
    stats.height              = static_cast<uint16_t>(naxes[1]);
    stats.channels            = static_cast<uint8_t>(naxes[2]);
    stats.samples_per_channel = stats.width * stats.height;

    delete[] m_ImageBuffer;
    m_ImageBuffer = nullptr;

    m_ImageBufferSize = stats.samples_per_channel * stats.channels * static_cast<uint16_t>(stats.bytesPerPixel);
    m_ImageBuffer = new uint8_t[m_ImageBufferSize];

    if (m_ImageBuffer == nullptr)
    {
        std::cout<<"IMG FITSData: Not enough memory for image_buffer channel.";
        delete[] m_ImageBuffer;
        m_ImageBuffer = nullptr;
        fits_close_file(fptr, &status);
        return false;
    }

    long nelements = stats.samples_per_channel * stats.channels;

    if (fits_read_img(fptr, static_cast<uint16_t>(stats.dataType), 1, nelements, nullptr, m_ImageBuffer, &anynullptr, &status))
    {
        std::cout<<"IMG Error reading imag: "<<status;
        fits_close_file(fptr, &status);
        return false;
    }

    fits_close_file(fptr,&status);
    
    // Load image into Cimg object
    img=nullptr;
    img.clear();
    img.resize(stats.width ,stats.height,1,1);
    cimg_forXY(img, x, y)
        {
            img(x, img.height() - y - 1) = (reinterpret_cast<uint16_t *>(m_ImageBuffer))[img.offset(x, y)]; // FIXME ???
        }

    CalcStats();
    return true;
}

void Image::CalcStats(void)
{
    stats.min[0] =img.min();
    stats.max[0] =img.max();
    stats.mean[0]=img.mean();
    stats.median[0]=img.median();
    stats.stddev[0]=sqrt(img.variance(1));
    std::cout<<"IMG Min = " << stats.min[0];
    std::cout<<"Max = " << stats.max[0];
    std::cout<<"Avg = " << stats.mean[0];
    std::cout<<"Med = " << stats.median[0];
    std::cout<<"StdDev = " << stats.stddev[0];
}

void Image::SolveStars(void)
{
    SolveStarsFinished = false;

    stellarSolver = new StellarSolver(stats, m_ImageBuffer, this);
    stellarSolver->moveToThread(this->thread());
    stellarSolver->setParent(this);
    connect(stellarSolver,&StellarSolver::logOutput,this,&Image::sslogOutput);
    connect(stellarSolver,&StellarSolver::ready,this,&Image::ssReadySolve);
    stellarSolver->setLogLevel(LOG_ALL);
    stellarSolver->setSSLogLevel(LOG_VERBOSE);
    stellarSolver->m_LogToFile=true;
    stellarSolver->m_LogFileName="/home/gnthibault/Documents/solver.log";
    stellarSolver->m_AstrometryLogLevel=LOG_ALL;

    /*typedef enum { EXTRACT,            //This just sextracts the sources
                   EXTRACT_WITH_HFR,   //This sextracts the sources and finds the HFR
                   SOLVE                //This solves the image
                 } ProcessType;
    typedef enum { EXTRACTOR_INTERNAL, //This uses internal SEP to Sextract Sources
                   EXTRACTOR_EXTERNAL,  //This uses the external sextractor to Sextract Sources.
                   EXTRACTOR_BUILTIN  //This uses whatever default sextraction method the selected solver uses
                 } ExtractorType;
    typedef enum { SOLVER_STELLARSOLVER,    //This uses the internal build of astrometry.net
                   SOLVER_LOCALASTROMETRY,  //This uses an astrometry.net or ANSVR locally on this computer
                   SOLVER_ASTAP,            //This uses a local installation of ASTAP
                   SOLVER_ONLINEASTROMETRY  //This uses the online astrometry.net or ASTAP
                 } SolverType;    */
    stellarSolver->setProperty("ProcessType",SOLVE);
    stellarSolver->setProperty("ExtractorType",EXTRACTOR_INTERNAL);
    stellarSolver->setProperty("SolverType",SOLVER_STELLARSOLVER);
    stellarSolver->start();
    std::cout << "IMG stellarSolver Solve Start";
}

void Image::sslogOutput(QString text)
{
    std::cout<< "IMG Stellarsolver log : " << text.toUtf8().data();
}

void Image::ssReadySolve(void)
{
    std::cout << "IMG stellarSolver ready";
    FindStarsFinished = true;
    SolveStarsFinished = true;
    //emit successSolve();
}


