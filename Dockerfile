FROM python:3.10 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM redis/redis-stack-server:latest as redis-stage

EXPOSE 6379

VOLUME /data

HEALTHCHECK CMD redis-cli -h localhost -p 6379 ping

RUN which redis-server && which redis-cli

FROM python:3.10

# # 创建tomcat用户
# RUN mkdir -p /home/tomcat && groupadd -r tomcat && useradd -r -g tomcat -d /home/tomcat -u 8080 tomcat
#
# # 指定操作用户为tomcat，并修改相关文件权限
# WORKDIR /home/tomcat
# RUN chown -R tomcat:tomcat /home/tomcat
# USER tomcat
#
# CMD ["sleep inf"]

# 设置环境变量
ENV DATASTORE=redis
ENV OPENAI_API_KEY=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

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
COPY --from=redis-stage /usr/bin/redis* /usr/bin/
COPY --from=redis-stage /data/ /data/

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/

# Heroku uses PORT, Azure App Services uses WEBSITES_PORT, Fly.io uses 8080 by default
CMD ["sh", "-c", "redis-server /etc/redis/redis.conf && uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-${WEBSITES_PORT:-8080}}"]
