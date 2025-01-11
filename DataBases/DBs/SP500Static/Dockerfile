FROM alpine:latest


ENV MONGO_TOOLS_VERSION=100.9.4-r0

RUN apk add --no-cache mongodb-tools && \
    rm -rf /var/cache/apk/*

ARG USER_ID=iftbigdata
ENV USER_ID $USER_ID

# make docker local directory home
RUN mkdir /home/${USER_ID}/ 

# load Mongodb
COPY SP500DataNested.json /home/${USER_ID}/
COPY SP500Data.json /home/${USER_ID}/

CMD mongoimport --uri mongodb://mongo_db:27017/EquitySP500 --collection NestedStatic --drop --mode upsert --file /home/${USER_ID}/SP500DataNested.json --jsonArray \
&& mongoimport --uri mongodb://mongo_db:27017/EquitySP500 --collection Static --drop --mode upsert --file /home/${USER_ID}/SP500Data.json --jsonArray
