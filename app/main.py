import os
import readline
import shutil
import subprocess
import sys

COMMANDS = ["echo", "type", "exit", "pwd", "cd"]

def tokenize_input(ipt: str):
    """Splits user input while keeping input in single and double quotes literal."""
    tokens = []
    current = []
    in_single_quote = False
    in_double_quote = False
    has_escape = False
    has_one = False
    has_two = False
    pending_append = False

    for char in ipt:

        if has_escape:
            if in_double_quote:
                if char in ['"', "\\"]:
                    current.append(char)
                else:
                    current.append("\\")
                    current.append(char)
            else:
                current.append(char)
            has_escape = False
            continue

        if char == "\\" and not in_single_quote:
            has_escape = True
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            continue

        if pending_append and not in_single_quote and not in_double_quote:
            if char == ">":
                # change previous token to '>>'
                if tokens and tokens[-1].endswith(">"):
                    tokens[-1] = tokens[-1] + ">"
                pending_append = False
                continue
            else:
                # keep previous token as-is
                pending_append = False

        if has_one:
            if char == ">":
                if current:
                    tokens.append("".join(current))
                    current = []
                tokens.append(">")
                pending_append = True
                has_one = False
                continue
            else:
                current.append("1")
                has_one = False

        if has_two:
            if char == ">":
                if current:
                    tokens.append("".join(current))
                    current = []
                tokens.append("2>")
                pending_append = True
                has_two = False
                continue
            else:
                current.append("2")
                has_two = False

        if char == ">" and not in_single_quote and not in_double_quote:
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(">")
            pending_append = True
            continue            

        if char == "1" and not in_single_quote and not in_double_quote:
            has_one = True
            continue

        if char == "2" and not in_single_quote and not in_double_quote:
            has_two = True
            continue

        if char.isspace() and not in_single_quote and not in_double_quote:
            if current:
                tokens.append("".join(current))
                current = []

            continue

        current.append(char)

    if has_one:
        current.append("1")

    if has_two:
        current.append("2")

    if current:
        tokens.append("".join(current))

    return tokens

def get_executables_in_path():
    executables = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(directory):
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.access(filepath, os.X_OK) and not os.path.isdir(filepath):
                    executables.add(filename)
    return sorted(executables)

def complete(text, state):
    # commands = command + executable files in PATH
    commands = COMMANDS + get_executables_in_path()
    options = [cmd for cmd in commands if cmd.startswith(text)]
    if state < len(options):
        if len(options) == 1 and state == 0:
            return options[state] + " "
        return options[state]
    else:
        return None
    
def setup_readline():
    readline.set_completer(complete)

    # libedit (macOS default) vs GNU readline
    if "libedit" in readline.__doc__:
        # macOS / libedit syntax
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        # GNU readline syntax
        readline.parse_and_bind("tab: complete")


def main():
    setup_readline()

    while True:
        try:
            sys.stdout.write("$ ")
            ipt = input()

            parts = tokenize_input(ipt)

            if not parts:
                continue

            redirect_path = None
            error_path = None
            has_append = False

            if ">" in parts or ">>" in parts:
                if ">>" in parts:
                    idx = parts.index(">>")
                    has_append = True
                else:
                    idx = parts.index(">")

                if idx == len(parts) - 1:
                    print("Syntax error: no file specified for redirection", file=sys.stderr)
                    continue

                redirect_path = parts[idx + 1]
                parts = parts[:idx] + parts[idx + 2:]

                if not parts:
                    print("Syntax error: no command specified before redirection", file=sys.stderr)
                    continue

            if "2>" in parts or "2>>" in parts:
                if "2>>" in parts:
                    idx = parts.index("2>>")
                    has_append = True
                else:
                    idx = parts.index("2>")
                
                if idx == len(parts) - 1:
                    print("Syntax error: no file specified for error redirection", file=sys.stderr)
                    continue

                error_path = parts[idx + 1]
                parts = parts[:idx] + parts[idx + 2:]

                if not parts:
                    print("Syntax error: no command specified before error redirection", file=sys.stderr)
                    continue

            command = parts[0]
            args = parts[1:]

            redirect_stream = None
            target_stream = sys.stdout
            error_stream = sys.stderr

            if redirect_path:
                try:
                    if has_append:
                        redirect_stream = open(redirect_path, "a")
                    else:
                        redirect_stream = open(redirect_path, "w")
                    target_stream = redirect_stream
                except OSError as exc:
                    print(f"Error opening file {redirect_path} for writing: {exc}", file=sys.stderr)
                    continue

            if error_path:
                try:
                    if has_append:
                        error_stream = open(error_path, "a")
                    else:
                        error_stream = open(error_path, "w")
                except OSError as exc:
                    print(f"Error opening file {error_path} for writing: {exc}", file=sys.stderr)
                    if redirect_stream:
                        redirect_stream.close()
                    continue
            
            try:
                if command == "exit":
                    sys.exit(0)
                elif command == "echo":
                    print(" ".join(args), file=target_stream)
                elif command == "type":
                    if not args:
                        continue
                    target = args[0]
                    if target in COMMANDS:
                        print(f"{target} is a shell builtin", file=target_stream)
                    else:
                        path = shutil.which(target)
                        if path is None:
                            print(f"{target}: not found", file=target_stream)
                        else: 
                            # get absolute path
                            print(f"{target} is {path}", file=target_stream)
                elif command == "pwd":
                    print(os.getcwd(), file=target_stream)
                elif command == "cd":
                    if not args:
                        target_dir = os.environ.get("HOME", "")
                    else:
                        target_dir = args[0]

                    # support 'cd' with both absolute and relative path
                    home = os.environ.get('HOME')
                    if target_dir == "~":
                        target_dir = home

                    # try to change directory, return error if fails
                    try:
                        os.chdir(target_dir)
                    except FileNotFoundError:
                        print(f"cd: no such file or directory: {target_dir}", file=error_stream)
                else:
                    # Check if command exists in system PATH
                    path = shutil.which(command)
                    if path is None:
                        print(f"{command}: command not found", file=error_stream)
                    else:
                        subprocess.run(
                            [command] + args,
                            stdout=redirect_stream if redirect_stream else None,
                            stderr=error_stream if error_path else None,
                        )
            finally:
                if redirect_stream:
                    redirect_stream.close()
                if error_path and error_stream not in (None, sys.stderr):
                    error_stream.close()
        except EOFError:
            break

if __name__ == "__main__":
    main()
