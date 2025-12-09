import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        
        command = input()
        if command == "exit":
            sys.exit(0)
        else:
            print(f"{command}: command not found")
        pass


if __name__ == "__main__":
    main()
