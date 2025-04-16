current_index = 0  # Track token position

TYPES = ["CT_INT",  "CT_REAL", "CT_STRING", "CT_CHAR"]  # Supported types

def parse_program(tokens, exit_token):
    """Parses the entire program."""
    global current_index
    print(f"Parsing program with current token: {tokens[current_index]}")
    while current_index < len(tokens):
        token_type, token_value, line_number = tokens[current_index]
        if token_value == exit_token:
            print("\n\nExiting\n\n")
            break
        elif token_type == "KEYWORD" and token_value in ["int", "char", "double", "void"]:
            if not parse_function_declaration(tokens):
                parse_var_declaration(tokens)
        elif token_type == "KEYWORD" and token_value == "if":
            if_statement_parse(tokens)
        elif token_type == "KEYWORD" and token_value == "while":
            while_statement_parse(tokens)
        elif token_type == "KEYWORD" and token_value == "for":
            parse_for_loop(tokens)
        elif token_type == "IDENTIFIER":
            parse_variable_list(tokens)  # Could be assignment or standalone expression
        elif token_type == "DELIMITER" and token_value == ";":
            consume(tokens, "DELIMITER")  # Skip standalone semicolons (empty statements)
        else:
            if tokens[current_index][0] == "EOF":
                break
            print(f"Exit token: {exit_token} token is : {tokens[current_index][0]}")
            raise SyntaxError(f"Line {line_number}: Unexpected token {token_value}")

    print("✅ Parsing completed successfully!")


def consume(tokens, expected_type, expected_value=None):
    global current_index
    if current_index >= len(tokens):
        return False
    token_type, token_value, _ = tokens[current_index]
    if token_type == expected_type and (expected_value is None or token_value == expected_value):
        current_index += 1
        return True
    return False

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

def typeName(tokens):
    if not typeBase(tokens):
        return False
    #arrayDecl(tokens)  # optional, you could check its result if needed
    return True

def typeBase(tokens):
    global current_index
    if consume(tokens, "KEYWORD", "int") or \
       consume(tokens, "KEYWORD", "double") or \
       consume(tokens, "KEYWORD", "char"):
        return True
    if consume(tokens, "KEYWORD", "struct"):
        if not consume(tokens, "IDENTIFIER"):
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected struct name")
        return True
    return False




def parse_function_call_parameters(tokens):
    global current_index
    while tokens[current_index][1] != ")":
        '''
        if tokens[current_index][0] == "IDENTIFIER":
            consume(tokens, "IDENTIFIER")
        elif tokens[current_index][0] == "CT_INT":
            consume(tokens, "CT_INT")
        elif tokens[current_index][0] == "CT_REAL":
            consume(tokens, "CT_REAL")
        '''
        if tokens[current_index][0] == "CT_STRING":
            consume(tokens, "CT_STRING")
        elif tokens[current_index][0] == "CT_CHAR":
            consume(tokens, "CT_CHAR")
        else:
            parse_expression(tokens)
            #raise SyntaxError(f"Line {tokens[current_index][2]}: Unexpected token {tokens[current_index]}")
        if tokens[current_index][1] == ")":
            break
        elif tokens[current_index][1] == ",":
            consume(tokens, "DELIMITER")
        else:
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected , or ), got {tokens[current_index]}")

def parse_function_call(tokens):
    """Parses a function call like `function_name(a, b)`."""
    global current_index
    if tokens[current_index][0] != "IDENTIFIER":
        return False
    consume(tokens, "IDENTIFIER")  # Consume function name

    if tokens[current_index][1] != "(":
        return False
    consume(tokens, "DELIMITER")  # Consume `(`
    parse_function_call_parameters(tokens)

    if tokens[current_index][1] != ")":
        parse_expression(tokens)  # Parse function arguments
        while tokens[current_index][1] == ',':
            consume(tokens, "DELIMITER")
            parse_expression(tokens)
        if tokens[current_index][1] != ")":
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")
    consume(tokens, "DELIMITER")  # Consume `)`

