from Base.Base import Base


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

latest_calibration = b.db.get_current(collection='calibrations')


def find(self, collection, obj_id):
