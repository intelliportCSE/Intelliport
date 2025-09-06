#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os


# ------------------- Directories --------------------

DIRECTORY_MAIN = "/".join(os.path.realpath(__file__).split("/")[:-3])
DIRECTORY_OUTPUT_BASE = DIRECTORY_MAIN + "/output"
DIRECTORY_OUTPUT = ""
DIRECTORY_TMP = ""
DIRECTORY_BACKUP = DIRECTORY_MAIN + "/backup"
DIRECTORY_TESTS = DIRECTORY_MAIN + "/tests"
DIRECTORY_VECTORS_A = DIRECTORY_OUTPUT + "/vectors-a"
DIRECTORY_VECTORS_B = DIRECTORY_OUTPUT + "/vectors-b"
DIRECTORY_VECTORS_C = DIRECTORY_OUTPUT + "/vectors-c"
DIRECTORY_TOOLS = DIRECTORY_MAIN + "/third-party"
DIRECTORY_DATA = DIRECTORY_MAIN + "/data"

# ------------------- Files --------------------

FILE_ERROR_LOG = DIRECTORY_MAIN +  "/log-error"
FILE_STANDARD_FUNCTION_LIST = DIRECTORY_DATA + "/standard-function-list"
FILE_STANDARD_MACRO_LIST = DIRECTORY_DATA + "/standard-macro-list"
FILE_STANDARD_DATATYPE_LIST = DIRECTORY_DATA + "/standard-data-type-list"

FILE_AST_SCRIPT = DIRECTORY_TMP + "/ast-script"
FILE_TEMP_DIFF = DIRECTORY_TMP + "/temp_diff"
FILE_AST_MAP = DIRECTORY_TMP + "/ast-map"
FILE_AST_DIFF_ERROR = DIRECTORY_TMP + "/errors_ast_diff"
FILE_PARTIAL_PATCH = DIRECTORY_TMP + "/gen-patch"
FILE_EXCLUDED_EXTENSIONS = DIRECTORY_TMP + "/excluded-extensions"
FILE_EXCLUDED_EXTENSIONS_A = DIRECTORY_TMP + "/excluded-extensions-a"
FILE_EXCLUDED_EXTENSIONS_B = DIRECTORY_TMP + "/excluded-extensions-b"
FILE_GIT_UNTRACKED_FILES = DIRECTORY_TMP + "/untracked-list"
FILE_DIFF_C = DIRECTORY_TMP + "/diff_C"
FILE_DIFF_H = DIRECTORY_TMP + "/diff_H"
FILE_DIFF_ALL = DIRECTORY_TMP + "/diff_all"
FILE_FIND_RESULT = DIRECTORY_TMP + "/find_tmp"
FILE_TEMP_TRANSFORM = DIRECTORY_TMP + "/temp-transform"

FILE_DIFF_INFO = ""
FILE_ORIG_DIFF_INFO = ""
FILE_PORT_DIFF_INFO = ""
FILE_TRANSPLANT_DIFF_INFO = ""
FILE_ORIG_DIFF = ""
FILE_PORT_DIFF = ""
FILE_TRANSPLANT_DIFF = ""
FILE_CLONE_INFO = ""
FILE_LIST_PATCH_FILES = ""
FILE_VECTOR_MAP = ""
FILE_SOURCE_MAP = ""
FILE_DATATYPE_MAP = ""
FILE_NAMESPACE_MAP_LOCAL = ""
FILE_NAMESPACE_MAP_GLOBAL = ""
FILE_SCRIPT_INFO = ""
FILE_MACRO_DEF = ""
FILE_FUNCTION_TRIPLETS = ""

FILE_AST_MAP_LOCAL = ""
FILE_AST_MAP_GLOBAL = ""

FILE_TRANSLATED_SCRIPT_INFO = ""
FILE_COMPARISON_RESULT = ""
FILE_TEMP_FIX = ""

FILE_PROJECT = ""
FILE_PROJECT_A = ""
FILE_PROJECT_B = ""
FILE_PROJECT_C = ""
FILE_PROJECT_D = ""
FILE_PROJECT_E = ""
FILE_VAR_MAP_STORE = ""
FILE_VEC_MAP_STORE = ""
FILE_SOURCE_MAP_STORE = ""
FILE_MISSING_FUNCTIONS = ""
FILE_MISSING_MACROS = ""
FILE_MISSING_HEADERS = ""
FILE_MISSING_TYPES = ""
FILE_SEGMENT_STATE = ""
FILE_ORIG_N = ""
FILE_PORT_N = ""
FILE_TRANS_N = ""