def parse_function_declaration(tokens):
    """Parses a function declaration like `int main() { ... }`."""
    global current_index
    clone_current_index = current_index
    if tokens[current_index][1] not in ["int", "char", "double", "void"]:
        return False
    if (current_index + 2 <= len(tokens) and
            tokens[current_index][1] == "void" and
            (tokens[current_index + 1][0] != "IDENTIFIER" or
             tokens[current_index + 2][1] != "(")):
        raise SyntaxError(f"Void function syntax error {tokens[current_index][2]}")

    consume(tokens, "KEYWORD")
    if tokens[current_index][0] != "IDENTIFIER":
        current_index = clone_current_index
        return False

    consume(tokens, "IDENTIFIER")  # Consume function name
    if tokens[current_index][1] != "(":
        current_index = clone_current_index
        return False

    consume(tokens, "DELIMITER")  # Consume `(`
    parse_function_parameters(tokens)

    if tokens[current_index][1] != ")":
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")
    consume(tokens, "DELIMITER")  # Consume `)`

    if tokens[current_index][1] != "{":
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected {{, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")  # Consume `{`

    parse_program_function(tokens, "}")  # Parse function body

    if tokens[current_index][1] != "}":
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected }}, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")  # Consume `}`
    print("✅ Function parsed successfully!")
    return True


def parse_function_parameters(tokens):
    """Parses function parameters like `int a, char b`."""
    global current_index
    if tokens[current_index][1] == ")":
        return

    if tokens[current_index][1] not in ["int", "char", "double"]:
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected type keyword, got {tokens[current_index]}")
    consume(tokens, "KEYWORD")

    if tokens[current_index][0] != "IDENTIFIER":
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected variable name, got {tokens[current_index]}")
    consume(tokens, "IDENTIFIER")

    while tokens[current_index][1] == ',':
        consume(tokens, "DELIMITER")
        if tokens[current_index][1] not in ["int", "char", "double"]:
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected type keyword, got {tokens[current_index]}")
        consume(tokens, "KEYWORD")
        if tokens[current_index][0] != "IDENTIFIER":
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected variable name, got {tokens[current_index]}")
        consume(tokens, "IDENTIFIER")

    if tokens[current_index][1] != ")":
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")


def parse_program_function(tokens, exit_token):
    """Parses the entire program."""
    global current_index
    print(f"Parsing program with current token: {tokens[current_index]}")
    while current_index < len(tokens):
        token_type, token_value, line_number = tokens[current_index]
        if token_value == exit_token:
            print("\n\nExiting\n\n")
            break
        elif token_type == "KEYWORD" and token_value in ["int", "char", "double", "void"]:
            if not parse_function_declaration(tokens):
                parse_var_declaration(tokens)
        elif token_type == "KEYWORD" and token_value == "if":
            if_statement_parse(tokens)
        elif token_type == "KEYWORD" and token_value == "while":
            while_statement_parse(tokens)
        elif token_type == "KEYWORD" and token_value == "for":
            parse_for_loop(tokens)
        elif token_type == "IDENTIFIER":
            parse_variable_list(tokens)
        elif token_type == "DELIMITER" and token_value == ";":
            consume(tokens, "DELIMITER")
        else:
            if tokens[current_index][0] == "EOF":
                break
            raise SyntaxError(f"Line {line_number}: Unexpected token {token_value}")

