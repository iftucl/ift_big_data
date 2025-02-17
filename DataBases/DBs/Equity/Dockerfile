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
COPY ./DataBases/DBs/Equity/Equity.db /home/${USER_ID}/

# load postgres
# data dump from sqlite needs to be in this order else will fail on primary/foreign keys
COPY ./DataBases/DBs/Equity/create_db.sql /home/${USER_ID}/
COPY ./DataBases/DBs/Equity/create_tables.sql /home/${USER_ID}/

# create db, tables and backfill database
CMD psql -d 'postgres://postgres:postgres@postgres_db:5432' -a -f /home/${USER_ID}/create_db.sql \
    && psql -d 'postgres://postgres:postgres@postgres_db:5432/fift' -a -f /home/${USER_ID}/create_tables.sql \
	&& psql -c "TRUNCATE cash_equity.equity_static, cash_equity.equity_prices, cash_equity.portfolio_positions RESTART IDENTITY;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from equity_static;" > /home/equity_static.csv \
	&& chmod 777 /home/equity_static.csv \
	&& psql -c "\copy cash_equity.equity_static FROM /home/equity_static.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from portfolio_positions limit 100;" > /home/portfolio_positions.csv \	
	&& chmod 777 /home/portfolio_positions.csv \	
	&& psql -c "\copy cash_equity.portfolio_positions FROM /home/portfolio_positions.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from equity_prices;" > /home/equity_prices.csv \	
	&& chmod 777 /home/equity_prices.csv \	
	&& psql -c "\copy cash_equity.equity_prices FROM /home/equity_prices.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \    
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from company_statistics;" > /home/company_statistics.csv \	
	&& chmod 777 /home/company_statistics.csv \	
	&& psql -c "\copy cash_equity.company_statistics FROM /home/company_statistics.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift' \    
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from exchange_rates;" > /home/exchange_rates.csv \
	&& chmod 777 /home/exchange_rates.csv \
	&& psql -c "TRUNCATE cash_equity.exchange_rates;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& psql -c "\copy cash_equity.exchange_rates FROM /home/exchange_rates.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from trader_limits;" > /home/trader_limits.csv \
	&& chmod 777 /home/trader_limits.csv \
	&& psql -c "TRUNCATE cash_equity.trader_limits;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& psql -c "\copy cash_equity.trader_limits FROM /home/trader_limits.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& sqlite3 -header -csv /home/${USER_ID}/Equity.db "select * from trader_static;" > /home/trader_static.csv \
	&& chmod 777 /home/trader_static.csv \
	&& psql -c "TRUNCATE cash_equity.trader_static;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& psql -c "\copy cash_equity.trader_static FROM /home/trader_static.csv WITH csv HEADER;" -d 'postgres://postgres:postgres@postgres_db:5432/fift'\
	&& rm /home/*.csv 