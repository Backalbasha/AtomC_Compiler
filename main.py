import re
from lexical_analyzer import tokenize
from syntactic_analyzer import parse_program, current_index

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