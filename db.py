import redis


class MyDB(redis.client.Redis):
    _db_connection = None

    def __init__(self, host, port, db):
        self._db_connection = redis.Redis(
            host=host, port=port, db=db)

    def __del__(self):
        self._db_connection.client_kill("localhost:6379")

    def get(self, field):
        return self._db_connection.smembers(field)

    def save(self):
        self._db_connection.bgsave()

    @property
    def redis_obj(self):
        return self._db_connection