# ------------------- Configuration --------------------

CONF_PATH_A = "path_a:"
CONF_PATH_B = "path_b:"
CONF_PATH_C = "path_c:"
CONF_PATH_E = "path_e:"
CONF_COMMIT_A = "commit_a:"
CONF_COMMIT_B = "commit_b:"
CONF_COMMIT_C = "commit_c:"
CONF_COMMIT_E = "commit_e:"
CONF_PATH_POC = "path_poc:"
CONF_EXPLOIT_A = "exploit_command_a:"
CONF_CONFIG_COMMAND_A = "config_command_a:"
CONF_BUILD_COMMAND_A = "build_command_a:"
CONF_EXPLOIT_C = "exploit_command_c:"
CONF_CONFIG_COMMAND_C = "config_command_c:"
CONF_BUILD_COMMAND_C = "build_command_c:"
CONF_FLAGS_A = "build_flags_a:"
CONF_FLAGS_C = "build_flags_c:"
CONF_ASAN_FLAG = "asan_flag:"
CONF_KLEE_FLAGS_A = "klee_flags_a:"
CONF_KLEE_FLAGS_C = "klee_flags_c:"
CONF_DIFF_SIZE = "diff_size:"
CONF_VC = "version-control:"
CONF_LINUX_KERNEL = "linux-kernel:"
CONF_BACKPORT = "backport:"
CONF_CONTEXT_LEVEL = "context_level:"
CONF_TAG_ID = "tag_id:"


# ----------------- KEY DEFINITIONS -------------------

KEY_DURATION_TOTAL = 'run-time'
KEY_DURATION_INITIALIZATION = 'initialization'
KEY_DURATION_BUILD_ANALYSIS = "build-process"
KEY_DURATION_DIFF_ANALYSIS = 'diff-analysis'
KEY_DURATION_CLONE_ANALYSIS = "clone-analysis"
KEY_DURATION_SLICE = "slicing-process"
KEY_DURATION_EXTRACTION = "patch-extraction"
KEY_DURATION_MAP_GENERATION = "map-generation"
KEY_DURATION_TRANSLATION = 'translation'
KEY_DURATION_EVOLUTION = "evolution"
KEY_DURATION_TRANSPLANTATION = "transplantation"
KEY_DURATION_VERIFICATION = 'verification'
KEY_DURATION_REVERSE = "reverse"
KEY_DURATION_EVALUATION = 'evaluation'
KEY_DURATION_SUMMARIZATION = "summarize-analysis"
KEY_DURATION_COMPARISON = "comparison-analysis"


# ---------------- PHASES ---------------------------
PHASE_BUILD = "build"
PHASE_DIFF = "diff"
PHASE_DETECTION = "detect"
PHASE_SLICING = "slice"
PHASE_EXTRACTION = "extract"
PHASE_MAPPING = "map"
PHASE_TRANSLATION = "translate"
PHASE_EVOLUTION = "evolve"
PHASE_WEAVE = "weave"
PHASE_VERIFY = "verify"
PHASE_REVERSE = "reverse"
PHASE_EVALUATE = "eval"
PHASE_COMPARE = "compare"
PHASE_SUMMARIZE = "summary"




# ----------------- TOOLS --------------------------------
TOOL_VECGEN = "third-party/deckard/cvecgen_fail "
TOOL_VECGEN_ORIG = "third-party/deckard/cvecgen "

APP_AST_DIFF = "crochet-diff"
PATCH_COMMAND = "crochet-patch"
LINUX_PATCH_COMMAND = "patch"
PATCH_SIZE = "1000"
DIFF_COMMAND = "crochet-diff "
LINUX_DIFF_COMMAND = "diff "
DIFF_SIZE = "1000"
SYNTAX_CHECK_COMMAND = "clang-check "
STYLE_FORMAT_COMMAND = "clang-format -style=LLVM "

crash_word_list = ["abort", "core dumped", "crashed", "exception", "dumped core"]
error_word_list = ["runtime error", "buffer-overflow", "unsigned integer overflow"]


UPDATEMOVE = "UpdateMove"
UPDATE = "Update"
MOVE = "Move"
INSERT = "Insert"
DELETE = "Delete"
MATCH = "Match"
REPLACE = "Replace"
TO = " to "
AT = " at "
INTO = " into "
AND = "and"
WITH = " with "
