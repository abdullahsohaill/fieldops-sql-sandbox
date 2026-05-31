PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS equipment_alerts;
DROP TABLE IF EXISTS spray_events;
DROP TABLE IF EXISTS weed_detections;
DROP TABLE IF EXISTS missions;
DROP TABLE IF EXISTS weather_daily;
DROP TABLE IF EXISTS crop_stats;
DROP TABLE IF EXISTS fields;

CREATE TABLE fields (
  field_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  state TEXT NOT NULL,
  county TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  crop TEXT NOT NULL,
  area_acres REAL NOT NULL CHECK (area_acres > 0),
  soil_type TEXT NOT NULL,
  irrigation_type TEXT NOT NULL
);

CREATE TABLE crop_stats (
  stat_id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  county TEXT NOT NULL,
  commodity TEXT NOT NULL,
  year INTEGER NOT NULL,
  statistic TEXT NOT NULL,
  unit TEXT NOT NULL,
  value REAL NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL
);

CREATE TABLE weather_daily (
  weather_id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL REFERENCES fields(field_id),
  date TEXT NOT NULL,
  temp_min_c REAL NOT NULL,
  temp_max_c REAL NOT NULL,
  precipitation_mm REAL NOT NULL,
  wind_speed_m_s REAL NOT NULL,
  humidity_pct REAL NOT NULL,
  source_name TEXT NOT NULL
);

CREATE TABLE missions (
  mission_id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL REFERENCES fields(field_id),
  mission_date TEXT NOT NULL,
  mission_type TEXT NOT NULL,
  status TEXT NOT NULL,
  coverage_pct REAL NOT NULL CHECK (coverage_pct >= 0 AND coverage_pct <= 100),
  operator_name TEXT NOT NULL,
  equipment_id TEXT NOT NULL
);

CREATE TABLE weed_detections (
  detection_id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL REFERENCES missions(mission_id),
  field_id TEXT NOT NULL REFERENCES fields(field_id),
  detected_at TEXT NOT NULL,
  weed_species TEXT NOT NULL,
  severity_score REAL NOT NULL CHECK (severity_score >= 0 AND severity_score <= 10),
  density_per_m2 REAL NOT NULL CHECK (density_per_m2 >= 0),
  confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE spray_events (
  spray_id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL REFERENCES fields(field_id),
  mission_id TEXT NOT NULL REFERENCES missions(mission_id),
  spray_date TEXT NOT NULL,
  chemical_name TEXT NOT NULL,
  application_rate_l_per_acre REAL NOT NULL CHECK (application_rate_l_per_acre >= 0),
  total_liters REAL NOT NULL CHECK (total_liters >= 0),
  wind_speed_m_s REAL NOT NULL CHECK (wind_speed_m_s >= 0),
  status TEXT NOT NULL
);

CREATE TABLE equipment_alerts (
  alert_id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL REFERENCES missions(mission_id),
  equipment_id TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE INDEX idx_weather_field_date ON weather_daily(field_id, date);
CREATE INDEX idx_missions_field_date ON missions(field_id, mission_date);
CREATE INDEX idx_weed_field_severity ON weed_detections(field_id, severity_score);
CREATE INDEX idx_spray_field_date ON spray_events(field_id, spray_date);
CREATE INDEX idx_alerts_equipment ON equipment_alerts(equipment_id, severity);

