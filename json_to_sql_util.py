import json
import argparse
import os
import re
from datetime import datetime

# 转换字段名函数
def convert_camel_to_snake(name):
    return ''.join(['_' + char.lower() if char.isupper() else char for char in name]).lstrip('_')

# 使用正则表达式来匹配 ISO 8601 日期格式
iso8601_regex = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
def convert_datetime_to_sql(dt_str):
    if iso8601_regex.match(dt_str):
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt_str

# 解析命令行参数
parser = argparse.ArgumentParser(description='Convert JSON to SQL statements.')
parser.add_argument('table_name', help='Name of the SQL table to insert/update/delete rows.')
parser.add_argument('unique_id_field', help='Unique identifier field for UPDATE and DELETE operations.')
parser.add_argument('json_file', default='data.json', help='Name of the JSON file to process (default: data.json).')
args = parser.parse_args()

# 获取文件路径
json_file_path = os.path.join(os.getcwd(), args.json_file)
try:
    with open(json_file_path, 'r') as file:
        nested_data = json.load(file)
except FileNotFoundError:
    print(f'Error: The file {args.json_file} was not found.')
    exit(1)

# 确保数据格式正确
if not isinstance(nested_data, list) or len(nested_data) != 2 or not all(isinstance(lst, list) for lst in nested_data):
    print('Error: JSON file should contain a list of two lists.')
    exit(1)

# 第一个子列表处理 Delete 条目
for entry in nested_data[0]:
    if entry.get("Status") == "Delete":
        entry_snake_case = {convert_camel_to_snake(k): convert_datetime_to_sql(v) if isinstance(v, str) else v for k, v in entry.items()}
        unique_id_key_snake_case = convert_camel_to_snake(args.unique_id_field)
        unique_id_val = entry_snake_case.get(unique_id_key_snake_case)
        if unique_id_val is None:
            continue
        sql = f"DELETE FROM {args.table_name} WHERE {unique_id_key_snake_case} = '{unique_id_val}';"
        print(sql)

# 第二个子列表处理 Update 和 Create 条目
for entry in nested_data[1]:
    if entry.get("Status") in ["Update", "Create"]:
        entry_snake_case = {convert_camel_to_snake(k): convert_datetime_to_sql(v) if isinstance(v, str) else v for k, v in entry.items()}
        status = entry_snake_case.pop("status", None)
        unique_id_key_snake_case = convert_camel_to_snake(args.unique_id_field)
        unique_id_val = entry_snake_case.get(unique_id_key_snake_case)
        if status == "Create":
            columns = ', '.join(entry_snake_case.keys())
            values = ', '.join(f"'{v}'" if isinstance(v, str) else str(v) for v in entry_snake_case.values())
            sql = f"INSERT INTO {args.table_name} ({columns}) VALUES ({values});"
        elif status == "Update":
            if unique_id_val is None:
                continue
            update_pairs = ', '.join(f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in entry_snake_case.items())
            sql = f"UPDATE {args.table_name} SET {update_pairs} WHERE {unique_id_key_snake_case} = '{unique_id_val}';"
        else:
            continue
        print(sql)