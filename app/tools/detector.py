#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os

import app.common.utilities
from app.common.utilities import error_exit, definitions, id_from_string
from app.tools import generator, slicer, parallel, emitter, finder, extractor
from app.common import values, utilities
from app.ast import ast_parser, ast_vector, ast_generator


def detect_matching_variables(func_name_a, file_a, func_name_c, file_c):
    try:
        ast_generator.generate_ast_script(values.Project_A.path + file_a, values.Project_C.path + file_c, definitions.FILE_AST_MAP, True)
        # generate_ast_map(Definitions.Pa.path + file_a, Definitions.Pc.path + file_c)
    except Exception as e:
        error_exit(e, "Error at generate_ast_map.")

    function_a = values.Project_A.function_list[values.Project_A.path + file_a][func_name_a]
    variable_list_a = function_a.variables.copy()

    while '' in variable_list_a:
        variable_list_a.remove('')

    variable_list_a = [i.split(" ")[-1] for i in variable_list_a]

    # print(Values.Project_C.functions[Values.Project_C.path + file_c])
    ast_generator.generate_function_list(values.Project_C, values.Project_C.path + file_c)

    function_c = values.Project_C.function_list[values.Project_C.path + file_c][func_name_c]
    variable_list_c = function_c.variables
    while '' in variable_list_c:
        variable_list_c.remove('')
    json_file_a = values.Project_A.path + file_a + ".AST"
    ast_a = ast_parser.AST_from_file(json_file_a)
    json_file_c = values.Project_C.path + file_c + ".AST"
    ast_c = ast_parser.AST_from_file(json_file_c)
    ast_map = dict()

    try:
        with open(definitions.FILE_AST_MAP, "r", ) as ast_map_file:
            map_line = ast_map_file.readline().strip()
            while map_line:
                node_a, node_c = clean_parse(map_line, definitions.TO)
                var_a = id_from_string(node_a)
                var_a = ast_a[var_a].value_calc(values.Project_A.path + file_a)

                var_c = id_from_string(node_c)
                var_c = ast_c[var_c].value_calc(values.Project_C.path + file_c)

                if var_a in variable_list_a:
                    if var_a not in ast_map.keys():
                        ast_map[var_a] = dict()
                    if var_c in ast_map[var_a].keys():
                        ast_map[var_a][var_c] += 1
                    else:
                        ast_map[var_a][var_c] = 1
                map_line = ast_map_file.readline().strip()
    except Exception as e:
        error_exit(e, "Unexpected error while parsing ast-map")

    UNKNOWN = "#UNKNOWN#"
    variable_mapping = dict()
    try:
        while variable_list_a:
            var_a = variable_list_a.pop()
            if var_a not in variable_mapping.keys():
                a_name = var_a.split(" ")[-1]
                if a_name in ast_map.keys():
                    max_match = -1
                    best_match = None
                    for var_c in ast_map[a_name].keys():
                        if max_match == -1:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                        elif ast_map[a_name][var_c] > max_match:
                            max_match = ast_map[a_name][var_c]
                            best_match = var_c
                    if best_match:
                        for var_c in variable_list_c:
                            c_name = var_c.split(" ")[-1]
                            if c_name == best_match:
                                variable_mapping[var_a] = var_c
                if var_a not in variable_mapping.keys():
                    variable_mapping[var_a] = UNKNOWN
    except Exception as e:
        error_exit(e, "Unexpected error while mapping vars.")

    with open("output/var-map", "w") as var_map_file:
        for var_a in variable_mapping.keys():
            var_map_file.write(var_a + " -> " + variable_mapping[var_a] + "\n")

    return variable_mapping


