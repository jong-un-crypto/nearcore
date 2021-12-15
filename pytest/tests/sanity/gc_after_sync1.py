#!/usr/bin/env python3
# Spin up one validating node and one nonvalidating node
# stop the nonvalidating node in the second epoch and
# restart it in the fourth epoch to trigger state sync
# Check that after 10 epochs the node has properly garbage
# collected blocks.

import sys, time
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / 'lib'))

from cluster import start_cluster
from configured_logger import logger
import utils

TARGET_HEIGHT1 = 15
TARGET_HEIGHT2 = 35
TARGET_HEIGHT3 = 105
TIMEOUT = 80

node0_config = {"gc_blocks_limit": 10}

node1_config = {
    "consensus": {
        "block_fetch_horizon": 10,
        "block_header_fetch_horizon": 10,
        "state_fetch_horizon": 0
    },
    "tracked_shards": [0],
    "gc_blocks_limit": 10,
}

nodes = start_cluster(
    1, 1, 1, None,
    [["epoch_length", 10], ["block_producer_kickout_threshold", 80],
     ["chunk_producer_kickout_threshold", 80]], {
         0: node0_config,
         1: node1_config
     })

status1 = nodes[1].get_status()
height = status1['sync_info']['latest_block_height']

utils.wait_for_blocks(nodes[0], target=TARGET_HEIGHT1, timeout=TIMEOUT)

logger.info('Kill node 1')
nodes[1].kill()

utils.wait_for_blocks(nodes[0], target=TARGET_HEIGHT2, timeout=TIMEOUT)

logger.info('Restart node 1')
nodes[1].start(boot_node=nodes[0])

utils.wait_for_blocks(nodes[0], target=TARGET_HEIGHT3, timeout=TIMEOUT)

nodes[0].kill()

for i in range(1, 60):
    res = nodes[1].json_rpc('block', [i], timeout=10)
    assert 'error' in res, f'height {i}, {res}'

for i in range(60, 101):
    res = nodes[1].json_rpc('block', [i], timeout=10)
    assert 'result' in res, f'height {i}, {res}'
