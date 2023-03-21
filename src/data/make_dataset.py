import lxml.etree as ET
import pandas as pd
import re
import os
import time
from sys import getsizeof
import configparser
from src.logging_config import setup_logging
import datetime
from typing import Dict, Generator

# Read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")

# Get the values from the config file
input_file = config.get("make_dataset", "input_file")
chunk_size = config.getint("make_dataset", "chunk_size")
output_dir = config.get("make_dataset", "output_dir")
log_directory = config.get("logging", "log_directory")

# Apply the logging configuration
logger = setup_logging()


def log_performance_data(start_time, end_time, file_path, output_file, total_lines_processed, input_file_size,
                         output_file_size):
    duration = end_time - start_time
    performance_data = {
        'file_path': file_path,
        'output_file': output_file,
        'start_time': start_time,
        'end_time': end_time,
        'duration': duration,
        'total_lines_processed': total_lines_processed,
        'input_file_size': input_file_size,
        'output_file_size': output_file_size
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


def parse_stackexchange_posts_xml(file_path, output_dir, chunk_index):
    input_file_size = os.path.getsize(file_path)
    output_file = None
    output_file_size = None

    logger.debug(f"Looping {file_path}")
    start_time = time.perf_counter()

    path_parts = os.path.normpath(file_path).split(os.sep)
    domain = path_parts[-2]
    logger.debug(f"Processing {domain}")

    context = ET.iterparse(file_path, events=('end',))
    _, root = next(context)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    record_counter = 0
    chunk = []

    for event, elem in context:
        if elem.tag == 'row':
            record_counter += 1
            post_data = {}
            fields = [
                'Id', 'PostTypeId', 'ParentId', 'AcceptedAnswerId',
                'CreationDate', 'Score', 'ViewCount', 'Body',
                'OwnerUserId', 'LastEditorUserId', 'LastEditDate',
                'LastActivityDate', 'Title', 'Tags', 'AnswerCount',
                'CommentCount', 'FavoriteCount', 'ClosedDate'
            ]

            for field in fields:
                if elem.get(field) is not None:
                    if field == 'Body':
                        post_data[field] = clean_text(elem.get(field))
                    else:
                        post_data[field] = elem.get(field)

            chunk.append(post_data)

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []

            root.clear()

    if chunk:
        yield chunk

    end_time = time.perf_counter()
    logger.debug(f"{file_path} took {round(end_time - start_time)} seconds to run")

    performance_data = log_performance_data(start_time, end_time, file_path, output_file, record_counter,
                                            input_file_size, output_file_size)
    return performance_data

chunk_index = 0
loop_record_counter = 0
performance_data_list = []

with open(input_file) as f:
    for file_path in f:
        file_path = file_path.strip()
        performance_data = None

        for chunk in parse_stackexchange_posts_xml(file_path, output_dir, chunk_index):
            df_chunk = pd.DataFrame(chunk)
            logger.debug(f"Created a dataframe with shape {df_chunk.shape} and columns {df_chunk.columns}")
            output_file = os.path.join(output_dir, f"chunk_{chunk_index:05d}.parquet")

            if os.path.exists(output_file):
                df_existing = pd.read_parquet(output_file)
                df_combined = pd.concat([df_existing, df_chunk], ignore_index=True)
            else:
                df_combined = df_chunk

            df_combined.to_parquet(output_file, index=False)
            output_file_size = os.path.getsize(output_file)
            logger.debug(f"Saved {output_file}")
            chunk_index += 1

        performance_data_list.append(performance_data)

current_datetime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_file_name = f"performance_data_{current_datetime}.csv"

performance_df = pd.DataFrame(performance_data_list)
performance_df.to_csv(os.path.join(log_directory, output_file_name), index=False)
logger.debug(f"Saving performance data to {os.path.join(log_directory, output_file_name)}")
