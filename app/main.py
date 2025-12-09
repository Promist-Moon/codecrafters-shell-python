import os
import shutil
import sys


def main():
    while True:
        sys.stdout.write("$ ")

        commands = ["echo", "type", "exit"]
        
        ipt = input()
        parts = ipt.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        if command == "exit":
            sys.exit(0)
        elif command == "echo":
            print(command[5:])
        elif command == "type":
            if args in commands:
                print(f"{args} is a shell builtin")
            elif shutil.which(args):
                # get absolute path
                print(f"{args} is {os.path.abspath(args)}")
            else:
                print(f"{args}: not found")
        else:
            print(f"{command}: command not found")
        pass


if __name__ == "__main__":
    main()
