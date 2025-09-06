#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os

import app.common.utilities
from app.common import values
from app.common.utilities import remove_bracketed_content
from app.ast import ast_generator as ASTGenerator
from app.tools import emitter

def slice_source_file(source_path, segment_code, segment_identifier, project_path, use_macro=False):
    print("Inside slice_source_file", source_path, segment_code, segment_identifier, project_path, use_macro)
    
    output_file_name = "." + segment_code + "." + segment_identifier + ".slice"
    output_file_path = source_path + output_file_name
    if os.path.isfile(output_file_path):
        return True
    try:
        ast_tree = ASTGenerator.get_ast_json(source_path, use_macro, True)
    except Exception as e:
        print("Error in slice_source_file: ", e)
        return False
        
    segment_type = values.segment_map[segment_code]
    print("Segment type:", segment_type)
    
    project_path = app.common.utilities.extract_project_path(source_path)
    source_relative_path = source_path.replace(project_path, "")[1:]
    segment_found = False
    target_function_lines = None
    
    # Find the target function and get its line range
    def find_target_function(ast_node):
        nonlocal segment_found, target_function_lines
        
        node_id = ast_node['id']
        node_type = ast_node['type']
        
        # Check if this is the target function
        if node_type in segment_type:
            if node_type in ["FunctionDecl", "CXXMethodDecl"] and 'qualified_identifier' in ast_node:
                node_identifier = remove_bracketed_content(ast_node['qualified_identifier'])
            else:
                node_identifier = remove_bracketed_content(ast_node['value'])
            
            print("Checking function:", node_identifier, "vs target:", segment_identifier)
            if node_identifier == segment_identifier:
                print("Found target function!")
                segment_found = True
                start_line = ast_node.get('start line', 0)
                end_line = ast_node.get('end line', 0)
                target_function_lines = (start_line, end_line)
                print(f"Function spans lines {start_line} to {end_line}")
                return True
        
        # Recursively search children
        if node_type not in ["FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl"]:
            for child in ast_node.get('children', []):
                if find_target_function(child):
                    return True
        
        return False
    
    # Find the target function
    for ast_node in ast_tree.get('children', []):
        if find_target_function(ast_node):
            break
    
    if not segment_found:
        emitter.information("Target function not found")
        return False
    
    # Extract only the function lines from the source file
    try:
        with open(source_path, 'r', encoding='utf-8', errors='ignore') as source_file:
            all_lines = source_file.readlines()
        
        start_line, end_line = target_function_lines
        
        # Extract the function lines (1-indexed to 0-indexed conversion)
        if start_line > 0 and end_line > 0 and start_line <= len(all_lines) and end_line <= len(all_lines):
            function_lines = all_lines[start_line-1:end_line]
            
            # Write only the function to the slice file
            with open(output_file_path, 'w', encoding='utf-8') as slice_file:
                slice_file.writelines(function_lines)
            
            print(f"Created function-only slice with lines {start_line}-{end_line}")
        else:
            print(f"Invalid line range: {start_line}-{end_line} for file with {len(all_lines)} lines")
            return False
            
    except Exception as e:
        print(f"Error extracting function lines: {e}")
        return False

    emitter.normal("\t\t\tcreated " + output_file_path)
    return segment_found


def slice_ast_tree(ast_tree, segment_code, segment_identifier):
    segment_type = values.segment_map[segment_code]
    sliced_ast_tree = ast_tree
    del sliced_ast_tree['children']
    sliced_ast_tree['children'] = list()
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier == segment_identifier:
                sliced_ast_tree['children'].append(ast_node)
        elif node_type == "FunctionDecl":
            continue
        else:
            sliced_ast_tree['children'].append(ast_node)

    emitter.normal("\t\t\tcreated AST Slice for " + segment_identifier)
    return sliced_ast_tree
