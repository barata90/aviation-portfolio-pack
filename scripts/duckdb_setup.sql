-- Quick DuckDB starter: load OpenFlights and make a few helper views
.mode csv
-- Airports (OpenFlights CSV is comma-quoted; better to use read_csv with columns)
CREATE OR REPLACE TABLE airports AS
SELECT * FROM read_csv_auto('data/openflights/airports.dat', header=false, columns={
    id:INTEGER, name:TEXT, city:TEXT, country:TEXT, iata:TEXT, icao:TEXT,
    lat:DOUBLE, lon:DOUBLE, alt_ft:INTEGER, tz_offset:DOUBLE, dst:TEXT,
    tz:TEXT, type:TEXT, src:TEXT
});

CREATE OR REPLACE TABLE airlines AS
SELECT * FROM read_csv_auto('data/openflights/airlines.dat', header=false, columns={
    id:INTEGER, name:TEXT, alias:TEXT, iata:TEXT, icao:TEXT, callsign:TEXT,
    country:TEXT, active:TEXT
});

CREATE OR REPLACE TABLE routes AS
SELECT * FROM read_csv_auto('data/openflights/routes.dat', header=false, columns={
    airline:TEXT, airline_id:INTEGER, src:TEXT, src_id:INTEGER, dst:TEXT, dst_id:INTEGER,
    codeshare:TEXT, stops:INTEGER, equipment:TEXT
});

CREATE OR REPLACE VIEW airport_nodes AS
SELECT icao, iata, name, country, lat, lon FROM airports WHERE icao IS NOT NULL;

-- Example: count routes per airport pair
CREATE OR REPLACE VIEW route_counts AS
SELECT src AS src_iata, dst AS dst_iata, COUNT(*) AS num_routes
FROM routes
GROUP BY 1,2;
