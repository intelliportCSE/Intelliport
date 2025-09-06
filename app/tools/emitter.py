# -*- coding: utf-8 -*-

import sys
import os
from app.common import definitions, values
import textwrap


GREY = '\t\x1b[1;30m'
RED = '\t\x1b[1;31m'
GREEN = '\x1b[1;32m'
YELLOW = '\t\x1b[1;33m'
BLUE = '\t\x1b[1;34m'
ROSE = '\t\x1b[1;35m'
CYAN = '\x1b[1;36m'
WHITE = '\t\x1b[1;37m'

PROG_OUTPUT_COLOR = '\t\x1b[0;30;47m'
STAT_COLOR = '\t\x1b[0;32;47m'
rows, columns = os.popen('stty size', 'r').read().split()


def write(print_message, print_color, new_line=True, prefix=None, indent_level=0):
    if not values.silence_emitter:
        message = "\033[K" + print_color + str(print_message) + '\x1b[0m'
        if prefix:
            prefix = "\033[K" + print_color + str(prefix) + '\x1b[0m'
            len_prefix = ((indent_level+1) * 4) + len(prefix)
            wrapper = textwrap.TextWrapper(initial_indent=prefix, subsequent_indent=' '*len_prefix, width=int(columns))
            message = wrapper.fill(message)
        sys.stdout.write(message)
        if new_line:
            r = "\n"
            sys.stdout.write("\n")
        else:
            r = "\033[K\r"
            sys.stdout.write(r)
        sys.stdout.flush()


def title(title):
    write("\n" + "="*100 + "\n\n\t" + title + "\n" + "="*100+"\n", CYAN)


def sub_title(subtitle):
    write("\n\t" + subtitle + "\n\t" + "_"*90+"\n", CYAN)


def sub_sub_title(sub_title):
    write("\n\t\t" + sub_title + "\n\t\t" + "-"*90+"\n", CYAN)


def command(message):
    if values.DEBUG:
        prefix = "\t\t[command] "
        write(message, ROSE, prefix=prefix, indent_level=2)


def normal(message, jump_line=True):
    write(message, BLUE, jump_line)


def highlight(message, jump_line=True):
    indent_length = message.count("\t")
    prefix = "\t" * indent_length
    message = message.replace("\t", "")
    write(message, WHITE, jump_line, indent_level=indent_length, prefix=prefix)


def information(message, jump_line=True):
    if values.DEBUG_DATA:
        prefix = "\t\t[information] "
        write(message, GREY, prefix=prefix, indent_level=2)


def statistics(message):
    write(message, WHITE)


def error(message):
    emit_message = "\t\t[ERROR] " + message.replace("\n", "")
    write(emit_message, RED)


def success(message):
    write(message, GREEN)


def special(message):
    write(message, ROSE)


def warning(message):
    append_message = message
    if "[warning]" not in message:
        append_message = "\t[warning] " + message
    write(append_message, YELLOW)


def debug(message):
    if values.DEBUG:
        prefix = "\t\t[debug] "
        write(message, GREY, prefix=prefix, indent_level=2)


def data(message, info=None):
    if values.DEBUG_DATA:
        prefix = "\t\t[data] "
        write(message, GREY, prefix=prefix, indent_level=2)
        if info:
            write(info, GREY, prefix=prefix, indent_level=2)

def configuration(setting, value):
    message = "\t[config] " + setting + ": " + str(value)
    write(message, WHITE, True)




def help():
    print("Usage: python3 " + values.TOOL_NAME + ".py --conf=$CONFIGURATION_FILE_PATH")
    print("Example: python3 IntelliPort.py --conf=/home/cseroot/New/T/repair.conf")
    print("")
    print("For Gemini AI patch generation:")
    print("1. Copy .env.example to .env")
    print("2. Add your Gemini API key to .env: GEMINI_API_KEY=your-key-here")
    print("3. Get API key from: https://aistudio.google.com/app/apikey")


