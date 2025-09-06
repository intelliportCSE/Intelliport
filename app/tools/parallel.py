import multiprocessing as mp

import app.common.utilities
from app.common import definitions, values, utilities
from app.tools import converter, emitter, finder, extractor
from app.ast import ast_generator

BREAK_LIST = [",", " ", " _", ";", "\n"]


def collect_result(result):
    global result_list
    result_list.append(result)


def derive_namespace_map(ast_node_map, source_a, source_c, neighbor_id_a, neighbor_id_c):
    global pool, result_list, expected_count
    result_list = []

    namespace_map = dict()
    refined_namespace_map = dict()
    emitter.normal("\tderiving namespace map")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)
    ast_array_a = converter.convert_dict_to_array(ast_tree_a)
    ast_array_c = converter.convert_dict_to_array(ast_tree_c)
    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())
    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        if ast_node_id_a == 0 or ast_node_id_c == 0:
            continue
        ast_node_a = ast_array_a[ast_node_id_a]
        ast_node_c = ast_array_c[ast_node_id_c]
        parent_id_a = int(ast_node_a['parent_id'])
        parent_id_c = int(ast_node_c['parent_id'])

        value_score = 1
        if ast_node_a:
            pool.apply_async(extractor.extract_mapping, args=(ast_node_a, ast_node_c, value_score),
                             callback=collect_result)
        if parent_id_c != 0:

            # TODO: Improve this mapping
            if parent_id_c != 0:
                parent_c = ast_array_c[parent_id_c]
            if ast_node_c['type'] == "MemberExpr" and parent_c['type'] == "MemberExpr":
                grand_id = parent_c['parent_id']
                if grand_id != 0:
                    grand_parent_c = ast_array_c[parent_c['parent_id']]
                    pool.apply_async(extractor.extract_mapping, args=(ast_node_a, parent_c, value_score),
                                     callback=collect_result)
                    if grand_parent_c["type"] == "BinaryOperator" and ast_node_c['data_type'] == "ktime_t":
                        var_mapping = "." + ast_node_a['value'][1:], "." + ast_node_c['value'][1:] + "." + parent_c['value'][1:], 100, "MemberExpr", "MemberExpr"
                        result_list.append(var_mapping)
                        values.data_type_map[ast_node_a['data_type']] = parent_c['data_type']

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for id_a, id_c, score, type_a, type_c in result_list:
        if id_a is None or id_c is None:
            continue
        if id_a not in namespace_map:
            namespace_map[id_a] = dict()
        if id_c not in namespace_map[id_a]:
            namespace_map[id_a][id_c] = score
        else:
            namespace_map[id_a][id_c] = namespace_map[id_a][id_c] + score

        if "(" in id_a and "(" in id_c:
            id_a = id_a.split("(")[0] + "("
            id_c = id_c.split("(")[0] + "("
            if id_a not in namespace_map:
                namespace_map[id_a] = dict()
            if id_c not in namespace_map[id_a]:
                namespace_map[id_a][id_c] = score
            else:
                namespace_map[id_a][id_c] = namespace_map[id_a][id_c] + score
    function_name_cache = list()
    for value_a in namespace_map:
        candidate_list = namespace_map[value_a]
        max_score = 0
        best_candidate = None
        for candidate in candidate_list:
            if "(" in candidate and "(" not in value_a:
                continue
            candidate_score = candidate_list[candidate]
            if max_score < candidate_score:
                best_candidate = candidate
                max_score = candidate_score
        if best_candidate:
            if "(" in value_a:
                function_name_cache.append(value_a)
                function_name_cache.append(value_a[:-1])
                continue
            if value_a in function_name_cache:
                continue
            if not value_a or not best_candidate:
                continue
            if any(token in str(value_a).lower() for token in BREAK_LIST):
                continue
            if any(token in str(best_candidate).lower() for token in BREAK_LIST):
                continue

            refined_namespace_map[value_a] = best_candidate

    return refined_namespace_map


def read_mapping(map_file_name):
    global pool, result_list, expected_count
    result_list = []
    node_map = dict()
    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    with open(map_file_name, 'r') as ast_map:
        line_list = ast_map.readlines()

    for line in line_list:
        line = line.strip()
        line = line.split(" ")
        operation = line[0]
        content = " ".join(line[1:])
        if operation == definitions.MATCH:
            node_pair = utilities.clean_parse(content, definitions.TO)
            result_list.append(node_pair)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for node_a, node_c in result_list:
        node_map[node_a] = node_c
    return node_map


