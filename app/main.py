#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
from app.tools import emitter, configuration
from app.phases import differencing, detection, slicing
from app.common import definitions, values, utilities

def clean_data():
    temp_dir = definitions.DIRECTORY_TMP
    if os.path.isdir(temp_dir):
        clean_command = "rm -rf " + temp_dir + "/*"
        utilities.execute_command(clean_command)


def create_files():
    definitions.FILE_PROJECT_A = definitions.DIRECTORY_OUTPUT + "/project-A"
    open(definitions.FILE_PROJECT_A, 'a').close()
    definitions.FILE_PROJECT_B = definitions.DIRECTORY_OUTPUT + "/project-B"
    open(definitions.FILE_PROJECT_B, 'a').close()
    definitions.FILE_PROJECT_C = definitions.DIRECTORY_OUTPUT + "/project-C"
    open(definitions.FILE_PROJECT_C, 'a').close()
    definitions.FILE_PROJECT_D = definitions.DIRECTORY_OUTPUT + "/project-D"
    open(definitions.FILE_PROJECT_D, 'a').close()
    definitions.FILE_VAR_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/var-map-store"
    open(definitions.FILE_VAR_MAP_STORE, 'a').close()
    definitions.FILE_DATATYPE_MAP = definitions.DIRECTORY_OUTPUT + "/datatype-map"
    open(definitions.FILE_DATATYPE_MAP, 'a').close()
    definitions.FILE_VEC_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/vec-map-store"
    open(definitions.FILE_VEC_MAP_STORE, 'a').close()
    definitions.FILE_SOURCE_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/source-map-store"
    open(definitions.FILE_SOURCE_MAP_STORE, 'a').close()
    definitions.FILE_MISSING_FUNCTIONS = definitions.DIRECTORY_OUTPUT + "/missing-functions"
    open(definitions.FILE_MISSING_FUNCTIONS, 'a').close()
    definitions.FILE_MISSING_HEADERS = definitions.DIRECTORY_OUTPUT + "/missing-headers"
    open(definitions.FILE_MISSING_HEADERS, 'a').close()
    definitions.FILE_MISSING_MACROS = definitions.DIRECTORY_OUTPUT + "/missing-macros"
    open(definitions.FILE_MISSING_MACROS, 'a').close()
    definitions.FILE_MISSING_TYPES = definitions.DIRECTORY_OUTPUT + "/missing-types"
    open(definitions.FILE_MISSING_TYPES, 'a').close()

    if values.CONF_PATH_E:
        definitions.FILE_PROJECT_E = definitions.DIRECTORY_OUTPUT + "/project-E"
        open(definitions.FILE_PROJECT_E, 'a').close()


def bootstrap(config_file_path):
    emitter.title("Starting " + values.TOOL_NAME + " - Automated Code Transfer")
    emitter.sub_title("Loading Configurations")
    configuration.read_conf_file(config_file_path)
    configuration.update_configuration()
    configuration.print_configuration()
    utilities.clean_files()


def create_directories():
    if not os.path.isdir(definitions.DIRECTORY_OUTPUT_BASE):
        os.makedirs(definitions.DIRECTORY_OUTPUT_BASE)


def run(config_file_path):
    create_directories()

    bootstrap(config_file_path)
    create_files()

    differencing.start()
    detection.start()

    slicing.start()
    
    # Extract function triplets after all slice files are created
    try:
        from app.tools import function_extractor
        function_extractor.process_and_save_function_triplets()
    except ImportError:
        emitter.error("Function extractor not available")
    except Exception as e:
        emitter.error("Error during function triplet extraction: " + str(e))

def main():
    import sys
    
    # Only accept --conf parameter
    if len(sys.argv) != 2:
        emitter.help()
        sys.exit(1)
    
    arg = sys.argv[1]
    if not arg.startswith("--conf="):
        emitter.help()
        sys.exit(1)
    
    config_file_path = arg.replace("--conf=", "").strip()
    if not config_file_path:
        emitter.help()
        sys.exit(1)
    
    try:
        run(config_file_path)
        
        # Optional Gemini patch generation (configured via .env file)
        try:
            emitter.title("Gemini AI Patch Generation")
            from app.tools.gemini_integration import integrate_gemini_patch_generation
            patches_file = integrate_gemini_patch_generation(
                output_dir=definitions.DIRECTORY_OUTPUT
            )
            emitter.sub_title("Gemini patch generation completed")
            emitter.normal("Generated patches saved to: " + patches_file)
        except ImportError:
            emitter.warning("Gemini integration not available. Install python-dotenv and google-genai packages.")
        except ValueError as e:
            emitter.warning("Gemini patch generation skipped: " + str(e))
        except Exception as e:
            emitter.error("Gemini patch generation failed: " + str(e))
        
    except KeyboardInterrupt as e:
        emitter.error("Program Interrupted by User")
    except Exception as e:
        emitter.error("Runtime Error")
        emitter.error(str(e))
    finally:
        # Final running time and exit message
        utilities.restore_slice_source()

