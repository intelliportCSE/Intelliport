import os
import shutil
from app.common import definitions, values
from app.tools import emitter
from app.entity import project


def load_standard_list():
    with open(definitions.FILE_STANDARD_FUNCTION_LIST, "r") as list_file:
        values.STANDARD_FUNCTION_LIST = [line[:-1] for line in list_file]
    with open(definitions.FILE_STANDARD_MACRO_LIST, "r") as list_file:
        values.STANDARD_MACRO_LIST = [line[:-1] for line in list_file]
    with open(definitions.FILE_STANDARD_DATATYPE_LIST, "r") as list_file:
        for line in list_file:
            values.STANDARD_DATATYPE_LIST.append(line[:-1])
            values.STANDARD_DATATYPE_LIST.append("const " + line[:-1])
            values.STANDARD_DATATYPE_LIST.append(line[:-1] + " *")


def read_conf_file(config_file_path):
    emitter.normal("reading configuration file")
    if not os.path.exists(config_file_path):
        emitter.error("[NOT FOUND] Configuration file " + config_file_path)
        exit()

    values.FILE_CONFIGURATION = config_file_path
    
    with open(config_file_path, 'r') as conf_file:
        configuration_list = [i.strip() for i in conf_file.readlines()]

    for configuration in configuration_list:
        if definitions.CONF_PATH_A in configuration:
            values.CONF_PATH_A = configuration.replace(definitions.CONF_PATH_A, '')
            if "$HOME$" in values.CONF_PATH_A:
                values.CONF_PATH_A = values.CONF_PATH_A.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_B in configuration:
            values.CONF_PATH_B = configuration.replace(definitions.CONF_PATH_B, '')
            if "$HOME$" in values.CONF_PATH_B:
                values.CONF_PATH_B = values.CONF_PATH_B.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_C in configuration:
            values.CONF_PATH_C = configuration.replace(definitions.CONF_PATH_C, '')
            if "$HOME$" in values.CONF_PATH_C:
                values.CONF_PATH_C = values.CONF_PATH_C.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if values.CONF_PATH_C[-1] == "/":
                values.CONF_PATH_C = values.CONF_PATH_C[:-1]
        elif definitions.CONF_PATH_E in configuration:
            values.CONF_PATH_E = configuration.replace(definitions.CONF_PATH_E, '')
            if "$HOME$" in values.CONF_PATH_E:
                values.CONF_PATH_E = values.CONF_PATH_E.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if values.CONF_PATH_E[-1] == "/":
                values.CONF_PATH_E = values.CONF_PATH_E[:-1]

        elif definitions.CONF_COMMIT_A in configuration:
            values.CONF_COMMIT_A = configuration.replace(definitions.CONF_COMMIT_A, '')
        elif definitions.CONF_COMMIT_B in configuration:
            values.CONF_COMMIT_B = configuration.replace(definitions.CONF_COMMIT_B, '')
        elif definitions.CONF_COMMIT_C in configuration:
            values.CONF_COMMIT_C = configuration.replace(definitions.CONF_COMMIT_C, '')
        elif definitions.CONF_COMMIT_E in configuration:
            values.CONF_COMMIT_E = configuration.replace(definitions.CONF_COMMIT_E, '')
        elif definitions.CONF_TAG_ID in configuration:
            values.CONF_TAG_ID = configuration.replace(definitions.CONF_TAG_ID, "").strip().replace("\n", "")
        elif definitions.CONF_PATH_POC in configuration:
            values.CONF_PATH_POC = configuration.replace(definitions.CONF_PATH_POC, '')
            if "$HOME$" in values.CONF_PATH_POC:
                values.CONF_PATH_POC = values.CONF_PATH_POC.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_FLAGS_A in configuration:
            values.CONF_BUILD_FLAGS_A = configuration.replace(definitions.CONF_FLAGS_A, '')
        elif definitions.CONF_FLAGS_C in configuration:
            values.CONF_BUILD_FLAGS_C = configuration.replace(definitions.CONF_FLAGS_C, '')
        elif definitions.CONF_CONFIG_COMMAND_A in configuration:
            values.CONF_CONFIG_COMMAND_A = configuration.replace(definitions.CONF_CONFIG_COMMAND_A, '')
        elif definitions.CONF_CONFIG_COMMAND_C in configuration:
            values.CONF_CONFIG_COMMAND_C = configuration.replace(definitions.CONF_CONFIG_COMMAND_C, '')
        elif definitions.CONF_BUILD_COMMAND_A in configuration:
            values.CONF_BUILD_COMMAND_A = configuration.replace(definitions.CONF_BUILD_COMMAND_A, '')
        elif definitions.CONF_BUILD_COMMAND_C in configuration:
            values.CONF_BUILD_COMMAND_C = configuration.replace(definitions.CONF_BUILD_COMMAND_C, '')
        elif definitions.CONF_ASAN_FLAG in configuration:
            values.CONF_ASAN_FLAG = configuration.replace(definitions.CONF_ASAN_FLAG, '')
        elif definitions.CONF_DIFF_SIZE in configuration:
            values.CONF_AST_DIFF_SIZE = configuration.replace(definitions.CONF_DIFF_SIZE, '')
        elif definitions.CONF_EXPLOIT_C in configuration:
            values.CONF_EXPLOIT_C = configuration.replace(definitions.CONF_EXPLOIT_C, '')
        elif definitions.CONF_VC in configuration:
            values.CONF_VC = configuration.replace(definitions.CONF_VC, '')
        elif definitions.CONF_CONTEXT_LEVEL in configuration:
            values.CONF_CONTEXT_LEVEL = int(configuration.replace(definitions.CONF_CONTEXT_LEVEL, ""))
        elif definitions.CONF_LINUX_KERNEL in configuration:
            value = configuration.replace(definitions.CONF_LINUX_KERNEL, '')
            if "true" in value:
                values.IS_LINUX_KERNEL = True
            else:
                values.IS_LINUX_KERNEL = False
        elif definitions.CONF_BACKPORT in configuration:
            value = configuration.replace(definitions.CONF_BACKPORT, '')
            if "true" in value:
                values.IS_BACKPORT = True
            else:
                values.IS_BACKPORT = False





