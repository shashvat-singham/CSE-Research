# from 'game_src/game/views' import * 
from collections import *
def specs():
    
    config = {
        'num_rules': 3, #Number of rules
        'size_rules' : 3, #Number of symbols in RHS
        'num_nonterms' : 2, #Number of nonterms
        'expansion_constant' : 4, #Determines the max. number of parse actions to take while parsing
        'optimize' : False, # enable optimized mode
        'neg_egs' : True, # consider negative examples 
        'threshold' : 0.2  # number of unsat cores to break
    }
    
    return accept_strings,reject_strings,config
    
def find_original_grammar(eps=True):
    # original_grammar contains list of rules. First element of list is the left nonterminal in each rule.
    original_grammar = [['S','c','eps','eps'],['S','c','eps','eps'],['S','c','eps','eps']]
    # return get_original_grammar()
    return original_grammar
    
def get_parse_table(convert = False):
    parse_table = [{'non_term':'S','$':'0','aaaa':'0','aa':'0','abc':'0'}]
    return parse_table
    
def nums():
    original_grammar = find_original_grammar()
    num_vars = {'num_rules':len(original_grammar), 'size_rules':len(original_grammar[0])-1}
    return num_vars