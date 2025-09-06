#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from app.common.utilities import execute_command, get_file_extension_list, definitions
from app.ast import ast_generator
from app.tools import mapper, emitter, filter
from app.common import values
from git import Repo


def diff_files(output_diff_file, output_c_diff, output_h_diff,
               output_ext_a, output_ext_b, output_ext,
               project_path_a, project_path_b):
    emitter.normal("\tfinding changed files...")

    extensions = get_file_extension_list(project_path_a, output_ext_a)
    extensions = extensions.union(get_file_extension_list(project_path_b, output_ext_b))
    untrack_file = definitions.FILE_GIT_UNTRACKED_FILES

    if values.IS_LINUX_KERNEL:
        repo = Repo(project_path_b)
        patch_commit = repo.head.commit
        parent_commit = patch_commit.parents[0]
        diff_list = parent_commit.diff(patch_commit)
        file_list = list()
        c_file_list = list()
        h_file_list = list()
        for diff in diff_list:
            file_list.append(diff.a_path)
        for file_path in file_list:
            if file_path[-1] == 'c':
                c_file_list.append(file_path)
            else:
                h_file_list.append(file_path)

        with open(output_c_diff, 'w') as c_diff:
            for path_a in c_file_list:
                if project_path_a not in path_a:
                    path_a = project_path_a + "/" + path_a
                path_b = path_a.replace(project_path_a, project_path_b)
                c_diff.write("Files " + path_a + " and " + path_b + " differ")

        with open(output_h_diff, 'w') as h_diff:
            for path_a in h_file_list:
                if project_path_a not in path_a:
                    path_a = project_path_a + "/" + path_a
                path_b = path_a.replace(project_path_a, project_path_b)
                h_diff.write("Files " + path_a + " and " + path_b + " differ")
        return

    untracked_list_command = "cd " + project_path_a + ";" + "touch " + untrack_file
    if values.CONF_VC == "git":
        untracked_list_command += "git ls-files --others  > " + untrack_file + ";"
        untracked_list_command += "cd " + project_path_b + ";"
        untracked_list_command += "git ls-files --others  >> " + untrack_file
    execute_command(untracked_list_command)

    with open(output_ext, 'w') as exclusions:
        for pattern in extensions:
            exclusions.write(pattern + "\n")

    # TODO: Include cases where a file is added or removed
    diff_command = "diff -ENZBbwqr " + project_path_a + " " + project_path_b
    diff_command += " -X " + output_ext + " | grep -v -f " + untrack_file
    diff_command += " > " + output_diff_file + ";"
    diff_command += "cat " + output_diff_file + "| grep -P '\.cc and ' > " + output_c_diff + ";"
    diff_command += "cat " + output_diff_file + "| grep -P '\.h and ' > " + output_h_diff
    # print(diff_command)
    execute_command(diff_command)


def diff_h_files(diff_file_path, project_path_a, untracked_file_list):
    emitter.normal("\t\textracting changed header files...")
    file_list = list()
    filtered_file_list = list()
    with open(diff_file_path, 'r') as diff_file:
        diff_line = diff_file.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            # ASTGenerator.parse_ast(file_a, project_path_a, is_deckard=True, is_header=True)
            file_list.append((file_a, file_b))
            diff_line = diff_file.readline().strip()

    emitter.normal("\t\theader files:")
    if len(file_list) > 0:
        for h_file in file_list:
            file_a = h_file[0]
            file_a_rel_path = file_a.replace(project_path_a, "")[1:]
            if file_a_rel_path not in untracked_file_list:
                filtered_file_list.append(h_file)
                emitter.normal("\t\t\t" + file_a)
    else:
        emitter.normal("\t\t\t-none-")

    return filtered_file_list


def diff_c_files(diff_file_path, project_path_a, untracked_file_list):
    emitter.normal("\t\textracting changed c/cpp files...")
    file_list = list()
    filtered_file_list = list()
    with open(diff_file_path, 'r') as diff_file:
        diff_line = diff_file.readline().strip()
        while diff_line:
            diff_line = diff_line.split(" ")
            file_a = diff_line[1]
            file_b = diff_line[3]
            file_list.append((file_a, file_b))
            diff_line = diff_file.readline().strip()
    emitter.normal("\t\tsource files:")
    if len(file_list) > 0:
        for c_file in file_list:
            file_a = c_file[0]
            file_a_rel_path = file_a.replace(project_path_a, "")[1:]
            if file_a_rel_path not in untracked_file_list:
                filtered_file_list.append(c_file)
                emitter.normal("\t\t\t" + file_a)
    else:
        emitter.normal("\t\t\t-none-")
    #return filtered_file_list
    return file_list


