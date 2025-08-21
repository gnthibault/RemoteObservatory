# Inspired by sample from https://docs.pydantic.dev/latest/concepts/models/#arbitrary-class-instances
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, constr, Field, field_validator
#from sqlmodel import Field, Session, SQLModel, select
from typing import List, Optional

# get_facility_status()
# Returns a dictionary describing the current availability of the Facility telescopes. This is intended to be useful in
# observation planning. The top-level (Facility) dictionary has a list of sites. Each site is represented by a site
# dictionary which has a list of telescopes. Each telescope has an identifier (code) and an status string.
# The dictionary hierarchy is of the form:
# facility_dict = {‘code’: ‘XYZ’, ‘sites’: [ site_dict, … ]}
# where site_dict = {‘code’: ‘XYZ’, ‘telescopes’: [ telescope_dict, … ]}
# where telescope_dict = {‘code’: ‘XYZ’, ‘status’: ‘AVAILABILITY’}

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String)
# Not compatible with sqlite
#from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship, DeclarativeBase

# Local imports
from observatory_server.db_utils import pk_hash, PKTYPE_MODEL, PKTYPE_ORM

default_past_datetime = datetime(1900, 1, 1, 0, 0, 0)
default_future_datetime = datetime(2099, 12, 31, 23, 59, 59)


class Base(DeclarativeBase):
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

# TODO TN: https://sqlmodel.tiangolo.com/tutorial/fastapi/simple-hero-api/

class SequenceType(str, Enum):
    DEFAULT_BR_SPECTRO_SEQUENCE = "default_br_spectro_sequence"
    DEFAULT_HR_SPECTRO_SEQUENCE = "default_hr_spectro_sequence"
    IMAGING_SEQUENCE            = "imaging_sequence"
    CALIBRATION_SEQUENCE        = "calibration_sequence"

class ImageType(str, Enum):
    OBSERVATION            = "observation"
    CALIBRATION            = "calibration"

class InstrumentSetup(str, Enum):
    LR_SPECTROSCOPY        = "lr_spectroscopy"
    HR_SPECTROSCOPY        = "hr_spectroscopy"
    FIEL_IMAGING           = "field_imaging"

class AcquisitionWorkflow(str, Enum):
    DEFAULT                = "default"

class ObservationStatus(str, Enum):
    SUBMITTED              = "submitted"
    SCHEDULED              = "scheduled"
    ACQUIRING              = "acquiring"
    WAITING_CALIBRATION    = "waiting_calibration"
    WAITING_UPLOAD         = "waiting_upload"
    READY                  = "ready"
    CANCELED               = "canceled"
    FAILED                 = "failed"
    TIMED_OUT              = "timed_out"

class SequenceStatus(str, Enum):
    CREATED                = "created"
    FAILED                 = "failed"
    SUCCESSFUL             = "successful"
    TIMED_OUT              = "timed_out"

class ObservationImageType(str, Enum):
    POINTING               = "pointing"
    ADJUST_POINTING        = "adjust_pointing"
    FIELD_MONITORING       = "field_monitoring"

    # Imaging stuff
    FIELD_SCIENCE          = "field_science"

    # Spectro stuff
    SPECTRO_SCIENCE        = "spectro_science"

class CalibrationImageType(str, Enum):
    # Generic calib
    OFFSET_CALIB           = "offset_calib"
    DARK_CALIB             = "dark_calib"

    # Imaging stuff
    FLAT_CALIB             = "flat_calib"

    # Spectro stuff
    SPECTRO_FLAT_CALIB     = "spectro_flat_calib"
    SPECTRO_SPECTRAL_CALIB = "spectro_spectral_calib"

class ObservationOrm(Base):
    __tablename__          = 'observations'
    #id                     = Column(PKTYPE_ORM, primary_key=True, nullable=False)
    id                     = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    target                 = Column(String, nullable=False)
    instrument_setup       = Column(String, nullable=False)
    acquisition_workflow   = Column(String, default=AcquisitionWorkflow.DEFAULT)
    number_exposure        = Column(Integer)
    time_per_exposure      = Column(Float)
    target_snr             = Column(Float)
    submitted_at           = Column(DateTime)
    status                 = Column(String,)
    scheduled_start_at     = Column(DateTime)
    scheduled_end_at       = Column(DateTime)
    updated_at             = Column(DateTime, onupdate=lambda: datetime.now(tz=timezone.utc)),

    # Sequences can be observation sequences of calibration sequences
    sequences              = relationship("SequenceOrm", back_populates="observation")

