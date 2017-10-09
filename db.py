import redis


class MyDB(object):
    _db_connection = None
    # _db_cur = None

    def __init__(self):
        self._db_connection = redis.Redis(
            host="localhost", port=6379, db=1)
        # self._db_cur = self._db_connection.cursor()

    def __del__(self):
        self._db_connection.client_kill("localhost:6379")

    def get(self, field):
        self._db_connection.get(field)

    def save(self):
        self._db_connection.bgsave()

    @property
    def redis_obj(self):
        return self._db_connection
