#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os

from app.common.utilities import error_exit, is_intersect, get_code, remove_bracketed_content
import collections
from app.common import values
from app.tools import oracle, merger
from app.tools import converter, generator as Gen, emitter, finder, extractor
from app.ast import ast_vector, ast_generator

def identify_missing_labels(neighborhood_a, neighborhood_b, neighborhood_c, insert_node_b, source_path_b, var_map):
    emitter.normal("\t\t\tanalysing for missing labels")
    missing_label_list = dict()
    label_list_a = extractor.extract_label_node_list(neighborhood_a)
    label_list_b = extractor.extract_label_node_list(neighborhood_b)
    label_list_c = extractor.extract_label_node_list(neighborhood_c)
    goto_list = extractor.extract_goto_node_list(insert_node_b)
    for goto_node in goto_list:
        line_number = int(goto_node['start line'])
        emitter.information("extracting line number: " + str(line_number))
        goto_code = get_code(source_path_b, line_number)
        emitter.information("extracted line: " + str(goto_code))
        identifier = goto_code.strip().replace("goto", "").replace(";", "").replace("\n", "").replace(" ", "")
        if identifier not in label_list_c and identifier in label_list_a:
            if identifier + "." in var_map:
                alias = var_map[identifier + "."][:-1]
                if alias in label_list_c:
                    continue
            info = dict()
            info['ref_list'] = list()
            info['ast-node'] = label_list_b[identifier]
            missing_label_list[identifier] = info
    return missing_label_list


def identify_missing_functions(ast_node, source_path_b, source_path_d, ast_tree_a, ast_tree_b, ast_tree_c, ast_map_key):
    emitter.normal("\t\t\tanalysing for missing function calls")
    missing_function_info = dict()
    call_list_b = extractor.extract_call_node_list(ast_node)
    function_list_c = extractor.extract_function_node_list(ast_tree_c)
    source_path_a = source_path_b.replace(values.CONF_PATH_B, values.CONF_PATH_A)
    macro_list = extractor.extract_macro_node_list(ast_node)
    missing_function_list = dict()
    for macro_node in macro_list:
        if "value" in macro_node:
            macro_value = macro_node['value']
            if "(" in macro_value:
                function_name = macro_value.split("(")[0]
                if function_name in function_list_c.keys():
                    function_node = function_list_c[function_name]
                    signature_node = function_node['children'][0]
                    num_param = len(signature_node['children'])
                    num_args = len(macro_value.replace(function_name, "").split(","))
                    if num_args == num_param:
                        continue
                    # TODO: handle if diff args
                else:
                    missing_function_list[function_name] = macro_node

    for call_expr in call_list_b:
        function_ref_node = call_expr['children'][0]
        if "value" in function_ref_node.keys():
            function_name = function_ref_node['value']
            if function_name in function_list_c.keys():
                function_node = function_list_c[function_name]
                signature_node = function_node['children'][0]
                num_param = len(signature_node['children']) - 1
                num_args = len(call_expr['children'][0]) - 1
                if num_args == num_param:
                    continue
                # TODO: handle if diff args
            else:
                missing_function_list[function_name] = function_ref_node

    for function_name in missing_function_list:
        if function_name in values.STANDARD_FUNCTION_LIST:
            continue
        ref_node = missing_function_list[function_name]
        function_node_a = finder.search_function_node_by_name(ast_tree_a, function_name)
        function_node_b = finder.search_function_node_by_name(ast_tree_b, function_name)
        if function_node_a is not None and function_node_b is not None:
            if function_name not in missing_function_info.keys():
                info = dict()
                info['node_id'] = function_node_a['id']
                info['ref_node_id'] = ref_node['id']
                info['source_a'] = source_path_a
                info['source_d'] = source_path_d
                info['ast-key'] = ast_map_key
                missing_function_info[function_name] = info
            else:
                info = dict()
                info['node_id'] = function_node_a['id']
                info['ref_node_id'] = ref_node['id']
                info['source_a'] = source_path_a
                info['source_d'] = source_path_d
                info['ast-key'] = ast_map_key
                if info != missing_function_info[function_name]:
                    print(missing_function_info[function_name])
                    error_exit("MULTIPLE FUNCTION REFERENCES ON DIFFERENT TARGETS FOUND!!!")
        elif function_node_a is None and function_node_b is not None:
            if function_name not in missing_function_info.keys():
                info = dict()
                info['node_id'] = function_node_b['id']
                info['ref_node_id'] = ref_node['id']
                info['source_a'] = source_path_b
                info['source_d'] = source_path_d
                info['ast-key'] = ast_map_key
                info['is-new'] = True
                missing_function_info[function_name] = info
    return missing_function_info


