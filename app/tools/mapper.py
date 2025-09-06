from app.common import definitions, values, utilities
from app.common.utilities import get_source_name_from_slice, generate_map_gumtree
from app.tools import parallel, emitter, finder
from app.ast import ast_generator
import sys
import time
BREAK_LIST = [",", " ", " _", ";", "\n"]


def map_ast_from_source(source_a, source_b, script_file_path):
    ast_generator.generate_ast_script(source_a, source_b, script_file_path, True)
    mapping = dict()
    with open(script_file_path, 'r', encoding='utf8', errors="ignore") as script_file:
        script_lines = script_file.readlines()
        for script_line in script_lines:
            if "Match" in script_line:
                node_id_a = int(((script_line.split(" to ")[0]).split("(")[1]).split(")")[0])
                node_id_b = int(((script_line.split(" to ")[1]).split("(")[1]).split(")")[0])
                mapping[node_id_b] = node_id_a
    return mapping


def generate_map(file_list):

    slice_file_a = file_list[0]
    slice_file_c = file_list[2]
    vector_source_a = get_source_name_from_slice(slice_file_a)
    vector_source_c = get_source_name_from_slice(slice_file_c)
    utilities.shift_slice_source(slice_file_a, slice_file_c)
    time_check = time.time()
    ast_tree_a = ast_generator.get_ast_json(vector_source_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = ast_generator.get_ast_json(vector_source_c, values.DONOR_REQUIRE_MACRO, regenerate=True)
    duration = format((time.time() - time_check) / 60, '.3f')
    emitter.information("AST Generation A: " + str(duration))

    neighbor_ast_a = None
    neighbor_ast_c = None
    neighbor_ast_range = None
    neighbor_type_a, neighbor_name_a, slice_a = str(slice_file_a).split("/")[-1].split(".cc.")[-1].split(".")
    neighbor_type_c, neighbor_name_c, slice_c = str(slice_file_c).split("/")[-1].split(".cc.")[-1].split(".")
    if neighbor_type_a == "func":
        neighbor_ast_a = finder.search_function_node_by_name(ast_tree_a, neighbor_name_a)
        neighbor_ast_c = finder.search_function_node_by_name(ast_tree_c, neighbor_name_c)
    elif neighbor_type_a == "var":
        # neighbor_name = neighbor_name[:neighbor_name.rfind("_")]
        neighbor_ast_a = finder.search_node(ast_tree_a, "VarDecl", neighbor_name_a)
        neighbor_ast_c = finder.search_node(ast_tree_c, "VarDecl", neighbor_name_c)
    elif neighbor_type_a == "struct":
        neighbor_ast_a = finder.search_node(ast_tree_a, "RecordDecl", neighbor_name_a)
        neighbor_ast_c = finder.search_node(ast_tree_c, "RecordDecl", neighbor_name_c)
    if neighbor_ast_a:
        neighbor_ast_range = (int(neighbor_ast_a['begin']), int(neighbor_ast_a['end']))
    else:
        utilities.error_exit("No neighbor AST Found")

    map_file_name = definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1] + ".map"
    time_check = time.time()
    if not values.CONF_USE_CACHE:
        generate_map_gumtree(vector_source_a, vector_source_c, map_file_name)
    duration = format((time.time() - time_check) / 60, '.3f')
    emitter.information("AST Map Generation: " + str(duration))

    time_check = time.time()
    ast_node_map = parallel.read_mapping(map_file_name)
    duration = format((time.time() - time_check) / 60, '.3f')
    emitter.information("Read Mapping: " + str(duration))

    if values.DEFAULT_OPERATION_MODE == 0:
        time_check = time.time()
        ast_node_map = parallel.extend_mapping(ast_node_map, vector_source_a, vector_source_c, int(neighbor_ast_a['id']))
        duration = format((time.time() - time_check) / 60, '.3f')
        emitter.information("Anti Unification: " + str(duration))

        # emitter.data(ast_node_map)
    time_check = time.time()
    namespace_map = parallel.derive_namespace_map(ast_node_map, vector_source_a,
                                                  vector_source_c,
                                                  int(neighbor_ast_a['id']),
                                                  int(neighbor_ast_c['id']))
    duration = format((time.time() - time_check) / 60, '.3f')
    emitter.information("Namespace Mapping: " + str(duration))

    utilities.restore_slice_source()

    return ast_node_map, namespace_map


