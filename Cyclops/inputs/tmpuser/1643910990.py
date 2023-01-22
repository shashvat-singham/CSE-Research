# from 'game_src/game/views' import * 
from collections import *
def specs():
    
    config = {
        'num_rules': 5, #Number of rules
        'size_rules' : 3, #Number of symbols in RHS
        'num_nonterms' : 3, #Number of nonterms
        'expansion_constant' : 4, #Determines the max. number of parse actions to take while parsing
        'optimize' : False, # enable optimized mode
        'neg_egs' : True, # consider negative examples 
        'threshold' : 0.2  # number of unsat cores to break
    }
    
    return accept_strings,reject_strings,config

def reverse_grammar(original_grammar):
    max_len=len(original_grammar[0])
    for i in range(len(original_grammar)):
        count=0
        for j in range(max_len):
            if(original_grammar[i][j]=='eps'):
                count+=1
        if(count==0):
            continue
        tmp_list=count*["eps"]
        new_grammar=[original_grammar[i][0]]+tmp_list+original_grammar[i][1:]
        original_grammar[i]=new_grammar
        original_grammar[i]=original_grammar[i][0:max_len]
    return original_grammar
    
def find_original_grammar(eps=True):
    # original_grammar contains list of rules. First element of list is the left nonterminal in each rule.
    original_grammar = [['S ','A','b','B'],['A ','a','A','b'],['A ','eps','eps','eps'],['B ','b','B','eps'],['B ','eps','eps','eps']]
    # return get_original_grammar()
    return reverse_grammar(original_grammar)
    
def get_parse_table(convert = False):
    parse_table = [{'non_term':'S','$':'0','b':'1','a':'1'},{'non_term':'A','$':'0','b':'0','a':'2'},{'non_term':'B','$':'5','b':'4','a':'0'}]
    return parse_table
    
def nums():
    original_grammar = find_original_grammar()
    num_vars = {'num_rules':len(original_grammar), 'size_rules':len(original_grammar[0])-1}
    return num_vars