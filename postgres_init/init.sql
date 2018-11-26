CREATE TABLE graphs (id VARCHAR(36), func VARCHAR(10), graph bytea, time_interval int, dt int, ts timestamp default current_timestamp, error VARCHAR(255));
