#! /usr/bin/env pythonutf-8 -*-
from app.common import definitions

TOOL_NAME = "IntelliPort"
Project_A = None
Project_B = None
Project_C = None
Project_D = None
Project_E = None

DEBUG = False
DEBUG_DATA = False
IS_BACKPORT = False
IS_FORK = False
IS_LINUX_KERNEL = False


PHASE_SETTING = {
    definitions.PHASE_BUILD: 1,
    definitions.PHASE_DIFF: 1,
    definitions.PHASE_DETECTION: 1,
    definitions.PHASE_SLICING: 1,
    definitions.PHASE_EXTRACTION: 1,
    definitions.PHASE_MAPPING: 1,
    definitions.PHASE_TRANSLATION: 1,
    definitions.PHASE_EVOLUTION: 1,
    definitions.PHASE_WEAVE: 1,
    definitions.PHASE_VERIFY: 1,
    definitions.PHASE_REVERSE: 1,
    definitions.PHASE_EVALUATE: 1,
    definitions.PHASE_COMPARE: 1,
    definitions.PHASE_SUMMARIZE: 1
}

STANDARD_FUNCTION_LIST = list()
STANDARD_MACRO_LIST = list()
STANDARD_DATATYPE_LIST = list()

PROJECT_A_FUNCTION_LIST = ""
PROJECT_B_FUNCTION_LIST = ""
PROJECT_C_FUNCTION_LIST = ""
PROJECT_E_FUNCTION_LIST = ""
DIFF_FUNCTION_LIST = ""
DIFF_LINE_LIST = dict()
DIVERGENT_POINT_LIST = list()
FUNCTION_MAP = ""
MODIFIED_SOURCE_LIST = list()
IS_IDENTICAL = False

# ------------------ Default Values ---------------
DEFAULT_TAG_ID = "test"
DEFAULT_AST_DIFF_SIZE = 1000
DEFAULT_OPERATION_MODE = 0
DEFAULT_CONTEXT_LEVEL = 3
DEFAULT_OUTPUT_FORMAT = "normal"
DEFAULT_SIMILARITY_FACTOR = 0.4


# ------------------ Configuration Values ---------------
CONF_BUG_ID = ""
CONF_PATH_A = ""
CONF_PATH_B = ""
CONF_PATH_C = ""
CONF_PATH_E = ""
CONF_COMMIT_A = None
CONF_COMMIT_B = None
CONF_COMMIT_C = None
CONF_COMMIT_E = None
CONF_EXPLOIT_C = ""
CONF_BUILD_FLAGS_A = ""
CONF_BUILD_FLAGS_C = ""
CONF_CONFIG_COMMAND_A = ""
CONF_CONFIG_COMMAND_C = ""
CONF_BUILD_COMMAND_A = ""
CONF_BUILD_COMMAND_C = ""
CONF_PATH_POC = ""
CONF_EXPLOIT_PREPARE = ""
CONF_ASAN_FLAG = ""
CONF_KLEE_FLAG_A = ""
CONF_KLEE_FLAG_C = ""
FILE_CONFIGURATION = ""
CONF_AST_DIFF_SIZE = ""
CONF_VC = ""
CONF_USE_CACHE = False
CONF_TAG_ID = None
CONF_CONTEXT_LEVEL = -1
CONF_OUTPUT_FORMAT = None

silence_emitter = False
file_list_to_patch = []
diff_transformation_info = dict()
ast_transformation_info = dict()
file_transformation_info = dict()

ast_map = dict()
map_allow_type_list = [
        "DeclRefExpr", "StringLiteral", "VarDecl", "MemberExpr", "Macro", "LabelStmt", "GotoStmt",
        "ParmVarDecl", "RecordDecl", "FieldDecl", "FunctionDecl", "CallExpr"
    ]
original_diff_info = dict()
ported_diff_info = dict()
data_type_map = dict()
current_slice_tuple = None

CONF_FILE_NAME = "crochet.conf"
DIFF_COMMAND = "crochet-diff "

interesting = ["VarDecl", "DeclRefExpr", "ParmVarDecl", "TypedefDecl",
               "FieldDecl", "EnumDecl", "EnumConstantDecl", "RecordDecl"]

segment_map = {"func": ["FunctionDecl", "CXXConstructorDecl", "CXXMethodDecl"], "var": "VarDecl",  "enum": "EnumDecl", "macro": "Macro", "struct": "RecordDecl"}

IS_FUNCTION = False
IS_STRUCT = False
IS_ENUM = False
IS_MACRO = False
IS_TYPEDEF = False
IS_TYPEDEC = False
VECTOR_MAP = dict()
SOURCE_MAP = dict()
map_namespace_global = dict()
map_namespace_local = dict()

FUNCTION_MAP = dict()
FUNCTION_MAP_LOCAL = dict()
FUNCTION_MAP_GLOBAL = dict()
NODE_MAP = dict()

DONOR_REQUIRE_MACRO = False
TARGET_REQUIRE_MACRO = False
PRE_PROCESS_MACRO = ""
DONOR_PRE_PROCESS_MACRO = ""
TARGET_PRE_PROCESS_MACRO = ""

USE_PREPROCESS = False

missing_function_list = dict()
missing_macro_list = dict()
missing_header_list = dict()
missing_data_type_list = dict()
modified_source_list = list()
missing_var_list = dict()

diff_del_only = True

# Function triplets for extraction
function_triplets = []