def detect_segment_clone_by_similarity(vector_list_a, vector_list_c):
    candidate_list_all_a = dict()
    candidate_list_all_b = dict()
    map_file_name = definitions.DIRECTORY_TMP + "/sydit.map"
    for vector_a in vector_list_a:
        candidate_list_a = []
        candidate_list_b = []
        vector_path_a, vector_matrix_a = vector_a
        source_file_a, segment_a = vector_path_a.split(".cc.")
        source_file_a = source_file_a + ".cc"
        seg_type_a = segment_a.replace(".vec", "").split("_")[0]
        segment_identifier_a = "_".join(segment_a.replace(".vec", "").split("_")[1:])
        slice_file_a = source_file_a + "." + seg_type_a + "." + segment_identifier_a + ".slice"
        slicer.slice_source_file(source_file_a, seg_type_a, segment_identifier_a,
                                 values.CONF_PATH_A,
                                 values.DONOR_REQUIRE_MACRO)
        if os.stat(slice_file_a).st_size == 0:
            error_exit("SLICE NOT CREATED")
        utilities.shift_per_slice(slice_file_a)
        ast_tree_a = ast_generator.get_ast_json(source_file_a, values.DONOR_REQUIRE_MACRO, regenerate=True)
        if seg_type_a == "func":
            ast_node_a = finder.search_function_node_by_name(ast_tree_a, segment_identifier_a)
            if not ast_node_a:
                error_exit("FUNCTION NODE NOT FOUND")
            id_list_a = extractor.extract_child_id_list(ast_node_a)
            node_size_a = len(id_list_a)
            for vector_c in vector_list_c:
                vector_path_c, vector_matrix_c = vector_c
                source_file_c, segment_c = vector_path_c.split(".cc.")
                source_file_c = source_file_c + ".cc"
                seg_type_c = segment_c.replace(".vec", "").split("_")[0]
                segment_identifier_c = "_".join(segment_c.replace(".vec", "").split("_")[1:])
                slice_file_c = source_file_c + "." + seg_type_c + "." + segment_identifier_c + ".slice"
                slicer.slice_source_file(source_file_c, seg_type_c, segment_identifier_c,
                                         values.CONF_PATH_C,
                                         values.TARGET_REQUIRE_MACRO)

                if not os.path.isfile(slice_file_c):
                    continue
                if os.stat(slice_file_c).st_size == 0:
                    continue
                utilities.shift_per_slice(slice_file_c)
                ast_tree_c = ast_generator.get_ast_json(source_file_c, values.TARGET_REQUIRE_MACRO, regenerate=True)
                ast_node_c = finder.search_function_node_by_name(ast_tree_c, segment_identifier_c)
                id_list_c = extractor.extract_child_id_list(ast_node_c)
                app.common.utilities.generate_map_gumtree(source_file_a, source_file_c, map_file_name)
                ast_node_map = parallel.read_mapping(map_file_name)
                utilities.restore_per_slice(slice_file_c)
                node_size_c = len(id_list_c)
                match_count = 0
                for node_str_a in ast_node_map:
                    node_id_a = utilities.id_from_string(node_str_a)
                    if node_id_a in id_list_a:
                        match_count = match_count + 1
                similarity_a = float(match_count / (node_size_a))
                similarity_b = float(match_count / (node_size_a + node_size_c))
                emitter.information("Segment A Type: " + str(seg_type_a))
                emitter.information("Segment A Name: " + str(segment_identifier_a))
                emitter.information("Segment C Type: " + str(seg_type_c))
                emitter.information("Segment C Name: " + str(segment_identifier_c))
                emitter.information("Match Count: " + str(match_count))
                emitter.information("Size of A: " + str(node_size_a))
                emitter.information("Size of C: " + str(node_size_c))
                emitter.information("Similarity 1: " + str(similarity_a))
                emitter.information("Similarity 2: " + str(similarity_b))
                # if len(candidate_list) > 1:
                #     emitter.error("Found more than one candidate")
                #     for candidate in candidate_list:
                #         emitter.error(str(candidate))
                #     utilities.error_exit("Too many candidates")
                if similarity_a > values.DEFAULT_SIMILARITY_FACTOR:
                    candidate_list_a.append((vector_path_c, similarity_a))
                if similarity_b > values.DEFAULT_SIMILARITY_FACTOR:
                    candidate_list_b.append((vector_path_c, similarity_b))
            # if len(candidate_list) > 1:
            #     emitter.error("Found more than one candidate")
            #     for candidate in candidate_list:
            #         emitter.error(str(candidate))
            #     utilities.error_exit("Too many candidates")
            # elif len(candidate_list) == 0:
            #     utilities.error_exit("NO CANDIDATE FOUND")
            # if len(candidate_list) == 1:
            #     candidate_list_all[vector_path_a] = candidate_list
            candidate_list_all_a[vector_path_a] = candidate_list_a
            candidate_list_all_b[vector_path_a] = candidate_list_b

        else:
            utilities.error_exit("DOES NOT SUPPORT OTHER SEGMENTS THAN FUNCTIONS")

        utilities.restore_per_slice(slice_file_a)

    return candidate_list_all_a


