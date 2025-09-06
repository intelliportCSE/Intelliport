# -*- coding: utf-8 -*-

''' Main vector generation functions '''

from app.common.utilities import error_exit, execute_command
from app.ast import ast_vector, ast_obj
from app.tools import emitter
from app.common import definitions, values
import json
import os
import io

APP_FORMAT_LLVM = "clang-format -style=LLVM "
APP_AST_DIFF = "crochet-diff"

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

skip_name_list = ["test", "tests", 'thirdparty', 'cmake', 'CMakeFiles', 'empty']


def generate_vector(file_path, f_or_struct, start_line, end_line, is_deckard=True):
    v = ast_vector.Vector(file_path, f_or_struct, start_line, end_line, is_deckard)
    if not v.vector:
        return None
    return v


def ast_dump(file_path, output_path, is_header=True, use_macro=False, use_local=False):
    dump_command = APP_AST_DIFF + " -ast-dump-json "
    if use_macro:
        if values.CONF_PATH_A in file_path or values.CONF_PATH_B in file_path:
            dump_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg") + "  "
        else:
            dump_command += " " + values.TARGET_PRE_PROCESS_MACRO.replace("--extra-arg-c", "--extra-arg") + "  "

    dump_command += file_path
    if file_path[-1] == 'h' or use_local:
        dump_command += " --"
    error_file = definitions.DIRECTORY_OUTPUT + "/errors_AST_dump"
    dump_command += " 2> " + error_file + " > " + output_path
    return_code = execute_command(dump_command)
    emitter.debug("return code:" + str(return_code))
    return return_code


def get_ast_json(file_path, use_macro=False, regenerate=False):
    json_file = file_path + ".AST"
    if not (os.path.exists(json_file) and not values.CONF_USE_CACHE) or regenerate:
        generate_json(file_path, use_macro, regenerate)
    # ast_dump(file_path, json_file, False, use_macro)
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']


def generate_json(file_path, use_macro=False, regenerate=False, use_local=False):
    json_file = file_path + ".AST"
    if not (os.path.exists(json_file) and not values.CONF_USE_CACHE) or regenerate:
        ast_dump(file_path, json_file, False, use_macro, use_local)
    return ast_obj.load_from_file(json_file)


def parse_ast(file_path, use_deckard=True, use_macro=False, use_local=False):
    # Save functions here
    function_lines = list()
    # Save variables for each function d[function] = "typevar namevar; ...;"
    dict_file = dict()

    if any(skip_word in str(file_path).lower() for skip_word in skip_name_list):
        return function_lines, dict_file
    try:
        ast = generate_json(file_path, use_macro, use_local)
    except Exception as exception:
        # print(exception)
        emitter.warning("\t\t[warning] failed parsing AST for file: " + file_path)
        return function_lines, dict_file

    start_line = 0
    end_line = 0
    file_line = file_path.split("/")[-1]

    function_nodes = []
    root = ast[0]
    root.get_node_list("type", "FunctionDecl", function_nodes)
    for node in function_nodes:
        set_struct_nodes = set()
        # Output.yellow(node.file)
        if node.file is not None and file_line == node.file.split("/")[-1]:
            f = node.value.split("(")[0]
            start_line = int(node.line)
            end_line = int(node.line_end)
            function_lines.append((f, start_line, end_line))
            generate_vector(file_path, f, start_line, end_line, use_deckard)
            structural_nodes = []
            for interesting_type in interesting:
                node.get_node_list("type", interesting_type, structural_nodes)
            for struct_node in structural_nodes:
                var = struct_node.value.split("(")
                var_type = var[-1][:-1]
                var = var[0]
                line = var_type + " " + var + ";"
                if f not in dict_file.keys():
                    dict_file[f] = ""
                dict_file[f] = dict_file[f] + line
                set_struct_nodes.add(struct_node.value)

    return function_lines, dict_file


def get_vars(proj, file, dict_file):
    for func in dict_file.keys():
        for line in dict_file[func].split(";"):
            if file in proj.function_list.keys():
                if func in proj.function_list[file].keys():
                    proj.function_list[file][func].variables.append(line)

def generate_ast_script(source_a, source_b, outfile_path, dump_matches=False):
    extra_args = " "
    if dump_matches:
        extra_args = " -dump-matches "
    generate_command = APP_AST_DIFF + " -s=" + values.CONF_AST_DIFF_SIZE + extra_args
    if values.DONOR_REQUIRE_MACRO:
        generate_command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
        if values.CONF_PATH_B in source_b:
            generate_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg-c") + " "
    if values.TARGET_REQUIRE_MACRO:
        if values.CONF_PATH_C in source_b:
            generate_command += " " + values.TARGET_PRE_PROCESS_MACRO + " "
    generate_command += source_a + " " + source_b
    if source_a[-1] == 'h':
        generate_command += " --"
    generate_command += " 2> " + definitions.FILE_AST_DIFF_ERROR
    if dump_matches:
        generate_command += " | grep -P '^Match ' | grep -P '^Match '"
    generate_command += " > " + outfile_path

    try:
        # print(generate_command)
        execute_command(generate_command, False)
    except Exception as exception:
        error_exit(exception, "Unexpected error in generate_ast_script.")


def generate_function_list(project, source_file):
    function_list = dict()
    definition_list = dict()
    try:
        function_list, definition_list = parse_ast(source_file, False)
    except Exception as e:
        error_exit(e, "Error in parse_ast.")

    project.function_list[source_file] = dict()
    for function_name, begin_line, finish_line in function_list:
        if function_name not in project.function_list[source_file]:
            project.function_list[source_file][function_name] = ast_vector.Vector(source_file, function_name, begin_line, finish_line, True)
    get_vars(project, source_file, definition_list)
