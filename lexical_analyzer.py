import re

# Define token types
TOKEN_SPECIFICATIONS = [
    ('COMMENT', r'//.*?(?:\n|\Z)|/\*.*?\*/'),
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