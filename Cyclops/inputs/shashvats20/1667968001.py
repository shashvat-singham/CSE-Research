# from 'game_src/game/views' import * 
from collections import *
def specs():
    
    config = {
        'num_rules': 7, #Number of rules
        'size_rules' : 3, #Number of symbols in RHS
        'num_nonterms' : 4, #Number of nonterms
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

def getError():
    return "2nd rule of follow set A,b"
    
def find_original_grammar(eps=True):
    # original_grammar contains list of rules. First element of list is the left nonterminal in each rule.
    original_grammar = [['E ','T','X','eps'],['T ','(','E',')'],['T ','int','Y','eps'],['X ','+','E','eps'],['X ','eps','eps','eps'],['Y ','*','T','eps'],['Y ','eps','eps','eps']]
    # return get_original_grammar()
    return reverse_grammar(original_grammar)
    
def get_parse_table(convert = False):
    parse_table = [{'non_term':'E','$':'2','(':'0',')':'0','int':'0','+':'0','*':'0'},{'non_term':'T','$':'0','(':'0',')':'0','int':'0','+':'0','*':'0'},{'non_term':'X','$':'0','(':'7',')':'0','int':'0','+':'0','*':'0'},{'non_term':'Y','$':'0','(':'0',')':'0','int':'0','+':'0','*':'0'}]
    return parse_table
    
def nums():
    original_grammar = find_original_grammar()
    num_vars = {'num_rules':len(original_grammar), 'size_rules':len(original_grammar[0])-1}
    return num_vars
    
accept_strings = ["b","a b b"]
reject_strings = ["b a"]
    