import json
import argparse
import os
import re
from datetime import datetime

# 转换字段名函数
def convert_camel_to_snake(name):
    return ''.join(['_' + char.lower() if char.isupper() else char for char in name]).lstrip('_')

# 使用正则表达式来匹配 ISO 8601 日期格式
def convert_datetime_to_sql(dt_str):
    iso8601_regex = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
    if iso8601_regex.match(dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt_str  # 如果不匹配 ISO 8601 格式，返回原始字符串

# 解析命令行参数
parser = argparse.ArgumentParser(description='Convert JSON to SQL statements.')
parser.add_argument('table_name', help='Name of the SQL table to insert/update/delete rows.')
parser.add_argument('unique_id', help='Unique identifier field for UPDATE and DELETE operations.')
parser.add_argument('json_file', help='Name of the JSON file to process.')
args = parser.parse_args()

# 获取当前目录
current_dir = os.getcwd()

# 读取JSON文件
json_file_path = os.path.join(current_dir, args.json_file)
try:
    with open(json_file_path, 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print(f'Error: The file {args.json_file} was not found in the current directory.')
    exit(1)

# 遍历数据并生成 SQL 语句
for entry in data:
    # 将字典键转换为小写下划线形式
    entry_snake_case = {convert_camel_to_snake(k): v for k, v in entry.items()}
    entry_snake_case = {k: convert_datetime_to_sql(v) if isinstance(v, str) else v for k, v in entry_snake_case.items()}
    status = entry_snake_case.pop("status", None)
    unique_id_key = convert_camel_to_snake(args.unique_id)

    if status == "Create":
        columns = ', '.join(entry_snake_case.keys())
        values = ', '.join(f"'{v}'" if isinstance(v, str) else str(v) for v in entry_snake_case.values())
        sql = f"INSERT INTO {args.table_name} ({columns}) VALUES ({values});"
    elif status == "Update":
        unique_id_val = entry_snake_case.pop(unique_id_key, None)
        update_pairs = ', '.join(f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in entry_snake_case.items())
        sql = f"UPDATE {args.table_name} SET {update_pairs} WHERE {unique_id_key} = '{unique_id_val}';"
    elif status == "Delete":
        unique_id_val = entry_snake_case.pop(unique_id_key, None)
        sql = f"DELETE FROM {args.table_name} WHERE {unique_id_key} = '{unique_id_val}';"
    else:
        continue # 跳过JSON中Status没有出现的条目
    
    print(sql)