def print_configuration():
    emitter.configuration("output dir", definitions.DIRECTORY_OUTPUT)
    emitter.configuration("config file", values.FILE_CONFIGURATION)


def update_configuration():
    emitter.normal("updating configuration values")
    # create log files and other directories
    if values.CONF_TAG_ID:
        values.DEFAULT_TAG_ID = values.CONF_TAG_ID
    else:
        values.DEFAULT_TAG_ID = "test"
    
    dir_name = values.DEFAULT_TAG_ID

    definitions.DIRECTORY_OUTPUT = definitions.DIRECTORY_OUTPUT_BASE + "/" + dir_name
    definitions.DIRECTORY_TMP = definitions.DIRECTORY_OUTPUT + "/tmp"

    if not os.path.isdir(definitions.DIRECTORY_OUTPUT):
        os.mkdir(definitions.DIRECTORY_OUTPUT)

    if not os.path.isdir(definitions.DIRECTORY_TMP):
        os.makedirs(definitions.DIRECTORY_TMP)

    if values.CONF_CONTEXT_LEVEL > -1:
        values.DEFAULT_CONTEXT_LEVEL = values.CONF_CONTEXT_LEVEL
        
    patch_dir = values.CONF_PATH_C + "-patch"
    if os.path.isdir(patch_dir):
        if definitions.DIRECTORY_TESTS in patch_dir:
            shutil.rmtree(patch_dir)
    if not os.path.isdir(patch_dir):
        shutil.copytree(values.CONF_PATH_C, values.CONF_PATH_C + "-patch")

    input_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    output_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-output"
    if not os.path.isdir(input_dir):
        os.makedirs(input_dir)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    values.Project_A = project.Project(values.CONF_PATH_A, "Pa")
    values.Project_B = project.Project(values.CONF_PATH_B, "Pb")
    values.Project_C = project.Project(values.CONF_PATH_C, "Pc")
    values.Project_D = project.Project(values.CONF_PATH_C + "-patch", "Pd")
    if values.CONF_PATH_E:
        values.Project_E = project.Project(values.CONF_PATH_E, "Pe")

    load_standard_list()

    definitions.FILE_AST_SCRIPT = definitions.DIRECTORY_TMP + "/ast-script"
    definitions.FILE_TEMP_DIFF = definitions.DIRECTORY_TMP + "/temp_diff"
    definitions.FILE_AST_MAP = definitions.DIRECTORY_TMP + "/ast-map"
    definitions.FILE_AST_DIFF_ERROR = definitions.DIRECTORY_TMP + "/errors_ast_diff"
    definitions.FILE_PARTIAL_PATCH = definitions.DIRECTORY_TMP + "/gen-patch"
    definitions.FILE_EXCLUDED_EXTENSIONS = definitions.DIRECTORY_TMP + "/excluded-extensions"
    definitions.FILE_EXCLUDED_EXTENSIONS_A = definitions.DIRECTORY_TMP + "/excluded-extensions-a"
    definitions.FILE_EXCLUDED_EXTENSIONS_B = definitions.DIRECTORY_TMP + "/excluded-extensions-b"
    definitions.FILE_GIT_UNTRACKED_FILES = definitions.DIRECTORY_TMP + "/untracked-list"
    definitions.FILE_DIFF_C = definitions.DIRECTORY_TMP + "/diff_C"
    definitions.FILE_DIFF_H = definitions.DIRECTORY_TMP + "/diff_H"
    definitions.FILE_DIFF_ALL = definitions.DIRECTORY_TMP + "/diff_all"
    definitions.FILE_FIND_RESULT = definitions.DIRECTORY_TMP + "/find_tmp"
    definitions.FILE_TEMP_TRANSFORM = definitions.DIRECTORY_TMP + "/temp-transform"



