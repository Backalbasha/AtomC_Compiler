import re

# Define token types
TOKEN_SPECIFICATIONS = [
    ('COMMENT', r'//.*?\n|/\*.*?\*/'),
    ('KEYWORD', r'\b(break|char|double|else|for|if|int|return|struct|void|while)\b'),
    ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('CT_REAL', r'\b\d+(\.\d+([eE][-+]?\d+)?)|\d+[eE][-+]?\d+\b'),  # Floating-point with exponent
    ('CT_INT', r'0[xX][0-9a-fA-F]+|\b0[0-7]*\b|\b[1-9][0-9]*\b'),  # Hex, octal, decimal
    ('CT_CHAR', r"'(\\[abfnrtv'\"\\0]|[^'\\])'"),  # Character literals with escape sequences
    ('CT_STRING', r'"(\\[abfnrtv\'"?\\0]|[^"\\])*"'),  # String literals
    ('OPERATOR', r'(\+|-|\*|/|==|!=|<=|>=|<|>|=|&&|\|\||!|\.)'),
    ('DELIMITER', r'[;,{}()\[\]]'),
    ('WHITESPACE', r'\s+'),
    ('UNKNOWN', r'.')  # Catch-all for unrecognized characters
]

# Compile regex patterns
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATIONS)
TOKEN_PATTERN = re.compile(TOKEN_REGEX, re.DOTALL)

def tokenize(code):
    """
    Lexical analyzer function that scans the given Atomic code and generates tokens.
    """
    tokens = []
    line_number = 1

    for match in TOKEN_PATTERN.finditer(code):
        token_type = match.lastgroup
        token_value = match.group(token_type)

        if token_type == "WHITESPACE":
            line_number += token_value.count('\n')  # Track new lines
            continue  # Ignore spaces
        if token_type == 'COMMENT':
            line_number += token_value.count('\n')
            continue
        if token_type == "UNKNOWN":
            raise SyntaxError(f"LEXICAL ERROR: Line {line_number}: Unexpected character '{token_value}'")
        tokens.append((token_type, token_value, line_number))
    tokens.append(('EOF', '', line_number))

    return tokens


current_index = 0  # Track token position


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


def consume(tokens, expected_type):
    """Consumes the expected token and moves to the next one."""
    global current_index
    token_type, token_value, line_number = tokens[current_index]
    if token_type == expected_type:
        current_index += 1
        return token_value
    raise SyntaxError(f"Line {line_number}: Expected {expected_type}, got {token_type}")

def parse_function_call_parameters(tokens):
    global current_index
    while tokens[current_index][1] != ")":
        if tokens[current_index][0] == "IDENTIFIER":
            consume(tokens, "IDENTIFIER")
        elif tokens[current_index][0] == "CT_INT":
            consume(tokens, "CT_INT")
        elif tokens[current_index][0] == "CT_REAL":
            consume(tokens, "CT_REAL")
        elif tokens[current_index][0] == "CT_STRING":
            consume(tokens, "CT_STRING")
        elif tokens[current_index][0] == "CT_CHAR":
            consume(tokens, "CT_CHAR")
        else:
            raise SyntaxError(f"Line {tokens[current_index][2]}: Unexpected token {tokens[current_index]}")
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
        elif token_type == "IDENTIFIER":
            parse_variable_list(tokens)
        elif token_type == "DELIMITER" and token_value == ";":
            consume(tokens, "DELIMITER")
        else:
            if tokens[current_index][0] == "EOF":
                break
            raise SyntaxError(f"Line {line_number}: Unexpected token {token_value}")


def parse_var_declaration(tokens):
    """Parses variable declarations like `int speed = 70, a, b = 5;`"""
    global current_index
    if tokens[current_index][1] not in ["int", "char", "double"]:
        raise SyntaxError(f"Line {tokens[current_index][2]}: Expected type keyword, got {tokens[current_index]}")
    consume(tokens, "KEYWORD")  # Consume type
    parse_variable_list(tokens)
    print("✅ Variable declaration parsed successfully!")


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
        else:
            consume(tokens, "IDENTIFIER")
    elif tokens[current_index][0] == "CT_INT":
        consume(tokens, "CT_INT")
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


if __name__ == "__main__":
    with open("input.c", 'r') as file:
        code = file.read()

    token_list = tokenize(code)
    for token in token_list:
        print(token)
    print(f"Total tokens: {len(token_list)}")
    token_list_clone = token_list
    parse_program(token_list, "EOF")
    print('\nfinished')
    print(token_list[current_index])