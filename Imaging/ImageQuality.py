# common stuff

#astronomy related tools 
import astroalign as aa

class ImageQuality:
    def __init__():
        pass
        
        
    def generate_quality_report(self, source, target):
        """Abstract from Astroalign (https://github.com/toros-astro/astroalign)
        documentation: If we are only interested in knowing the transformation
        and the correspondence of control points in both images, use
        find_transform will return the transformation in a Scikit-Image
        SimilarityTransform object and a list of stars in source with the
        corresponding stars in target.

        The returned transf object is a scikit-image SimilarityTranform object
        that contains the transformation matrix along with the scale, rotation
        and translation parameters.

        s_list and t_list are numpy arrays of (x, y) point correspondence
        between source and target. transf applied to s_list will approximately
        render t_list.

        Oh, I'm sorry I misunderstood your question. For source detection I basically use sep. I would recommend using sep or photutils instead, because my wrapper is pretty simple and naive, but you can still check the code I use, it's in the private _find_sources method.
        SEP does not estimate psf AFAIK, but if you're looking for something like that, you may want to open an issue in properimage. The author there does PSF estimation, I can't remember now what method he uses.
        """

        transf, (s_list, t_list) = aa.find_transform(source, target)


