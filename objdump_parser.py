#!/usr/bin/env python3

import sys
import subprocess
import math
from operator import add
from functools import reduce
from itertools import cycle
from pprint import pprint


skip_sections = ['.init', '.fini', '.plt', '.plt.got']
O = cycle((0, ))


def distance(p0, p1):
    return math.sqrt(reduce(add, map(lambda x: (x[0] - x[1]) ** 2, zip(p0, p1)), 0))


def dict_distance(d0, d1):
    keys = set(d0.keys()).union(set(d1.keys()))
    p0 = tuple(d0[k] if k in d0 else 0 for k in keys)
    p1 = tuple(d1[k] if k in d1 else 0 for k in keys)
    return distance(p0, p1) / max(distance(p0, O), distance(p1, O)) * 100



def decodeelf(f):
    p = subprocess.Popen(('objdump', '-d', f), stdout=subprocess.PIPE)

    d_sections = {}
    d_funcs = None
    d_inst = None
    cur_func = ''

    for l in p.stdout:
        l = l.decode()
        if l.startswith('Disassembly of section '):
            d_funcs = {}
            section = l[23:-2]
            if section not in skip_sections:
                d_sections[section] = d_funcs
        elif l.endswith('>:\n'):
            d_inst = {}
            d_funcs[l[18:-3]] = d_inst
        else:
            l = l.split('\t')
            if len(l) != 3:
                continue
            inst = l[2].split()[0]
            if inst in d_inst:
                d_inst[inst] += 1
            else:
                d_inst[inst] = 1

    return d_sections


if len(sys.argv) == 2:
    pprint(decodeelf(sys.argv[1]))
elif len(sys.argv) == 3:
    profile1 = decodeelf(sys.argv[1])
    profile2 = decodeelf(sys.argv[2])
    for section in set(profile1.keys()).union(set(profile2.keys())):
        if (section in profile1) ^ (section in profile2):
            if section in profile1:
                print(f'{section} only in elf1')
            else:
                print(f'{section} only in elf2')
            print()
            continue
        print(f'section {section}:')

        section1 = profile1[section]
        section2 = profile2[section]
        d_func_score = {}
        for func in set(section1.keys()).union(set(section2.keys())):
            if (func in section1) ^ (func in section2):
                if func in section1:
                    print(f' {func} only in elf1')
                else:
                    print(f' {func} only in elf2')
                continue
            d_func_score[func] = dict_distance(section1[func], section2[func])
        for func in sorted(d_func_score.keys(), key=d_func_score.get, reverse=True):
            if d_func_score[func] == 0:
                break
            print(f' <{func}>: {d_func_score[func]}')
        print()

else:
    print(f'usage: {sys.argv[0]} elf1 [elf2]')
