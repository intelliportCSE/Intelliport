#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import json


def write_as_json(data_list, output_file_path):
    content = json.dumps(data_list)
    with open(output_file_path, 'w') as out_file:
        out_file.writelines(content)


def write_var_map(var_map, output_file_path):
    content = ""
    for var in var_map:
        content += var + ":" + var_map[var] + "\n"
    with open(output_file_path, 'w') as map_file:
        map_file.writelines(content)


def write_clone_list(clone_list, output_file_path):
    data_list = list()
    content = json.dumps(clone_list)
    with open(output_file_path, 'w') as out_file:
        out_file.writelines(content)


