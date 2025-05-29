current_index = 0  # Track token position

TYPES = ["CT_INT",  "CT_REAL", "CT_STRING", "CT_CHAR"]  # Supported types
SPECIAL_FUNCTIONS = ["put_i", "put_s", "get_i", "put_c", "get_c", "put_d", "get_d"]

# Global semantic state
symbols = []           # Stack of all defined symbols (global + locals)
crtDepth = 0           # Current scope level
crtStruct = None       # Pointer to current struct
crtFunc = None         # Pointer to current function
maxDepth = 0             # Maximum depth of nested scopes

CLS_VAR = "var"
CLS_FUNC = "func"
CLS_STRUCT = "struct"
MEM_GLOBAL = "global"
MEM_ARG = "arg"
MEM_LOCAL = "local"
TB_INT = "int"
TB_DOUBLE = "double"
TB_CHAR = "char"
TB_STRUCT = "struct"
TB_VOID = "void"

class Type:
    def __init__(self, typeBase, nElements=-1, structSymbol=None):
        self.typeBase = typeBase  # "int", "double", "char", "struct", "void"
        self.nElements = nElements
        self.structSymbol = structSymbol  # Only for structs

class Symbol:
    def __init__(self, name, cls, type_, mem, depth):
        self.name = name
        self.cls = cls  # CLS_VAR, CLS_FUNC, CLS_STRUCT
        self.type = type_  # Type object
        self.mem = mem  # MEM_GLOBAL, MEM_LOCAL, MEM_ARG
        self.depth = depth
        self.args = []  # For functions
        self.members = []  # For structs

def findSymbol(name, scope=None, depth=None):
    scope = scope or symbols
    for sym in reversed(scope):
        if sym.name == name and (depth is None or sym.depth == depth):
            return sym
    return None

def addSymbol(name, cls, type_, mem, scope=None):
    scope = scope or symbols
    if any(s.name == name and s.depth == crtDepth for s in scope):
        raise SyntaxError(f"Symbol redefinition: {name}")
    sym = Symbol(name, cls, type_, mem, crtDepth)
    scope.append(sym)
    return sym

def deleteSymbolsAfter(start_index):
    global symbols
    symbols = symbols[:start_index]

def addVar(name, type_):
    global crtFunc, crtStruct
    if crtStruct:
        if findSymbol(name, scope=crtStruct.members):
            raise SyntaxError(f"Struct member redefinition: {name}")
        crtStruct.members.append(Symbol(name, CLS_VAR, type_, None, 1))
    elif crtFunc:
        if any(sym.name == name and sym.depth == crtDepth for sym in symbols):
            print_symbol_table()
            print (f"Current function: {crtFunc.name} at depth {crtDepth}")
            raise SyntaxError(f"Variable redefinition in function: {name}")
        addSymbol(name, CLS_VAR, type_, MEM_LOCAL)
    else:
        if findSymbol(name):
            raise SyntaxError(f"Global variable redefinition: {name}")
        addSymbol(name, CLS_VAR, type_, MEM_GLOBAL)

def print_symbol_table():
    print("\n🔍 SYMBOL TABLE DUMP:")
    print("-" * 60)
    for sym in symbols:
        print(f"Name: {sym.name}")
        print(f"  Class: {sym.cls}")
        print(f"  Type: {sym.type.typeBase}", end='')
        if sym.type.nElements != -1:
            print(f"[{sym.type.nElements}]", end='')
        if sym.type.structSymbol:
            print(f" (struct {sym.type.structSymbol.name})", end='')
        print()
        print(f"  Mem: {sym.mem}")
        print(f"  Depth: {sym.depth}")
        if sym.cls == CLS_FUNC:
            print("  Args:")
            for arg in sym.args:
                print(f"    - {arg.name}: {arg.type.typeBase}")
        if sym.cls == CLS_STRUCT:
            print("  Members:")
            for mem in sym.members:
                print(f"    - {mem.name}: {mem.type.typeBase}")
        print("-" * 60)


# ---------- Token Helpers ----------

def current_token(tokens):
    global current_index
    return tokens[current_index] if current_index < len(tokens) else ("EOF", "EOF", -1)

def consume(tokens, expected_type, expected_value=None):
    global current_index
    if current_index >= len(tokens):
        return False
    token_type, token_value, _ = tokens[current_index]
    if token_type == expected_type and (expected_value is None or token_value == expected_value):
        current_index += 1
        return True
    return False

