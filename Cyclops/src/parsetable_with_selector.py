import sys
import pandas as pd 
sys.setrecursionlimit(80)

def find_original_grammar():
    # original_grammar = [['S','a','A','B','b'],['A','a','A','c','eps'],['A','eps','eps','eps','eps'],['B','b','B','eps','eps'],['B','c','eps','eps','eps']]
    original_grammar = [['SS','aa','AA','BB','bb'],['AA','aa','AA','cc','eps'],['AA','eps','eps','eps','eps'],['BB','bb','BB','AA','eps'],['BB','cc','eps','eps','eps']]
    return original_grammar

def get_parse_table():
    # parse_table = [{'non_term':'S' ,'a':1 ,'b':0 ,'c':0 ,'$':0},{'non_term':'A' ,'a':2 ,'b':3 ,'c':3 ,'$':0},{'non_term':'B' ,'a':0 ,'b':4 ,'c':5 ,'$':0}]
    parse_table = [{'non_term':'SS' ,'aa':1 ,'bb':0 ,'cc':0 ,'$':0},{'non_term':'AA' ,'aa':2 ,'bb':3 ,'cc':3 ,'$':0},{'non_term':'BB' ,'aa':0 ,'bb':4 ,'cc':5 ,'$':0}]
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

print("PRODUCTIONS:\n", productions)

prod_dict=dict()

for p in range(len(productions)):
    s=''
    for k in range(len(productions[p+1])):
        if k==0: 
            continue
        s+=productions[p+1][k] + '_'
    s= s[0:-1]
    n = [s]
    if productions[p+1][0] in prod_dict:
        st = prod_dict[productions[p+1][0]]
        st.append(s)
        prod_dict.update({productions[p+1][0]: st})
    else:
        prod_dict[productions[p+1][0]] = n

print("PROD DICTIONARY:\n", prod_dict)
selector1 = 0
selector2 = 0
selector3 = 0
selector4 = 0
selector5 = 0
selector6 = 0
selector7 = 0
selector8 = 0

def first(string):
    # i=0
    # print("STR",string[i:])
    # print("first({})".format(string))
    first_ = set()
    if string in non_terminals and selector2==0:    ## selector2
        # print("STR", string)
        alternatives = prod_dict[string]

        for alternative in alternatives:
            first_2 = first(alternative)
            first_ = first_ |first_2

    elif string in terminals and selector1==0:   ## selector1
        first_ = {string}

    elif string=='' or string=='@' and selector3==0:     ## selector3
        first_ = {'@'}

    # elif selector2==0 and selector1==0 and selector3==0:
    else:
        w=str(string[0:]).split("_")
        # print("STR",string[0:])
        # print(w[0])
        # print(type(w[0]))
        # print(string[0])
        # print(type(string[0]))\

        if selector1==1 and w[0] in terminals:
            first_2=set()
        elif selector2==1 and w[0] in non_terminals:
            first_2=set()
        elif selector3==1 and (w[0]=='' or w[0]=='@'):
            first_2=set()
        else:
            first_2 = first(w[0])
            if '@' in first_2:
                i = 1
                while '@' in first_2:
                    # print("inside while")

                    first_ = first_ | (first_2 - {'@'})
                    # print('string[i:]=', string[i:])
                    if string[i:] in terminals:
                        print(string[i:])
                        first_ = first_ | {string[i:]}  ## selector1
                        break
                    elif string[i:] == '':    ## selector3
                        print(string[i:])
                        first_ = first_ | {'@'}
                        break
                    # print("STRFIRST",string[i:])
                    first_2 = first(string[i:])
                    first_ = first_ | first_2 - {'@'}
                    i += 1
            else:
                first_ = first_ | first_2    ## selector2
    # print("returning for first({})".format(string),first_)
    return first_


