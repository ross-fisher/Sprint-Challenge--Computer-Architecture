"""CPU functionality."""

import sys

def filterl(f, coll):
    return list(filter(f, coll))

def mapl(f, coll):
    return list(map(f, coll))


def top(byte, n):
    "Read top n digits from a byte"
    return byte >> (8 - n)


def bottom(byte, n):
    "Read bottom n digits from a byte"
    return byte & ((2**n)-1)


def read_register(x):
    return bottom(x, 3)


class CPU:
    """Main CPU class."""


# * `PC`: Program Counter, address of the currently executing instruction
# * `IR`: Instruction Register, contains a copy of the currently executing instruction
# * `MAR`: Memory Address Register, holds the memory address we're reading or writing
# * `MDR`: Memory Data Register, holds the value to write or the value just read
# * `FL`: Flags, see below


# The flags register `FL` holds the current flags status. These flags
# can change based on the operands given to the `CMP` opcode.

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 2**8
        self.reg = [0] * 8
        self.pc = 0
        self.ir = 0
        self.mar = 0  # memory address register (is being read or written to)
        self.mdr = 0  # memory data register (was read or written to)
        self.fl = 0
        self.sp = 0xf3


        # SP Stack Pointer. Points to the top of the stack
        # self.sp


    def load(self, program=None):
        """Load a program into memory."""

        address = 0

        content = []
        import re
        with open(program) as f:
            content = f.readlines()

        # remove comments
        for i, line in enumerate(content):
            content[i] = re.sub(re.compile('#.*'), "", line).strip()

        content = filter(bool, content)  # remove empty strings
        content =  map(lambda s: int(s, 2), content) # read number, convert from base 2

        program = content


        for instruction in program:
            self.ram[address] = instruction
            address += 1


    def alu(self, op, a, b):
        """ALU operations."""

        if op == 0xA0: # add
            self.reg[a] += self.reg[b]
        elif op == 0xA1: # sub
            self.reg[a] -= self.reg[b]
        elif op == 0xA2: #mult
            self.reg[a] *= self.reg[b]
        elif op == 0xA3: # div TODO call hlt
            if self.reg[b] == 0:
                raise Exception('Division by 0')
            else:
                self.reg[a] /= self.reg[b]
        elif op == 0xA7:
            if self.reg[a] < self.reg[b]:
                self.fl = 1
            elif self.reg[a] == self.reg[b]:
                self.fl = 2
            elif self.reg[a] > self.reg[b]:
                self.fl = 3


        elif op == 0xA8:
            self.reg[a] &= self.reg[b]
        else:
            raise Exception("Unsupported ALU operation")

    def other(self, op, a, b):
        if op == 0x82: # ldi
            self.reg[a] = b
        elif op == 0x47: # prn
            print(self.reg[a])
        elif op == 0x01: # hlt
            raise Exception('Halt')
        elif op == 0x50: # call
            # push the address right after this call instruction onto the stack so
            # we can return to it
            self.stack_push(self.pc + 2)
            self.pc = self.reg[a]
        elif op == 0x11:
            val = self.stack_pop()
            self.pc = val
        elif op == 0x54: # jmp
            self.pc = self.reg[a]
        elif op == 0x55: # jeq
#            print('JEQ', self.fl)
            if self.fl == 2: # equal
                self.pc = self.reg[a]
            else:
                self.pc += 2
            self.fl = 0
        elif op == 0x56:
            if self.fl == 1 or self.fl == 3: # neq
                self.pc = self.reg[a]
            else:
                self.pc += 2
            self.fl = 0


    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()


    def read_opcode(self):
        self.ir = self.ram_read(self.pc)
        a2 = top(self.ir, 2) # number of bytes to read extra
        b = bottom(top(self.ir, 3), 1) # if set to 1, alu operation
        c = bottom(top(self.ir, 4), 1) # if set to 1, don't increment pc
        d4 = bottom(self.ir, 4) # instruction identifier (not using right now)

#        print('Ram', self.ram)

        A = 0
        B = 0
        if a2 > 0:
            A = self.ram_read(self.pc + 1)
        if a2 > 1:
            B = self.ram_read(self.pc + 2)

        # b 1 if is an alu operation
        if b == 1:
            self.alu(self.ir, A, B)
        else:
            self.other(self.ir, A, B)

        if c == 0:
            self.pc += 1 + a2


    def run(self):
        """Run the CPU."""
        self.trace()
        while True:
            self.read_opcode()
#            print(self.ram)
#            input()



    def ram_read(self, position):
#        print(position)
#        print(self.ram[position:])
        self.mar = position
        self.mdr = self.ram[self.mar]
        return self.mdr


    def ram_write(self, position, number):
        self.mar = position
        self.mdr = number
        return self.mdr


    def stack_push(self, value):
        self.ram[self.sp] = value
        self.sp -= 1


    def stack_pop(self):
        self.sp += 1
        value = self.ram[self.sp]
        return value