class Observation(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    #id                     : PKTYPE_MODEL = Field(default_factory=lambda: pk_hash(datetime.now(tz=timezone.utc).isoformat()))
    id                     : Optional[PKTYPE_MODEL] = Field(default=None)
    target                 : str
    instrument_setup       : InstrumentSetup
    acquisition_workflow   : Optional[AcquisitionWorkflow]
    number_exposure        : Optional[int]
    time_per_exposure      : Optional[float]
    target_snr             : Optional[float]
    submitted_at           : datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    status                 : ObservationStatus = Field(default=ObservationStatus.SUBMITTED)
    scheduled_start_at     : Optional[datetime] = Field(default=None)
    scheduled_end_at       : Optional[datetime] = Field(default=None)
    updated_at             : datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @field_validator("target")
    def validate_target(cls, v: str) -> str:
        try:
            t = SkyCoord.from_name(v)
        except NameResolveError as e:
            raise ValueError(f"{v} is not a valid target name: {e}")
        return v


class CameraOrm(Base):
    __tablename__          = 'cameras'
    #id                     = Column(PKTYPE_ORM, primary_key=True, nullable=False)
    id                     = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    serial                 = Column(String,  nullable=False)
    name                   = Column(String,  unique=True)
    # images                 = relationship("ImageOrm", back_populates="CameraOrm")
    # No array in sqlite
    # domains = Column(ARRAY(String(255)))
    #domains = Column(JSON)

class Camera(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    id                     : PKTYPE_MODEL
    serial                 : str
    name                   : str
    # optimal_gain    : float
    # No array in sqlite
    # domains: List[constr(max_length=255)]


class ImageOrm(Base):
    __tablename__          = 'images'
    #id                     = Column(PKTYPE_ORM, primary_key=True, nullable=False)
    id                     = Column(Integer, primary_key=True, autoincrement=True, nullable=False)   # Altair AA183MPRO_012345_20230822T220825
    camera_id              = Column(PKTYPE_ORM, ForeignKey('cameras.id'))   # 012345

    file_path              = Column(String) # /opt/RemoteObservatory/images/targets/Alioth/012345/20230822T220718/pointing01.fits
    asset_uri              = Column(String) # Likely a gs:// uri
    uploaded_at            = Column(DateTime)

    # image_type Discriminator column
    image_type             = Column(String) #ImageType
    sequence_id            = Column(PKTYPE_ORM, ForeignKey('sequences.id'))
    sequence               = relationship("SequenceOrm", back_populates="images")

    creator                = Column(String)   # RemoteObservatory_0.0.0
    observer               = Column(String)   # Remote observatory
    elevation              = Column(Float)    # 650.0000000006121
    latitude               = Column(Float)    # 43.93499999999999
    longitude              = Column(Float)    # 5.710999999999999

    started_at             = Column(DateTime)
    exp_time_sec           = Column(Float) # 10.0
    temperature_deg_c      = Column(Float) # 15
    gain                   = Column(Float) # 150 #TODO WARNING OBSERVATION
    offset                 = Column(Float) # 30 #TODO WARNING OBSERVATION
    filter                 = Column(String) # no-filter
    # roi for reduced acquisition size ?

    __mapper_args__ = {
        'polymorphic_identity': 'image',
        'polymorphic_on'      : image_type
    }

class ObservationImageOrm(ImageOrm):
    __tablename__          = 'observation_images'
    image_id               = Column(PKTYPE_ORM, ForeignKey('images.id'), primary_key=True)
    observation_image_type = Column(String)
    target_name            = Column(String)   # Alioth
    field_name             = Column(String)   # Alioth
    field_ra               = Column(Float) # 193.50728958333332
    field_dec              = Column(Float) # 55.95982277777778
    field_equinox          = Column(Float) # 2000.0
    # has_astrometry         = Column(Boolean) # True/False
    astrometry_ra          = Column(Float)
    astrometry_dec         = Column(Float)
    airmass                = Column(Float) # 2.468465912826544
    moon_fraction          = Column(Float) # 0.34879647646572376
    moon_separation        = Column(Float) # 125.02644862252754
    ra_mnt                 = Column(Float) # 193.50543122078386
    dec_mnt                = Column(Float) # 55.959837368488195
    merit                  = Column(Float) # 1.0
    priority               = Column(Float) # 0

    __mapper_args__ = {
        'polymorphic_identity': 'observation'
    }

class CalibrationImageOrm(ImageOrm):
    __tablename__          = 'calibration_images'
    image_id               = Column(PKTYPE_ORM, ForeignKey('images.id'), primary_key=True)
    calibration_image_type = Column(String)
    valid_from             = Column(DateTime)
    valid_to               = Column(DateTime)

    __mapper_args__ = {
        'polymorphic_identity': 'calibration'
    }

class Image(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    id                     : PKTYPE_MODEL   # Altair AA183MPRO_012345_20230822T220825
    camera_id              : str   # 012345
    file_path              : Optional[str]   # /opt/RemoteObservatory/images/targets/Alioth/012345/20230822T220718/pointing01.fits
    asset_uri              : Optional[str]   # /opt/RemoteObservatory/images/targets/Alioth/012345/20230822T220718/pointing01.fits
    uploaded_at            : Optional[datetime]

    img_type               : ImageType # observation / calibration
    sequence_id            : PKTYPE_MODEL

    creator                : str   # RemoteObservatory_0.0.0
    observer               : str   # Remote observatory
    elevation              : float # 650.0000000006121
    latitude               : float # 43.93499999999999
    longitude              : float # 5.710999999999999

    started_at             : datetime   # 20230822T220825
    exp_time_sec           : float # 10.0
    temperature_deg_c      : float # 15
    gain                   : float # 150 #TODO WARNING OBSERVATION
    offset                 : float # 30 #TODO WARNING OBSERVATION
    filter                 : str   # no-filter


class ObservationImage(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    image_id               : PKTYPE_MODEL
    observation_image_type : ObservationImageType
    target_name            : str   # Alioth
    field_name             : str   # Alioth
    field_ra               : float # 193.50728958333332
    field_dec              : float # 55.95982277777778
    field_equinox          : float # 2000.0
    # has_astrometry         : bool # True/False
    astrometry_ra          : Optional[float]
    astrometry_dec         : Optional[float]
    airmass                : float # 2.468465912826544
    moon_fraction          : float # 0.34879647646572376
    moon_separation        : float # 125.02644862252754
    ra_mnt                 : float # 193.50543122078386
    dec_mnt                : float # 55.959837368488195
    merit                  : float # 1.0
    priority               : float # 0


class CalibrationImage(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    image_id               : PKTYPE_MODEL
    calibration_image_type : CalibrationImageType
    valid_from             : datetime
    valid_to               : datetime
    #     valid_from             = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc))
    #     valid_to               = Column(DateTime, default=lambda: datetime.now(tz=timezone.utc)+timedelta(days=60))

class SequenceOrm(Base):
    __tablename__          = 'sequences'
    id                     = Column(PKTYPE_ORM, primary_key=True)
    name                   = Column(String)
    sequence_type          = Column(String)
    status                 = Column(String, default=SequenceStatus.CREATED)
    observation_id         = Column(PKTYPE_ORM, ForeignKey('observations.id'))
    observation            = relationship("ObservationOrm", back_populates="sequences")
    images                 = relationship("ImageOrm", back_populates="sequence")


    # Reference to a calibration sequence if applicable
    calibration_sequence_id = Column(PKTYPE_ORM, ForeignKey('sequences.id'))

    sequence_time          = Column(DateTime)  # 20230822T220718
    number_exposure        = Column(Integer)   # 2
    time_per_exposure      = Column(Float)     # 5.0
    total_exposure         = Column(Float)     # 10.0
    current_exposure       = Column(Integer)   # 0


class Sequence(BaseModel):
    model_config           = ConfigDict(from_attributes=True)
    id                     : PKTYPE_MODEL
    name                   : str
    sequence_type          : SequenceType
    status                 : SequenceStatus
    observation_id         : Optional[PKTYPE_MODEL]

    calibration_sequence_id : Optional[PKTYPE_MODEL]

    sequence_time          : datetime # 20230822T220718
    number_exposure        : int   # 2
    time_per_exposure      : float # 5.0
    total_exposure         : float # 10.0
    current_exposure       : int   # 0

# WARNING FOR CALIBRATION
# sequence_id: None

#erdantic erdantic.examples.pydantic.Party -t erdantic erdantic.examples.pydantic.Quest -o party.png