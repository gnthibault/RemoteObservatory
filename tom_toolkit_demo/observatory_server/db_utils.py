# Generic imports
import erdantic as erd
import farmhash
from importlib import resources
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker


# Int primary key in BQ: https://cloud.google.com/bigquery/docs/best-practices-performance-compute#use_int64_data_types_in_joins
#np.uint64(farmhash.fingerprint64('6823339101')).astype('int64')
# Unfortunately not compatible with SQLite
PKTYPE_MODEL = str
PKTYPE_ORM   = String

def pk_hash(pk_str: str) -> PKTYPE_MODEL:
    return PKTYPE_MODEL(farmhash.fingerprint64(pk_str))

# -----------------------------
# Database setup (SQLite here)
# -----------------------------
#SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
with resources.path(
        "data", "datamodel_usage_demo.db"
) as sqlite_filepath:
    engine = create_engine(f"sqlite:///{sqlite_filepath}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Brutal initialization with Base from your datamodel
#Base.metadata.drop_all(bind=engine)
#Base.metadata.create_all(engine)


# -----------------------------
# Dependency (DB session)
# -----------------------------
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

