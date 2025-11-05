ALTER TABLE xp_sameer.nc_parcel_code 
ADD COLUMN mhp_classifier INTEGER DEFAULT 0;

UPDATE xp_sameer.nc_parcel_code
SET mhp_classifier = 1
WHERE parusecode IN ('416', '2004', 'R210', '0210');