# ---------- Grammar Parsing Functions ----------
def parse_unit(tokens):
    global current_index
    while current_token(tokens)[0] != "EOF":
        token = current_token(tokens)
        if token[0] == "KEYWORD" and token[1] == "struct":
            if declStruct(tokens):
                continue  # Restart the loop to check all cases
            elif declVar(tokens):
                    continue
            else:
                raise SyntaxError(f"Line {token[2]}: Unexpected token {token}")
        if token[0] == "KEYWORD" and token[1] in ["int", "char", "double", "void"]:
            if declFunc(tokens):  # Check for function declaration
                continue  # Restart the loop
            if declVar(tokens):  # Check for variable declaration
                continue  # Restart the loop
            raise SyntaxError("Invalid declaration")
        else:
            raise SyntaxError(f"Line {token[2]}: Unexpected token {token}")
    if not consume(tokens, "EOF"):
        raise SyntaxError("Expected 'EOF' token at the end of the program")
    print("✅ Program parsed successfully!")

# ---------- declStruct: STRUCT ID LACC declVar* RACC SEMICOLON ----------
def declStruct(tokens):
    global crtStruct, current_index
    clone_index = current_index
    start_index = len(symbols)

    if not consume(tokens, "KEYWORD", "struct"): return False
    if not consume(tokens, "IDENTIFIER"):
        raise SyntaxError("Missing struct name")

    name = tokens[current_index - 1][1]


    if not consume(tokens, "DELIMITER", "{"):
        current_index = clone_index
        return False  # Not a struct definition

    if findSymbol(name):
        print("test")
        raise SyntaxError(f"Symbol redefinition: {name}")

    type_ = Type(TB_STRUCT)
    struct_sym = addSymbol(name, CLS_STRUCT, type_, None)
    crtStruct = struct_sym
    struct_sym.members = []  # Init inner scope for members

    while declVar(tokens): pass

    if not consume(tokens, "DELIMITER", "}"): raise SyntaxError("Expected '}'")
    if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")

    crtStruct = None
    return True


# ---------- declVar: typeBase ID arrayDecl? ( COMMA ID arrayDecl? )* SEMICOLON ----------
def declVar(tokens):
    global crtStruct, crtFunc
    t = parse_type_base(tokens)
    if not t:
        return False

    if not consume(tokens, "IDENTIFIER"):
        raise SyntaxError("Missing variable name")
    name = tokens[current_index - 1][1]

    # Check for array declaration
    if not arrayDecl(tokens):
        t = Type(t.typeBase, -1, t.structSymbol)

    addVar(name, t)

    while consume(tokens, "DELIMITER", ","):
        if not consume(tokens, "IDENTIFIER"):
            raise SyntaxError("Missing variable name after ','")
        name = tokens[current_index - 1][1]
        if not arrayDecl(tokens):
            temp_type = Type(t.typeBase, -1, t.structSymbol)
        else:
            temp_type = t  # With array info
        addVar(name, temp_type)

    if not consume(tokens, "DELIMITER", ";"):
        raise SyntaxError("Expected ';'")
    return True


def parse_type_base(tokens): #  if next token is a type (int | double | char | struct ID): return Type object, else return None
    global current_index
    if consume(tokens, "KEYWORD", "int"):
        return Type(TB_INT)
    if consume(tokens, "KEYWORD", "double"):
        return Type(TB_DOUBLE)
    if consume(tokens, "KEYWORD", "char"):
        return Type(TB_CHAR)
    if consume(tokens, "KEYWORD", "struct"):
        if not consume(tokens, "IDENTIFIER"):
            raise SyntaxError("Expected struct name")
        struct_name = tokens[current_index - 1][1]
        s = findSymbol(struct_name)
        if not s:
            raise SyntaxError(f"Undefined struct: {struct_name}")
        if s.cls != CLS_STRUCT:
            raise SyntaxError(f"{struct_name} is not a struct")
        return Type(TB_STRUCT, -1, s)
    return None


# ---------- typeBase: INT | DOUBLE | CHAR | STRUCT ID ----------
def typeBase(tokens): # returns True if next token is a type (int | double | char | struct ID), else False
    global  current_index
    start_index = current_index
    t = parse_type_base(tokens)
    current_index = start_index  # Restore state
    return t is not None


