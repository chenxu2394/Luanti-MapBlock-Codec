import struct
import zstandard as zstd
import logging
import binascii
import sqlite3
import math
import re
from .encode_position import int64, getBlockAsInteger

logger = logging.getLogger(__name__)

def log_param0(param0):
    # Loop over the 16x16x16 grid
    for i in range(16):  # x dimension (slowest changing)
        for j in range(16):  # y dimension
            row = []
            for k in range(16):  # z dimension
                index = k * (16 * 16) + j * 16 + i
                high = param0[2 * index]
                low = param0[2 * index + 1]
                # Format the two bytes as a hex string (e.g., "1a2b")
                row.append("{:02x}{:02x}".format(high, low))
            print(" ".join(row))
        print("")  # Blank line after each x-layer

def hex_dump(data, bytes_per_line=16):
    """Return a formatted hex dump of the data."""
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        hex_part = ' '.join(f"{b:02x}" for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        lines.append(f"{i:08x}: {hex_part:<{bytes_per_line*3}} {ascii_part}")
    return "\n".join(lines)

# Define the mapping from material names to IDs.
MATERIAL_MAP = {
    "cactus": 15,
    "cobble": 4,
    "dirt": 5,
    "glass": 13,
    "coral_pink": 20,
}

def load_pattern_file(file_path, stripe_height=4):
    """
    Read the pattern file and return a dictionary mapping (x, z, y) to material ID.
    Lines should have the format: (x,y,z) material
    """
    pattern = {}
    max_x = max_y = max_z = 0
    regex = r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)\s+(\w+)"
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.match(regex, line)
            if match:
                x_str, z_str, y_str, material_name = match.groups()
                gx, gz, gy = int(x_str), int(z_str), int(y_str) * stripe_height
                material = MATERIAL_MAP.get(material_name.lower(), 0)
                pattern[(gx, gy, gz)] = material
                max_x = max(max_x, gx)
                max_y = max(max_y, gy)
                max_z = max(max_z, gz)
            else:
                logger.warning(f"Skipping invalid line: {line}")
    global_size_x = max_x + 1
    global_size_y = max_y + 1
    global_size_z = max_z + 1
    logger.info(f"Loaded pattern for a {global_size_x} x {global_size_y} x {global_size_z} volume with {len(pattern)} cells defined.")
    return pattern, (global_size_x, global_size_y, global_size_z)

def construct_mapblock_param0_for_region(mb_x, mb_y, mb_z, custom_pattern_global):
    """
    Build a param0 binary array for a single MapBlock,
    filling only the nodes that fall within the mapblock's local 16x16x16 area
    from the global custom pattern.
    """
    total_nodes = 16 * 16 * 16  # 4096 nodes per mapblock
    node_ids = [0] * total_nodes  # initialize to air (0)
    
    for (gx, gy, gz), material in custom_pattern_global.items():
        # Determine which mapblock this global coordinate belongs to.
        block_x = gx // 16
        block_y = gy // 16
        block_z = gz // 16
        
        if block_x == mb_x and block_y == mb_y and block_z == mb_z:
            local_x = gx % 16
            local_y = gy % 16
            local_z = gz % 16
            index = local_z * (16 * 16) + local_y * 16 + local_x
            node_ids[index] = material
    param0 = struct.pack(">4096H", *node_ids)
    return param0

def construct_mapblock(new_param0):
    """
    Construct a new MapBlock blob.
    """
    header = bytearray()
    header.extend(b'\x00\x00\x00\x00\x00\x00\x00')  # flags, lighting, timestamp
    header.append(0)  # Name-ID Mapping version

    mappings = [
        (0, "air"),
        (1, "default:stone"),
        (2, "default:stone_with_coal"),
        (3, "default:obsidian"),
        (4, "default:cobble"),
        (5, "default:dirt"),
        (6, "default:dirt_with_grass"),
        (7, "default:dirt_with_rainforest_litter"),
        (8, "default:dirt_with_dry_grass"),
        (9, "default:dry_dirt"),
        (10, "default:dry_dirt_with_dry_grass"),
        (11, "default:silver_sand"),
        (12, "default:gravel"),
        (13, "default:glass"),
        (14, "default:papyrus"),
        (15, "default:cactus"),
        (16, "default:snow"),
        (17, "default:lava_source"),
        (18, "default:lava_flowing"),
        (19, "default:water_source"),
        (20, "default:coral_pink"),
        (21, "default:ice"),
        (22, "default:permafrost"),
        (23, "default:mossycobble"),
    ]

    header.extend(struct.pack(">H", len(mappings)))
    for mid, name in mappings:
        header.extend(struct.pack(">H", mid))
        header.extend(struct.pack(">H", len(name)))
        header.extend(name.encode('utf-8'))

    header.append(2)  # content_width
    header.append(2)  # params_width

    new_param1 = b'\x00' * 4096
    new_param2 = b'\x00' * 4096

    result = bytes(header) + new_param0 + new_param1 + new_param2 + b"\x00\x00\x00\x00\n\x00\x00"
    print(hex_dump(result))
    # print length of result
    print(len(result))
    return result

def compress_blob(version, decompressed_data, compression_level=3):
    """
    Compress the mapblock data using Zstandard and prepend the version byte.
    """
    version_byte = bytes([version])
    cctx = zstd.ZstdCompressor(level=compression_level)
    try:
        compressed = cctx.compress(decompressed_data)
    except zstd.ZstdError as e:
        raise ValueError(f"Compression failed: {e}")
    blob = version_byte + compressed
    return binascii.hexlify(blob).decode('ascii')

def save_to_sqlite(position, blob_data, db_path='map.sqlite'):
    """
    Save the compressed blob to an SQLite database.
    """
    blob_bytes = binascii.unhexlify(blob_data)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            pos INTEGER PRIMARY KEY,
            data BLOB
        )
    ''')
    cursor.execute('INSERT OR REPLACE INTO blocks (pos, data) VALUES (?, ?)',
                   (position, blob_bytes))
    conn.commit()
    conn.close()

if __name__ == "__main__":

    logger.info("Constructing a dynamic N x N layer from text file pattern split into adjacent MapBlocks")

    version = 29

    # Load the pattern and determine global size.
    custom_pattern_global, (global_size_x, global_size_y, global_size_z) = load_pattern_file("pattern.txt", stripe_height=4)

    # Calculate how many mapblocks are needed in each direction.
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
                
                # Compute the position from the mapblock's (mb_x, mb_y, mb_z) coordinates.
                pos = getBlockAsInteger([mb_x, mb_y, mb_z])
                mapblocks[(mb_x, mb_y, mb_z)] = (pos, compressed_blob)
                logger.info(f"MapBlock at ({mb_x}, {mb_y}, {mb_z}) computed pos {pos}, blob starts with: {compressed_blob[:60]}...")

    # Save each mapblock to SQLite.
    for (mb_x, mb_y, mb_z), (pos, blob) in mapblocks.items():
        save_to_sqlite(pos, blob, db_path='map.sqlite')
        logger.info(f"MapBlock at ({mb_x}, {mb_y}, {mb_z}) with pos {pos} saved to SQLite database.")
