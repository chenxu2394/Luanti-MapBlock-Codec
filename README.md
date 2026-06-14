# Luanti MapBlock Codec

A collection of Python tools to encode and decode individual Minetest/Luanti MapBlocks. A **MapBlock** is a 16x16x16 chunk of the world, consisting of 4096 individual **nodes**. A node is the minimal destructible unit in the game world.

This project provides scripts to both **encode** a single MapBlock into its compressed format and **decode** a compressed MapBlock to inspect its contents. The target map format version is 29.
![Luanti logo](demo.png)

## Core Capabilities

This repository provides two main functionalities at the MapBlock level:

- **MapBlock Encoding**: Generate a single, compressed MapBlock from a list of nodes and their positions.

- **MapBlock Decoding**: Decompress and parse a single, compressed MapBlock to inspect its raw data, view node contents, and analyze its structure programmatically.

The included example script (`createMapSqlite.py`) demonstrates how to use the single MapBlock encoder to generate a complete `map.sqlite` file for a world.

## Modules

| Module               | Description                                                             |
| -------------------- | ----------------------------------------------------------------------- |
| `mapBlockEncode.py`  | Encodes and compresses a list of nodes into a single MapBlock.          |
| `mapBlockDecode.py`  | Decompresses and parses a single MapBlock to inspect its contents.      |
| `encode_position.py` | Encodes MapBlock coordinates into the format used by Minetest.          |
| `decode_position.py` | Decodes the position from the database back into (x, y, z) coordinates. |

## Requirements

- Python 3.10.13
- zstandard 0.23.0
- uv CLI
- Minetest/Luanti client that understands map format 29 (e.g. version 5.12.0)

## Quick Start: Generating a Map Database

The following steps show how to use the example script to generate a `map.sqlite` file from a simple text pattern.

```bash
git clone https://github.com/chenxu2394/Luanti-MapBlock-Codec.git
cd Luanti-MapBlock-Codec

uv sync
```

If uv cannot find Python 3.10.13, run `uv python install 3.10.13` and retry `uv sync`.

### **The Pattern File**

To generate a map, you need a pattern file. Each line in this file defines a single node using the format `(x, y, z) material`, where `x`, `y`, and `z` are integer coordinates and `material` is the node's name.

For example:

```bash
# The sample pattern draws the Luanti logo.
# Letter L
(0,50,0) cactus
(1,50,0) cactus
(2,50,0) cactus
(3,50,0) cactus
(4,50,0) cactus
...

# Letter u
(7,50,0) dirt
(8,50,0) dirt
(9,50,0) dirt
(10,50,0) dirt
...
```

### **Build the Luanti logo example**

```bash
cd example
uv run python createMapSqlite.py
cd ..
```

The script reads `pattern_logo.txt`, groups the nodes by their respective MapBlocks, encodes each MapBlock individually, and creates `example/map.sqlite`.

### **Load into Luanti**

1. Open Luanti, install or enable the `Minetest Game`, and create a new _singlenode_ world.

   ![Create a singlenode world in Luanti](docs/images/create-singlenode-world.gif)

2. Close the world, then overwrite its `map.sqlite` with the generated file:

   ```bash
   cp example/map.sqlite /path/to/minetest/worlds/<world_name>/map.sqlite
   ```

   ![Copy over the map db](docs/images/map.png)

3. Optional: enable flying before starting the world. On macOS, `minetest.conf` is usually located at `~/Library/Application Support/minetest/minetest.conf`; other installs keep it in the Luanti/Minetest user-data directory. Add or update:

   ![Enable fly privilege and freeze time in minetest.conf](docs/images/minetest-conf.png)

   ```conf
   #    The privileges that new users automatically get.
   #    See /privs in game for a full list on your server and mod configuration.
   #    type: string
   default_privs = interact, shout, privs, basic_privs, fly

   time_speed = 0
   ```

4. Start the world. The Luanti logo appears near the spawn point.

![Luanti logo in the generated world](demo.png)

### **Custom patterns**

Edit `pattern_logo.txt` or supply another file with the same `(x, y, z) material` syntax, then edit `pattern_filename` and rerun `createMapSqlite.py`.
