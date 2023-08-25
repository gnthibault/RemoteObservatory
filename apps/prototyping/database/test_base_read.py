from Base.Base import Base
from utils.database import FileDB, create_storage_obj
#from utils.datamodel import

b = Base()
print(b.db.collection_names)
"""
    collection_names = [
        'scope_controller', # useless ?
        'config',        # useless ?
        'current',       # useless ?
        'calibrations',
        'environment',   # useless ?
        'mount',         # useles
        'observations',
        'offset_info',   # Legacy: Used to be there to store guiding delta info
        'state',
        'weather',
    ]
"""

# Test actual DB
latest_observation = b.db.get_current(collection="observations")
latest_calibration = b.db.get_current(collection='calibrations')

# Test DB creation and usage
file_db = FileDB()

# test storage object (unstructured)
obj = create_storage_obj()
print(obj)