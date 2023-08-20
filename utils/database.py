# Generic
import abc
from glob import glob
import logging
import os
import pymongo
import threading
from uuid import uuid4
from warnings import warn
import weakref

# Local
from utils import serializers as json_util
from utils.config import load_config
from Service.HostTimeService import HostTimeService

class AbstractDB(metaclass=abc.ABCMeta):
    def __init__(self, db_name=None, collection_names=list(), logger=None,
                 serv_time=HostTimeService(), **kwargs):
        """
        Init base class for db instances.

        Args:
            db_name: Name of the database, typically panoptes or
                     panoptes_testing.
            collection_names (list of str): Names of the valid collections.
            logger: (Optional) logger to use for warnings.
        """
        self.db_name = db_name
        self.collection_names = collection_names
        self.logger = logger or logging.getLogger(__name__)
        self.serv_time = serv_time

    def _warn(self, *args, **kwargs):
        if self.logger:
            self.logger.warning(*args, **kwargs)
        else:
            warn(*args)

    def validate_collection(self, collection):
        if collection not in self.collection_names:
            msg = 'Collection type {!r} not available'.format(collection)
            self._warn(msg)
            # Can't import utils.error earlier
            from utils.error import InvalidCollection
            raise InvalidCollection(msg)

    @abc.abstractclassmethod
    def insert_current(self, collection, obj, store_permanently=True):
        """Insert an object into both the `current` collection and the
           collection provided.

        Args:
            collection (str): Name of valid collection within the db.
            obj (dict or str): Object to be inserted.
            store_permanently (bool): Whether to also update the collection,
                defaults to True.

        Returns:
            str: identifier of inserted record. If `store_permanently` is True,
                will be the identifier of the object in the `collection`,
                otherwise will be the identifier of object in the `current`
                collection. These may or may not be the same.
                Returns None if unable to insert into the collection.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def insert(self, collection, obj):
        """Insert an object into the collection provided.

        The `obj` to be stored in a collection should include the `type`
        and `date` metadata as well as a `data` key that contains the actual
        object data. If these keys are not provided then `obj` will be wrapped
        in a corresponding object that does contain the metadata.

        Args:
            collection (str): Name of valid collection within the db.
            obj (dict or str): Object to be inserted.

        Returns:
            str: identifier of inserted record in `collection`.
                Returns None if unable to insert into the collection. Can be
                considered as an object_id
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_current(self, collection):
        """Returns the most current record for the given collection

        Args:
            collection (str): Name of the collection to get most current from

        Returns:
            dict|None: Current object of the collection or None.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def find(self, collection, obj_id):
        """Find an object by it's identifier.

        Args:
            collection (str): Collection to search for object.
            obj_id (ObjectID|str): Record identifier returned earlier by insert
                or insert_current.

        Returns:
            dict|None: Object matching identifier or None.
        """
        raise NotImplementedError

    @abc.abstractclassmethod
    def clear_current(self, type):
        """Clear the current record of a certain type

        Args:
            type (str): The type of entry in the current collection that
                should be cleared.
        """
        raise NotImplementedError


###############################################################################
#    MongoDB implementation
###############################################################################

_shared_mongo_clients = weakref.WeakValueDictionary()

def get_shared_mongo_client(host, port, connect):
    """Provides a mongodb database manager class as a singleton

    Args:
        host (str): domain name or ip address of the server hosting the db
        port (int): Port on which the server database listen
        connect (?): ?

    Returns:
        pymongo.MongoClient: the database connector class 
    """
    global _shared_mongo_clients
    key = (host, port, connect)
    try:
        client = _shared_mongo_clients[key]
        if client:
            return client
    except KeyError:
        pass

    client = pymongo.MongoClient(host, port, connect=connect)

    _shared_mongo_clients[key] = client
    return client


def create_storage_obj(collection, data, obj_id=None,
                       serv_time=HostTimeService()):
    """Returns the object to be stored in the database"""
    obj = dict(data=data, type=collection, date=serv_time.get_utc())
    if obj_id:
        obj['_id'] = obj_id
    return obj


class DB():
    """Simple class to load the appropriate DB type based on the config.

    We don't actually create instances of this class, but instead create
    an instance of the 'correct' type of db.
    """

    def __new__(cls, db_type=None, db_name=None, *args, **kwargs):
        """Create an instance based on db_type."""

        if not isinstance(db_name, str) and db_name:
            raise ValueError('db_name, a string, must not be empty')

        if db_type is None:
            db_type = load_config()['db']['type']

        if db_name is None:
            db_name = load_config()['db']['name']

        if not isinstance(db_type, str) and db_type:
            raise ValueError('db_type, a string, must  not be empty')

        # Pre-defined list of collections that are valid.
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

        if db_type == 'mongo':
            try:
                return MongoDB(collection_names=collection_names,
                               db_name=db_name, **kwargs)
            except Exception:
                raise Exception('Cannot connect to mongo, please check '
                                'settings or change DB storage type')
        elif db_type == 'file':
            return FileDB(collection_names=collection_names,
                          db_name=db_name, **kwargs)
        elif db_type == 'memory':
            return MemoryDB.get_or_create(collection_names=collection_names,
                                          db_name=db_name, **kwargs)
        else:
            raise Exception('Unsupported database type: {}', db_type)

    @classmethod
    def permanently_erase_database(cls, db_type, db_name, really=False,
                                   dangerous=False):
        """Permanently delete the contents of the identified database."""
        if not isinstance(db_type, str) and db_type:
            raise ValueError('db_type, a string, must be provided and not '
                             'empty; was {!r}', db_type)
        if not isinstance(db_name, str) or 'test' not in db_name:
            raise ValueError('permanently_erase_database() called for non-test'
                             ' database {!r}'.format(db_name))
        if really != 'Yes' or dangerous != 'Totally':
            raise Exception('DB.permanently_erase_database called with '
                            'invalid args!')
        if db_type == 'mongo':
            MongoDB.permanently_erase_database(db_name)
        elif db_type == 'file':
            FileDB.permanently_erase_database(db_name)
        elif db_type == 'memory':
            MemoryDB.permanently_erase_database(db_name)
        else:
            raise Exception('Unsupported database type: {}', db_type)


class MongoDB(AbstractDB):
    def __init__(self, db_name='remote_observatory', host='localhost',
                 port=27017, connect=False, **kwargs):
        """Connection to the running MongoDB instance

        This is a collection of parameters that are initialized when the unit
        starts and can be read and updated as the project is running.
        The server is a wrapper around a mongodb collection.

        Note:
            Because mongo can create collections at runtime, the pymongo module
            will also lazily create both databases and collections based off of
            attributes on the client. This means the attributes do not need to
            exist on the client object beforehand and attributes assigned to the
            object will automagically create a database and collection.

            Because of this, we manually store a list of valid collections that
            we want to access so that we do not get spuriously created
            collections or databases.

        Args:
            db_name (str, optional): Name of the database containing the
                                     collections.
            host (str, optional): hostname running MongoDB.
            port (int, optional): port running MongoDb.
            connect (bool, optional): Connect to mongo on create, defaults to
                                      True.
        """

        super().__init__(**kwargs)

        # Get the mongo client.
        self._client = get_shared_mongo_client(host, port, connect)

        # Create an attribute on the client with the db name.
        db_handle = self._client[db_name]

        # Setup static connections to the collections we want.
        for collection in self.collection_names:
            # Add the collection as an attribute.
            setattr(self, collection, getattr(db_handle, collection))

    def insert_current(self, collection, obj, store_permanently=True):
        self.validate_collection(collection)
        obj = create_storage_obj(collection, obj, self.serv_time)
        try:
            # Update `current` record. If one doesn't exist, insert one. This
            # combo is known as UPSERT (i.e. UPDATE or INSERT).
            upsert = True
            obj_id = self.current.replace_one({'type': collection}, obj,
                                              upsert).upserted_id
            if not store_permanently and not obj_id:
                # There wasn't a pre-existing record, so upserted_id was None.
                obj_id = self.get_current(collection)['_id']
        except Exception as e:
            self._warn('Problem inserting object into current collection: '
                       '{}, {!r}'.format(e, obj))
            obj_id = None

        if store_permanently:
            try:
                col = getattr(self, collection)
                obj_id = col.insert_one(obj).inserted_id
            except Exception as e:
                self._warn('Problem inserting object into collection: '
                           '{}, {!r}'.format(e, obj))
                obj_id = None

        if obj_id:
            return str(obj_id)
        return None

    def insert(self, collection, obj):
        self.validate_collection(collection)
        try:
            obj = create_storage_obj(collection, obj)
            # Insert record into db
            col = getattr(self, collection)
            return col.insert_one(obj).inserted_id
        except Exception as e:
            self._warn('Problem inserting object into collection: '
                       '{}, {!r}'.format(e, obj))
            return None

    def get_current(self, collection):
        return self.current.find_one({'type': collection})

    def find(self, collection, obj_id):
        collection = getattr(self, collection)
        return collection.find_one({'_id': obj_id})

    def clear_current(self, type):
        self.current.remove({'type': type})

    @classmethod
    def permanently_erase_database(self, db_name):
        # TODO(jamessynge): Clear the known collections?
        pass


class FileDB(AbstractDB):
    """Stores collections as files of JSON records."""

    __db_thread_lock = threading.Lock()

    def thread_safe(func):
        def function_wrapper(*args, **kwargs):
            with FileDB.__db_thread_lock:
                return func(*args, **kwargs)
        return function_wrapper

    def __init__(self, db_name='remote_observatory_file_db', **kwargs):
        """Flat file storage for json records

        This will simply store each json record inside a file corresponding
        to the type. Each entry will be stored in a single line.
        Args:
            db_name (str, optional): Name of the database containing the
            collections.
        """

        super().__init__(db_name=db_name, **kwargs)

        self.db_folder = db_name

        # Set up storage directory.
        self._storage_dir = self.db_folder
        os.makedirs(self._storage_dir, exist_ok=True)

    @thread_safe
    def insert_current(self, collection, obj, store_permanently=True):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        current_fn = self.get_file(collection, permanent=False)
        result = obj_id
        try:
            # Overwrite current collection file with obj.
            json_util.dumps_file(current_fn, obj, clobber=True)
        except Exception as e:
            self._warn(f"Problem inserting object into current collection: "
                       f"{e}, {obj}")
            result = None

        if not store_permanently:
            return result

        collection_fn = self.get_file(collection)
        try:
            # Append obj to collection file.
            json_util.dumps_file(collection_fn, obj)
            return obj_id
        except Exception as e:
            self._warn('Problem inserting object into collection: '
                       '{}, {!r}'.format(e, obj))
            return None

    @thread_safe
    def insert(self, collection, obj):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        collection_fn = self.get_file(collection)
        try:
            # Insert record into file
            json_util.dumps_file(collection_fn, obj)
            return obj_id
        except Exception as e:
            self._warn('Problem inserting object into collection: '
                       '{}, {!r}'.format(e, obj))
            return None

    @thread_safe
    def get_current(self, collection):
        current_fn = self.get_file(collection, permanent=False)
        try:
            return json_util.loads_file(current_fn)
        except FileNotFoundError as e:
            self._warn("No record found for {}".format(collection))
            return None

    @thread_safe
    def find(self, collection, obj_id):
        collection_fn = self.get_file(collection)
        with open(collection_fn, 'r') as f:
            for line in f:
                # Note: We can speed this up for the case where the obj_id
                # doesn't contain any characters that json would need to escape
                # first check if the line contains the obj_id; if not skip.
                # Else, parse as json, and then check for the _id match.
                obj = json_util.loads(line)
                if obj['_id'] == obj_id:
                    return obj
        return None

    @thread_safe
    def clear_current(self, type):
        current_f = os.path.join(self._storage_dir,
                                 'current_{}.json'.format(type))
        try:
            os.remove(current_f)
        except FileNotFoundError as e:
            pass

    def get_file(self, collection, permanent=True):
        if permanent:
            name = '{}.json'.format(collection)
        else:
            name = 'current_{}.json'.format(collection)
        return os.path.join(self._storage_dir, name)

    def _make_id(self):
        return str(uuid4())

    @classmethod
    def permanently_erase_database(cls, db_name):
        with cls.__db_thread_lock:
            # Clear out any .json files.
            storage_dir = os.path.join(os.environ['PANDIR'], 'json_store', db_name)
            for f in glob(os.path.join(storage_dir, '*.json')):
                os.remove(f)


class MemoryDB(AbstractDB):
    """In-memory store of serialized objects.

    We serialize the objects in order to test the same code path used
    when storing in an external database.
    """

    active_dbs = weakref.WeakValueDictionary()

    @classmethod
    def get_or_create(cls, db_name='remote_observatory_memory', **kwargs):
        """Returns the named db, creating if needed.

        This method exists because DB gets called multiple times for
        the same database name. With mongo or a file store where the storage
        is external from the instance, that is not a problem, but with
        MemoryDB the instance is the store, so the instance must be
        shared."""
        db = MemoryDB.active_dbs.get(db_name)
        if not db:
            db = MemoryDB(db_name=db_name, **kwargs)
            MemoryDB.active_dbs[db_name] = db
        return db

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current = {}
        self.collections = {}
        self.lock = threading.Lock()

    def _make_id(self):
        return str(uuid4())

    def insert_current(self, collection, obj, store_permanently=True):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        try:
            obj = json_util.dumps(obj)
        except Exception as e:
            self._warn('Problem inserting object into current collection: '
                       '{}, {!r}'.format(e, obj))
            return None
        with self.lock:
            self.current[collection] = obj
            if store_permanently:
                self.collections.setdefault(collection, {})[obj_id] = obj
        return obj_id

    def insert(self, collection, obj):
        self.validate_collection(collection)
        obj_id = self._make_id()
        obj = create_storage_obj(collection, obj, obj_id=obj_id)
        try:
            obj = json_util.dumps(obj)
        except Exception as e:
            self._warn('Problem inserting object into collection: '
                       '{}, {!r}'.format(e, obj))
            return None
        with self.lock:
            self.collections.setdefault(collection, {})[obj_id] = obj
        return obj_id

    def get_current(self, collection):
        with self.lock:
            obj = self.current.get(collection, None)
        if obj:
            obj = json_util.loads(obj)
        return obj

    def find(self, collection, obj_id):
        with self.lock:
            obj = self.collections.get(collection, {}).get(obj_id)
        if obj:
            obj = json_util.loads(obj)
        return obj

    def clear_current(self, type):
        try:
            del self.current['type']
        except KeyError:
            pass

    @classmethod
    def permanently_erase_database(self, db_name):
        # For some reason we're not seeing all the references disappear
        # after tests. Perhaps there is some global variable pointing at
        # the db or one of its referrers, or perhaps a pytest fixture
        # hasn't been removed.
        MemoryDB.active_dbs = weakref.WeakValueDictionary()
