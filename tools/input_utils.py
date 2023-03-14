#!/usr/bin/env python3

def yn_input(q, default_ret='Y'):
    if default_ret == 'Y': tail = ' [Y/n] '
    elif default_ret == 'N': tail = ' [y/N] '
    else: tail = ' [y/n] '
    while True:
        yn = input(q+tail).strip().upper()
        if yn == '': yn = default_ret
        if yn in ('Y', 'N'): break
        print('Not understood')
    return yn

def choice_input(lst, q, q_one='Choose this one?'):
    ret = None
    print('\n'.join(str(i+1)+': '+k for i, k in enumerate(lst)))
    nbmax = len(lst)
    while ret is None:
        if nbmax == 0: return None
        elif nbmax == 1:
            yn = yn_input(q_one)
            if yn == 'Y': return 0
            if yn == 'N': return None
        else:
            nb = input(q+' [1-' + str(nbmax) + '] ').strip()
            try:
                nb = int(nb)
            except:
                continue
            if nb > 0 and nb <= nbmax: return nb
            print('Not understood')

if __name__ == '__main__':
    import sys

    lst = ['Yes/no', 'quit']

    nb = choice_input(lst, 'What to do?')
    if nb == 1:
        yn = yn_input('Yes or no?')
        print('You said ' + ('yes' if yn == 'Y' else 'no'))
