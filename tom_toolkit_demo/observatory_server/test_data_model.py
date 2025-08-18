# Generic imports
from datetime import datetime, timedelta
import erdantic as erd
import farmhash
from importlib import resources
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.mssql.information_schema import sequences
from sqlalchemy.orm import sessionmaker

# Local imports
from observatory_server.datamodel import (
    Base,
    CalibrationImage,
    CalibrationImageOrm,
    CalibrationImageType,
    Camera,
    CameraOrm,
    Image,
    ImageOrm,
    ImageType,
    Observation,
    ObservationImage,
    ObservationImageOrm,
    ObservationImageType,
    ObservationOrm,
    ObservationStatus,
    Sequence,
    SequenceOrm,
    SequenceStatus,
    SequenceType,
)
from observatory_server.db_utils import PKTYPE_MODEL

def pk_hash(pk_str: str) -> PKTYPE_MODEL:
    return PKTYPE_MODEL(farmhash.fingerprint64(pk_str))


def update_objects(*args):
    session.add_all([el for el in args])
    session.commit()


# Utility, because image is too long...
def gen_obs_image(obs_target, field_name, camera, sequence):
    img_time = datetime.now(tz=None)
    img_name = obs_target + '_' + img_time.isoformat()
    img_id = pk_hash(img_name)

    obs_image = ObservationImageOrm(
        id=img_id,
        camera_id=camera.id,  # 012345
        file_path=None,
        asset_uri=None,
        uploaded_at=None,
        image_type=ImageType.OBSERVATION,
        sequence_id=sequence.id,
        creator="Observatory",
        observer="gnthibault",
        elevation=650,
        latitude=43.2,
        longitude=5.2,
        started_at=datetime.now(tz=None),
        exp_time_sec=300,
        temperature_deg_c=-10,
        gain=125,
        offset=10,
        filter=None,
        # roi for reduced acquisition size ?
        # Starting definition of observation image
        image_id=img_id,
        observation_image_type=ObservationImageType.SPECTRO_SCIENCE,
        target_name=obs_target,
        field_name=field_name,
        field_ra=193.5,
        field_dec=55.9,
        field_equinox=2000.0,
        astrometry_ra=None,
        astrometry_dec=None,
        airmass=2.46,
        moon_fraction=0.35,
        moon_separation=125.2,
        ra_mnt=193.3,
        dec_mnt=55.9,
        merit=1,
        priority=0,
    )
    ObservationImage.model_validate(obs_image)
    return obs_image


def gen_calib_image(camera, sequence, calib_type=CalibrationImageType.SPECTRO_FLAT_CALIB):
    img_time = datetime.now(tz=None)
    img_name = f'calibration_{calib_type}_' + img_time.isoformat()
    img_id = pk_hash(img_name)

    calibration_image = CalibrationImageOrm(
        id=img_id,
        camera_id=camera.id,  # 012345
        file_path=None,
        asset_uri=None,
        uploaded_at=None,
        image_type=ImageType.CALIBRATION,
        sequence_id=sequence.id,
        creator="Observatory",
        observer="gnthibault",
        elevation=650,
        latitude=43.2,
        longitude=5.2,
        started_at=datetime.now(tz=None),
        exp_time_sec=300,
        temperature_deg_c=-10,
        gain=125,
        offset=10,
        filter=None,
        # roi for reduced acquisition size ?
        # Starting definition of observation image
        image_id=img_id,
        calibration_image_type=calib_type,
        valid_from=datetime.now(tz=None) + timedelta(days=30),
        valid_to=datetime.now(tz=None) + timedelta(days=30),
    )
    CalibrationImage.model_validate(calibration_image)
    return calibration_image


# Now Real orm stuff
with resources.path(
        "data", "datamodel_usage_demo.db"
) as sqlite_filepath:
    engine = create_engine(f"sqlite:///{sqlite_filepath}")
# engine = create_engine('sqlite:///:memory:', echo=False)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

# Create a camera
camera_name = "ASI 533 MMM Pro"
serial = "5a3399b"
camera = CameraOrm(
    id=pk_hash(camera_name + "_" + serial),
    serial=serial,
    name=camera_name
)
Camera.model_validate(camera)
update_objects(camera)

# Create an observation A
obs_target = 'M_42'
field_name = obs_target
submit_time = datetime.now(tz=None)
obs_name = obs_target + '_' + submit_time.isoformat()
observation_a = ObservationOrm(
    id=pk_hash(obs_name),
    name=obs_name,
    submitted_at=submit_time,
    status=ObservationStatus.SUBMITTED)
Observation.model_validate(observation_a)
update_objects(observation_a)

# Create an observation sequence for observation A and add observation images
seq_time = datetime.now(tz=None)
seq_name = obs_target + '_' + seq_time.isoformat()
sequence_a1 = SequenceOrm(
    id=pk_hash(seq_name),
    name=seq_name,
    sequence_type=SequenceType.DEFAULT_BR_SPECTRO_SEQUENCE,
    status=SequenceStatus.CREATED,
    observation_id=observation_a.id,
    sequence_time=seq_time,
    number_exposure=2,
    time_per_exposure=5,
    total_exposure=10,
    current_exposure=0
)
Sequence.model_validate(sequence_a1)
update_objects(sequence_a1)
obs_image = gen_obs_image(obs_target, field_name, camera, sequence_a1)
update_objects(obs_image)
sequence_a1.current_exposure = 1  # UPDATE NEEDED
update_objects(sequence_a1)