def diff_line(diff_file_list, output_file):
    diff_info = dict()
    for diff_file in diff_file_list:
        file_a = diff_file[0]
        file_b = diff_file[1]
        diff_command = "diff -ENBZbwr " + file_a + " " + file_b + " > " + output_file
        execute_command(diff_command)
        pertinent_lines_a = []
        pertinent_lines_b = []
        with open(output_file, 'r') as temp_diff_file:
            file_line = temp_diff_file.readline().strip()
            emitter.normal("\t\t\t" + file_a + ":")
            while file_line:
                operation = ""
                # We only want lines starting with a line number
                if 48 <= ord(file_line[0]) <= 57:
                    # add
                    if 'a' in file_line:
                        line_info = file_line.split('a')
                        operation = "insert"
                    # delete
                    elif 'd' in file_line:
                        line_info = file_line.split('d')
                        operation = "delete"
                    # change (delete + add)
                    elif 'c' in file_line:
                        line_info = file_line.split('c')
                        operation = "modify"

                    # range for file_a
                    line_a = line_info[0].split(',')
                    start_a = int(line_a[0])
                    end_a = int(line_a[-1])

                    # range for file_b
                    line_b = line_info[1].split(',')
                    start_b = int(line_b[0])
                    end_b = int(line_b[-1])

                    diff_loc = file_a + ":" + str(start_a)
                    diff_info[diff_loc] = dict()
                    diff_info[diff_loc]['operation'] = operation

                    pertinent_lines_a.append((start_a, end_a))
                    pertinent_lines_b.append((start_b, end_b))

                    if operation == 'insert':
                        diff_info[diff_loc]['new-lines'] = (start_b, end_b)
                        diff_info[diff_loc]['old-lines'] = (start_a, end_a)
                    elif operation == "delete":
                        diff_info[diff_loc]['old-lines'] = (start_a, end_a)
                    elif operation == "modify":
                        diff_info[diff_loc]['old-lines'] = (start_a, end_a)
                        diff_info[diff_loc]['new-lines'] = (start_b, end_b)

                    emitter.normal("\t\t\t\t" + operation + ": " + str(start_a) + "-" + str(end_a))
                file_line = temp_diff_file.readline().strip()

    return diff_info


def get_ast_script(source_a, source_b, script_file_path):
    emitter.normal("\tgenerating AST script")
    ast_generator.generate_ast_script(source_a, source_b, script_file_path)
    with open(script_file_path, "r") as script_file:
        script_lines = script_file.readlines()
        return script_lines


def diff_ast(diff_info, project_path_a, project_path_b, script_file_path):
    source_path_a = ""
    line_number_a = ""
    source_path_b = ""
    ast_script = ""
    ast_map_a = ""
    ast_map_b = ""
    mapping_ba = ""

    grouped_line_info = dict()
    for source_loc in diff_info:
        source_file, start_line = source_loc.split(":")
        diff_line_info = diff_info[source_loc]
        if source_file not in grouped_line_info:
            grouped_line_info[source_file] = list()
        grouped_line_info[source_file].append(diff_line_info)

    for source_path_a in grouped_line_info.keys():
        emitter.sub_sub_title(source_path_a)
        source_path_b = str(source_path_a).replace(project_path_a, project_path_b)
        ast_script = get_ast_script(source_path_a, source_path_b, script_file_path)
        try:
            ast_map_a = ast_generator.get_ast_json(source_path_a)
            ast_map_b = ast_generator.get_ast_json(source_path_b)
            mapping_ba = mapper.map_ast_from_source(source_path_a, source_path_b, script_file_path)
        except Exception as e:
            print(e)
            emitter.warning("\t\twarning: no AST generated")
            del grouped_line_info[source_path_a]
            continue

        diff_loc_list = grouped_line_info[source_path_a]
        for diff_loc_info in diff_loc_list:
            start_a, end_a = diff_loc_info['old-lines']
            diff_loc = source_path_a + ":" + str(start_a)
            emitter.normal("\tline number:" + str(start_a))
            operation = diff_loc_info['operation']
            filtered_ast_script = list()
            if operation == 'insert':
                start_line_b, end_line_b = diff_loc_info['new-lines']
                line_range_b = (start_line_b, end_line_b)
                line_range_a = (-1, -1)
                info_a = (source_path_a, line_range_a, ast_map_a)
                info_b = (source_path_b, line_range_b, ast_map_b)
                filtered_ast_script = filter.filter_ast_script(ast_script,
                                                               info_a,
                                                               info_b,
                                                               mapping_ba
                                                               )
            elif operation == 'modify':
                line_range_a = diff_loc_info['old-lines']
                line_range_b = diff_loc_info['new-lines']
                info_a = (source_path_a, line_range_a, ast_map_a)
                info_b = (source_path_b, line_range_b, ast_map_b)
                filtered_ast_script = filter.filter_ast_script(ast_script,
                                                               info_a,
                                                               info_b,
                                                               mapping_ba
                                                               )
            elif operation == 'delete':
                line_range_a = diff_loc_info['old-lines']
                info_a = (source_path_a, line_range_a, ast_map_a)
                info_b = (source_path_b, None, ast_map_b)
                filtered_ast_script = filter.filter_ast_script(ast_script,
                                                               info_a,
                                                               info_b,
                                                               mapping_ba
                                                               )

            if filtered_ast_script is None:
                del diff_info[diff_loc]
                continue
            diff_info[diff_loc]['ast-script'] = filtered_ast_script
    return diff_info
