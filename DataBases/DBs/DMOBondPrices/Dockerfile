FROM postgres:11-alpine

ARG USER_ID=iftbigdata
ENV USER_ID $USER_ID

# refresh os
RUN apk update && apk upgrade

# get sqlite3 alpine
RUN apk add --no-cache sqlite-libs sqlite sqlite-dev
# ubuntu
# RUN apt-get install -y sqlite3 libsqlite3-dev

# make home
RUN mkdir /home/${USER_ID}/ 
COPY ./DataBases/DBs/DMOBondPrices/BondPrice.db /home/${USER_ID}/

# load postgres
# data dump from sqlite needs to be in this order else will fail on primary/foreign keys
COPY ./DataBases/DBs/DMOBondPrices/create_db.sql /home/${USER_ID}/
COPY ./DataBases/DBs/DMOBondPrices/create_tables.sql /home/${USER_ID}/

# create db, tables and backfill database
CMD psql -d 'postgres://postgres:postgres@postgres_db:5432' -a -f /home/${USER_ID}/create_db.sql \
    && psql -d 'postgres://postgres:postgres@postgres_db:5432/fift' -a -f /home/${USER_ID}/create_tables.sql \
	&& psql -c "TRUNCATE fixed_income.bond_static, fixed_income.bond_prices, fixed_income.risk_positions RESTART IDENTITY;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \
	&& sqlite3 -header -csv /home/${USER_ID}/BondPrice.db "select * from bond_static;" > /home/bond_static.csv \
	&& chmod 777 /home/bond_static.csv \
	&& psql -c "\copy fixed_income.bond_static FROM /home/bond_static.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& sqlite3 -header -csv /home/${USER_ID}/BondPrice.db "select * from risk_positions limit 100;" > /home/risk_positions.csv \	
	&& chmod 777 /home/risk_positions.csv \	
	&& psql -c "\copy fixed_income.risk_positions FROM /home/risk_positions.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \
	&& sqlite3 -header -csv /home/${USER_ID}/BondPrice.db "select * from bond_prices;" > /home/bond_prices.csv \	
	&& chmod 777 /home/bond_prices.csv \	
	&& psql -c "\copy fixed_income.bond_prices FROM /home/bond_prices.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \    
	&& sqlite3 -header -csv /home/${USER_ID}/BondPrice.db "select * from exchange_rates;" > /home/exchange_rates.csv \
	&& chmod 777 /home/exchange_rates.csv \
	&& psql -c "TRUNCATE fixed_income.exchange_rates;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& psql -c "\copy fixed_income.exchange_rates FROM /home/exchange_rates.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& rm /home/*.csv 