# ---------- arrayDecl: LBRACKET expr? RBRACKET ----------
def arrayDecl(tokens):
    if not consume(tokens, "DELIMITER", "["): return False
    expr(tokens)  # Optional expression
    if not consume(tokens, "DELIMITER", "]"):
        raise SyntaxError("Expected ']'")
    return True

# ---------- typeName: typeBase arrayDecl? ----------
def typeName(tokens):
    if not typeBase(tokens): return False
    arrayDecl(tokens)
    return True

# ---------- declFunc: ( typeBase MUL? | VOID ) ID ( funcArg ( , funcArg )* )? ) stmCompound ----------
def declFunc(tokens):
    global crtFunc, crtDepth, current_index, maxDepth
    print(f"DeclFunc called {current_index}")
    start_index = current_index

    t = None
    if consume(tokens, "KEYWORD", "void"):
        t = Type(TB_VOID)
    else:
        t = parse_type_base(tokens)
        if not t:
            current_index = start_index
            return False
        if consume(tokens, "OPERATOR", "*"):
            t.nElements = 0
        else:
            t.nElements = -1

    if not consume(tokens, "IDENTIFIER"):
        current_index = start_index
        return False
    name = tokens[current_index - 1][1]

    if not consume(tokens, "DELIMITER", "("):
        current_index = start_index
        return False

    if findSymbol(name):
        raise SyntaxError(f"Symbol redefinition: {name}")

    crtFunc = addSymbol(name, CLS_FUNC, t, None)
    crtFunc.args = []

    # Assign a unique depth for this function
    maxDepth += 1
    crtDepth = maxDepth

    if funcArg(tokens):
        while consume(tokens, "DELIMITER", ","):
            if not funcArg(tokens):
                raise SyntaxError("Invalid function argument")

    if not consume(tokens, "DELIMITER", ")"):
        raise SyntaxError("Expected ')'")

    stmCompound(tokens)
    deleteSymbolsAfter(len(symbols))  # Clean up locals
    crtFunc = None
    return True

# ---------- funcArg: typeBase ID arrayDecl? ----------
def funcArg(tokens):
    t = parse_type_base(tokens)
    if not t:
        return False

    if not consume(tokens, "IDENTIFIER"):
        raise SyntaxError("Expected argument name")
    name = tokens[current_index - 1][1]

    if not arrayDecl(tokens):
        t.nElements = -1

    # Define in global scope for semantic validation
    s = addSymbol(name, CLS_VAR, t, MEM_ARG)
    # Also save to the current function's arg list
    print(f"Adding argument {name} of type {t.typeBase} to function {crtFunc.name} at depth {crtDepth + 1}")
    arg = Symbol(name, CLS_VAR, t, MEM_ARG, crtDepth + 1 )
    crtFunc.args.append(arg)

    return True


# ---------- stmCompound: { (declVar | stm)* } ----------
def stmCompound(tokens):
    global crtDepth
    if not consume(tokens, "DELIMITER", "{"): return False
    crtDepth += 1
    while True:
        if tokens[current_index][1] == "}": break
        if not (declVar(tokens) or stm(tokens)):
            raise SyntaxError(f"Unexpected token {tokens[current_index]} inside compound statement")
    if not consume(tokens, "DELIMITER", "}"): raise SyntaxError("Expected '}'")
    crtDepth -= 1
    return True

