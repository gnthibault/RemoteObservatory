from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class SequenceType(str, Enum):
    SPECTRO_SEQUENCE = "spectro_sequence"
    IMAGING_SEQUENCE = "imaging_sequence"
    CALIBRATION_SEQUENCE = "calibrate_sequence"

class SequenceImageType(str, Enum):
    POINTING          = "pointing"
    ADJUST_POINTING   = "adjust_pointing"
    FIELD_MONITORING  = "field_monitoring"

    # Generic calib
    OFFSET_CALIB      = "offset_calib"
    DARK_CALIB        = "dark_calib"

    # Imaging stuff
    FIELD_SCIENCE     = "field_science"
    FLAT_CALIB        = "flat_calib"

    # Spectro stuff
    SPECTRO_SCIENCE   = "spectro_science"
    SPECTRO_FLAT_CALIB = "spectro_flat_calib"
    SPECTRO_SPECTRAL_CALIB = "spectro_spectral_calib"

class Image(BaseModel):
    id: str
    path: str

class SequenceImage(Image):
    seq_type: SequenceImageType
    reference_sequence_id: str


class FieldMonitoringImage(SequenceImage):
    reference_sequence_id: str

class SpectroImage(SequenceImage):
    reference_sequence_id: str


class Sequence(BaseModel):
    id: str

class ImagingSequence(Sequence):
    id: str

class SpectroSequence(Sequence):
    profession: str
    level: int

#erdantic erdantic.examples.pydantic.Party -t erdantic erdantic.examples.pydantic.Quest -o party.png