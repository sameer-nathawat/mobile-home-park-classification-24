import gc
import os
import time
from random import randint
import math
import traceback
import pandas as pd
import geopandas as gpd
from scipy import spatial
from functools import partial
from multiprocessing import Pool
from tqdm.contrib.concurrent import process_map
from typing import Any, Generator, Union, Tuple, List, Type
import sqlalchemy

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def count_vertex(geom):

    if geom.geom_type.startswith("Multi"):
            n = 0
            for part in geom.geoms:
                n += len(part.exterior.coords) - 1
    else:
        n = len(geom.exterior.coords) - 1

    return n

def slice_frame(frame:Union[pd.DataFrame, gpd.GeoDataFrame], slice_count:int) -> List[Union[pd.DataFrame, gpd.GeoDataFrame]]:
    """
    A function to divide either a pandas or geopandas dataframe in to slice_count number of frames    
    """

    chunk = int(len(frame) / slice_count)
    counts = range(slice_count)
    counts = [chunk for _ in counts]
    startIndex = [sum(counts[:index]) for index, _ in enumerate(counts)]
    startIndex.append(len(frame))

    tasks = []
    for index, _ in enumerate(startIndex):
        if index == slice_count:
            break
        tasks.append(frame.iloc[startIndex[index]:startIndex[index + 1]])

    return tasks

def multi_buffer(frame:gpd.GeoDataFrame, tree:spatial.cKDTree) -> gpd.GeoDataFrame:

    frame[["points_in_polygon_buffers", "ls_ratios_mean", "ls_ratios_std", "ls_ratios_min", "ls_ratios_max", "area_mean", "area_std", "area_min", "area_max"]] = pd.DataFrame(frame.apply(lambda x: buffer_metrics(x.lon, x.lat, tree, all_ls, all_area, 250), axis=1).tolist(), index=frame.index)
  
    return frame
    
def buffer_metrics(x:float, y:float, tree:spatial.cKDTree, ls_ratio:float, all_areas:float, buff:int) -> Tuple[int, float, float, float, float, float, float, float, float]:
    """
    buffer_metrics generates a variety of contextual features to use for classification 

    points_in_polygon_buffers: Count of points within buff meters
    ls_ration_mean:
    ls_ratio_std:
    ls_ratio_min:
    ls_ratio_max:
    area_mean:
    area_std:
    area_min:
    area_max:    
    """

    try:
        results = tree.query_ball_point((x, y), buff)
        points_in_polygon_buffers = len(results)
        if points_in_polygon_buffers == 0:
            return 0, None, None, None, None, None, None, None, None

        if points_in_polygon_buffers == 1:
            ls_ratios = ls_ratio.iloc[results].describe()
            area_buffs = all_areas.iloc[results].describe()
            ls_ratio_mean, ls_ratio_std, ls_ratio_min, ls_ratio_max = ls_ratios[1], ls_ratios[2], ls_ratios[3], ls_ratios[-1]
            area_mean, area_std, area_min, area_max = area_buffs[1], area_buffs[2], area_buffs[3], area_buffs[-1]
            return 1, ls_ratio_mean, 0, ls_ratio_min, ls_ratio_max, area_mean, 0, area_min,area_max
        else:                    
            ls_ratios = ls_ratio.iloc[results].describe()
            area_buffs = all_areas.iloc[results].describe()

            ls_ratios_mean,ls_ratios_std, ls_ratios_min, ls_ratios_max = ls_ratios[1], ls_ratios[2], ls_ratios[3], ls_ratios[-1]
            area_mean, area_std, area_min, area_max = area_buffs[1], area_buffs[2], area_buffs[3], area_buffs[-1]
            return points_in_polygon_buffers, ls_ratios_mean, ls_ratios_std, ls_ratios_min, ls_ratios_max, area_mean, area_std, area_min, area_max
       
    except:
        traceback.print_exc()


if __name__ == "__main__":

    user='hifld_summer'
    pw='hifld_summer'
    name='hifld_summer'
    host='moria'
    port=2023
    engine = sqlalchemy.create_engine(
        f'postgresql://{user}:{pw}@{host}:{port}/{name}'
        )
    
    sql="""
    select st_transform(geom,102003) as geom, build_id, prim_occ from structures.alabama
    """

    print('pulling data')
    gdf = gpd.GeoDataFrame.from_postgis(sql, con=engine,geom_col='geom')

    print('working on normal features')
    gdf["new_sqmeters"] = gdf.area
    gdf["perimeter"] = gdf.length

    gdf["vertex_count"] = gdf.apply(lambda x : count_vertex(x.geom), axis=1)

    gdf["length"] = gdf.bounds["maxy"] - gdf.bounds["miny"]
    gdf["width"] = gdf.bounds["maxx"] - gdf.bounds["minx"]

    gdf["long_side"] = gdf[["width", "length"]].max(axis=1)
    gdf["short_side"] = gdf[["width", "length"]].min(axis=1)

    gdf["ls_ratio"] = gdf["long_side"] / gdf["short_side"]

    gdf["pp_compactness"] = (4 * math.pi * gdf.new_sqmeters) / (gdf.perimeter ** 2)

    gdf["min_bounding_circle_area"] = gdf.minimum_bounding_circle().area    
    gdf["reock_compactness"] = gdf.new_sqmeters / gdf.min_bounding_circle_area

    gdf["sch_compactness"] = 1 / (gdf.perimeter / (2 * math.pi * ((gdf.new_sqmeters / math.pi)**.5)))

    gdf['lon'] = gdf.geom.centroid.x
    gdf['lat'] = gdf.geom.centroid.y

    bigtree_points = tuple(zip(gdf.lon, gdf.lat))
    bigtree = spatial.cKDTree(bigtree_points)
    del bigtree_points
    gc.collect()

    global all_ls
    all_ls = gdf.ls_ratio
    global all_area
    all_area = gdf.area

    pool = Pool(20)
    tasks = slice_frame(gdf,20)

    print('Going multi')
    assignment = partial(multi_buffer, tree=bigtree) 
    frames = pool.map(assignment, tasks)

    print('Merging slices and pushing data to db')
    final = gpd.GeoDataFrame(pd.concat(frames))

    final.to_postgis('all_features',schema='results',con=engine)    

    print('Finished')