# Create another observation sequence for observation A and add observation images
seq_time = datetime.now(tz=None)
seq_name = obs_target + '_' + seq_time.isoformat()
sequence_a2 = SequenceOrm(
    id=pk_hash(seq_name),
    name=seq_name,
    sequence_type=SequenceType.DEFAULT_BR_SPECTRO_SEQUENCE,
    status=SequenceStatus.CREATED,
    observation_id=observation_a.id,
    sequence_time=seq_time,
    number_exposure=2,
    time_per_exposure=5,
    total_exposure=10,
    current_exposure=0
)
update_objects(sequence_a2)
obs_image2 = gen_obs_image(obs_target, field_name, camera, sequence_a2)
update_objects(obs_image2)
sequence_a2.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_a2)
obs_image3 = gen_obs_image(obs_target, field_name, camera, sequence_a2)
update_objects(obs_image3)
sequence_a2.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_a2)
sequence_a2.status = SequenceStatus.SUCCESSFUL
update_objects(sequence_a2)

# Create an observation B
obs_target = 'M_51'
field_name = obs_target
submit_time = datetime.now(tz=None)
obs_name = obs_target + '_' + submit_time.isoformat()
observation_b = ObservationOrm(
    id=pk_hash(obs_name),
    name=obs_name,
    submitted_at=submit_time,
    status=ObservationStatus.SUBMITTED)
Observation.model_validate(observation_b)
update_objects(observation_b)

# Create an observation sequence B and add observation images
seq_time = datetime.now(tz=None)
seq_name = obs_target + '_' + seq_time.isoformat()
sequence_b1 = SequenceOrm(
    id=pk_hash(seq_name),
    name=seq_name,
    sequence_type=SequenceType.DEFAULT_BR_SPECTRO_SEQUENCE,
    status=SequenceStatus.CREATED,
    observation_id=observation_b.id,
    sequence_time=seq_time,
    number_exposure=2,
    time_per_exposure=5,
    total_exposure=10,
    current_exposure=0
)
Sequence.model_validate(sequence_b1)
update_objects(sequence_b1)
obs_image4 = gen_obs_image(obs_target, field_name, camera, sequence_b1)
update_objects(obs_image4)
sequence_b1.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_b1)
obs_image5 = gen_obs_image(obs_target, field_name, camera, sequence_b1)
update_objects(obs_image5)
sequence_b1.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_b1)
sequence_b1.status = SequenceStatus.SUCCESSFUL
update_objects(sequence_b1)

# Create a calibration sequences for both A and B observations and add calibration images
seq_time = datetime.now(tz=None)
seq_name = 'calibration_' + seq_time.isoformat()
sequence_calib = SequenceOrm(
    id=pk_hash(seq_name),
    name=seq_name,
    sequence_type=SequenceType.CALIBRATION_SEQUENCE,
    status=SequenceStatus.CREATED,
    observation_id=None,
    sequence_time=seq_time,
    number_exposure=2,
    time_per_exposure=5,
    total_exposure=10,
    current_exposure=0
)
calib_image1 = gen_calib_image(camera, sequence_calib, calib_type=CalibrationImageType.SPECTRO_FLAT_CALIB)
update_objects(calib_image1)
sequence_calib.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_calib)
calib_image2 = gen_calib_image(camera, sequence_calib, calib_type=CalibrationImageType.DARK_CALIB)
update_objects(calib_image2)
sequence_calib.current_exposure += 1  # UPDATE NEEDED
update_objects(sequence_calib)
sequence_calib.status = SequenceStatus.SUCCESSFUL
update_objects(sequence_calib)

# UPDATE NEEDED
sequence_a1.calibration_sequence_id = sequence_calib.id
sequence_a2.calibration_sequence_id = sequence_calib.id
sequence_b1.calibration_sequence_id = sequence_calib.id
update_objects(sequence_a1, sequence_a2, sequence_b1)

# Update needed
observation_a.status = ObservationStatus.READY
observation_b.status = ObservationStatus.READY
update_objects(observation_a, observation_b)
####################################
##            Querying            ##
####################################

# Cleanup: Check if there are observations that are not in final stage

# Cleanup: check if there are pending sequences

# Check if a given observation is completed, ie the amount of images for a given sequence is ok as well as if there is
# a valid calibration sequence

# Find all images (obs+calib) for a given observation
observation = observation_a
## Step 1: find all successful sequences for the observation
all_valid_seq = session.query(SequenceOrm). \
    join(ObservationOrm, SequenceOrm.observation_id == ObservationOrm.id). \
    filter(ObservationOrm.id == observation.id). \
    filter(ObservationOrm.status == ObservationStatus.READY). \
    filter(SequenceOrm.status == SequenceStatus.SUCCESSFUL).all()

all_valid_calib_seq = session.query(SequenceOrm). \
    filter(SequenceOrm.id in [el.calibration_sequence_id for el in all_valid_seq]).all()

#results = query.all()
# from sqlalchemy.sql import text user = session.query(User).from_statement(    text("""SELECT * FROM users where name=:name""") ).params(name="ed").all() return user
# for user in results:
#     print(user)

# Useless, as foreign keys are not taken into account
# diagram = erd.create(
#     CalibrationImage,
#     Camera,
#     Image,
#     ObservationImage,
#     Observation,
#     Sequence,
#     )
# diagram.draw("datamodel_usage_demo.png")

# This is much more useful
# eralchemy -i sqlite:///data/datamodel_usage_demo.db -o ./datamodel_usage_demo_diagram.pdf

session.close()










