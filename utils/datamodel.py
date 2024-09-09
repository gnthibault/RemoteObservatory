from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import List, Optional

# TODO TN: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/

class Sequence(BaseModel):
    id: str

class SequenceType(str, Enum):
    SPECTRO_SEQUENCE       = "spectro_sequence"
    IMAGING_SEQUENCE       = "imaging_sequence"
    CALIBRATION_SEQUENCE   = "calibration_sequence"

class SequenceImageType(str, Enum):
    POINTING               = "pointing"
    ADJUST_POINTING        = "adjust_pointing"
    FIELD_MONITORING       = "field_monitoring"

    # Generic calib
    OFFSET_CALIB           = "offset_calib"
    DARK_CALIB             = "dark_calib"

    # Imaging stuff
    FIELD_SCIENCE          = "field_science"
    FLAT_CALIB             = "flat_calib"

    # Spectro stuff
    SPECTRO_SCIENCE        = "spectro_science"
    SPECTRO_FLAT_CALIB     = "spectro_flat_calib"
    SPECTRO_SPECTRAL_CALIB = "spectro_spectral_calib"

class Image(BaseModel):
    image_id:         str   # Altair AA183MPRO_012345_20230822T220825
    camera_name:      str   # Altair AA183MPRO
    camera_uid:       str   # 012345
    file_path:        str   # /var/RemoteObservatory/images/targets/Alioth/012345/20230822T220718/pointing01.fits

    creator:          str   # RemoteObservatory_0.0.0
    observer:         str   # Remote observatory
    elevation:        float # 650.0000000006121
    latitude:         float # 43.93499999999999
    longitude:        float # 5.710999999999999

    start_time:       str   # 20230822T220825
    exp_time:         float # 10.0
    temperature_degC: float # 15
    gain:             float # 150 #TODO WARNING OBSERVATION
    offset:           float # 30 #TODO WARNING OBSERVATION
    filter:           str   # no-filter

class SequenceImage(Image):
    seq_type:              SequenceImageType # POINTING: bool True / calibration_name': 'dark',
    sequence_id:           str # 20230822T220718
    seq_time:              str # 20230822T220718

    number_exposure:       int   # 2
    time_per_exposure:     float # 5.0
    total_exposure:        float # 10.0
    current_exp:           int   # 0

class ObservationSequenceImage(SequenceImage):
    observation_id:    str   # Alioth_8781831698517
    target_name:       str   # Alioth
    airmass:           float # 2.468465912826544
    moon_fraction:     float # 0.34879647646572376
    moon_separation:   float # 125.02644862252754
    ra_mnt:            float # 193.50543122078386
    ha_mnt:            float # 12.900362081385593
    dec_mnt:           float # 55.959837368488195
    track_mode_mnt:    str   # TRACK_SIDEREAL
    slew_rate_mnt:     str   # 2x
    guide_rate_ns_mnt: float # 0.5
    guide_rate_we_mnt: float # 0.5
    equinox:           float # 2000.0
    field_name:        str   # Alioth
    field_ra:          float # 193.50728958333332
    field_ha:          float # 12.900485972222224
    field_dec:         float # 55.95982277777778
    merit:             float # 1.0
    priority:          float # 0

# WARNING FOR CALIBRATION
# sequence_id: None

#erdantic erdantic.examples.pydantic.Party -t erdantic erdantic.examples.pydantic.Quest -o party.png