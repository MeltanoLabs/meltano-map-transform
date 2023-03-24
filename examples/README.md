# Examples for meltano-map-transformer

Either clone this repository, or just open it up in codespaces. To execute the commands as shown below, either use codespaces or have at least sqlite3 3.33.0.

1. cd to this directory if you haven't
2. Run ```meltano install```
3. Feel free to run the pipeline without a mapper ```meltano run tap-csv target-sqlite```
5. check your database with ```sqlite3 -markdown output/tap_csv.db 'select * from customers limit 20'```

To clean up afterwards, just remove the file:  ```rm output/tap_csv.db```

# Example 1: Hashing with built-in functions
**What:** Splitting email adresses, save the domain in separate, hash the mail itself, remove "other" columns and use the "config" object.

**The configuration:**
```yaml
  mappers:
  - name: meltano-map-transformer
    pip_url: ../.
    executable: meltano-map-transform
    settings:
    - name: stream_maps
      kind: object
    mappings:
    - name: hash_email
      config:
        stream_maps:
          customers:
            id: id
            email:      # drop the PII field from RECORD and SCHEMA messages
            email_domain: email.split('@')[-1]
            email_hash: md5(config['hash_seed'] + email)
            __else__: null
        stream_map_config:
          hash_seed: 01AWZh7A6DzGm6iJZZ2T
```

**Steps:**
1. Run ```meltano run tap-csv hash_email target-sqlite```
2. Look at the data ```sqlite3 -markdown output/tap_csv.db 'select * from customers limit 20'```

**Output:**
| email_domain |  email_hash                   |     id    |      __loaded_at    |
|------------|  --------------------------------|  ----------|  --------------------------|
|twitter.com |  a283215a8272692d77dec9138e996c04 | 1         |  2023-03-17 14:19:46.214774|


# Example 2: dropping columns, aliasing streams
**What:** Whitelist one column, rename another one, remove everything else, and rename the stream.

**The configuration:**
```yaml
    - name: whitelist
      config:
        stream_maps:
          # Whitelist `id` and `description` fields, drop all others
          customers:
            id: id
            description: last_name
            __else__: __NULL__
            __alias__: customers_v2
```
**Steps:**
1. Run ```meltano run tap-csv whitelist target-sqlite```
2. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v2 limit 20'```

**Output:**
|description | id   |       __loaded_at  |
|----------- | ---------- | --------------------------|
|Book        | 1          | 2023-03-17 14:29:15.257726|

# Example 3: dropping columns, aliasing streams
**What:** Use the datetime library (one of the built in libraries) to set a timestamp.

**The configuration:**
```yaml
    - name: add_timestamp
      config:
        stream_maps:
          customers:
            mapping_time: datetime.date.today()
            __alias__: customers_v3
```
**Steps:**
1. Run ```meltano run tap-csv add_timestamp target-sqlite```
2. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v3 limit 20'```

**Output:**
|email              | first_name | id       |   ip_address   |  last_name |  mapping_time | __loaded_at               |
|------------------ | ---------- | ----------  |------------- | ---------- | ------------ | --------------------------|
|ebook0@twitter.com | Ethe       | 1       |    67.61.243.220 | Book     |   2023-03-17    |2023-03-17 14:31:50.454788|

# Example 4: type casting
**What:** Add a literal string to a column, type cast one column from str to int, set up a new key property.

**The configuration:**
```yaml
    - name: add_str
      config:
        stream_maps:
          customers:
            client_id: "\"client_123\""
            id: int(id)
            __alias__: customers_v4
            hash_id: md5(str(id))
            __key_properties__: ["hash_id"]
```

**Steps:**
1. Run ```sqlite3 -markdown output/tap_csv.db 'PRAGMA table_info(customers_v3)'``` to check the type of the "id" column from the last example (it should be VARCHAR).
2. Run ```meltano run tap-csv add_str target-sqlite```
3. Run ```sqlite3 -markdown output/tap_csv.db 'PRAGMA table_info(customers_v4)'``` to check the type of the "id" column (it should be BIGINT)
4. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v4 limit 20'```

**Output:**
|client_id  | email              | first_name  |hash_id                          | id         | ip_address   |  last_name  | __loaded_at               |
|---------- | ------------------ | ----------  |-------------------------------- | ----------|  ------------- | ---------- | --------------------------|
|client_123 | ebook0@twitter.com | Ethe       | c4ca4238a0b923820dcc509a6f75849b | 1          | 67.61.243.220 | Book       | 2023-03-17 14:33:28.225243|

# Example 5: upper and lower case
**What:** Use str functions, and reference variables in different ways.

**The configuration:**
```yaml
    - name: lower
      config:
        stream_maps:
          customers:
            __alias__: customers_v5
            first_name: first_name.lower() # three different ways of accessing the variable
            last_name: record['last_name'].lower()
            email:  _['email'].upper()
            count_t: str(last_name.count("t")) # need to cast to str because it could be NULL!
            ip_address: __NULL__
```

**Steps:**
1. Run ```meltano run tap-csv lower target-sqlite```
4. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v5 limit 20'```

**Output:**
|count_t     |email              | first_name | id         | last_name  | __loaded_at               |
|---------- | ------------------ | ---------- | ---------- | ---------- | --------------------------|
|0          | EBOOK0@TWITTER.COM | ethe       | 1          | book       | 2023-03-17 14:35:01.229091|

# Example 6: Use other python logic
**What:** Use arbitrary Python statements to manipulate data.

**The configuration:**
```yaml
    - name: find
      config:
        stream_maps:
          customers:
            __alias__: customers_v6
            first_name: "config[last_name] if last_name == 'Book' else 'no_book'"
            id: id
            __else__: __NULL__
```

**Steps:**
1. Run ```meltano run tap-csv find target-sqlite```
4. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v6 limit 20'```

**Output:**

|first_name | id          |__loaded_at               |
|----------  |---------- | --------------------------|
|found_book | 1          | 2023-03-17 14:35:32.223231|
|no_book    | 2          | 2023-03-17 14:35:32.223335|

# Example 7: Combine config and custom Python logic
**What:** Use arbitrary Python statements to manipulate data, and combine them with configs.

**The configuration:**
```yaml
    - name: mask
      config:
        stream_maps:
          customers:
            __alias__: customers_v7
            last_name: "config[last_name] if last_name in config else 'no-mask-found'"
            first_name: first_name
            id: id
            __else__: __NULL__
        stream_map_config:
          Book: mask-1
          Tire: mask-2
          Dorian: mask-1
          Suddock: mask-1
          Daws: mask-3
          Maddison: mask-2
          Biernat: mask-4
          Wisden: mask-4
          Loyndon: Mask-2
```

**Steps:**
1. Run ```meltano run tap-csv mask target-sqlite```
4. Inspect using  ```sqlite3 -markdown output/tap_csv.db 'select * from customers_v7 limit 20'```

**Output:**
|first_name | id         | last_name  | __loaded_at               |
|---------- | ---------- | ---------- | --------------------------|
|Ethe       | 1          | mask-1      |2023-03-17 14:35:56.096918|
|Myranda    | 2          | mask-2     | 2023-03-17 14:35:56.097042|
|Serge      | 5          | mask-3     | 2023-03-17 14:35:56.097279|
|Giffy      | 7          | mask-4      |2023-03-17 14:35:56.097433|
|Vitoria   |  8         |  no-mask-fo | 2023-03-17 14:35:56.097508|
|Doreen     | 13        |  Mask-2     | 2023-03-17 14:35:56.097884|
