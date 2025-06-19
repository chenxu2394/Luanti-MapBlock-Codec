import logging
logging.basicConfig(level=logging.INFO)

from luanti_map_builder.mapBlockEncode import *

sqlite_path = "map.sqlite"
pattern_file = "pattern_logo.txt"
stripe_height = 1

version = 29
custom_pattern_global, (global_size_x, global_size_y, global_size_z) = load_pattern_file(file_path=pattern_file, stripe_height=stripe_height)

num_mb_x = math.ceil(global_size_x / 16)
num_mb_y = math.ceil(global_size_y / 16)
num_mb_z = math.ceil(global_size_z / 16)

mapblocks = {}
for mb_y in range(num_mb_y):
    for mb_x in range(num_mb_x):
        for mb_z in range(num_mb_z):
            param0 = construct_mapblock_param0_for_region(mb_x, mb_y, mb_z, custom_pattern_global)
            mapblock_blob = construct_mapblock(param0)
            compressed_blob = compress_blob(version, mapblock_blob)
            
            pos = getBlockAsInteger([mb_x, mb_y, mb_z])
            mapblocks[(mb_x, mb_y, mb_z)] = (pos, compressed_blob)
            logging.info(f"MapBlock at ({mb_x}, {mb_y}, {mb_z}) computed pos {pos}, blob starts with: {compressed_blob[:60]}...")

for (mb_x, mb_y, mb_z), (pos, compressed_blob) in mapblocks.items():
    save_to_sqlite(pos, compressed_blob, db_path=sqlite_path)
    logging.info(f"Saved MapBlock at ({mb_x}, {mb_y}, {mb_z}) to SQLite")