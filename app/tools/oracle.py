#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from app.ast import ast_generator
from app.common import definitions
from app.tools import finder, extractor, converter

def is_loc_in_if_cond(source_file, line_number):
    ast_tree = ast_generator.get_ast_json(source_file)
    ast_node = finder.search_node_by_loc(ast_tree,
                                         int(line_number))
    if ast_node is None:
        return False
    return is_node_in_if_cond(ast_tree, ast_node)


def is_node_in_if_cond(ast_tree, ast_node):

    parent_node_id = int(ast_node['parent_id'])
    parent_node = finder.search_ast_node_by_id(ast_tree, parent_node_id)
    parent_node_type = parent_node['type']
    node_type = ast_node['type']
    if parent_node_type == "IfStmt":
        if node_type == "CompoundStmt":
            return False
        return True
    elif parent_node_type == "FunctionDecl":
        return False
    elif parent_node_type == "TranslationUnitDecl":
        return False
    else:
        return is_node_in_if_cond(ast_tree, parent_node)


def is_node_in_function(ast_tree, ast_node):
    parent_node_id = int(ast_node['parent_id'])
    parent_node = finder.search_ast_node_by_id(ast_tree, parent_node_id)
    parent_node_type = parent_node['type']
    node_type = ast_node['type']
    if parent_node_type == "FunctionDecl":
        return True
    elif parent_node_type == "TranslationUnitDecl":
        return False
    else:
        return is_node_in_function(ast_tree, parent_node)


def is_function_important(source_path, function_call_node, sym_path_list):
    ast_tree = ast_generator.get_ast_json(source_path)
    function_ref_node = function_call_node
    if len(function_call_node['children']) > 0:
        function_ref_node = function_call_node['children'][0]
    function_name = function_ref_node['value']

    if is_node_in_if_cond(ast_tree, function_call_node):
        return True

    function_def_node = finder.search_function_node_by_name(ast_tree, function_name)
    if function_def_node is None:
        return False
    function_node, file_path = extractor.extract_complete_function_node(function_def_node, source_path)
    if function_node is None:
        return False
    file_path = os.path.abspath(file_path)
    start_line = function_node['start line']
    end_line = function_node['end line']
    line_numbers = set(range(int(start_line), int(end_line) + 1))
    for line_number in line_numbers:
        loc_id = file_path + ":" + str(line_number)
        if loc_id in sym_path_list:
            return True
    return False


def is_declaration_line(source_file, line_number):
    ast_tree = ast_generator.get_ast_json(source_file)
    function_node = finder.search_function_node_by_loc(ast_tree,
                                                       int(line_number),
                                                       source_file)
    if function_node is None:
        return False
    dec_line_list = extractor.extract_declaration_line_list(function_node)
    if line_number in dec_line_list:
        return True
    return False


def did_program_crash(program_output):
    if any(crash_word in str(program_output).lower() for crash_word in definitions.crash_word_list):
        return True
    return False


def any_runtime_error(program_output):
    if any(error_word in str(program_output).lower() for error_word in definitions.error_word_list):
        return True
    return False


def is_loc_on_stack(source_path, function_name, line_number, stack_info):
    if source_path in stack_info.keys():
        source_info = stack_info[source_path]
        if function_name in source_info.keys():
            line_list = source_info[function_name]
            if str(line_number) in line_list:
                return True
    return False


def is_loc_on_sanitizer(source_path, line_number, suspicious_lines):
    source_loc = source_path + ":" + str(line_number)
    if source_loc in suspicious_lines.keys():
        return True
    return False


def is_node_in_func(ast_node, ast_tree):
    parent_id = int(ast_node['parent_id'])
    while parent_id != 0:
        ast_node = finder.search_ast_node_by_id(ast_tree, parent_id)
        if ast_node["type"] == "FunctionDecl":
            return True
        parent_id = int(ast_node['parent_id'])
    return False


def is_node_equal(node_a, node_b, var_map):
    node_type_a = str(node_a['type'])
    node_type_b = str(node_b['type'])
    if node_type_a != node_type_b:
        return False

    if node_type_a in ["DeclStmt", "DeclRefExpr", "VarDecl"]:
        node_value_a = node_a['value']
        node_value_b = node_b['value']
        if node_value_a == node_value_b or node_value_a == var_map[node_value_b] or \
                node_value_b == var_map[node_value_a]:
            return True
        else:
            return False
    elif node_type_a == "ArraySubscriptExpr":
        node_value_a, node_type_a, var_list = converter.convert_array_subscript(node_a)
        node_value_b, node_type_b, var_list = converter.convert_array_subscript(node_b)
        if node_value_a == node_value_b or node_value_a == var_map[node_value_b] or \
                node_value_b == var_map[node_value_a]:
            return True
        else:
            return False
    elif node_type_a == "IntegerLiteral":
        node_value_a = int(node_a['value'])
        node_value_b = int(node_b['value'])
        if node_value_a == node_value_b:
            return True
        else:
            return False

    elif node_type_a == "MemberExpr":
        node_value_a, node_type_a, var_list = converter.convert_member_expr(node_a, True)
        node_value_b, node_type_b, var_list = converter.convert_member_expr(node_b, True)
        if node_value_a == node_value_b:
            return True
        else:
            if node_value_b in var_map and node_value_a == var_map[node_value_b]:
                return True
            else:
                return False
    elif node_type_a == "ParenExpr":
        child_node_a = node_a['children'][0]
        child_node_b = node_b['children'][0]
        return is_node_equal(child_node_a, child_node_b, var_map)
    elif node_type_a == "BinaryOperator":
        left_child_a = node_a['children'][0]
        right_child_a = node_a['children'][1]
        left_child_b = node_b['children'][0]
        right_child_b = node_b['children'][1]
        if is_node_equal(left_child_a, left_child_b, var_map) and \
                is_node_equal(right_child_a, right_child_b, var_map):
            return True
        else:
            return False