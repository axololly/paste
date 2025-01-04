# :oil_drum: Database Schema

> :memo: :wrench: **Note:** the database behind this project is the all-amazing SQLite, interfaced by [Rapptz's](https://github.com/Rapptz) `sqlite3` wrapper: [`asqlite`](https://github.com/Rapptz/asqlite).

This section of the documentation goes over how the database is arranged.

There are only two tables, so don't be afraid.

## 1. `pastes` - Where your pastes are

This is where all the general information about a paste is stored - things like its unique ID, expiration timestamp and deletion link are found here.

To save on space, a maximum of 100,000 (subject to change) rows are allowed in this table. A `403` response is sent for requests made after this limit is reached.

### SQL

```sql
CREATE TABLE pastes (
    id TEXT NOT NULL UNIQUE,
    expiration INT NOT NULL,
    removal_id TEXT NOT NULL,
    
    PRIMARY KEY (id)
);
```

## 2. `files` - Where each paste's files are

This is where every file in every paste is located. The contents are compressed using `zlib`'s `compress` function, allowing 100 KB to be squeezed down into around 16 KB, making storage far more efficient.

There is also a `filepos` column that lets you retain the order of files after pasting.

### SQL

```sql
CREATE TABLE files (
    id TEXT NOT NULL UNIQUE,
    filename TEXT,
    content BLOB NOT NULL,
    filepos INT NOT NULL DEFAULT 1
);
```

***

That's it! Nothing more to see...

...for now. :eyes: