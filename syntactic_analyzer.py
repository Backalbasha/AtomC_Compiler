current_index = 0  # Track token position

TYPES = ["CT_INT",  "CT_REAL", "CT_STRING", "CT_CHAR"]  # Supported types


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
    global current_index
    clone_current_index = current_index
    print (f"DeclStruct called {current_index}")
    if not consume(tokens, "KEYWORD", "struct"): return False
    if not consume(tokens, "IDENTIFIER"): raise SyntaxError("Missing struct name")
    if not consume(tokens, "DELIMITER", "{"):
        current_index = clone_current_index
        return False
        #raise SyntaxError("Expected '{'")
    while declVar(tokens): pass
    if not consume(tokens, "DELIMITER", "}"): raise SyntaxError("Expected '}'")
    if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
    return True

# ---------- declVar: typeBase ID arrayDecl? ( COMMA ID arrayDecl? )* SEMICOLON ----------
def declVar(tokens):
    global current_index
    print (f"DeclVar called {current_index}")
    if not typeBase(tokens): return False
    if not consume(tokens, "IDENTIFIER"): raise SyntaxError("Missing variable name")
    arrayDecl(tokens)
    while consume(tokens, "DELIMITER", ","):
        if not consume(tokens, "IDENTIFIER"): raise SyntaxError("Missing variable name after ','")
        arrayDecl(tokens)
    if not consume(tokens, "DELIMITER", ";"): raise SyntaxError("Expected ';'")
    print (f"DeclVar exiting {current_index}")
    return True

# ---------- typeBase: INT | DOUBLE | CHAR | STRUCT ID ----------
def typeBase(tokens):
    if consume(tokens, "KEYWORD", "int"): return True
    if consume(tokens, "KEYWORD", "double"): return True
    if consume(tokens, "KEYWORD", "char"): return True
    if consume(tokens, "KEYWORD", "struct"):
        if not consume(tokens, "IDENTIFIER"): raise SyntaxError("Expected struct name")
        return True
    return False

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
    global current_index
    print (f"DeclFunc called {current_index}")
    clone_current_index = current_index
    if not (consume(tokens, "KEYWORD", "void") or typeBase(tokens)):
        current_index = clone_current_index
        return False
    consume(tokens, "OPERATOR", "*")  # optional
    if not consume(tokens, "IDENTIFIER"):
        current_index = clone_current_index
        return  False
        #raise SyntaxError("Expected function name")
    if not consume(tokens, "DELIMITER", "("):
        current_index = clone_current_index
        return False
        #raise SyntaxError("Expected '('")
    if funcArg(tokens):
        while consume(tokens, "DELIMITER", ","):
            if not funcArg(tokens):
                current_index = clone_current_index
                return False
                #raise SyntaxError("Invalid function argument")
    if not consume(tokens, "DELIMITER", ")"):
        current_index = clone_current_index
        return False
        #raise SyntaxError("Expected ')'")
    stmCompound(tokens)
    return True

# ---------- funcArg: typeBase ID arrayDecl? ----------
def funcArg(tokens):
    if not typeBase(tokens): return False
    if not consume(tokens, "IDENTIFIER"): raise SyntaxError("Expected argument name")
    arrayDecl(tokens)
    return True

# ---------- stmCompound: { (declVar | stm)* } ----------
def stmCompound(tokens):
    if not consume(tokens, "DELIMITER", "{"): return False
    while True:
        if tokens[current_index][1] == "}": break
        if not (declVar(tokens) or stm(tokens)):  # Attempt to parse declVar or stm
            raise SyntaxError(f"Unexpected token {tokens[current_index]} inside compound statement")
    if not consume(tokens, "DELIMITER", "}"): raise SyntaxError("Expected '}'")
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
        if consume(tokens, "DELIMITER", "("):  # function call
            if expr(tokens):
                while consume(tokens, "DELIMITER", ","):
                    if not expr(tokens):
                        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected argument expression after ','")
            if not consume(tokens, "DELIMITER", ")"):
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ')' after arguments")
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