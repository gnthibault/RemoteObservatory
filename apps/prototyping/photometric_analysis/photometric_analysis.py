# https://astroquery.readthedocs.io/en/latest/gaia/gaia.html
# https://astroquery.readthedocs.io/en/latest/simbad/simbad.html
# https://sep.readthedocs.io/en/v1.1.x/reference.html

# The coordinate convention in SEP is that (0, 0) corresponds to the center of the first element of the data array.
# This agrees with the 0-based indexing in Python and C. However, note that this differs from the FITS convention
# where the center of the first element is at coordinates (1, 1). As Source Extractor deals with FITS files,
# its outputs follow the FITS convention. Thus, the coordinates from SEP will be offset from Source Extractor
# coordinates by -1 in x and y.



def get_similar_spectral_stars(ra_decimal, dec_decimal, teff, radius_search=0.5, top_n=10):
    # Effectue une requête GAIA pour trouver les étoiles avec une température similaire
    # et trie les résultats par distance (proximité)

    teff_lower_bound = teff - 500
    teff_upper_bound = teff + 500

    query = f"""
    SELECT TOP {top_n} *, DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra_decimal}, {dec_decimal})) as d 
    FROM gaiadr2.gaia_source 
    WHERE 
        teff_val BETWEEN {teff_lower_bound} AND {teff_upper_bound}
        AND phot_g_mean_mag BETWEEN 10 AND 13  -- Ajout de la condition pour la magnitude
        AND 1 = CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra_decimal}, {dec_decimal}, {radius_search})) 
        AND DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', {ra_decimal}, {dec_decimal})) > 0.01
    ORDER BY d ASC"""

    job = Gaia.launch_job(query)
    result = job.get_results()

    return result