# ---------- stm: all statement forms ----------
def stm(tokens):
    print (f"Current token: {tokens[current_index]}")
    if stmCompound(tokens): return True
    if consume(tokens, "KEYWORD", "if"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'if'")
        if not expr(tokens): raise SyntaxError("Expected expression in 'if'")
        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')' after 'if'")
        stm(tokens)
        if consume(tokens, "KEYWORD", "else"):
            stm(tokens)
        return True
    if consume(tokens, "KEYWORD", "while"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'while'")
        if not expr(tokens): raise SyntaxError("Expected expression in 'while'")
        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')' after 'while'")
        stm(tokens)
        return True
    if consume(tokens, "KEYWORD", "for"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'for'")
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')'")
        stm(tokens)
        return True
    if consume(tokens, "KEYWORD", "break"):
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';' after 'break'")
        return True
    if consume(tokens, "KEYWORD", "return"):
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';' after 'return'")
        return True
    expr(tokens)  # optional
    if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
    return True

def expr(tokens):
    return exprAssign(tokens)

def exprAssign(tokens):
    global current_index
    start_index = current_index

    if exprOr(tokens):  # Try left-hand side
        if consume(tokens, "OPERATOR", "="):
            if exprAssign(tokens):
                return True
            else:
                raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid expression after '='")
        return True  # Just an OR-expression, not assignment
    current_index = start_index
    return False
def exprOr(tokens):
    global current_index
    if not exprAnd(tokens):
        return False
    while consume(tokens, "OPERATOR", "||"):
        if not exprAnd(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '||'")
    return True

def exprAnd(tokens):
    global current_index
    if not exprEq(tokens):
        return False
    while consume(tokens, "OPERATOR", "&&"):
        if not exprEq(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '&&'")
    return True

def exprEq(tokens):
    global current_index
    if not exprRel(tokens):
        return False
    while True:
        if consume(tokens, "OPERATOR", "==") or consume(tokens, "OPERATOR", "!="):
            if not exprRel(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after equality operator")
        else:
            break
    return True

def exprRel(tokens):
    global current_index
    if not exprAdd(tokens):
        return False
    while True:
        if consume(tokens, "OPERATOR", "<") or consume(tokens, "OPERATOR", "<=") or \
           consume(tokens, "OPERATOR", ">") or consume(tokens, "OPERATOR", ">="):
            if not exprAdd(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after relational operator")
        else:
            break
    return True

def exprAdd(tokens):
    global current_index
    if not exprMul(tokens):
        return False
    while True:
        if consume(tokens, "OPERATOR", "+") or consume(tokens, "OPERATOR", "-"):
            if not exprMul(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '+' or '-'")
        else:
            break
    return True

def exprMul(tokens):
    global current_index
    if not exprCast(tokens):  # You can later change to exprCast if needed
        return False
    while True:
        if consume(tokens, "OPERATOR", "*") or consume(tokens, "OPERATOR", "/"):
            if not exprPrimary(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '*' or '/'")
        else:
            break
    return True

def exprCast(tokens):
    global current_index
    start_index = current_index

    if consume(tokens, "DELIMITER", "("):
        if typeName(tokens):  # You'll need to implement this
            if consume(tokens, "DELIMITER", ")"):
                if exprCast(tokens):
                    return True
                else:
                    raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid expression after cast")
            else:
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing ')' after type name")
        else:
            current_index = start_index  # Not a type cast — backtrack
    return exprUnary(tokens)

def exprUnary(tokens):
    global current_index
    if consume(tokens, "OPERATOR", "-") or consume(tokens, "OPERATOR", "!"):
        if not exprUnary(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid operand for unary operator")
        return True
    return exprPostfix(tokens)

def exprPostfix(tokens):
    global current_index
    if not exprPrimary(tokens):
        return False

    while True:
        if consume(tokens, "DELIMITER", "["):  # array indexing
            if not expr(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing expression inside []")
            if not consume(tokens, "DELIMITER", "]"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing ']'")
        elif consume(tokens, "OPERATOR", "."):  # struct access
            if not consume(tokens, "IDENTIFIER"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected field name after '.'")
        else:
            break
    return True

def exprPrimary(tokens):
    global current_index
    if consume(tokens, "IDENTIFIER"):
        name = tokens[current_index - 1][1]
        sym = findSymbol(name)
        if consume(tokens, "DELIMITER", "("):  # function call
            if not sym and name not in SPECIAL_FUNCTIONS:
                raise SyntaxError(f"Undeclared variable or function: {name}")
            if expr(tokens):
                while consume(tokens, "DELIMITER", ","):
                    if not expr(tokens):
                        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected argument expression after ','")
            if not consume(tokens, "DELIMITER", ")"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ')' after arguments")
        else:
            if not sym:
                raise SyntaxError(f"Undeclared variable or function: {name}")
        return True
    elif consume(tokens, "CT_INT") or consume(tokens, "CT_REAL") or \
         consume(tokens, "CT_CHAR") or consume(tokens, "CT_STRING"):
        return True
    elif consume(tokens, "DELIMITER", "("):
        if not expr(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression inside parentheses")
        if not consume(tokens, "DELIMITER", ")"):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ')' after expression")
        return True
    return False