def parse_for_loop(tokens):
    """Parses a for loop."""
    global current_index
    if tokens[current_index][1] != "for":
        return False
    consume(tokens, "KEYWORD")
    if tokens[current_index][1] != '(':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected (, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != ';':
        expr(tokens)
    if tokens[current_index][1] != ';':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ;, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != ';':
        expr(tokens)
    if tokens[current_index][1] != ';':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ;, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != ')':
        expr(tokens)
    if tokens[current_index][1] != ')':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != '{':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected {{, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    parse_program(tokens, '}')
    if tokens[current_index][1] != '}':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected }}, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")

def parse_var_declaration(tokens):
    """Parses variable declarations like `int speed = 70, a, b = 5;`"""
    global current_index
    if tokens[current_index][1] not in ["int", "char", "double"]:
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected type keyword, got {tokens[current_index]}")
    consume(tokens, "KEYWORD")  # Consume type
    parse_variable_list_in_var_declaration(tokens)
    print("✅ Variable declaration parsed successfully!")

def parse_variable_list_in_var_declaration(tokens):
    """Parses a comma-separated list of variables."""
    global current_index
    if tokens[current_index][0] != "IDENTIFIER":
        print(f"Next token: {tokens[current_index + 1][1]}")
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected variable name, got {tokens[current_index]}")
    consume(tokens, "IDENTIFIER")  # Consume variable name

    # split in 2 : array declaration and normal variable declaration
    if tokens[current_index][1] == '[':
        consume(tokens, "DELIMITER")
        if tokens[current_index][0] != "CT_INT":
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected number, got {tokens[current_index]}")
        consume(tokens, "CT_INT")
        if tokens[current_index][1] != ']':
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ], got {tokens[current_index]}")
        consume(tokens, "DELIMITER")

        if tokens[current_index][1] == '=':
            consume(tokens, "OPERATOR")
            if tokens[current_index][1] != '{':
                raise  SyntaxError (f"Line {tokens[current_index][2]}: Expected {{, got {tokens[current_index]}")
            consume(tokens, "DELIMITER")
            if tokens[current_index][1] == '}':
                consume(tokens, "DELIMITER")
            else:
                parse_expression(tokens)
                while tokens[current_index][1] == ',':
                    consume(tokens, "DELIMITER")
                    parse_expression(tokens)
                if tokens[current_index][1] != '}':
                    raise SyntaxError(f"Line {tokens[current_index][2]}: Expected }}, got {tokens[current_index]}")
                consume(tokens, "DELIMITER")
    # Check for assignment
    else:
        if tokens[current_index][1] == '=':
            consume(tokens, "OPERATOR")
            parse_expression(tokens)

    # Check for more variables
    if tokens[current_index][1] == ',':
        print(f"Before consuming: {tokens[current_index][1]}")
        consume(tokens, "DELIMITER")
        print(f"After consuming: {tokens[current_index][1]}")
        parse_variable_list_in_var_declaration(tokens)
    elif tokens[current_index][1] == ';':
        print(f"Consuming ; {tokens[current_index][0]}")
        consume(tokens, "DELIMITER")
    else:
        raise SyntaxError(f"Line {tokens[current_index][2]}: Unexpected token {tokens[current_index]}")


def parse_variable_list(tokens):
    """Parses a comma-separated list of variables."""
    global current_index
    if tokens[current_index][0] != "IDENTIFIER":
        print(f"Next token: {tokens[current_index + 1][1]}")
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected variable name, got {tokens[current_index]}")
    consume(tokens, "IDENTIFIER")  # Consume variable name

    # Check for array declaration
    if tokens[current_index][1] == '[':
        consume(tokens, "DELIMITER")
        if tokens[current_index][0] != "CT_INT":
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected number, got {tokens[current_index]}")
        consume(tokens, "CT_INT")
        if tokens[current_index][1] != ']':
            raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ], got {tokens[current_index]}")
        consume(tokens, "DELIMITER")

        if tokens[current_index][1] == '=':
            consume(tokens, "OPERATOR")
            if tokens[current_index][0] in ["CT_INT", "CT_REAL", "IDENTIFIER"]:
                print("bbbbbb")
                consume(tokens, tokens[current_index][0])
            elif tokens[current_index][1] == '{':
                consume(tokens, "DELIMITER")
                if tokens[current_index][1] == '}':
                    consume(tokens, "DELIMITER")
                else:
                    parse_expression(tokens)
                    while tokens[current_index][1] == ',':
                        consume(tokens, "DELIMITER")
                        parse_expression(tokens)
                    if tokens[current_index][1] != '}':
                        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected }}, got {tokens[current_index]}")
                    consume(tokens, "DELIMITER")
    #check for function call
    else:
        print("YYYYYYYYYYYYYYYYYYYYYY")
        if tokens[current_index][1] == '(':
            print("ZZZZZZZZZZZZZZZZZ")
            current_index = current_index - 1 # this is not good, needs to be fixed, but works for now
            parse_function_call(tokens)

        # Check for assignment
        elif tokens[current_index][1] == '=':
            consume(tokens, "OPERATOR")
            parse_expression(tokens)

    # Check for more variables
    if tokens[current_index][1] == ',':
        print(f"Before consuming: {tokens[current_index][1]}")
        consume(tokens, "DELIMITER")
        print(f"After consuming: {tokens[current_index][1]}")
        parse_variable_list(tokens)
    elif tokens[current_index][1] == ';':
        print(f"Consuming ; {tokens[current_index][0]}")
        consume(tokens, "DELIMITER")
    else:
        raise SyntaxError(f"Line {tokens[current_index][2]}: Unexpected token {tokens[current_index]}")


