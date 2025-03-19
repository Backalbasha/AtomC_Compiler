import re

# Define token types
TOKEN_SPECIFICATIONS = [
    ('KEYWORD', r'\b(break|char|double|else|for|if|int|return|struct|void|while)\b'),
    ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('NUMBER', r'\b\d+(\.\d+)?\b'),  # Integer and floating-point numbers
    ('OPERATOR', r'(\+|-|\*|/|==|!=|<=|>=|<|>)'),
    ('DELIMITER', r'[;,{}()\[\]]'),
    ('WHITESPACE', r'\s+'),
    ('UNKNOWN', r'.')  # Catch-all for unrecognized characters
]

# Compile regex patterns
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATIONS)
TOKEN_PATTERN = re.compile(TOKEN_REGEX)

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

        tokens.append((token_type, token_value, line_number))

    return tokens

# Example usage
if __name__ == "__main__":
    with open("input.c", 'r') as file:
        code = file.read()

    token_list = tokenize(code)
    for token in token_list:
        print(token)
