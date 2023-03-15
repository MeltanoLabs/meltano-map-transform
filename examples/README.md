## Examples for meltano-map-transformer

### Some setup ###
1. Open e.g. in codespaces
2. cd to this directory if you haven't
3. Run ```meltano install````
4. Feel free to run the pipeline without a mappper ```meltano run tap-csv target-sqlite```
5. check your database with ```sqlite3 -markdown output/tap_csv.db 'select * from customers limit 20'```

### Run example 1: Hashing with built-in functions### 

1. Run ```meltano run tap-csv hash_email target-sqlite```
2. Check on the data

### Run example 2: dropping columns, aliasing streams ###
1. Run ```meltano run tap-csv whitelist target-sqlite```
2. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v2 limit 20'```

### Run example 3: dropping columns, aliasing streams ###
meltano run tap-csv add_timestamp target-sqlite
sqlite3 -markdown output/tap_csv.db 'select * from customers_v3 limit 20'


(this was the last of the built in functions)

## example 4 type casting

meltano run tap-csv add_str target-sqlite

sqlite3 -markdown output/tap_csv.db 'PRAGMA table_info(customers_v5)'.  <= Works!! nice

However, my "hash_id" is null for some reason ??ß