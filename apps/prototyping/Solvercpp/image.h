#ifndef IMAGE_h_
#define IMAGE_h_

#include <memory>
#include <vector>
#include <QtCore>
#include <QtCore/QString>

//Includes for this project
#include <libstellarsolver/stellarsolver.h>
#define cimg_display 0
#include <CImg.h>

using namespace cimg_library;


class Image : public QObject
{
    Q_OBJECT
public:
    Image() {ResetData();};
    virtual ~Image() {};
    // Stellasolver stuff
    QPointer<StellarSolver> stellarSolver;
    //std::unique_ptr<StellarSolver> stellarSolver =nullptr;
    
    // Regular stuff
    FITSImage::Statistic stats;

    std::vector<FITSImage::Star> stars;
    uint8_t m_Channels { 1 };
    uint8_t *m_ImageBuffer { nullptr };
    uint32_t m_ImageBufferSize { 0 };

    CImg<uint16_t> img;


    bool LoadFromFile(std::string& filepath);
    void ResetData(void);
    void CalcStats(void);
    void FindStars(void);
    void SolveStars(void);

    bool FindStarsFinished = true;
    bool SolveStarsFinished = true;
    
public slots:
    void sslogOutput(QString text);
    void ssReadySolve(void);
//signals:
//    void successSolve(void);

};

#endif
