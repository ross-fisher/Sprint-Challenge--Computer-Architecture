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


def bit_not(n, numbits=8):
    return (1 << numbits) - 1 - n


class CPU:
    """Main CPU class."""

IM = 5
IS = 6
SP = 7


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
        self.reg[7] = 0xf3 # stack pointer


        # SP Stack Pointer. Points to the top of the stack
        # self.sp

    def get_interrupt(self, i):
        return self.ram[0xff - i]


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
        elif op == 0xA8: # and
            self.reg[a] &= self.reg[b]
        elif op == 0xAA: # or
            self.reg[a] |= self.reg[b]
        elif op == 0xAB: # xor
            self.reg[a] ^= self.reg[b]
        elif op == 0x69: # not
            self.reg[a] = bit_not(self.reg[a], numbits=8)
        elif op == 0xAC: # shl
            self.reg[a] <<= self.reg[b]
        elif op == 0xAD: # shl
            self.reg[a] >>= self.reg[b]
        elif op == 0xA4: # mod
            if self.reg[b] == 0:
                raise Exception('Mod by 0')
            self.reg[a] %= self.reg[b]
        elif op == 0x99: # addi
            self.reg[a] += b

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
        elif op == 0x56: #jne
            if self.fl == 1 or self.fl == 3: # neq
                self.pc = self.reg[a]
            else:
                self.pc += 2
            self.fl = 0
        elif op == 0x52: # int
            self.reg[IS] |= (1 << self.reg[a])
        elif op == 0x13: # iret
            for i in range(6, -1, -1):
                self.reg[i] = self.stack_pop()
            self.fl = self.stack_pop()
            self.pc = self.stack_pop()
            self.interrupts_enabled = True


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

    def handle_interrupts(self):
        if self.reg[IM] != 0 and self.interrupts_enabled:
            maskedInterrupts = self.reg[IS]  & self.reg[IM]
            i = 0
            while maskedInterrupts > 0:
                interrupt = maskedInterrupts & 1
                if interrupt:
                    # disable further interrupts
                    self.interrupts_enabled = False
                    self.reg[IS] &= bit_not(i) # clear the bit (set nth bit to 0)
                    self.stack_push(self.pc)
                    self.stack_push(self.fl)
                    for i in range(0, 7, 1):
                        self.stack_push(self.reg[i])

                    interupt_handler = self.get_interrupt(i)
                    self.pc = interrupt_handler

                maskedInterrupts >>= 2
                i += 1



    def run(self):
        """Run the CPU."""
        self.trace()
        while True:
            self.read_opcode()
            self.handle_interrupts()
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
        self.ram[self.reg[7]] = value
        self.reg[7] -= 1


    def stack_pop(self):
        self.reg[7] += 1
        value = self.ram[self.reg[7]]
        return value


