import sys

print_yo = 1
halt = 2

memory = [
        print_yo,
        print_yo,
        print_yo,
        print_yo,
        print_yo,
        print_yo,
        halt]

pc = 0
running = True

while running:
    command = memory[pc]


    if command == print_yo:
        print('yo')
    elif command == halt:
        running = False

    pc += 1
