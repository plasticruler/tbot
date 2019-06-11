docker run --name redis -v redis.conf:/usr/local/etc/redis/redis.conf -d -p 0.0.0.0:6379:6379 --restart unless-stopped --network=host arm32v7/redis redis-server /usr/local/etc/redis/redis.conf
