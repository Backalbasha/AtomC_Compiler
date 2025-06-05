current_index = 0  # Track token position

TYPES = ["CT_INT", "CT_REAL", "CT_STRING", "CT_CHAR"]  # Supported types
SPECIAL_FUNCTIONS = ["put_i", "put_s", "get_i", "put_c", "get_c", "put_d", "get_d", "seconds"]

# Global semantic state
symbols = []  # Stack of all defined symbols (global + locals)
crtDepth = 0  # Current scope level
crtStruct = None  # Pointer to current struct
crtFunc = None  # Pointer to current function
maxDepth = 0  # Maximum depth of nested scopes

CLS_VAR = "var"
CLS_FUNC = "func"
CLS_EXTFUNC = "extfunc"
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
        self.nElements = nElements  # -1 for scalar, 0 for array without size, >0 for sized array
        self.structSymbol = structSymbol  # Only for structs


class CtVal:
    def __init__(self):
        self.i = 0  # int, char
        self.d = 0.0  # double
        self.str = ""  # char[]


class RetVal:
    def __init__(self):
        self.type = Type(TB_INT)  # type of the result
        self.isLVal = False  # if it is a LVal
        self.isCtVal = False  # if it is a constant value
        self.ctVal = CtVal()  # the constant value


class Symbol:
    def __init__(self, name, cls, type_, mem, depth):
        self.name = name
        self.cls = cls  # CLS_VAR, CLS_FUNC, CLS_STRUCT, CLS_EXTFUNC
        self.type = type_  # Type object
        self.mem = mem  # MEM_GLOBAL, MEM_LOCAL, MEM_ARG
        self.depth = depth
        self.args = []  # For functions
        self.members = []  # For structs


def createType(typeBase, nElements=-1, structSymbol=None):
    """Create a new Type object"""
    return Type(typeBase, nElements, structSymbol)


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
    if (mem == MEM_GLOBAL):
        sym = Symbol(name, cls, type_, mem, 0)  # Global symbols have depth 0
    else:
        sym = Symbol(name, cls, type_, mem, crtDepth)
    scope.append(sym)
    return sym


def addExtFunc(name, type_):
    """Add external/predefined function"""
    s = addSymbol(name, CLS_EXTFUNC, type_, None)
    s.args = []
    return s


def addFuncArg(func, name, type_):
    """Add argument to function"""
    arg = Symbol(name, CLS_VAR, type_, MEM_ARG, 1)
    func.args.append(arg)
    return arg


def addExtFuncs():
    """Add predefined functions to symbol table"""
    # void put_s(char s[])
    s = addExtFunc("put_s", createType(TB_VOID))
    addFuncArg(s, "s", createType(TB_CHAR, 0))

    # void get_s(char s[])
    s = addExtFunc("get_s", createType(TB_VOID))
    addFuncArg(s, "s", createType(TB_CHAR, 0))

    # void put_i(int i)
    s = addExtFunc("put_i", createType(TB_VOID))
    addFuncArg(s, "i", createType(TB_INT))

    # int get_i()
    s = addExtFunc("get_i", createType(TB_INT))

    # void put_d(double d)
    s = addExtFunc("put_d", createType(TB_VOID))
    addFuncArg(s, "d", createType(TB_DOUBLE))

    # double get_d()
    s = addExtFunc("get_d", createType(TB_DOUBLE))

    # void put_c(char c)
    s = addExtFunc("put_c", createType(TB_VOID))
    addFuncArg(s, "c", createType(TB_CHAR))

    # char get_c()
    s = addExtFunc("get_c", createType(TB_CHAR))

    # double seconds()
    s = addExtFunc("seconds", createType(TB_DOUBLE))