# adjust the mapping via anti-unification
def extend_mapping(ast_node_map, source_a, source_c, neighbor_id_a):
    global pool, result_list, expected_count
    result_list = []

    emitter.normal("\tupdating ast map using anti-unification")
    ast_tree_a = ast_generator.get_ast_json(source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(source_c, values.TARGET_REQUIRE_MACRO, regenerate=True)

    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    for node_a in ast_node_map:
        node_c = ast_node_map[node_a]
        ast_node_id_a = int(str(node_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(node_c).split("(")[1].split(")")[0])
        ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

        pool.apply_async(anti_unification, args=(ast_node_a, ast_node_c),
                         callback=collect_result)

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for au_pairs in result_list:
        for au_pair_key in au_pairs:
            au_pair_value = au_pairs[au_pair_key]
            if au_pair_key not in ast_node_map:
                ast_node_map[au_pair_key] = au_pair_value

    return ast_node_map


def generate_method_invocation_map(source_a, source_c, ast_tree_a, ast_tree_c, method_name):
    global pool, result_list, expected_count
    result_list = []
    method_invocation_map = dict()
    emitter.normal("\tderiving method invocation map")

    map_file_name = definitions.DIRECTORY_OUTPUT + "/" + source_a.split("/")[-1] + ".map"
    app.common.utilities.generate_map_gumtree(source_a, source_c, map_file_name)
    global_ast_node_map = read_mapping(map_file_name)
    result_list = []
    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    for ast_node_txt_a in global_ast_node_map:
        ast_node_txt_c = global_ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        node_type_a = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        node_type_c = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        if node_type_a in ["CallExpr"] and node_type_c in ["CallExpr"]:
            ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
            ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
            children_a = ast_node_a["children"]
            children_c = ast_node_c["children"]
            if len(children_a) < 1 or len(children_c) < 1:
                continue
            if "value" not in children_a[0]:
                continue
            if method_name == children_a[0]["value"]:
                result_list.append(extractor.extract_method_invocations(global_ast_node_map,
                                                                        ast_node_a, ast_node_c, method_name))

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for method_name_a, method_name_c, arg_operation in result_list:
        if method_name_a is not None:
            if method_name_a not in method_invocation_map:
                method_invocation_map[method_name_a] = dict()
            mappings = method_invocation_map[method_name_a]
            if method_name_c not in mappings:
                mappings[method_name_c] = (1, arg_operation)
            else:
                score, arg_operation = mappings[method_name_c]
                mappings[method_name_c] = (score + 1, arg_operation)
            method_invocation_map[method_name_a] = mappings
    return method_invocation_map


def generate_function_signature_map(source_a, source_c, ast_tree_a, ast_tree_c, method_name):
    global pool, result_list, expected_count
    result_list = []
    function_map = dict()
    emitter.normal("\tderiving function signature map")
    map_file_name = definitions.DIRECTORY_OUTPUT + "/" + source_a.split("/")[-1] + ".map"
    global_ast_node_map = read_mapping(map_file_name)
    result_list = []
    emitter.normal("\t\tstarting parallel computing")
    pool = mp.Pool(mp.cpu_count())

    for ast_node_txt_a in global_ast_node_map:
        ast_node_txt_c = global_ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        node_type_a = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        node_type_c = str(ast_node_txt_c).split("(")[0].split(" ")[-1]
        if node_type_a in ["FunctionDecl"] and node_type_c in ["FunctionDecl"]:
            ast_node_a = finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
            ast_node_c = finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
            children_a = ast_node_a["children"]
            children_c = ast_node_c["children"]
            if len(children_a) < 1 or len(children_c) < 1:
                continue
            if "identifier" not in ast_node_a.keys():
                continue
            if method_name == ast_node_a["identifier"]:
                result_list.append(extractor.extract_method_signatures(global_ast_node_map,
                                                                       ast_node_a, ast_node_c, method_name))

    pool.close()
    emitter.normal("\t\twaiting for thread completion")
    pool.join()

    for method_name_a, method_name_c, arg_operation in result_list:
        if method_name_a is not None:
            if method_name_a not in function_map:
                function_map[method_name_a] = dict()
            mappings = function_map[method_name_a]
            if method_name_c not in mappings:
                mappings[method_name_c] = (1, arg_operation)
            else:
                score, arg_operation = mappings[method_name_c]
                mappings[method_name_c] = (score + 1, arg_operation)
            function_map[method_name_a] = mappings
    return function_map


def anti_unification(ast_node_a, ast_node_c):
    au_pairs = dict()
    waiting_list_a = [ast_node_a]
    waiting_list_c = [ast_node_c]

    while len(waiting_list_a) != 0 and len(waiting_list_c) != 0:
        current_a = waiting_list_a.pop()
        current_c = waiting_list_c.pop()

        children_a = current_a["children"]
        children_c = current_c["children"]

        # do not support anti-unification with different number of children yet
        if len(children_a) != len(children_c):
            continue

        length = len(children_a)
        for i in range(length):
            child_a = children_a[i]
            child_c = children_c[i]
            if child_a["type"] == child_c["type"]:
                waiting_list_a.append(child_a)
                waiting_list_c.append(child_c)
            key = child_a["type"] + "(" + str(child_a["id"]) + ")"
            value = child_c["type"] + "(" + str(child_c["id"]) + ")"
            au_pairs[key] = value

    return au_pairs