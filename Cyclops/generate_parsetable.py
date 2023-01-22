import sys
import imp
import os

# import pandas as pd 
sys.setrecursionlimit(80)

if len(sys.argv)!=2:
    # print("Server Error")
    sys.exit(0)

inputFile = sys.argv[1].split('/')[-1].replace('.','')
packageLink = '/cyclopsWeb/inputs/' + str(sys.argv[1])
handle = imp.load_source(inputFile, packageLink)


def find_original_grammar():
    original_grammar = handle.find_original_grammar()
    return original_grammar

def get_parse_table():
    parse_table=handle.get_parse_table()
    return parse_table

grammar=find_original_grammar()
inp_parse_table=get_parse_table()

non_terms=[]
terms=[]
terms2=[]

for nt in inp_parse_table:
    non_terms.append(nt['non_term'])

for t in grammar:
    for p in t:
        if p not in terms and p not in non_terms:
            terms.append(p)
# terms.append('$')
terms2=terms
terms2.append('$')
terms2.remove('eps')
var=non_terms+terms

# print("GRAMMAR: \n", grammar)

productions=dict()
flag = 0

for t in range(len(grammar)):
    for i in range(len(grammar[t])):
        if i==0 and grammar[t][1]=='eps':
            productions[t+1] = grammar[t][0:1]
            productions[t+1].append('@')
            flag=1
            break
        elif i!=0 and grammar[t][i]=='eps':
            productions[t+1] = grammar[t][0:i]
            flag=1
            break
    if flag==0:
        productions[t+1] = grammar[t]

# print("PRODUCTIONS:\n", productions)

prod_dict=dict()

for p in range(len(productions)):
    s=''
    for k in range(len(productions[p+1])):
        if k==0: 
            continue
        s+=productions[p+1][k] + '_'
    s= s[0:-1]
    # prod_dict.update({productions[p+1][0]: s})
    n = [s]
    if productions[p+1][0] in prod_dict:
        st = prod_dict[productions[p+1][0]]
        st.append(s)
        # prod_dict[productions[p+1][0]].append(n)
        prod_dict.update({productions[p+1][0]: st})
    else:
        prod_dict[productions[p+1][0]] = n
    # prod_dict[p[0]]= s 

# print("DICTIONARY:\n", prod_dict)

def first(string):
    # i=0
    # print("STR",string[i:])
    # print("first({})".format(string))
    first_ = set()
    if string in non_terminals:
        # print("STR", string)
        alternatives = prod_dict[string]

        for alternative in alternatives:
            first_2 = first(alternative)
            first_ = first_ |first_2

    elif string in terminals:
        first_ = {string}

    elif string=='' or string=='@':
        first_ = {'@'}

    else:
        w=str(string[0:]).split("_")
        # print("STR",string[0:])
        # print(w[0])
        # print(type(w[0]))
        # print(string[0])
        # print(type(string[0]))
        first_2 = first(w[0])
        if '@' in first_2:
            i = 1
            while '@' in first_2:
                # print("inside while")

                first_ = first_ | (first_2 - {'@'})
                # print('string[i:]=', string[i:])
                if string[i:] in terminals:
                    first_ = first_ | {string[i:]}
                    break
                elif string[i:] == '':
                    first_ = first_ | {'@'}
                    break
                # print("STRFIRST",string[i:])
                first_2 = first(string[i:])
                first_ = first_ | first_2 - {'@'}
                i += 1
        else:
            first_ = first_ | first_2
    # print("returning for first({})".format(string),first_)
    return  first_