def cast(dst, src):
    """Type casting function - checks if src can be converted to dst"""
    # Arrays can only be converted to same type arrays
    if src.nElements > -1:
        if dst.nElements > -1:
            if src.typeBase != dst.typeBase:
                raise SyntaxError("an array cannot be converted to an array of another type")
        else:
            raise SyntaxError("an array cannot be converted to a non-array")
    else:
        if dst.nElements > -1:
            raise SyntaxError("a non-array cannot be converted to an array")

    # Type conversion rules
    if src.typeBase in [TB_CHAR, TB_INT, TB_DOUBLE]:
        if dst.typeBase in [TB_CHAR, TB_INT, TB_DOUBLE]:
            return  # Arithmetic types can convert to each other

    if src.typeBase == TB_STRUCT:
        if dst.typeBase == TB_STRUCT:
            if src.structSymbol != dst.structSymbol:
                raise SyntaxError("a structure cannot be converted to another one")
            return

    raise SyntaxError("incompatible types")


def getArithType(s1, s2):
    """Get the arithmetic result type of two types"""
    # Both must be arithmetic types
    if s1.typeBase not in [TB_CHAR, TB_INT, TB_DOUBLE] or s2.typeBase not in [TB_CHAR, TB_INT, TB_DOUBLE]:
        raise SyntaxError("non-arithmetic types in arithmetic operation")

    # Promotion rules: double > int > char
    if s1.typeBase == TB_DOUBLE or s2.typeBase == TB_DOUBLE:
        return createType(TB_DOUBLE)
    elif s1.typeBase == TB_INT or s2.typeBase == TB_INT:
        return createType(TB_INT)
    else:
        return createType(TB_CHAR)


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
            print(f"Current function: {crtFunc.name} at depth {crtDepth}")
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
        if sym.cls in [CLS_FUNC, CLS_EXTFUNC]:
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
    # Add predefined functions
    addExtFuncs()

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
        raise SyntaxError(f"Symbol redefinition: {name}")

    type_ = Type(TB_STRUCT)
    struct_sym = addSymbol(name, CLS_STRUCT, type_, None)
    type_.structSymbol = struct_sym  # Set the struct symbol reference
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
    array_info = arrayDecl(tokens)
    if array_info is not None:
        t.nElements = array_info
    else:
        t.nElements = -1

    addVar(name, t)

    while consume(tokens, "DELIMITER", ","):
        if not consume(tokens, "IDENTIFIER"):
            raise SyntaxError("Missing variable name after ','")
        name = tokens[current_index - 1][1]

        # Create new type for each variable
        temp_type = Type(t.typeBase, -1, t.structSymbol)
        array_info = arrayDecl(tokens)
        if array_info is not None:
            temp_type.nElements = array_info

        addVar(name, temp_type)

    if not consume(tokens, "DELIMITER", ";"):
        raise SyntaxError("Expected ';'")
    return True


def parse_type_base(
        tokens):  # if next token is a type (int | double | char | struct ID): return Type object, else return None
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
def typeBase(tokens):  # returns True if next token is a type (int | double | char | struct ID), else False
    global current_index
    start_index = current_index
    t = parse_type_base(tokens)
    current_index = start_index  # Restore state
    return t is not None


# ---------- arrayDecl: LBRACKET expr? RBRACKET ----------
def arrayDecl(tokens):
    global current_index
    if not consume(tokens, "DELIMITER", "["):
        return None

    # Try to parse a constant expression for the array size
    size = parseConstExpr(tokens)
    if size is not None:
        if not isinstance(size, int) or size <= 0:
            raise SyntaxError("Array size must be a positive constant")
    else:
        size = 0  # Array without given size

    if not consume(tokens, "DELIMITER", "]"):
        raise SyntaxError("Expected ']'")
    return size

def parseConstExpr(tokens):
    global current_index
    start_index = current_index
    expr_str = ""
    paren_count = 0
    while current_index < len(tokens):
        token_type, token_value, _ = tokens[current_index]
        if token_type == "DELIMITER" and token_value == "]" and paren_count == 0:
            break
        if token_type == "DELIMITER" and token_value == "(":
            paren_count += 1
        if token_type == "DELIMITER" and token_value == ")":
            paren_count -= 1
        if token_type == "CT_INT":
            expr_str += token_value
        elif token_type == "OPERATOR" and token_value in "+-*/%":
            expr_str += token_value
        elif token_type == "DELIMITER" and token_value in "()":
            expr_str += token_value
        else:
            break
        current_index += 1
    if not expr_str:
        current_index = start_index
        return None
    try:
        # Evaluate the expression safely
        value = eval(expr_str, {"__builtins__": None}, {})
        return int(value)
    except Exception:
        raise SyntaxError("Invalid constant expression for array size")