def identify_missing_var(neighborhood_a, neighborhood_b, neighborhood_c, ast_node_b, source_path_b, source_path_d, var_map, relative_pos):
    emitter.normal("\t\t\tanalysing for missing variables")
    missing_var_list = dict()
    source_path_a = source_path_b.replace(values.CONF_PATH_B, values.CONF_PATH_A)
    ref_list = extractor.extract_reference_node_list(ast_node_b)
    dec_list_local_a = extractor.extract_decl_node_list(neighborhood_a)
    dec_list_local_b = extractor.extract_decl_node_list(neighborhood_b)
    source_path_c = source_path_d.replace(values.Project_D.path, values.CONF_PATH_C)
    dec_list_local_c = extractor.extract_decl_node_list(neighborhood_c)
    ast_tree_a = ast_generator.get_ast_json(source_path_a)
    ast_tree_b = ast_generator.get_ast_json(source_path_b)
    ast_tree_c = ast_generator.get_ast_json(source_path_c)
    dec_list_global_a = extractor.extract_decl_node_list_global(ast_tree_a)
    dec_list_global_b = extractor.extract_decl_node_list_global(ast_tree_b)
    dec_list_global_c = extractor.extract_decl_node_list_global(ast_tree_c)
    enum_list_b = extractor.extract_enum_node_list(ast_tree_b)
    if ast_node_b['type'] == "Macro":
        if "value" in ast_node_b:
            macro_value = ast_node_b['value']
            if "(" in macro_value:
                func_name = macro_value.split("(")[0]
                operand_list = macro_value.replace(func_name + "(", "")[:-1].split(",")
                var_list = list()
                for operand in operand_list:
                    identifier = operand.strip().replace("\n", "").replace(" ", "")
                    if "(" in identifier:
                        continue
                    if "\"" in identifier or "'" in identifier or str(identifier).isnumeric():
                        continue
                    if any(operator in operand for operator in ["|", "&&", ">", ">=", "==", "-", "+",
                                                                "<", "<=", "*", "/"]):
                        if "->" in operand:
                            continue
                        var_list = var_list + extractor.extract_identifier_list(operand)
                    else:
                        var_list.append(identifier)
                for identifier in var_list:
                    if identifier not in set(list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())):
                        is_mapping = (identifier in var_map) and \
                                     (var_map[identifier] in set(
                                         list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                        if identifier not in missing_var_list.keys():
                            info = dict()
                            info['ref_list'] = [neighborhood_b['value']]
                            info['ref-id'] = int(ast_node_b['id'])
                            info['rel-pos'] = relative_pos
                            if identifier in dec_list_local_a.keys():
                                info['ast-node'] = dec_list_local_b[identifier]
                                info['pre-exist'] = True
                                info['is_global'] = False
                                info['target-file'] = source_path_d
                                info['map-exist'] = is_mapping

                            elif identifier in dec_list_global_a.keys():
                                info['is_global'] = True
                                info['pre-exist'] = True
                                info['target-file'] = source_path_d
                                info['ast-node'] = dec_list_global_b[identifier]
                                info['map-exist'] = is_mapping

                            elif identifier in dec_list_local_b.keys():
                                info['is_global'] = False
                                info['pre-exist'] = False
                                info['target-file'] = source_path_d
                                info['ast-node'] = dec_list_local_b[identifier]
                                info['map-exist'] = is_mapping

                            elif identifier in dec_list_global_b.keys():
                                info['is_global'] = True
                                info['pre-exist'] = False
                                info['target-file'] = source_path_d
                                info['ast-node'] = dec_list_global_b[identifier]
                                info['map-exist'] = is_mapping
                            else:
                                print(identifier)
                                print(ast_node_b)
                                # print(dec_list_local_b)
                                emitter.error("Unhandled missing variable")

                            missing_var_list[identifier] = info
                        else:
                            if neighborhood_b['value'] not in missing_var_list[identifier]['ref_list']:
                                missing_var_list[identifier]['ref_list'].append(neighborhood_b['value'])
                                missing_var_list[identifier]['is_global'] = True

                return missing_var_list

    for ref_node in ref_list:
        node_type = str(ref_node['type'])
        node_start_line = int(ref_node['start line'])
        if node_type in ["DeclRefExpr"]:
            if "ref_type" in ref_node.keys():
                ref_type = str(ref_node['ref_type'])
                identifier = str(ref_node['value']).strip().replace("\n", "").replace(" ", "")
                if ref_type == "VarDecl":
                    if identifier not in set(list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())):
                        if identifier not in missing_var_list.keys():
                            info = dict()
                            info['ref_list'] = [neighborhood_b['value']]
                            info['ref-id'] = int(ast_node_b['id'])
                            info['rel-pos'] = relative_pos
                            if identifier in dec_list_local_a.keys():
                                info['ast-node'] = dec_list_local_b[identifier]
                                info['pre-exist'] = True
                                is_mapping = (identifier in var_map) and \
                                             (var_map[identifier] in set(
                                                 list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                                info['map-exist'] = is_mapping
                                info['is_global'] = False
                                info['target-file'] = source_path_d

                            elif identifier in dec_list_global_a.keys():
                                info['is_global'] = True
                                info['pre-exist'] = True
                                is_mapping = (identifier in var_map) and \
                                             (var_map[identifier] in set(
                                                 list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                                info['map-exist'] = is_mapping
                                info['ast-node'] = dec_list_global_b[identifier]
                                info['target-file'] = source_path_d

                            elif identifier in dec_list_local_b.keys():
                                info['is_global'] = False
                                info['pre-exist'] = False
                                is_mapping = (identifier in var_map) and \
                                             (var_map[identifier] in set(
                                                 list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                                info['map-exist'] = is_mapping
                                info['ast-node'] = dec_list_local_b[identifier]
                                info['target-file'] = source_path_d

                            elif identifier in dec_list_global_b.keys():
                                info['is_global'] = True
                                info['pre-exist'] = False
                                is_mapping = (identifier in var_map) and \
                                             (var_map[identifier] in set(
                                                 list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                                info['map-exist'] = is_mapping
                                info['ast-node'] = dec_list_global_b[identifier]
                                info['target-file'] = source_path_d

                            missing_var_list[identifier] = info
                        else:
                            if neighborhood_b['value'] not in missing_var_list[identifier]['ref_list']:
                                missing_var_list[identifier]['ref_list'].append(neighborhood_b['value'])
                                missing_var_list[identifier]['is_global'] = True
                elif ref_type == "FunctionDecl":
                    if identifier in values.STANDARD_FUNCTION_LIST:
                        continue
                elif node_type in ["ParmVarDecl"]:
                    # TODO: implement importing missing arguments
                    continue
            else:
                identifier = str(ref_node['value']).strip().replace("\n", "").replace(" ", "")
                if identifier not in missing_var_list.keys() and identifier in enum_list_b.keys():
                    info = dict()
                    info['ref_list'] = list()
                    info['ref-id'] = int(ast_node_b['id'])
                    info['rel-pos'] = relative_pos
                    enum_ref_node = enum_list_b[identifier]
                    enum_def_node = finder.search_ast_node_by_id(ast_tree_b, int(enum_ref_node['parent_id']))
                    enum_value_str = ""
                    enum_value_int = 0
                    for enum_const in enum_def_node['children']:
                        if enum_const['type'] == "EnumConstantDecl":
                            enum_value_int = enum_value_int + 1
                            if len(enum_const['children']):
                                enum_const_type = enum_const['children'][0]['type']
                                if enum_const_type == "IntegerLiteral":
                                    enum_value_int = int(enum_const['children'][0]['value'])
                                else:
                                    emitter.warning("Unhandled enum constant type")
                            enum_identifier = enum_const['identifier']
                            if enum_identifier == identifier:
                                info['enum-value'] = enum_value_int
                                is_mapping = (identifier in var_map) and \
                                             (var_map[identifier] in set(
                                                 list(dec_list_local_c.keys()) + list(dec_list_global_c.keys())))
                                info['map-exist'] = is_mapping
                                info['pre-exist'] = True
                                info['is_global'] = False
                                info['target-file'] = source_path_d
                                missing_var_list[identifier] = info

    return missing_var_list


def identify_missing_data_types(ast_tree_a, ast_tree_b, ast_tree_c, ast_node_b, source_path_b, source_path_d, var_map):
    emitter.normal("\t\t\tanalysing for missing data-types")
    missing_data_type_list = dict()
    type_loc_node_list = extractor.extract_typeloc_node_list(ast_node_b)
    ref_list = extractor.extract_reference_node_list(ast_node_b)
    type_def_node_list_a = extractor.extract_typedef_node_list(ast_tree_a)
    type_def_node_list_b = extractor.extract_typedef_node_list(ast_tree_b)
    type_def_node_list_c = extractor.extract_typedef_node_list(ast_tree_c)
    source_path_c = source_path_d.replace(values.Project_D.path, values.CONF_PATH_C)

    for ref_node in ref_list:
        node_type = str(ref_node['type'])
        node_start_line = int(ref_node['start line'])
        if node_type == "DeclRefExpr":
            if "ref_type" not in ref_node.keys():
                continue
            ref_type = str(ref_node['ref_type'])
            if ref_type == "VarDecl":
                identifier = str(ref_node['data_type'])
                var_name = str(ref_node['value'])
                identifier = identifier.replace("struct ", "")
                if identifier in values.STANDARD_DATATYPE_LIST or identifier in var_map or \
                        identifier not in type_def_node_list_a.keys():
                    continue
                if identifier not in type_def_node_list_c.keys():
                    if identifier not in missing_data_type_list.keys():
                        info = dict()
                        info['target'] = source_path_d
                        ast_node = type_def_node_list_b[identifier]
                        source_file = str(ast_node['file'])
                        if ".." in source_file:
                            source_file = source_path_b + "/../" + str(ast_node['file'])
                            source_file = os.path.abspath(source_file)
                            if not os.path.isfile(source_file):
                                emitter.warning("\t\tFile: " + str(source_file))
                                error_exit("\t\tFile Not Found!")
                        ast_node['file'] = source_file
                        info['ast-node'] = ast_node
                        missing_data_type_list[identifier] = info
        elif node_type == "MemberExpr":
                member_name = ref_node['value'].replace(":", "")
                dec_ref_node = ref_node['children'][0]
                if dec_ref_node['type'] == "DeclRefExpr":
                    if dec_ref_node['ref_type'] == "VarDecl":
                        data_type = dec_ref_node['data_type']
                        if "struct" in data_type:
                            data_type = data_type.replace("struct ", "")
                            full_qualify_name = "." + data_type + "." + member_name
                            if full_qualify_name in var_map:
                                continue
                            if data_type in type_def_node_list_c.keys():
                                record_dec_node = type_def_node_list_c[data_type]
                                is_missing = True
                                insert_line = 0
                                for field_dec_node in record_dec_node['children']:
                                    insert_line = field_dec_node['start line']
                                    if field_dec_node['identifier'] == member_name:
                                        is_missing = False
                                        break

                                if is_missing:
                                    record_dec_node_a = type_def_node_list_a[data_type]
                                    field_dec_node_a = None
                                    for field_dec_node in record_dec_node_a['children']:
                                        if field_dec_node['identifier'] == member_name:
                                            field_dec_node_a = field_dec_node
                                            break
                                    if field_dec_node_a:
                                        info = dict()
                                        info['target'] = source_path_d
                                        ast_node = field_dec_node_a
                                        source_file = str(ast_node['file'])
                                        if ".." in source_file:
                                            source_file = source_path_b + "/../" + str(ast_node['file'])
                                            source_file = os.path.abspath(source_file)
                                            if not os.path.isfile(source_file):
                                                emitter.warning("\t\tFile: " + str(source_file))
                                                error_exit("\t\tFile Not Found!")
                                        ast_node['file'] = source_file
                                        info['ast-node'] = ast_node
                                        info['insert-line'] = insert_line
                                        missing_data_type_list[member_name] = info

    for type_loc_name in type_loc_node_list:
        type_loc_node = type_loc_node_list[type_loc_name]
        identifier = str(type_loc_node['value']).replace("struct ", "").replace("*", "").strip()
        if identifier not in type_def_node_list_c:
            if identifier in values.STANDARD_DATATYPE_LIST:
                continue
            if "(" in identifier:
                continue
            if identifier not in missing_data_type_list.keys():
                info = dict()
                info['target'] = source_path_d
                ast_node = type_def_node_list_b[identifier]
                if "file" not in ast_node:
                    continue
                source_file = str(ast_node['file'])
                if ".." in source_file:
                    source_file = source_path_b + "/../" + str(ast_node['file'])
                    source_file = os.path.abspath(source_file)
                    if not os.path.isfile(source_file):
                        emitter.warning("\t\tFile: " + str(source_file))
                        error_exit("\t\tFile Not Found!")
                ast_node['file'] = source_file
                info['ast-node'] = ast_node
                missing_data_type_list[identifier] = info
    return missing_data_type_list


def identify_missing_headers(ast_node, target_file):
    emitter.normal("\t\t\tanalysing for missing headers")
    missing_header_list = dict()
    node_type = ast_node['type']
    if node_type == "FunctionDecl":
        function_definition = ast_node['value']
        function_name = ast_node['identifier']
        return_type = (function_definition.replace(function_name, "")).split("(")[1]
        if return_type.strip() == "_Bool":
            if "stdbool.h" not in missing_header_list.keys():
                missing_header_list["stdbool.h"] = target_file
            else:
                error_exit("UNKNOWN RETURN TYPE")
    else:
        data_type_list = extractor.extract_data_type_list(ast_node)
        std_int_list = ["uint_fast32_t", "uint_fast8_t"]
        if any(x in data_type_list for x in std_int_list):
            if "stdint.h" not in missing_header_list.keys():
                missing_header_list["stdint.h"] = target_file
            else:
                error_exit("UNKNOWN RETURN TYPE")
    return missing_header_list


def identify_missing_definitions(function_node, missing_function_list):
    emitter.normal("\t\t\tanalysing for missing definitions")
    missing_definition_list = list()
    ref_list = extractor.extract_reference_node_list(function_node)
    dec_list = extractor.extract_decl_list(function_node)
    function_identifier = function_node['identifier']
    dependent_missing_function_list = list()
    for ref_node in ref_list:
        node_type = str(ref_node['type'])
        if node_type == "DeclRefExpr":
            ref_type = str(ref_node['ref_type'])
            identifier = str(ref_node['value'])
            if ref_type == "VarDecl":
                if identifier not in dec_list:
                    missing_definition_list.append(identifier)
            elif ref_type == "FunctionDecl":
                if identifier in values.STANDARD_FUNCTION_LIST:
                    continue
                if identifier not in missing_function_list:
                    emitter.warning("\t\t[warning]: found a dependent function that is missing, attempting to transplant..")
                    dependent_missing_function_list.append(identifier)
    return list(set(missing_definition_list)), dependent_missing_function_list


def identify_missing_macros(ast_node, source_file, target_file, namespace_map_key, ast_tree_global_c):
    emitter.normal("\t\t\tanalysing for missing macros")
    missing_macro_list = dict()
    node_type = str(ast_node['type'])
    target_macro_def_list = list(converter.convert_macro_list_to_dict(
        extractor.extract_macro_definitions(target_file)).keys())
    target_macro_ref_list = extractor.extract_macro_ref_list(ast_tree_global_c)
    if node_type == "Macro":
        node_macro_list = extractor.extract_macro_definition(ast_node, source_file, target_file)
        for macro_name in node_macro_list:
            if "(" in macro_name:
                macro_name = macro_name.split("(")[0] + "("
            if macro_name not in (target_macro_def_list + target_macro_ref_list):
                if macro_name not in values.map_namespace_global[namespace_map_key]:
                    missing_macro_list[macro_name] = node_macro_list[macro_name]
                else:
                    mapped_value = values.map_namespace_global[namespace_map_key][macro_name]
                    if "(" in macro_name and "(" not in mapped_value:
                        missing_macro_list[macro_name] = node_macro_list[macro_name]

    else:
        macro_node_list = extractor.extract_macro_node_list(ast_node)
        macro_def_list = dict()
        for macro_node in macro_node_list:
            macro_def_list_temp = extractor.extract_macro_definition(macro_node, source_file, target_file)
            macro_def_list = merger.merge_macro_info(macro_def_list, macro_def_list_temp)
        for macro_name in macro_def_list:
            if "(" in macro_name:
                macro_name = macro_name.split("(")[0] + "("
            if macro_name not in (target_macro_def_list + target_macro_ref_list):
                if macro_name not in values.map_namespace_global[namespace_map_key]:
                    missing_macro_list[macro_name] = macro_def_list[macro_name]
                else:
                    mapped_value = values.map_namespace_global[namespace_map_key][macro_name]
                    if "(" in macro_name and "(" not in mapped_value:
                        missing_macro_list[macro_name] = macro_def_list[macro_name]

    return missing_macro_list


def identify_missing_macros_in_func(function_node, source_file, target_file):
    emitter.normal("\t\t\tidentifying missing macros in function")
    missing_macro_list = dict()
    ref_list = extractor.extract_reference_node_list(function_node)
    dec_list = extractor.extract_decl_list(function_node)
    function_identifier = function_node['identifier']
    for ref_node in ref_list:
        node_type = str(ref_node['type'])
        if node_type == "Macro":
            identifier = str(ref_node['value'])
            node_child_count = len(ref_node['children'])
            if function_identifier in identifier or "(" in identifier:
                continue
            if identifier in values.STANDARD_MACRO_LIST:
                continue
            if node_child_count:
                for child_node in ref_node['children']:
                    identifier = str(child_node['value'])
                    if identifier in values.STANDARD_MACRO_LIST:
                        continue
                    if identifier not in dec_list:
                        if identifier not in missing_macro_list.keys():
                            info = dict()
                            info['source'] = source_file
                            info['target'] = target_file
                            missing_macro_list[identifier] = info
                        else:
                            error_exit("MACRO REQUIRED MULTIPLE TIMES!!")

            else:
                if identifier not in dec_list:
                    token_list = identifier.split(" ")
                    for token in token_list:
                        if token in ["/", "+", "-"]:
                            continue
                        if token not in dec_list:
                            if identifier not in missing_macro_list.keys():
                                info = dict()
                                info['source'] = source_file
                                info['target'] = target_file
                                missing_macro_list[token] = info
                            else:
                                error_exit("MACRO REQUIRED MULTIPLE TIMES!!")
    return missing_macro_list


def identify_insertion_points(candidate_function):

    insertion_point_list = collections.OrderedDict()
    function_id, function_info = candidate_function
    source_path, function_name = function_id.split(":")
    start_line = int(function_info['start-line'])
    last_line = int(function_info['last-line'])
    exec_line_list = function_info['exec-lines']
    var_map = function_info['var-map']
    # don't include the last line (possible crash line)
    best_score = 0

    target_var_list = list()
    for var_a in var_map:
        var_b = var_map[var_a]
        if "(" in var_b:
            target_var_list.append(")".join(var_b.split(")")[1:]))
        else:
            target_var_list.append(var_b)
    for exec_line in exec_line_list:
        if oracle.is_declaration_line(source_path, int(exec_line)):
            continue
        emitter.special("\t\t" + source_path + "-" + function_name + ":" + str(exec_line))
        emitter.special("\t\t" + source_path + "-" + function_name + ":" + str(exec_line))
        available_var_list = extractor.extract_variable_list(source_path,
                                                             start_line,
                                                             exec_line,
                                                             False)
        unique_var_name_list = list()
        for (var_name, line_num, var_type) in available_var_list:
            if var_name not in unique_var_name_list:
                unique_var_name_list.append(var_name)

        score = len(list(set(unique_var_name_list).intersection(target_var_list)))
        emitter.normal("\t\t\t\tscore: " + str(score))
        insertion_point_list[exec_line] = score
        if score > best_score:
            best_score = score
    if best_score == 0 and not values.IS_BACKPORT:
        print(unique_var_name_list)
        print(target_var_list)
        error_exit("no matching line")

    return insertion_point_list, best_score


def identify_divergent_point(byte_list, sym_path_info, trace_list, stack_info):
    emitter.normal("\tfinding similar location in recipient")
    length = len(sym_path_info) - 1
    count_common = len(byte_list)
    candidate_list = list()
    estimated_loc = None
    trace_list = extractor.extract_unique_in_order(trace_list)
    # TODO: not sure why it was reduced by 1
    length = len(trace_list)
    grab_nearest = False
    for n in range(0, length, 1):
        trace_loc = trace_list[n]
        source_path, line_number = trace_loc.split(":")
        source_path = os.path.abspath(source_path)
        trace_loc_0 = trace_loc
        trace_loc_1 = source_path + ":" + str(int(line_number) + 1)
        trace_loc_2 = source_path + ":" + str(int(line_number) - 1)
        if trace_loc_0 in sym_path_info.keys():
            sym_path_list = sym_path_info[trace_loc_0]
            sym_path_latest = sym_path_list[-1]
            bytes_latest = extractor.extract_input_bytes_used(sym_path_latest)
            count_latest = len(list(set(byte_list).intersection(bytes_latest)))
            if count_latest == count_common:
                count_instant = 1
                if values.IS_BACKPORT:
                    return str(trace_loc_0), len(sym_path_list)
                for sym_path in sym_path_list:
                    bytes_temp = extractor.extract_input_bytes_used(sym_path)
                    count = len(list(set(byte_list).intersection(bytes_temp)))
                    if count == count_common:
                        return str(trace_loc_0), count_instant
                    else:
                        count_instant = count_instant + 1
        elif trace_loc_1 in sym_path_info.keys():
            sym_path_list = sym_path_info[trace_loc_1]
            sym_path_latest = sym_path_list[-1]
            bytes_latest = extractor.extract_input_bytes_used(sym_path_latest)
            count_latest = len(list(set(byte_list).intersection(bytes_latest)))
            if count_latest == count_common:
                if values.IS_BACKPORT:
                    return str(trace_loc_0), len(sym_path_list)
                count_instant = 1
                for sym_path in sym_path_list:
                    bytes_temp = extractor.extract_input_bytes_used(sym_path)
                    count = len(list(set(byte_list).intersection(bytes_temp)))
                    if count == count_common:
                        return str(trace_loc), count_instant
                    else:
                        count_instant = count_instant + 1
        elif trace_loc_2 in sym_path_info.keys():
            sym_path_list = sym_path_info[trace_loc_2]
            sym_path_latest = sym_path_list[-1]
            bytes_latest = extractor.extract_input_bytes_used(sym_path_latest)
            count_latest = len(list(set(byte_list).intersection(bytes_latest)))
            if count_latest == count_common:
                if values.IS_BACKPORT:
                    return str(trace_loc_0), len(sym_path_list)
                count_instant = 1
                for sym_path in sym_path_list:
                    bytes_temp = extractor.extract_input_bytes_used(sym_path)
                    count = len(list(set(byte_list).intersection(bytes_temp)))
                    if count == count_common:
                        return str(trace_loc), count_instant
                    else:
                        count_instant = count_instant + 1

    return estimated_loc, 0


def identify_fixed_errors(output_a, output_b):
    fixed_error_list = list()
    error_list_a = extractor.extract_error_list_from_output(output_a)
    error_list_b = extractor.extract_error_list_from_output(output_b)
    fixed_error_list = [error for error in error_list_a if error not in error_list_b]
    return list(set(fixed_error_list))


def separate_segment(project, source_file, use_macro=False):
    enum_list = []
    function_list = []
    macro_list = []
    struct_list = []
    type_def_list = []
    def_list = []
    decl_list = []
    asm_list = []

    ast_tree = Gen.generate_ast_json(source_file, use_macro)
    if not ast_tree:
        error_exit("AST Tree not built, probably compile command not found")
    source_file_pattern = [
        source_file,
        source_file.split("/")[-1],
        source_file.replace(project.path, '')
    ]

    # --- Recursive function ---
    def process_ast_node(ast_node):
        node_type = str(ast_node.get("type", ""))
        if node_type == "VarDecl":
            if 'file' in ast_node and ast_node['file'] in source_file_pattern:
                parent_id = int(ast_node.get('parent_id', 0))
                if parent_id == 0:
                    decl_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["EnumConstantDecl", "EnumDecl"]:
            if 'file' in ast_node and ast_node['file'] in source_file_pattern:
                enum_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type == "Macro":
            if 'file' in ast_node and ast_node['file'] in source_file_pattern:
                if 'value' in ast_node:
                    macro_value = ast_node["value"]
                    if "(" in macro_value:
                        macro_value = macro_value.split("(")[0]
                    macro_list.append((macro_value, ast_node["start line"], ast_node["end line"]))
        elif node_type == "TypedefDecl":
            if 'file' in ast_node and ast_node['file'] in source_file_pattern:
                type_def_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type == "RecordDecl":
            if 'file' in ast_node and ast_node['file'] in source_file_pattern:
                struct_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["FunctionDecl", "CXXMethodDecl"]:
            if ('qualified_identifier' in ast_node):
                function_list.append((ast_node["qualified_identifier"], ast_node["start line"], ast_node["end line"]))
            else:
                function_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type == "CXXConstructorDecl":
            function_list.append((ast_node["value"], ast_node["start line"], ast_node["end line"]))
        elif node_type in ["EmptyDecl", "FileScopeAsmDecl"]:
            return

        # Recursively process children
        if node_type not in ["FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl"]:
            for child in ast_node.get('children', []):
                process_ast_node(child)

    # --- Start recursive traversal ---
    for ast_node in ast_tree.get('children', []):
        process_ast_node(ast_node)
    
    print("Function list in identifier:", function_list)
    return enum_list, function_list, macro_list, struct_list, type_def_list, def_list, decl_list


def create_vectors(project, source_file, segmentation_list, pertinent_lines, out_file_path):
    emitter.normal("\t\t\tcreating vectors for neighborhoods")
    neighbor_list = list()
    enum_list, function_list, macro_list, \
    struct_list, type_def_list, def_list, decl_list = segmentation_list
    for function_name, begin_line, finish_line in function_list:
        function_name = "func_" + remove_bracketed_content(function_name)
        print("Function Name:", function_name, "Begin Line:", begin_line, "Finish Line:", finish_line, "pertinent lines:", pertinent_lines)
        for start_line, end_line in pertinent_lines:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                values.IS_FUNCTION = True
                if source_file not in project.function_list.keys():
                    project.function_list[source_file] = dict()
                if function_name not in project.function_list[source_file]:
                    emitter.success("\t\t\tFunction: " + function_name.replace("func_", ""))
                    neighbor_list.append(function_name)
                    print("generating vector for:", source_file, function_name)
                    project.function_list[source_file][function_name] = ast_vector.Vector(source_file, function_name,
                                                                                          begin_line, finish_line, True)

    for struct_name, begin_line, finish_line in struct_list:
        struct_name = "struct_" + struct_name.split(";")[0]
        for start_line, end_line in pertinent_lines:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                values.IS_STRUCT = True
                if source_file not in project.struct_list.keys():
                    project.struct_list[source_file] = dict()
                if struct_name not in project.struct_list[source_file]:
                    emitter.success("\t\t\tStruct: " + struct_name.replace("struct_", ""))
                    neighbor_list.append(struct_name)
                    project.struct_list[source_file][struct_name] = ast_vector.Vector(source_file, struct_name,
                                                                                      begin_line, finish_line, True)

    for var_name, begin_line, finish_line in decl_list:
        var_name = "var_" + var_name.split(";")[0]
        var_type = (var_name.split("(")[1]).split(")")[0]
        var_name = var_name.split("(")[0]
        for start_line, end_line in pertinent_lines:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                values.IS_TYPEDEC = True
                if source_file not in project.decl_list.keys():
                    project.decl_list[source_file] = dict()
                if var_name not in project.decl_list[source_file]:
                    emitter.success("\t\t\tVariable: " + var_name.replace("var_", ""))
                    neighbor_list.append(var_name)
                    project.decl_list[source_file][var_name] = ast_vector.Vector(source_file, var_name,
                                                                                 begin_line, finish_line, True)

    for macro_name, begin_line, finish_line in macro_list:
        macro_name = "macro_" + macro_name
        for start_line, end_line in pertinent_lines:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                values.IS_MACRO = True
                if source_file not in project.macro_list.keys():
                    project.macro_list[source_file] = dict()
                if macro_name not in project.macro_list[source_file]:
                    emitter.success("\t\t\tMacro: " + macro_name.replace("macro_", ""))
                    neighbor_list.append(macro_name)
                    project.macro_list[source_file][macro_name] = ast_vector.Vector(source_file, macro_name,
                                                                                    begin_line, finish_line, True)

    count = 0
    for enum_name, begin_line, finish_line in enum_list:
        enum_name = "enum_" + enum_name.split(";")[0]
        if "anonymous" in enum_name:
            count = count + 1
            enum_name = "enum_" + str(count)
        for start_line, end_line in pertinent_lines:
            if is_intersect(begin_line, finish_line, start_line, end_line):
                values.IS_ENUM = True

                if source_file not in project.enum_list.keys():
                    project.enum_list[source_file] = dict()
                if enum_name not in project.enum_list[source_file]:
                    emitter.success("\t\t\tEnum: " + enum_name.replace("enum_", ""))
                    neighbor_list.append(enum_name)
                    project.enum_list[source_file][enum_name] = ast_vector.Vector(source_file, enum_name,
                                                                                  begin_line, finish_line, True)

    with open(out_file_path, "w") as out_file:
        for neighbor_name in neighbor_list:
            out_file.write(neighbor_name + "\n")
    return values.IS_ENUM or values.IS_FUNCTION or values.IS_MACRO or values.IS_STRUCT or values.IS_TYPEDEC


def identify_code_segment(diff_info, project, out_file_path):
    grouped_line_info = dict()
    for source_loc in diff_info:
        source_file, start_line = source_loc.split(":")
        diff_line_info = diff_info[source_loc]
        operation = diff_line_info['operation']
        if source_file not in grouped_line_info:
            grouped_line_info[source_file] = list()
        grouped_line_info[source_file].append(diff_line_info['old-lines'])

    for source_file in grouped_line_info:
        emitter.normal("\t\t" + source_file)
        pertinent_lines = grouped_line_info[source_file]
        values.DONOR_PRE_PROCESS_MACRO = extractor.extract_pre_macro_command(source_file)
        segmentation_list = separate_segment(project, source_file)
        found_neighborhood = create_vectors(project, source_file, segmentation_list, pertinent_lines, out_file_path)
        if not found_neighborhood:
            segmentation_list = separate_segment(project, source_file, True)
            create_vectors(project, source_file, segmentation_list, pertinent_lines, out_file_path)
            values.DONOR_REQUIRE_MACRO = True


def identify_definition_segment(diff_info, project):
    grouped_line_info = dict()
    for source_loc in diff_info:
        source_file, start_line = source_loc.split(":")
        diff_line_info = diff_info[source_loc]
        if source_file not in grouped_line_info:
            grouped_line_info[source_file] = list()
        grouped_line_info[source_file].append(diff_line_info['old-lines'])

    for source_file_a in grouped_line_info:
        emitter.normal("\t\t" + source_file_a)
        source_file_b = source_file_a.replace(values.CONF_PATH_A, values.CONF_PATH_B)
        header_list_a = extractor.extract_header_list(source_file_a)
        header_list_b = extractor.extract_header_list(source_file_b)
        added_header_list = list(set(header_list_b) - set(header_list_a))
        removed_header_list = list(set(header_list_a) - set(header_list_b))
        project.header_list[source_file_a] = dict()
        project.header_list[source_file_a]['added'] = added_header_list
        project.header_list[source_file_a]['removed'] = removed_header_list
        for header_file in added_header_list:
            emitter.success("\t\t\tAdded: " + header_file)
        for header_file in removed_header_list:
            emitter.success("\t\t\tRemoved: " + header_file)