def follow(nT):
    # print("inside follow({})".format(nT))
    follow_ = set()
    # print("FOLLOW", FOLLOW)
    prods = prod_dict.items()
    # print("PRODS",prods)
    if nT==starting_symbol:
        follow_ = follow_ | {'$'}
    for nt,rhs in prods:
        # print("nt to rhs", nt,rhs)
        for alt in rhs:
            # print("ALT", alt)
            w=str(alt[0:]).split("_")
            for char in w:
                # print("CHAR", char)

                if char==nT:
                    # print("NTt",nT)
                    following_str = alt[alt.index(char)+len(char):]
                    # following_str = alt[alt.index('_')+1:]
                    # print()
                    if following_str=='':
                        # print("NT",nt)
                        if nt==nT:
                            continue
                        else:
                            follow_ = follow_ | follow(nt)
                    else:
                        # print("FSTR1",following_str)
                        if following_str[0]=='_':
                            following_str=following_str[1:]
                        # print("FSTR2",following_str)
                        # print("NT",nt)
                        follow_2 = first(following_str)
                        if '@' in follow_2:
                            follow_ = follow_ | follow_2-{'@'}
                            follow_ = follow_ | follow(nt)
                        else:
                            follow_ = follow_ | follow_2
    # print("returning for follow({})".format(nT),follow_)
    return follow_

def parsetable(follow, productions):
    
    # print("\nParsing Table\n")

    table = {}
    number_table = {}
    c=1
    for key in productions:
        for i in range(len(productions[key])):
            value = productions[key][i]
            if value!='@':
                for element in first(value):
                    table[key, element] = value.replace("_", " ")
                    number_table[key, element] = c
                    # print("NUMB, key, element, c, i",number_table[key, element], key, element, c, i)
            else:
                for element in follow[key]:
                    table[key, element] = value.replace("_", " ")
                    number_table[key, element] = c
                    # print("NUMB, key, element, c, i",number_table[key, element], key, element, c, i)
            c+=1

    # for key,val in number_table.items():
        # print (key,"=>",val)

    new_table = {}
    for pair in table:
        new_table[pair[1]] = {}

    for pair in table:
        # print("PAIRR", type(pair))
        new_table[pair[1]][pair[0]] = table[pair]


    # print ("\n")
    # print ("\nParsing Table in matrix form\n")
    # print (pd.DataFrame(new_table).fillna('0'))
    # print ("\n")

    for pair in table:
        new_table[pair[1]][pair[0]] = int(number_table[pair])

    # print ("\nParsing Table with numbers in matrix form\n")
    # print (pd.DataFrame(new_table).fillna('-'))
    # print ("\n")

    return number_table

def compare(PT, pti):
    comp = pti
    i=0
    correct=1
    for row in pti:
        # print("ROWW", row)
        nt = row['non_term']
        # comp['non_term'] =
        for t in terms2:
            # comp[i][t]=8
            # print("PAIRR", type(pair))
            if (nt,t) in PT:
                # print("row[t],PT[nt,t]: ",row[t],PT[nt,t])
                if int(row[t]) == int(PT[nt,t]):
                    comp[i][t] = 1
                else:
                    comp[i][t] = 0
                    correct=0
            else:
                comp[i][t] = 1
        i+=1
    return comp, correct


non_terminals = non_terms
terminals = terms
starting_symbol = productions[1][0]

FIRST = {}
FOLLOW = {}

for non_terminal in non_terminals:
    FIRST[non_terminal] = set()

for non_terminal in non_terminals:
    FOLLOW[non_terminal] = set()

# print("FIRST",FIRST)

for non_terminal in non_terminals:
    # print("NT",non_terminal)
    FIRST[non_terminal] = FIRST[non_terminal] | first(non_terminal)

# print("FIRST",FIRST)

FOLLOW[starting_symbol] = FOLLOW[starting_symbol] | {'$'}
for non_terminal in non_terminals:
    # print("NThhhh",non_terminal)
    FOLLOW[non_terminal] = FOLLOW[non_terminal] | follow(non_terminal)

# print("FOLLOW", FOLLOW)
# print('\n')
# print("{: ^20}{: ^20}{: ^20}".format('Non Terminals','First','Follow'))
# for non_terminal in non_terminals:
# print("{: ^20}{: ^20}{: ^20}".format(non_terminal,str(FIRST[non_terminal]),str(FOLLOW[non_terminal])))

parse_table = parsetable(FOLLOW, prod_dict)

# print(parse_table)

# print(get_parse_table())

ctab, corr = compare(parse_table,get_parse_table())
# print("COMPARISON:\n", ctab)
if corr:
    print("0,0,0,0,0,0,0,0")
else:
    tmp="python2 cyclops.py " + sys.argv[1]
    try:
        output,error=os.system(tmp)
        print(output)
    except:
        print("Execution Failed")
