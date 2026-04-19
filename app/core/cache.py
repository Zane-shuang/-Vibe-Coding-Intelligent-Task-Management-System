import json
import datetime
from redis import Redis

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = Redis(host=host, port=port, db=db)

    def get(self, key):
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key, value, ttl=3600):
        # datetime 自动序列化
        def serialize(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        # 使用自定义序列化函数
        self.client.setex(key, ttl, json.dumps(value, default=serialize))

    def delete(self, key):
        self.client.delete(key)


cache = RedisCache()