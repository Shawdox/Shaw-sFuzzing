def generate_print_maze(maze_string):
    return """
def print_maze(out, row, col):
    output  = out +"\\n"
    c_row = 0
    c_col = 0
    for c in list(\"\"\"%s\"\"\"):
        if c == '\\n':
            c_row += 1
            c_col = 0
            output += "\\n"
        else:
            if c_row == row and c_col == col: output += "X"
            elif c == "X": output += " "
            else: output += c
            c_col += 1
    return output
""" % maze_string

def generate_trap_tile(row, col):
    return """
def tile_%d_%d(input, index):
    try: HTMLParser().feed(input)
    except: pass
    return print_maze("INVALID", %d, %d)
""" % (row, col, row, col)

def generate_good_tile(c, row, col):
    code = """
def tile_%d_%d(input, index):
    if (index == len(input)): return print_maze("VALID", %d, %d)
    elif input[index] == 'L': return tile_%d_%d(input, index + 1)
    elif input[index] == 'R': return tile_%d_%d(input, index + 1)
    elif input[index] == 'U': return tile_%d_%d(input, index + 1)
    elif input[index] == 'D': return tile_%d_%d(input, index + 1)
    else : return tile_%d_%d(input, index + 1)
""" % (row, col, row, col,
       row, col - 1, 
       row, col + 1, 
       row - 1, col, 
       row + 1, col,
       row, col)

    if c == "X":
        code += """
def maze(input):
    return tile_%d_%d(list(input), 0)
""" % (row, col)

    return code


def generate_target_tile(row, col):
    return """
def tile_%d_%d(input, index):
    return print_maze("SOLVED", %d, %d)

def target_tile():
    return "tile_%d_%d"
""" % (row, col, row, col, row, col)

def generate_maze_code(maze, name="maze"):
    row = 0
    col = 0
    code = generate_print_maze(maze)

    for c in list(maze):
        if c == '\n':
            row += 1
            col = 0
        else:
            if c == "-" or c == "+" or c == "|":
                code += generate_trap_tile(row, col)
            elif c == " " or c == "X":
                code += generate_good_tile(c, row, col)
            elif c == "#":
                code += generate_target_tile(row, col)
            else:
                print("Invalid maze! Try another one.")
            col += 1

    return code