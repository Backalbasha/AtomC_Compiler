from lexical_analyzer import tokenize
from syntactic_analyzer import parse_program, parse_unit, arrayDecl, declStruct, declVar, typeBase
import syntactic_analyzer
if __name__ == "__main__":
    with open("input2.c", 'r') as file:
        code = file.read()

    token_list = tokenize(code)
    for token in token_list:
        print(token)
    print(f"Total tokens: {len(token_list)}")
    token_list_clone = token_list
    #print (declStruct(token_list))
    #print (declVar(token_list))
    #print (arrayDecl(token_list))
    #parse_program(token_list, "EOF")
    #print (declVar(token_list))
    print (f"{syntactic_analyzer.current_index}asgfsdgdsfg {token_list[syntactic_analyzer.current_index]}")
    parse_unit(token_list)

    print('\nfinished')
    print(token_list[syntactic_analyzer.current_index-1])