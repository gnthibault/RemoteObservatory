#ifndef IMAGE_h_
#define IMAGE_h_

#include <memory>
#include <vector>

//Includes for this project
#include <libstellarsolver/stellarsolver.h>
#define cimg_display 0
#include <CImg.h>

using namespace cimg_library;


class Image
{
public:
    Image();
    ~Image();
    // Stellasolver stuff
    FITSImage::Statistic stats;
    std::unique_ptr<StellarSolver> stellarSolver =nullptr;
    std::vector<FITSImage::Star> stars;
    uint8_t m_Channels { 1 };
    uint8_t *m_ImageBuffer { nullptr };
    uint32_t m_ImageBufferSize { 0 };

    CImg<uint16_t> img;


    void ResetData(void);
    void CalcStats(void);
    void FindStars(void);
    void SolveStars(void);

    bool FindStarsFinished = true;
    bool SolveStarsFinished = true;
};

#endif
