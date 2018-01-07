import capstone
import keystone

import utils
from modules.unicorndbgmodule import AbstractUnicornDbgModule


class ASM(AbstractUnicornDbgModule):
    def __init__(self, core_instance):
        AbstractUnicornDbgModule.__init__(self, core_instance)

        # we can hold keystone instance here
        self.keystone_instance = None

        self.context_name = "asm_module"
        self.command_map = {
            'dis': {
                'ref': "disassemble",
            },
            'disasm': {
                'ref': "disassemble",
            },
            'asm': {
                'ref': "assemble",
            },
            'assemble': {
                'short': 'asm',
                'function': {
                    "context": "asm_module",
                    "f": "assemble"
                },
                'help': 'assemble instructions',
                'usage': 'asm *instructions (\'mov r1, r3;add r0, r3, r2\') [! (will trigger arch/mode config)]'
            },
            'disassemble': {
                'short': 'dis,disasm',
                'usage': 'disasm *hex_payload [arch (arm)] [mode (thumb)]',
                'help': 'disassemble instructions',
                'function': {
                    "context": "asm_module",
                    "f": "disassemble"
                }
            },
        }

    def assemble(self, func_name, *args):
        sp = bytes(' ', 'utf8')
        instr = bytes()

        i = 0
        while i < len(args):
            a = str(args[i])
            if a.startswith("'") or a.startswith('"'):
                a = a[1:]
            b = False
            if a.endswith("'") or a.endswith('"'):
                a = a[:len(a) - 1]
                b = True
            instr += bytes(a, 'utf8')
            if not b:
                instr += sp
            i += 1
            if b:
                break

        if str(args[i]) == '!':
            self.keystone_instance = None

        if self.keystone_instance is None:
            arch = getattr(keystone, self.prompt_ks_arch())
            mode = getattr(keystone, self.prompt_ks_mode())
            self.keystone_instance = keystone.Ks(arch, mode)
        try:
            encoding, count = self.keystone_instance.asm(instr)
            h = ''
            for i in range(0, len(encoding)):
                h += hex(encoding[i])[2:]
            print("%s = %s (number of statements: %u)" % (str(instr), h, count))
        except keystone.KsError as e:
            print("ERROR: %s" % e)

    def disassemble(self, func_name, *args):
        p = bytes.fromhex(args[0])
        off = 0x00
        if len(args) == 1:
            cs = self.core_instance.get_cs_instance()
            for i in cs.disasm(p, off):
                print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
        else:
            try:
                arch = getattr(capstone.__all__, 'CS_ARCH_' + str(args[0]).upper())
            except Exception as e:
                raise Exception('arch not found')
            mode = self.core_instance.get_cs_mode()
            if len(args) > 2:
                try:
                    arch = getattr(capstone.__all__, 'CS_MODE_' + str(args[0]).upper())
                except Exception as e:
                    raise Exception('mode not found')
            cs = capstone.Cs(arch, mode)
            for i in cs.disasm(p, off):
                print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))

    def prompt_ks_arch(self):
        items = [k for k, v in keystone.__dict__.items() if not k.startswith("__") and k.startswith("KS_ARCH")]
        return utils.prompt_list(items, 'arch', 'Select arch')

    def prompt_ks_mode(self):
        items = [k for k, v in keystone.__dict__.items() if not k.startswith("__") and k.startswith("KS_MODE")]
        return utils.prompt_list(items, 'mode', 'Select mode')

    def init(self):
        pass

    def delete(self):
        pass
