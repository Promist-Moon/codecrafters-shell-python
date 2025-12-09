import os
import sys


def main():
    while True:
        sys.stdout.write("$ ")

        commands = ["echo", "type", "exit"]
        
        command = input()
        if command == "exit":
            sys.exit(0)
        elif command.startswith("echo"):
            print(command[5:])
        elif command.startswith("type"):
            cmd = command[5:]
            if cmd in commands:
                print(f"{cmd} is a shell builtin")
            elif os.access(cmd, os.X_OK):
                # get absolute path
                print(f"{cmd} is {os.path.abspath(cmd)}")
            else:
                print(f"{cmd}: not found")
        else:
            print(f"{command}: command not found")
        pass


if __name__ == "__main__":
    main()