def follow(nT):
    # print("inside follow({})".format(nT))
    follow_ = set()
    # print("FOLLOW", FOLLOW)
    prods = prod_dict.items()
    # print("PRODS",prods)
    if nT==starting_symbol and selector4==0:      ## selector4
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
                    # print("FSTR", following_str)
                    if following_str=='' and selector6==0:
                        # print("NT",nt)
                        if nt==nT:
                            continue
                        else:
                            follow_ = follow_ | follow(nt)   
                    elif following_str!='':
                    # else:
                        # print("FSTR1",following_str)
                        if following_str[0]=='_':
                            following_str=following_str[1:]
                        # print("FSTR2",following_str)
                        # print("NT",nt)
                        follow_2 = first(following_str)
                        if '@' in follow_2 and selector6==0:
                            # print("EEEEE")
                            follow_ = follow_ | follow_2-{'@'}
                            # follow_ = follow_ | follow(nT)
                        elif selector5==0:
                        # else:
                            follow_ = follow_ | follow_2
    # print("returning for follow({})".format(nT),follow_)
    return follow_

def parsetable(fir, fol, productions):
    
    # print("\nParsing Table\n")

    table = {}
    number_table = {}
    c=1
    prodKeys = [i for i in productions.keys()]
    prodKeys.sort()
    # print("PK", prodKeys)

    #for key in prodKeys
    for key in productions:
        # print(key)

        for i in range(len(productions[key])):
            value = productions[key][i]
            if value!='@' and selector7==0:
                for element in first(value):
                    if (key, element) in table:
                        print("ERROR, NOT AN LL1 GRAMMAR")
                        # break
                    else:
                        table[key, element] = value.replace("_", " ")
                    # print("dkkak",table[key, element])
                        number_table[key, element] = c
                    # print("NUMB, key, element, c, i",number_table[key, element], key, element, c, i)
            elif '@' in fir[key] and selector8==0:
                for element in fol[key]:
                    if (key, element) in table:
                        print("ERROR, NOT AN LL1 GRAMMAR")
                        # break
                    else:
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
    print (pd.DataFrame(new_table).fillna('0'))
    # print ("\n")

    for pair in table:
        new_table[pair[1]][pair[0]] = int(number_table[pair])

    # print ("\nParsing Table with numbers in matrix form\n")
    # print (pd.DataFrame(new_table).fillna('-'))
    # print ("\n")

    return number_table


def getparsetable(fir, fol, prod_dict):
    
    # print("\nParsing Table\n")

    table = {}
    number_table = {}
    c=1

    for key in prod_dict:
        for i in range(len(prod_dict[key])):
            value = prod_dict[key][i]
            if value!='@':
                for element in first(value):
                    table[key, element] = value.replace("_", " ")
                    number_table[key, element] = c
                    # print("NUMB, key, element, c, i",number_table[key, element], key, element, c, i)
            elif value in fir[key]:
                for element in fol[key]:
                    table[key, element] = value
                    number_table[key, element] = c
                    # print("NUMB, key, element, c, i",number_table[key, element], key, element, c, i)
            c+=1

    new_table = {}
    for pair in table:
        new_table[pair[1]] = {}

    for pair in table:
        new_table[pair[1]][pair[0]] = table[pair]


    # print ("\n")
    # print ("\nParsing Table in matrix form\n")
    print (pd.DataFrame(new_table).fillna('0'))
    # print ("\n")

    for pair in table:
        new_table[pair[1]][pair[0]] = int(number_table[pair])

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
                if(row[t]==0):
                    comp[i][t] = 1
                else:
                    comp[i][t] = 0
                    correct=0
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

print("FIRST",FIRST)

# FOLLOW[starting_symbol] = FOLLOW[starting_symbol] | {'$'}
for non_terminal in non_terminals:
    # print("NThhhh",non_terminal)
    FOLLOW[non_terminal] = FOLLOW[non_terminal] | follow(non_terminal)

print("FOLLOW", FOLLOW)
# print('\n')
# print("{: ^20}{: ^20}{: ^20}".format('Non Terminals','First','Follow'))
# for non_terminal in non_terminals:
    # print("{: ^20}{: ^20}{: ^20}".format(non_terminal,str(FIRST[non_terminal]),str(FOLLOW[non_terminal])))

parse_table = parsetable(FIRST, FOLLOW, prod_dict)

print(parse_table)

print(get_parse_table())

ctab, corr = compare(parse_table,get_parse_table())
print("COMPARISON:\n", ctab)
if corr:
    print("\n THE GRAMMAR IS CORRECT\n")
else:
    print("\n THE GRAMMAR IS WRONG\n")