def detect_segment_clone_by_distance(vector_list_a, vector_list_c, dist_factor):
    candidate_list_all = dict()
    for vector_a in vector_list_a:
        # Assume vector already created
        file_path_a = vector_a[0]
        matrix_a = vector_a[1]

        possible_candidate_path = file_path_a.replace(values.Project_A.path, values.Project_C.path)
        possible_candidate = None
        possible_candidate_distance = 0.0

        vector_c = vector_list_c[0]
        matrix_c = vector_c[1]
        best_vector = vector_c
        if not matrix_c:
            for vector_c in vector_list_c:
                matrix_c = vector_c[1]
                if matrix_c:
                    best_vector = vector_c
                    break
        best_distance = ast_vector.Vector.dist(matrix_a, matrix_c)
        distance_matrix = dict()

        # Get best match candidate
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if file_path_c == possible_candidate_path:
                distance = ast_vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                possible_candidate = vector_c
                possible_candidate_distance = distance
            if matrix_c is not None:
                distance = ast_vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                if distance < best_distance:
                    best_vector = vector_c
                    best_distance = distance

        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        # best_vector = (best_vector[0], best_vector[1], best_distance)
        if possible_candidate is not None:
            candidate_list = [(possible_candidate_path, possible_candidate_distance)]
        else:
            candidate_list = [(best_vector[0], best_distance)]
        candidate_distance = dict()
        candidate_location = dict()

        # Collect all vectors within range best_distance - 2 x best_distance
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if vector_c is not None:
                if vector_c[0] != best_vector[0]:
                    if matrix_c is not None:
                        distance = distance_matrix[file_path_c]
                        if distance <= dist_factor * best_distance:
                            # vector_c = (vector_c[0], vector_c[1], distance)
                            candidate_list.append((vector_c[0], distance))

        candidate_list_all[file_path_a] = candidate_list

    return candidate_list_all


def detect_file_clone_by_distance(file_list_a, vector_list_c, dist_factor):
    candidate_list_all = dict()
    for vector_a in file_list_a:
        # Assume vector already created
        file_path_a = vector_a[0]
        matrix_a = vector_a[1]

        possible_candidate_path = file_path_a.replace(values.Project_A.path, values.Project_C.path)
        possible_candidate = None
        possible_candidate_distance = 0.0

        vector_c = vector_list_c[0]
        matrix_c = vector_c[1]
        best_vector = vector_c
        if not matrix_c:
            for vector_c in vector_list_c:
                matrix_c = vector_c[1]
                if matrix_c:
                    best_vector = vector_c
                    break
        best_distance = ast_vector.Vector.dist(matrix_a, matrix_c)
        distance_matrix = dict()

        # Get best match candidate
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if file_path_c == possible_candidate_path:
                distance = ast_vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                possible_candidate = vector_c
                possible_candidate_distance = distance
            if matrix_c is not None:
                distance = ast_vector.Vector.dist(matrix_a, matrix_c)
                distance_matrix[file_path_c] = distance
                if distance < best_distance:
                    best_vector = vector_c
                    best_distance = distance

        # Get all pertinent matches (at d < factor*best_d) (with factor=2?)
        # best_vector = (best_vector[0], best_vector[1], best_distance)
        if possible_candidate is not None:
            candidate_list = [(possible_candidate_path, possible_candidate_distance)]
        else:
            candidate_list = [(best_vector[0], best_distance)]
        candidate_distance = dict()
        candidate_location = dict()

        # Collect all vectors within range best_distance - 2 x best_distance
        for vector_c in vector_list_c:
            matrix_c = vector_c[1]
            file_path_c = vector_c[0]
            if vector_c is not None:
                if vector_c[0] != best_vector[0]:
                    if matrix_c is not None:
                        distance = distance_matrix[file_path_c]
                        if distance <= dist_factor * best_distance:
                            # vector_c = (vector_c[0], vector_c[1], distance)
                            candidate_list.append((vector_c[0], distance))

        candidate_list_all[file_path_a] = candidate_list

    return candidate_list_all


