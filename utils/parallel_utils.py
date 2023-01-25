import math
import multiprocessing as mp

import numpy as np
import pandas as pd
from tqdm.contrib.concurrent import process_map

import logging_config as log


class ParallelUtils:

    @staticmethod
    def parallel(data_df, func, cpu_divide_count=2, split_len=100, desc="Processing"):
        num_processes = ParallelUtils.get_num_process(cpu_divide_count)
        total = len(data_df.index)
        if total > split_len * num_processes:
            divided_df = np.array_split(data_df, len(data_df.index) // split_len)
        else:
            divided_df = np.array_split(data_df, num_processes)
        return ParallelUtils.parallel_divided(divided_df, func, cpu_divide_count, desc, total)

    @staticmethod
    def parallel_divided(divided_data, func, cpu_divide_count=2, desc="Processing", total=None, chunk_size=None):
        num_processes = ParallelUtils.get_num_process(cpu_divide_count)
        if chunk_size is None:
            chunk_size = math.ceil(len(divided_data) / 1000)
        log.get_logger("ParallelUtils").debug(
            f"Total: {total}, Process Num: {num_processes}, Divided Length: {len(divided_data)}, Chunk Size: {chunk_size}")
        if total:
            desc = f"{desc} (total: {total})"
        results = process_map(func, divided_data, max_workers=num_processes, desc=desc, chunksize=chunk_size)
        return pd.concat(results, ignore_index=True)

    @staticmethod
    def get_num_process(cpu_divide_count):
        return max(mp.cpu_count() // cpu_divide_count, 2)

