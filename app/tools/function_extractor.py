#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from app.common import definitions, values
from app.common.utilities import remove_bracketed_content
from app.tools import emitter

def extract_function_content(slice_file_path):
    """Extract function content from a slice file"""
    try:
        with open(slice_file_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("\t\t\t[ERROR] Error extracting function content from {0}: [Errno 2] No such file or directory: '{1}'".format(slice_file_path, slice_file_path))
        return None
    except Exception as e:
        print("\t\t\t[ERROR] Error extracting function content from {0}: {1}".format(slice_file_path, str(e)))
        return None

def extract_function_line_numbers_from_project(project, source_file_path, function_name):
    """Extract start and end line numbers from existing project data"""
    try:
        if not project or not hasattr(project, 'function_list'):
            return None
            
        if source_file_path not in project.function_list:
            return None
            
        # Look for the function in the project's function list
        func_key = "func_" + function_name
        if func_key in project.function_list[source_file_path]:
            vector_obj = project.function_list[source_file_path][func_key]
            if hasattr(vector_obj, 'start_line') and hasattr(vector_obj, 'end_line'):
                return (vector_obj.start_line, vector_obj.end_line)
        
        return None
        
    except Exception as e:
        print("\t\t\t[WARNING] Could not extract line numbers from project data for function {0}: {1}".format(function_name, str(e)))
        return None

def extract_function_line_numbers_fallback(source_file_path, function_name):
    """Fallback method to extract line numbers using AST parsing (for PB only when needed)"""
    try:
        from app.ast import ast_generator as ASTGenerator
        ast_tree = ASTGenerator.get_ast_json(source_file_path, False, True)
        segment_type = ['FunctionDecl', 'CXXConstructorDecl', 'CXXMethodDecl']
        
        def find_function_lines(ast_node):
            node_type = ast_node.get('type', '')
            
            if node_type in segment_type:
                if node_type in ["FunctionDecl", "CXXMethodDecl"] and 'qualified_identifier' in ast_node:
                    node_identifier = remove_bracketed_content(ast_node['qualified_identifier'])
                else:
                    node_identifier = remove_bracketed_content(ast_node.get('value', ''))
                
                if node_identifier == function_name:
                    start_line = ast_node.get('start line', 0)
                    end_line = ast_node.get('end line', 0)
                    return (start_line, end_line)
            
            # Recursively search children
            if node_type not in ["FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl"]:
                for child in ast_node.get('children', []):
                    result = find_function_lines(child)
                    if result:
                        return result
            
            return None
        
        # Search through all nodes in the AST
        for ast_node in ast_tree.get('children', []):
            result = find_function_lines(ast_node)
            if result:
                return result
        
        return None
        
    except Exception as e:
        print("\t\t\t[WARNING] Fallback AST parsing failed for function {0} in {1}: {2}".format(function_name, source_file_path, str(e)))
        return None
    """Extract start and end line numbers from existing project data"""
    try:
        if not project or not hasattr(project, 'function_list'):
            return None
            
        if source_file_path not in project.function_list:
            return None
            
        # Look for the function in the project's function list
        func_key = "func_" + function_name
        if func_key in project.function_list[source_file_path]:
            vector_obj = project.function_list[source_file_path][func_key]
            if hasattr(vector_obj, 'start_line') and hasattr(vector_obj, 'end_line'):
                return (vector_obj.start_line, vector_obj.end_line)
        
        return None
        
    except Exception as e:
        print("\t\t\t[WARNING] Could not extract line numbers from project data for function {0}: {1}".format(function_name, str(e)))
        return None

def collect_function_triplets():
    """Collect function triplets using clone detection results"""
    function_triplets = []
    
    # Use clone detection results from detection phase instead of finding slice files manually
    from app.phases.detection import segment_clone_list
    
    if not segment_clone_list:
        print("\t\t❌ No clone detection results found")
        return function_triplets
    
    print("\t\tFound {0} clone detection results".format(len(segment_clone_list)))
    
    for clone_result in segment_clone_list:
        if len(clone_result) >= 2:
            pa_vector_path = clone_result[0]  # PA vector path
            pc_vector_path = clone_result[1]  # PC vector path (matched function)
            
            # Extract function information from vector paths
            # PA vector: /path/PA/file.cc.func_FunctionName.vec
            # PC vector: /path/PC/file.cc.func_FunctionName.vec
            
            try:
                # Extract PA function info
                if '.func_' not in pa_vector_path:
                    continue
                    
                pa_parts = pa_vector_path.split('.func_')
                pa_source_file = pa_parts[0]
                pa_function_name = pa_parts[1].replace('.vec', '')
                
                # Extract PC function info  
                if '.func_' not in pc_vector_path:
                    continue
                    
                pc_parts = pc_vector_path.split('.func_')
                pc_source_file = pc_parts[0]
                pc_function_name = pc_parts[1].replace('.vec', '')
                
                print("\t\t✅ Processing function pair:")
                print("\t\t\t PA: {0} in {1}".format(pa_function_name, pa_source_file))
                print("\t\t\t PC: {0} in {1}".format(pc_function_name, pc_source_file))
                
                # Construct slice file paths using actual function names
                pa_slice_file = "{0}.func.{1}.slice".format(pa_source_file, pa_function_name)
                pb_slice_file = pa_source_file.replace('/PA/', '/PB/') + ".func.{0}.slice".format(pa_function_name)
                pc_slice_file = "{0}.func.{1}.slice".format(pc_source_file, pc_function_name)
                
                # Extract function content from each slice file
                pa_content = extract_function_content(pa_slice_file)
                pb_content = extract_function_content(pb_slice_file)
                pc_content = extract_function_content(pc_slice_file)
                
                # Extract line numbers for each version using existing project data
                print("\t\t\t📍 Extracting line numbers from project data...")
                pb_source_file = pa_source_file.replace('/PA/', '/PB/')
                
                pa_lines = extract_function_line_numbers_from_project(values.Project_A, pa_source_file, pa_function_name)
                pb_lines = extract_function_line_numbers_from_project(values.Project_B, pb_source_file, pa_function_name)
                pc_lines = extract_function_line_numbers_from_project(values.Project_C, pc_source_file, pc_function_name)
                
                # Use fallback AST parsing for PB if project data is not available
                if pb_lines is None:
                    print("\t\t\t📍 PB project data not available, using fallback AST parsing...")
                    pb_lines = extract_function_line_numbers_fallback(pb_source_file, pa_function_name)
                
                # Use fallback for PC if project data is not available
                if pc_lines is None:
                    print("\t\t\t📍 PC project data not available, using fallback AST parsing...")
                    pc_lines = extract_function_line_numbers_fallback(pc_source_file, pc_function_name)
                
                if pa_lines:
                    print("\t\t\t📍 PA lines: {0}-{1}".format(pa_lines[0], pa_lines[1]))
                if pb_lines:
                    print("\t\t\t📍 PB lines: {0}-{1}".format(pb_lines[0], pb_lines[1]))
                if pc_lines:
                    print("\t\t\t📍 PC lines: {0}-{1}".format(pc_lines[0], pc_lines[1]))
                
                # Create triplet with both PA and PC function names
                triplet = {
                    "function_mapping": {
                        "pa_function_name": pa_function_name,
                        "pc_function_name": pc_function_name
                    },
                    "pa_pre_patch": {
                        "content": pa_content if pa_content is not None else "",
                        "source_file": pa_source_file,
                        "function_name": pa_function_name,
                        "start_line": pa_lines[0] if pa_lines else None,
                        "end_line": pa_lines[1] if pa_lines else None
                    },
                    "pb_post_patch": {
                        "content": pb_content if pb_content is not None else "",
                        "source_file": pb_source_file,
                        "function_name": pa_function_name,  # PB uses same name as PA
                        "start_line": pb_lines[0] if pb_lines else None,
                        "end_line": pb_lines[1] if pb_lines else None
                    },
                    "pc_pre_patch": {
                        "content": pc_content if pc_content is not None else "",
                        "source_file": pc_source_file,
                        "function_name": pc_function_name,
                        "start_line": pc_lines[0] if pc_lines else None,
                        "end_line": pc_lines[1] if pc_lines else None
                    },
                    "slice_files": {
                        "pa_slice": pa_slice_file,
                        "pb_slice": pb_slice_file,
                        "pc_slice": pc_slice_file
                    }
                }
                function_triplets.append(triplet)
                print("\t\t✅ Collected triplet for function pair: {0} -> {1}".format(pa_function_name, pc_function_name))
                
            except Exception as e:
                print("\t\t❌ Error processing clone result: {0}".format(str(e)))
                continue
    
    return function_triplets

def save_function_triplets(function_triplets, output_file):
    """Save function triplets to JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(function_triplets, f, indent=2)
        print("Function triplets saved to: {0}".format(output_file))
        print("\tTotal triplets saved: {0}".format(len(function_triplets)))
    except Exception as e:
        print("\t\t❌ Error saving function triplets: {0}".format(str(e)))

def process_and_save_function_triplets():
    """Main function to process and save function triplets"""
    emitter.title("Function Triplet Extraction")
    emitter.sub_title("Collecting Function Triplets")
    
    # Collect function triplets
    triplets = collect_function_triplets()
    
    if not triplets:
        print("\t\t❌ No function triplets found")
        return
    
    # Use the file path defined in definitions
    output_file = definitions.FILE_FUNCTION_TRIPLETS
    
    # Save triplets to JSON
    save_function_triplets(triplets, output_file)
    
    # Store in values for potential use by other phases
    values.function_triplets = triplets
    
    return triplets