# ---------- typeName: typeBase arrayDecl? ----------
def typeName(tokens):
    t = parse_type_base(tokens)
    if not t:
        return None

    array_info = arrayDecl(tokens)
    if array_info is not None:
        t.nElements = array_info

    return t


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

    array_info = arrayDecl(tokens)
    if array_info is not None:
        t.nElements = array_info

    # Define in global scope for semantic validation
    s = addSymbol(name, CLS_VAR, t, MEM_ARG)
    # Also save to the current function's arg list
    print(f"Adding argument {name} of type {t.typeBase} to function {crtFunc.name} at depth {crtDepth}")
    arg = Symbol(name, CLS_VAR, t, MEM_ARG, crtDepth)
    crtFunc.args.append(arg)

    return True


# ---------- stmCompound: { (declVar | stm)* } ----------
def stmCompound(tokens):
    global crtDepth
    if not consume(tokens, "DELIMITER", "{"): return False

    while True:
        if tokens[current_index][1] == "}": break
        if not (declVar(tokens) or stm(tokens)):
            raise SyntaxError(f"Unexpected token {tokens[current_index]} inside compound statement")
    if not consume(tokens, "DELIMITER", "}"): raise SyntaxError("Expected '}'")
    return True


# ---------- stm: all statement forms ----------
def stm(tokens):
    global expr_return_value
    print(f"Current token: {tokens[current_index]}")
    if stmCompound(tokens): return True

    if consume(tokens, "KEYWORD", "if"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'if'")
        if not expr(tokens): raise SyntaxError("Expected expression in 'if'")

        # Check if struct in logical test
        if expr_return_value.type.typeBase == TB_STRUCT:
            print (f"Line {tokens[current_index][2]}: {expr_return_value.type.typeBase}")
            print (current_token(tokens))
            raise SyntaxError("a structure cannot be logically tested")

        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')' after 'if'")
        stm(tokens)
        if consume(tokens, "KEYWORD", "else"):
            stm(tokens)
        return True

    if consume(tokens, "KEYWORD", "while"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'while'")
        if not expr(tokens): raise SyntaxError("Expected expression in 'while'")

        # Check if struct in logical test
        if expr_return_value.type.typeBase == TB_STRUCT:
            raise SyntaxError("a structure cannot be logically tested")

        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')' after 'while'")
        stm(tokens)
        return True

    if consume(tokens, "KEYWORD", "for"):
        if not consume(tokens, "DELIMITER", "("): raise SyntaxError("Expected '(' after 'for'")
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")

        if expr(tokens):  # optional condition
            if expr_return_value.type.typeBase == TB_STRUCT:
                raise SyntaxError("a structure cannot be logically tested")

        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
        expr(tokens)  # optional
        if not consume(tokens, "DELIMITER", ")"): raise SyntaxError("Expected ')'")
        stm(tokens)
        return True

    if consume(tokens, "KEYWORD", "break"):
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';' after 'break'")
        return True

    if consume(tokens, "KEYWORD", "return"):
        if expr(tokens):  # optional return value
            if crtFunc.type.typeBase == TB_VOID:
                raise SyntaxError("a void function cannot return a value")
            cast(crtFunc.type, expr_return_value.type)
        if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';' after 'return'")
        return True

    expr(tokens)  # optional
    if not consume(tokens, "DELIMITER", ";"):
        print(f"Line {tokens[current_index][2]}: {tokens[current_index]}")
        raise SyntaxError("Expected ';'")
    return True


# Global variable to store expression return value
expr_return_value = RetVal()


def expr(tokens):
    global expr_return_value
    result = exprAssign(tokens)
    return result


def exprAssign(tokens):
    global current_index, expr_return_value
    start_index = current_index

    if exprOr(tokens):  # Try left-hand side
        rv1 = RetVal()
        rv1.type = expr_return_value.type
        rv1.isLVal = expr_return_value.isLVal
        rv1.isCtVal = expr_return_value.isCtVal
        rv1.ctVal = expr_return_value.ctVal

        if consume(tokens, "OPERATOR", "="):
            if not rv1.isLVal:
                raise SyntaxError("cannot assign to a non-lval")

            if exprAssign(tokens):
                rv2 = expr_return_value

                # Check array assignment
                if rv1.type.nElements > -1 or rv2.type.nElements > -1:
                    raise SyntaxError("the arrays cannot be assigned")

                # Check type compatibility
                cast(rv1.type, rv2.type)

                # Update return value
                expr_return_value.type = rv1.type
                expr_return_value.isLVal = False
                expr_return_value.isCtVal = False
                return True
            else:
                raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid expression after '='")
        else:
            # Restore the original return value
            expr_return_value = rv1
        return True  # Just an OR-expression, not assignment
    current_index = start_index
    return False


def exprOr(tokens):
    global current_index, expr_return_value
    if not exprAnd(tokens):
        return False

    while consume(tokens, "OPERATOR", "||"):
        rv1 = expr_return_value
        if not exprAnd(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '||'")
        rv2 = expr_return_value

        # Check struct in logical operation
        if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
            raise SyntaxError("a structure cannot be logically tested")

        # Result is int
        expr_return_value.type = createType(TB_INT)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = False
    return True


def exprAnd(tokens):
    global current_index, expr_return_value
    if not exprEq(tokens):
        return False

    while consume(tokens, "OPERATOR", "&&"):
        rv1 = expr_return_value
        if not exprEq(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '&&'")
        rv2 = expr_return_value

        # Check struct in logical operation
        if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
            raise SyntaxError("a structure cannot be logically tested")

        # Result is int
        expr_return_value.type = createType(TB_INT)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = False
    return True


def exprEq(tokens):
    global current_index, expr_return_value
    if not exprRel(tokens):
        return False

    while True:
        if consume(tokens, "OPERATOR", "==") or consume(tokens, "OPERATOR", "!="):
            rv1 = expr_return_value
            if not exprRel(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after equality operator")
            rv2 = expr_return_value

            # Check struct comparison
            if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
                raise SyntaxError("a structure cannot be compared")

            # Result is int
            expr_return_value.type = createType(TB_INT)
            expr_return_value.isLVal = False
            expr_return_value.isCtVal = False
        else:
            break
    return True


def exprRel(tokens):
    global current_index, expr_return_value
    if not exprAdd(tokens):
        return False

    while True:
        if consume(tokens, "OPERATOR", "<") or consume(tokens, "OPERATOR", "<=") or \
                consume(tokens, "OPERATOR", ">") or consume(tokens, "OPERATOR", ">="):
            rv1 = expr_return_value
            if not exprAdd(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after relational operator")
            rv2 = expr_return_value

            # Check array comparison
            if rv1.type.nElements > -1 or rv2.type.nElements > -1:
                raise SyntaxError("an array cannot be compared")

            # Check struct comparison
            if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
                raise SyntaxError("a structure cannot be compared")

            # Result is int
            expr_return_value.type = createType(TB_INT)
            expr_return_value.isLVal = False
            expr_return_value.isCtVal = False
        else:
            break
    return True


def exprAdd(tokens):
    global current_index, expr_return_value
    if not exprMul(tokens):
        return False

    while True:
        if consume(tokens, "OPERATOR", "+") or consume(tokens, "OPERATOR", "-"):
            rv1 = expr_return_value
            if not exprMul(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '+' or '-'")
            rv2 = expr_return_value

            # Check array arithmetic
            if rv1.type.nElements > -1 or rv2.type.nElements > -1:
                raise SyntaxError("an array cannot be added or subtracted")

            # Check struct arithmetic
            if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
                raise SyntaxError("a structure cannot be added or subtracted")

            # Get arithmetic result type
            expr_return_value.type = getArithType(rv1.type, rv2.type)
            expr_return_value.isLVal = False
            expr_return_value.isCtVal = False
        else:
            break
    return True


def exprMul(tokens):
    global current_index, expr_return_value
    if not exprCast(tokens):
        return False

    while True:
        if consume(tokens, "OPERATOR", "*") or consume(tokens, "OPERATOR", "/"):
            rv1 = expr_return_value
            if not exprCast(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression after '*' or '/'")
            rv2 = expr_return_value

            # Check array arithmetic
            if rv1.type.nElements > -1 or rv2.type.nElements > -1:
                raise SyntaxError("an array cannot be multiplied or divided")

            # Check struct arithmetic
            if rv1.type.typeBase == TB_STRUCT or rv2.type.typeBase == TB_STRUCT:
                raise SyntaxError("a structure cannot be multiplied or divided")

            # Get arithmetic result type
            expr_return_value.type = getArithType(rv1.type, rv2.type)
            expr_return_value.isLVal = False
            expr_return_value.isCtVal = False
        else:
            break
    return True


def exprCast(tokens):
    global current_index, expr_return_value
    start_index = current_index

    if consume(tokens, "DELIMITER", "("):
        t = typeName(tokens)
        if t:  # Type cast
            if consume(tokens, "DELIMITER", ")"):
                if exprCast(tokens):
                    rv = expr_return_value

                    # Check if cast is valid
                    cast(t, rv.type)

                    # Update return value with cast type
                    expr_return_value.type = t
                    expr_return_value.isLVal = False
                    expr_return_value.isCtVal = False
                    return True
                else:
                    raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid expression after cast")
            else:
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing ')' after type name")
        else:
            current_index = start_index  # Not a type cast — backtrack

    return exprUnary(tokens)


def exprUnary(tokens):
    global current_index, expr_return_value

    if consume(tokens, "OPERATOR", "-"):
        if not exprUnary(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid operand for unary operator")

        rv = expr_return_value

        # Check if operand can be negated
        if rv.type.nElements > -1:
            raise SyntaxError("an array cannot be negated")
        if rv.type.typeBase == TB_STRUCT:
            raise SyntaxError("a structure cannot be negated")
        if rv.type.typeBase not in [TB_CHAR, TB_INT, TB_DOUBLE]:
            raise SyntaxError("invalid operand for unary minus")

        # Result keeps the same type, not an lvalue, not constant
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = False
        return True

    elif consume(tokens, "OPERATOR", "!"):
        if not exprUnary(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Invalid operand for unary operator")

        rv = expr_return_value

        # Check if operand can be logically negated
        if rv.type.typeBase == TB_STRUCT:
            raise SyntaxError("a structure cannot be logically tested")

        # Result is int
        expr_return_value.type = createType(TB_INT)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = False
        return True

    return exprPostfix(tokens)


def exprPostfix(tokens):
    global current_index, expr_return_value

    if not exprPrimary(tokens):
        return False

    while True:
        if consume(tokens, "DELIMITER", "["):  # array indexing
            # Save the array variable info before parsing index
            rv1 = RetVal()
            rv1.type = Type(expr_return_value.type.typeBase, expr_return_value.type.nElements,
                            expr_return_value.type.structSymbol)
            rv1.isLVal = expr_return_value.isLVal
            rv1.isCtVal = expr_return_value.isCtVal
            rv1.ctVal = expr_return_value.ctVal

            if not expr(tokens):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing expression inside []")

            rv2 = expr_return_value

            # Check array indexing semantics
            if rv1.type.nElements == -1:
                raise SyntaxError("only an array can be indexed")
            if rv2.type.typeBase != TB_INT:
                raise SyntaxError("an array can only be indexed by an integer")

            if not consume(tokens, "DELIMITER", "]"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Missing ']'")

            # Result is the element type, is lvalue
            expr_return_value.type = createType(rv1.type.typeBase, -1, rv1.type.structSymbol)
            expr_return_value.isLVal = True
            expr_return_value.isCtVal = False

        elif consume(tokens, "DELIMITER", "."):  # struct access
            rv = expr_return_value

            if rv.type.typeBase != TB_STRUCT:
                raise SyntaxError("a field can only be selected from a structure")

            if not consume(tokens, "IDENTIFIER"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected field name after '.'")

            field_name = tokens[current_index - 1][1]

            # Find field in struct
            field_symbol = findSymbol(field_name, scope=rv.type.structSymbol.members)
            if not field_symbol:
                raise SyntaxError(f"undefined structure member: {field_name}")

            # Result is the field type, is lvalue if original was lvalue
            expr_return_value.type = field_symbol.type
            expr_return_value.isLVal = rv.isLVal
            expr_return_value.isCtVal = False

        else:
            break
    return True


def exprPrimary(tokens):
    global current_index, expr_return_value

    if consume(tokens, "IDENTIFIER"):
        name = tokens[current_index - 1][1]

        if consume(tokens, "DELIMITER", "("):  # function call
            sym = findSymbol(name)
            if not sym:
                raise SyntaxError(f"undefined function: {name}")
            if sym.cls not in [CLS_FUNC, CLS_EXTFUNC]:
                raise SyntaxError(f"{name} is not a function")

            # Check arguments
            args = []
            if expr(tokens):
                args.append(expr_return_value)
                while consume(tokens, "DELIMITER", ","):
                    if not expr(tokens):
                        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected argument expression after ','")
                    args.append(expr_return_value)

            if not consume(tokens, "DELIMITER", ")"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ')' after arguments")

            # Check argument count and types
            if len(args) != len(sym.args):
                raise SyntaxError(f"incorrect number of arguments for function {name}")

            for i, (provided_arg, expected_arg) in enumerate(zip(args, sym.args)):
                try:
                    cast(expected_arg.type, provided_arg.type)
                except SyntaxError:
                    raise SyntaxError(f"incompatible type for argument {i + 1} of function {name}")

            # Function call result
            expr_return_value.type = sym.type
            expr_return_value.isLVal = False
            expr_return_value.isCtVal = False
            return True

        else:  # Variable reference
            sym = findSymbol(name)
            if not sym:
                raise SyntaxError(f"undefined symbol: {name}")
            if sym.cls != CLS_VAR:
                raise SyntaxError(f"{name} is not a variable")

            # Variable reference
            expr_return_value.type = sym.type
            expr_return_value.isLVal = True
            expr_return_value.isCtVal = False
            return True

    elif consume(tokens, "CT_INT"):
        value_str = tokens[current_index - 1][1]
        if value_str.startswith("0x") or value_str.startswith("0X"):
            value = int(value_str, 16)
        elif value_str.startswith("0") and value_str != "0":
            value = int(value_str, 8)
        else:
            value = int(value_str, 10)
        expr_return_value.type = createType(TB_INT)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = True
        expr_return_value.ctVal.i = value
        return True

    elif consume(tokens, "CT_REAL"):
        value = float(tokens[current_index - 1][1])
        expr_return_value.type = createType(TB_DOUBLE)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = True
        expr_return_value.ctVal.d = value
        return True

    elif consume(tokens, "CT_CHAR"):
        value = tokens[current_index - 1][1]
        expr_return_value.type = createType(TB_CHAR)
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = True
        expr_return_value.ctVal.i = ord(value[1]) if len(value) >= 3 else 0  # Extract char from 'c'
        return True

    elif consume(tokens, "CT_STRING"):
        value = tokens[current_index - 1][1]
        expr_return_value.type = createType(TB_CHAR, len(value) - 2)  # -2 for quotes
        expr_return_value.isLVal = False
        expr_return_value.isCtVal = True
        expr_return_value.ctVal.str = value[1:-1]  # Remove quotes
        return True

    elif consume(tokens, "DELIMITER", "("):
        if not expr(tokens):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression inside parentheses")
        if not consume(tokens, "DELIMITER", ")"):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ')' after expression")
        return True

    return False