def detect_struct_clones():
    extension = "*.struct_*\.vec"
    vector_list_a = finder.search_vector_list(values.Project_A, extension, 'struct')
    vector_list_c = finder.search_vector_list(values.Project_C, extension, 'struct')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    if not vector_list_c:
        return []
    candidate_list_all = detect_candidate_list(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".struct_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".struct_")
        vector_source_a = str(vector_source_a).replace(values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        similarity_sore = generator.generate_similarity_score(vector_path_a, candidate_file_path)
        if float(similarity_sore) > 0.4:
            values.IS_IDENTICAL = True
        else:
            values.IS_IDENTICAL = False
        emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        emitter.success("\t\t\tStructure: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        emitter.success("\t\t\tSimilarity: " + str(similarity_sore))
        emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
        values.VECTOR_MAP[vector_path_a] = candidate_file_path
    return clone_list


def detect_enum_clones():
    extension = "*.enum_*\.vec"
    vector_list_a = finder.search_vector_list(values.Project_A, extension, 'enum')
    vector_list_c = finder.search_vector_list(values.Project_C, extension, 'enum')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    if not vector_list_c:
        return []
    candidate_list_all = detect_candidate_list(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".enum_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".enum_")
        vector_source_a = str(vector_source_a).replace(values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        similarity_sore = generator.generate_similarity_score(vector_path_a, candidate_file_path)
        if float(similarity_sore) > 0.4:
            values.IS_IDENTICAL = True
        else:
            values.IS_IDENTICAL = False
        emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        emitter.success("\t\t\tEnum Definition: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        emitter.success("\t\t\tSimilarity: " + str(similarity_sore) + "\n")
        emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
        values.VECTOR_MAP[vector_path_a] = candidate_file_path
    return clone_list


def detect_function_clones():
    extension = "*.func_*\.vec"
    vector_list_a = finder.search_vector_list(values.Project_A, extension, 'function')
    vector_list_c = finder.search_vector_list(values.Project_C, extension, 'function')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    candidate_list_all = detect_candidate_list(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".func_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = None
        # TODO: use name distance as well
        for candidate_path, distance in candidate_list:
            if vector_name_a in candidate_path:
                best_candidate = (candidate_path, distance)
        if not best_candidate:
            for candidate_path, distance in candidate_list:
                if not best_candidate:
                    best_candidate = (candidate_path, distance)
                if distance < best_candidate[1]:
                    best_candidate = (candidate_path, distance)
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".func_")
        vector_source_a = str(vector_source_a).replace(values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        similarity_sore = generator.generate_similarity_score(vector_path_a, candidate_file_path)
        if float(similarity_sore) > 0.4:
            values.IS_IDENTICAL = True
        else:
            values.IS_IDENTICAL = False
        emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        emitter.success("\t\t\tFunction: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        emitter.success("\t\t\tSimilarity: " + str(similarity_sore) + "\n")
        emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
        values.VECTOR_MAP[vector_path_a] = candidate_file_path
    return clone_list


def detect_candidate_list(vector_list_a, vector_list_c, factor):
    if values.DEFAULT_OPERATION_MODE == 0:
        return detect_segment_clone_by_distance(vector_list_a, vector_list_c, factor)
    else:
        return detect_segment_clone_by_similarity(vector_list_a, vector_list_c)


def detect_decl_clones():
    extension = "*.var_*\.vec"
    vector_list_a = finder.search_vector_list(values.Project_A, extension, 'global variable')
    vector_list_c = finder.search_vector_list(values.Project_C, extension, 'global variable')
    clone_list = []
    factor = 2
    UNKNOWN = "#UNKNOWN#"
    if not vector_list_c:
        return []
    candidate_list_all = detect_candidate_list(vector_list_a, vector_list_c, factor)
    for vector_path_a in candidate_list_all:
        candidate_list = candidate_list_all[vector_path_a]
        vector_source_a, vector_name_a = vector_path_a.split(".var_")
        vector_name_a = vector_name_a.replace(".vec", "")
        best_candidate = candidate_list[0]
        candidate_file_path = best_candidate[0]
        candidate_source_path, candidate_name = candidate_file_path.split(".var_")
        vector_source_a = str(vector_source_a).replace(values.Project_A.path, '')
        candidate_source_path = str(candidate_source_path).replace(values.Project_C.path, '')
        candidate_name = candidate_name.replace(".vec", "")
        candidate_distance = best_candidate[1]
        similarity_sore = generator.generate_similarity_score(vector_path_a, candidate_file_path)
        if float(similarity_sore) > 0.4:
            values.IS_IDENTICAL = True
        else:
            values.IS_IDENTICAL = False
        emitter.normal("\t\tPossible match for " + vector_name_a + " in $Pa/" + vector_source_a + ":")
        emitter.success("\t\t\tDeclaration: " + candidate_name + " in $Pc/" + str(candidate_source_path))
        emitter.success("\t\t\tSimilarity: " + str(similarity_sore) + "\n")
        emitter.success("\t\t\tDistance: " + str(candidate_distance) + "\n")
        clone_list.append((vector_path_a, candidate_file_path, None))
        values.VECTOR_MAP[vector_path_a] = candidate_file_path
    return clone_list


def detect_segment_clones():
    struct_clones = list()
    enum_clones = list()
    decl_clones = list()
    function_clones = list()
    if values.IS_STRUCT:
        emitter.sub_sub_title("Finding clone structures in Target")
        struct_clones = detect_struct_clones()
        # print(struct_clones)
    if values.IS_ENUM:
        emitter.sub_sub_title("Finding clone enum in Target")
        enum_clones = detect_enum_clones()
        # print(enum_clones)
    if values.IS_FUNCTION:
        emitter.sub_sub_title("Finding clone functions in Target")
        function_clones = detect_function_clones()
        # print(function_clones)
    if values.IS_TYPEDEC:
        emitter.sub_sub_title("Finding clone variable declaration in Target")
        decl_clones = detect_decl_clones()
        # print(function_clones)
    clone_list = struct_clones + enum_clones + function_clones + decl_clones
    return clone_list


def detect_file_clones(diff_info):
    candidate_list = dict()
    for source_loc in diff_info:
        source_file, start_line = source_loc.split(":")
        if source_file not in candidate_list:
            candidate_list[source_file] = finder.find_clone(source_file)
    if not candidate_list:
        error_exit("CLONE FILE NOT FOUND")
    return candidate_list


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]
