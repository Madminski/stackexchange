from lxml import etree as ET
import pandas as pd
import re
import os
import time
from sys import getsizeof
import configparser
from src.logging_config import setup_logging
import datetime
import psutil
import gc
import sys

# Read the configuration file
config = configparser.ConfigParser()
config.read("/mnt/d/stackexchange/config.ini")

# Get the values from the config file
input_file = config.get("make_dataset", "input_file")
chunk_size = config.getint("make_dataset", "chunk_size")
output_dir = config.get("make_dataset", "output_dir")
log_directory = config.get("logging", "log_directory")

# Apply the logging configuration
logger = setup_logging()

chunk = []
loop_record_counter = 0


def get_top_vars_str(local_vars: dict):
    all_vars = dict(globals())
    all_vars.update(local_vars)

    data = [(name, sys.getsizeof(obj)) for name, obj in all_vars.items()]
    df = pd.DataFrame(data, columns=['Variable', 'Size'])
    df = df.sort_values(by='Size', ascending=False)

    top_vars = df.head(3)
    top_vars_str = ', '.join(
        [f"{row['Variable']}: {round(row['Size'] / (1024 ** 3), 2)} GB" for _, row in top_vars.iterrows()])

    return top_vars_str


def get_memory_usage():
    # Get the current process
    process = psutil.Process()
    memory_usage = process.memory_info().rss
    return memory_usage / (1024 * 1024 * 1024)


def log_performance_data(start_time, end_time, file_path, output_file, total_lines_processed, input_file_size,
                         output_file_size):
    duration = end_time - start_time
    mem_usage = get_memory_usage()
    performance_data = {
        'file_path': file_path,
        'output_file': output_file,
        'start_time': start_time,
        'end_time': end_time,
        'duration': duration,
        'total_lines_processed': total_lines_processed,
        'input_file_size': input_file_size,
        'output_file_size': output_file_size,
        'memory_usage': mem_usage
    }

    return performance_data


def clean_text(text):
    if text is None:
        return None
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub('\n|\t', ' ', text)
    text = re.sub(' +', ' ', text)
    return text.lower().strip()


def parse_stackexchange_posts_xml(chunk, file_path, output_dir, chunk_index, performance_data_list,
                                  loop_record_counter, subfolder):
    input_file_size = os.path.getsize(file_path)
    output_file_size = 0
    output_file = os.path.join(output_dir, f"chunk_{chunk_index:05d}.parquet")

    logger.debug(f"Looping {file_path}")
    start_time = time.perf_counter()

    path_parts = os.path.normpath(file_path).split(os.sep)
    domain = path_parts[-2]
    logger.debug(f"Processing {domain}")

    context = ET.iterparse(file_path, events=('end',))
    _, root = next(context)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for event, elem in context:
        if elem.tag == 'row':
            loop_record_counter += 1
            post_data = {}
            fields = [
                'Id', 'PostTypeId', 'ParentId', 'AcceptedAnswerId',
                'CreationDate', 'Score', 'ViewCount', 'Body',
                'OwnerUserId', 'LastEditorUserId', 'LastEditDate',
                'LastActivityDate', 'Title', 'Tags', 'AnswerCount',
                'CommentCount', 'FavoriteCount', 'ClosedDate', 'Subfolder'
            ]

            for field in fields:
                if elem.get(field) is not None:
                    if field == 'Body':
                        post_data[field] = clean_text(elem.get(field))
                    else:
                        post_data[field] = elem.get(field)
                if field == 'Subfolder':
                    post_data[field] = subfolder

            chunk.append(post_data)
            if loop_record_counter % 1000000 == 0:
                local_vars = dict(locals())
                top_vars_str = get_top_vars_str(local_vars)
                logger.debug(f"Looping row {loop_record_counter}. Data chunk: {round(getsizeof(chunk) / 1048576)} MB. "
                             f"Memory usage: {round(get_memory_usage())} GB. Top Vars: {top_vars_str}")
            if len(chunk) >= chunk_size:
                df_chunk = pd.DataFrame(chunk)
                df_chunk.to_parquet(output_file, index=False)
                output_file_size = os.path.getsize(output_file)
                logger.debug(f"Saved {output_file}")
                del fields
                del post_data
                del chunk
                del df_chunk
                chunk = []
                chunk_index += 1
                gc.collect()

            elem.clear()
            del event
        root.clear()
    del context
    gc.collect()

    output_file_size = getsizeof(chunk)
    end_time = time.perf_counter()
    logger.debug(f"{file_path} took {round(end_time - start_time)} seconds to run")

    performance_data = log_performance_data(start_time, end_time, file_path, output_file, loop_record_counter,
                                            input_file_size, output_file_size)
    performance_data_list.append(performance_data)
    return chunk_index, start_time, end_time, loop_record_counter


chunk_index = 17
loop_record_counter = 0
performance_data_list = []
input_file_size = 0

with open(input_file) as f:
    for file_path in f:
        file_path = file_path.strip()
        xml_dir = os.path.dirname(file_path)
        subfolder = os.path.basename(xml_dir)

        chunk_index, start_time, end_time, loop_record_counter = parse_stackexchange_posts_xml(chunk, file_path,
                                                                                               output_dir,
                                                                                               chunk_index,
                                                                                               performance_data_list,
                                                                                               loop_record_counter,
                                                                                               subfolder)

if len(chunk) > 0:
    # chunk_index += 1
    input_file_size = os.path.getsize(file_path)
    df_chunk = pd.DataFrame(chunk)
    output_file = os.path.join(output_dir, f"chunk_{chunk_index:05d}.parquet")
    df_chunk.to_parquet(output_file, index=False)
    logger.debug(f"Saved {output_file}")

    end_time = time.perf_counter()
    performance_data = log_performance_data(start_time, end_time,
                                            file_path, output_file,
                                            loop_record_counter + len(chunk),
                                            input_file_size,
                                            os.path.getsize(output_file))
    performance_data_list.append(performance_data)
    del chunk
    df_chunk.head()
    del df_chunk
    gc.collect()

current_datetime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_file_name = f"performance_data_{current_datetime}.csv"

performance_df = pd.DataFrame(performance_data_list)
print(performance_df)

performance_df.to_csv(os.path.join(log_directory, output_file_name), index=False)
logger.debug(f"Saving performance data to {os.path.join(log_directory, output_file_name)}")
