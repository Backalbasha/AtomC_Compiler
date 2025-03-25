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

        tokens.append((token_type, token_value, line_number))
    tokens.append(('EOF', '', line_number))

    return tokens

crtTk = 0
def consume1(tokens, expected_type):
    """
    Consume the next token if it matches the expected type.
    """
    global crtTk
    token_type, token_value, line_number = tokens[crtTk]
    if token_type == expected_type:
        crtTk+=1
        return tokens[0]
    else:
        raise SyntaxError(f"Syntax error at line {line_number}: Expected {expected_type}, but got {token_type}")

current_index = 0  # Track token position

def current_token(tokens):
    """Returns the current token type, value, and line number."""
    return tokens[current_index] if current_index < len(tokens) else ("EOF", None, None)

def parse_program (tokens):
    """Parses the entire program."""
    global  current_index
    while current_index < len(tokens):
        token_type, token_value, line_number = current_token(tokens)

        if token_type == "KEYWORD" and token_value in ["int", "char", "double"]:
            parse_var_declaration(tokens)
        elif token_type == "KEYWORD" and token_value == "if":
            if_statement_parse(tokens)
        elif token_type == "IDENTIFIER":
            parse_expression(tokens)  # Could be assignment or standalone expression
        elif token_type == "DELIMITER" and token_value == ";":
            consume(tokens, "DELIMITER")  # Skip standalone semicolons (empty statements)
        elif token_type == "EOF":
            break
        else:
            raise SyntaxError(f"Line {line_number}: Unexpected token {token_value}")

    print("✅ Parsing completed successfully!")

def consume(tokens, expected_type):
    """Consumes the expected token and moves to the next one."""
    global current_index
    token_type, token_value, line_number = current_token(tokens)
    if token_type == expected_type:
        current_index += 1
        return token_value
    raise SyntaxError(f"Line {line_number}: Expected {expected_type}, got {token_type}")

def match(tokens, expected_type):
    """Checks if the current token matches the expected type."""
    global current_index
    #return current_token(tokens)[current_index] == expected_type
    return tokens[current_index][0] == expected_type


def parse_var_declaration(tokens):
    """Parses variable declarations like `int speed = 70, a, b = 5;`"""
    global current_index
    if  tokens[current_index][1] not in ["int", "char", "double"]:
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected type keyword, got {current_token(tokens)}")
    consume(tokens, "KEYWORD")  # Consume `int`, `char`, etc.
    parse_variable_list(tokens)

    print("✅ Variable declaration parsed successfully!")

def parse_variable_list(tokens):
    """Parses a comma-separated list of variables."""
    #get first variable before assignment an assignmnet
    global current_index
    if not match(tokens, "IDENTIFIER"):
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected variable name, got {current_token(tokens)}")
    consume(tokens, "IDENTIFIER")  # Consume variable name
    if match(tokens, "OPERATOR") and current_token(tokens)[1] == "=":
        consume(tokens, "OPERATOR")  # Consume `=`\
        parse_expression(tokens)
        #while True:
            #if not parse_expression(tokens):
                #raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected expression, got {current_token(tokens)}")

    if match(tokens, "DELIMITER") and current_token(tokens)[1] == ",":
        print (f"Before consuming: {tokens[current_index][1]}")
        consume(tokens, "DELIMITER")  # Consume `,` and continue parsing the next variable
        print(f"After consuming: {tokens[current_index][1]}")
        parse_variable_list(tokens)
    elif match(tokens, "DELIMITER") and current_token(tokens)[1] == ";":
        consume(tokens, "DELIMITER")  # Consume `;` and stop parsing
    else:
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Unexpected token {current_token(tokens)}")
def parse_expression(tokens):
    """Parses an expression like `speed + 10 / 2`."""
    global current_index
    print("Function called")
    print(tokens[current_index])

    if match (tokens, "IDENTIFIER"):
        consume(tokens, "IDENTIFIER")
    elif match (tokens, "NUMBER"):
        consume(tokens, "NUMBER")
    else:
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected variable name or number, got {current_token(tokens)}")
    print (tokens[current_index][1])
    print (tokens[current_index][0])
    if tokens[current_index][0] == "OPERATOR" and tokens[current_index][1] in ["+", "-", "*", "/"]:
        print("DAAAAAAA")
        consume(tokens, "OPERATOR")
        parse_expression(tokens)

    print("✅ Expression parsed successfully!")
    return True

def parse_condition(tokens):
    """Parses a condition like `speed + 20 > b * c`    or expression COMPARATOR OPERATOR expression;"""
    global current_index
    if not parse_expression(tokens):
        raise SyntaxError (f"Line {current_token(tokens)[2]}: Expected expression, got {current_token(tokens)}")
    if not match (tokens, "OPERATOR") and current_token(tokens)[1] in ["==", "!=", "<", ">", "<=", ">="]:
        raise SyntaxError (f"Line {current_token(tokens)[2]}: Expected operator, got {current_token(tokens)}")
    consume(tokens, "OPERATOR")
    if not parse_expression(tokens):
        raise SyntaxError (f"Line {current_token(tokens)[2]}: Expected expression, got {current_token(tokens)}")
    ''' checks for ; at the end of the condition
    if not match (tokens, "DELIMITER") and tokens[current_index][1] == ";":
        raise SyntaxError (f"Line {current_token(tokens)[2]}: Expected ;, got {current_token(tokens)}")
    consume(tokens, "DELIMITER")
    print("✅ Condition parsed successfully!")
    '''

def if_statement_parse (tokens):
    global current_index
    if tokens[current_index][1] != "if":
        return False
    consume(tokens, "KEYWORD")
    if tokens[current_index][1] != '(':
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected (, got {current_token(tokens)}")
    consume(tokens, "DELIMITER")
    parse_condition(tokens)
    if tokens[current_index][1] != ')':
        raise SyntaxError(f"Line {current_token(tokens)[2]}: Expected ), got {current_token(tokens)}")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] != '{':
        raise SyntaxError("Expected {")
    consume(tokens, "DELIMITER")

    #content from if statement
    parse_variable_list(tokens)

    if tokens[current_index][1] != '}':
        raise SyntaxError("Expected }")
    consume(tokens, "DELIMITER")
    if tokens[current_index][1] == "else":
        consume(tokens, "KEYWORD")
        if tokens[current_index][1] != '{':
            raise SyntaxError("Expected {")
        consume(tokens, 'DELIMITER')
        #content from else statement
        parse_var_declaration(tokens)

        if tokens[current_index][1] != '}':
            raise SyntaxError("Expected }")
        consume(tokens, 'DELIMITER')


# Example usage
if __name__ == "__main__":
    with open("input.c", 'r') as file:
        code = file.read()

    token_list = tokenize(code)
    for token in token_list:
        print(token)
    #print(type(token_list))
    #print (type(token_list[0][0]))
    #print (consume1(token_list, "KEYWORD"))
    token_list_clone = token_list
    #parser = Parser(token_list)
    #parser.parse_var_declaration()

    #print (token_list [current_index])

    #parse_condition(token_list)
    #parse_expression(token_list)
    #parse_var_declaration(token_list)

    #parse_var_declaration(token_list)
    #if_statement_parse(token_list)

    print('\nfinished')
    print (token_list[current_index])

