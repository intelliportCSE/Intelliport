# -*- coding: utf-8 -*-

import json

ttype = [None]
label = [None]
typeLabel = ["Root"]
pos = [None]
length = [None]
children = [[]]
char = ""
line = ""
ast = []
index = 0


class AST:
    nodes = []
    attr_names = ['id', 'identifier', 'line', 'line_end', 'col', 'col_end',
                  'begin', 'end', 'value', 'type', 'file', 'parent_id']

    def __init__(self, dict_ast, char=""):
        AST.nodes.append(self)
        self.id = None
        self.identifier = None
        self.line = None
        self.col = None
        self.begin = None
        self.end = None
        self.value = None
        self.type = None
        self.file = None
        self.char = char + "  "
        self.parent_id = None
        self.children = []
        if 'id' in dict_ast.keys():
            self.id = dict_ast['id']
        if 'identifier' in dict_ast.keys():
            self.identifier = dict_ast['identifier']
        if 'start line' in dict_ast.keys():
            self.line = dict_ast['start line']
        if 'end line' in dict_ast.keys():
            self.line_end = dict_ast['end line']
        if 'start column' in dict_ast.keys():
            self.col = dict_ast['start column']
        if 'end column' in dict_ast.keys():
            self.col_end = dict_ast['end column']
        if 'begin' in dict_ast.keys():
            self.begin = dict_ast['begin']
        if 'end' in dict_ast.keys():
            self.end = dict_ast['end']
        if 'value' in dict_ast.keys():
            self.value = dict_ast['value']
        if 'type' in dict_ast.keys():
            self.type = dict_ast['type']
        if 'file' in dict_ast.keys():
            self.file = dict_ast['file']
        if 'parent_id' in dict_ast.keys():
            self.parent_id = dict_ast['parent_id']
        if 'children' in dict_ast.keys():
            for i in dict_ast['children']:
                child = AST(i, char + "    ")
                self.children.append(child)
                child.parent = self

    def __str__(self):
        self.attrs = [self.id, self.identifier, self.line, self.line_end,
                      self.col, self.col_end, self.begin, self.end, self.value,
                      self.type, self.file, self.parent_id]
        s = ""
        for i in range(len(self.attrs)):
            if self.attrs[i] != None:
                s += AST.attr_names[i] + "(" + str(self.attrs[i]) + ") "
        s += "children["
        s += str(len(self.children))
        s += "]"
        return s

    def get_code(self, file):
        with open(file, 'r', encoding='utf8', errors="ignore") as f:
            source_code = "".join(f.readlines())
        return source_code[int(self.begin):int(self.end)]

    def format_value(self, file):
        if "VarDecl" in self.type:
            nvalue = self.get_code(file)
        elif "(anonymous struct)::" in self.value:
            nvalue = self.get_code(file)
        else:
            nvalue = self.value
        return nvalue

    def info(self, file):
        if self.value:
            return self.type + ": " + self.format_value(file)
        return self.type

    def value_calc(self, file):
        if self.value:
            return self.format_value(file)

    def simple_print(self):
        return str(self.type) + "(" + str(self.id) + ")"


def AST_from_file(file):
    global ast

    with open(file, 'r', encoding='utf8', errors="ignore") as ast_file:
        ast = ast_file.readline()
    object_ast = json.loads(ast)
    AST(object_ast['root'])
    ast = [i for i in AST.nodes]
    AST.nodes = []
    return ast