def parse_expression(tokens):
    """Parses an expression like `speed + 10 / 2`."""
    global current_index
    print("Function called")
    print(tokens[current_index])

    if tokens[current_index][0] == "IDENTIFIER":
        if current_index + 1 < len(tokens) and tokens[current_index + 1][1] == '[':
            # Array access
            consume(tokens, "IDENTIFIER")
            consume(tokens, "DELIMITER")
            if tokens[current_index][0] in ["CT_INT", "IDENTIFIER"]:
                consume(tokens, tokens[current_index][0])
            else:
                raise SyntaxError(
                    f"Line {tokens[current_index][2]}: Expected variable name or number, got {tokens[current_index]}")
            if tokens[current_index][1] != ']':
                raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ], got {tokens[current_index]}")
            consume(tokens, "DELIMITER")
        elif current_index + 1 < len(tokens) and tokens[current_index + 1][1] == '(':
            parse_function_call(tokens)
        else:
            consume(tokens, "IDENTIFIER")
    elif tokens[current_index][0] == "CT_INT":
        consume(tokens, "CT_INT")
    elif tokens[current_index][0] == "CT_REAL":
        consume(tokens, "CT_REAL")
    else:
        raise SyntaxError(
            f"Line {tokens[current_index][2]}: Expected variable name or number, got {tokens[current_index]}")

    print(tokens[current_index][1])
    print(tokens[current_index][0])
    if tokens[current_index][0] == "OPERATOR" and tokens[current_index][1] in ["+", "-", "*", "/"]:
        print("DAAAAAAA")
        consume(tokens, "OPERATOR")
        parse_expression(tokens)

    print("✅ Expression parsed successfully!")
    return True


def parse_condition(tokens):
    """Parses a condition like `speed + 20 > b * c`"""
    global current_index
    if not parse_expression(tokens):
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression, got {tokens[current_index]}")
    if not (tokens[current_index][0] == "OPERATOR" and
            tokens[current_index][1] in ["==", "!=", "<", ">", "<=", ">="]):
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected operator, got {tokens[current_index]}")
    consume(tokens, "OPERATOR")
    if not parse_expression(tokens):
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected expression, got {tokens[current_index]}")


def if_statement_parse(tokens):
    """Parses an if statement."""
    global current_index
    if tokens[current_index][1] != "if":
        return False
    consume(tokens, "KEYWORD")
    if tokens[current_index][1] != '(':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected (, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    parse_condition(tokens)
    if tokens[current_index][1] != ')':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != '{':
        raise SyntaxError("Expected {")
    consume(tokens, "DELIMITER")

    parse_program(tokens, "}")

    if tokens[current_index][1] != '}':
        raise SyntaxError("Expected }")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] == "else":
        consume(tokens, "KEYWORD")
        if tokens[current_index][1] != '{':
            raise SyntaxError("Expected {")
        consume(tokens, 'DELIMITER')
        parse_program(tokens, "}")
        if tokens[current_index][1] != '}':
            raise SyntaxError("Expected }")
        consume(tokens, 'DELIMITER')


def while_statement_parse(tokens):
    """Parses a while statement."""
    global current_index
    if tokens[current_index][1] != "while":
        return False
    consume(tokens, "KEYWORD")
    if tokens[current_index][1] != '(':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected (, got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    parse_condition(tokens)
    if tokens[current_index][1] != ')':
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected ), got {tokens[current_index]}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != '{':
        raise SyntaxError("Expected {")
    consume(tokens, "DELIMITER")

    parse_program(tokens, "}")

    if tokens[current_index][1] != '}':
        raise SyntaxError("Expected }")
    consume(tokens, "DELIMITER")