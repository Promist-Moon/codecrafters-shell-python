import os
import shutil
import subprocess
import sys


def tokenize_input(ipt: str):
    """Splits user input while keeping input in single and double quotes literal."""
    tokens = []
    current = []
    in_single_quote = False
    in_double_quote = False
    has_escape = False
    has_one = False

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

        if has_one:
            if char == ">":
                if current:
                    tokens.append("".join(current))
                    current = []
                tokens.append(">")
                has_one = False
                continue
            else:
                current.append("1")
                has_one = False

        if char == ">" and not in_single_quote and not in_double_quote:
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(">")
            continue

        if char == "1" and not in_single_quote and not in_double_quote:
            has_one = True
            continue

        if char.isspace() and not in_single_quote and not in_double_quote:
            if current:
                tokens.append("".join(current))
                current = []

            continue

        current.append(char)

    if current:
        tokens.append("".join(current))

    return tokens


def main():
    while True:
        sys.stdout.write("$ ")

        commands = ["echo", "type", "exit", "pwd", "cd"]
        
        ipt = input()
        parts = tokenize_input(ipt)

        if not parts:
            continue

        redirect_path = None
        if ">" in parts:
            idx = parts.index(">")
            if idx == len(parts) - 1:
                print("Syntax error: no file specified for redirection", file=sys.stderr)
                continue

            redirect_path = parts[idx + 1]
            parts = parts[:idx] + parts[idx + 2:]

            if not parts:
                print("Syntax error: no command specified before redirection", file=sys.stderr)
                continue

        command = parts[0]
        args = parts[1:]

        redirect_stream = None
        target_stream = sys.stdout

        if redirect_path:
            try:
                redirect_stream = open(redirect_path, "w")
                target_stream = redirect_stream
            except OSError as exc:
                print(f"Error opening file {redirect_path} for writing: {exc}", file=sys.stderr)
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
                if target in commands:
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
                    print(f"cd: no such file or directory: {target_dir}", file=sys.stderr)
            else:
                # Check if command exists in system PATH
                path = shutil.which(command)
                if path is None:
                    print(f"{command}: command not found", file=sys.stderr)
                else:
                    if redirect_stream:
                        subprocess.run([command] + args, stdout=redirect_stream)
                    else:
                        subprocess.run([command] + args)
        finally:
            if redirect_stream:
                redirect_stream.close()


if __name__ == "__main__":
    main()
