SELECT xp_sameer.nc_parcel_4326.geom, xp_sameer.nc_parcel_4326.parusecode, xp_sameer.nc_parcel_4326.parusedesc, xp_sameer.nc_ussv2_geom_w_gauntlet.*
FROM xp_sameer.nc_parcel_4326
JOIN xp_sameer.nc_ussv2_geom_w_gauntlet
ON ST_Contains(xp_sameer.nc_parcel_4326.geom, xp_sameer.nc_ussv2_geom_w_gauntlet.geometry);