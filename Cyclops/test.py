#from finalTestFilesOOPSLA.input_specs_tiger6 import *

# from input_specs import *
#from init import *
from z3 import *
import datetime
import calendar
import time


def discover(original_grammar):
    non_tokens = []
    for string in original_grammar:
        ch = string[0]
        if ch not in non_tokens:
            non_tokens.append(ch)
        else:
            pass
    #print "len(non_tokens):",len(non_tokens)
    return non_tokens

def discover_tokens_from_grammar(handle):
    tokens = []
    original_grammar = handle.find_original_grammar()
    non_tokens = discover(handle.find_original_grammar())
    for string in original_grammar:
        for i in range(1,len(string)):
            if string[i] in non_tokens or string[i] == "eps":
                pass
            else:
                if string[i] in tokens:
                    pass
                else:
                    tokens.append(string[i])
    #print ('tokens',tokens)
    return tokens






def add_constraints(solver, view_assign, original_grammar, num_rules, size_rules):
	#print "asserting grammar in %s"%str(datetime.timedelta(seconds=(calendar.timegm(time.gmtime()))))

	s = solver['constraints']
	vars = solver['vars']
        #print ("vars", vars)
	i = 1
	size_rules = len(original_grammar[0])-1
	constdict = {}#solver["dictconst"]
	tempP = []
	for r in range(num_rules):
		# print "Asserting rule: ",r
		s.add(vars['x%d'%(r*(size_rules+1)+1)] == vars[view_assign[original_grammar[r][0]]])
		tempP.append(vars['x%d'%(r*(size_rules+1)+1)] == vars[view_assign[original_grammar[r][0]]])
		i += 1

		for j in range(1,size_rules+1):
			# print "j:",j
			if original_grammar[r][j] == 'eps':
				# print 'x%d = eps'%(r*(size_rules+1)+j+1)
				s.add(vars['x%d'%(r*(size_rules+1)+j+1)] == vars['eps'])
				tempP.append(vars['x%d'%(r*(size_rules+1)+j+1)] == vars['eps'])
				i += 1
			else:
				# constdict['input x%d'%(r*(size_rules+1)+j+1)] = vars['x%d'%(r*(size_rules+1)+j+1)] == vars[view_assign[original_grammar[r][j]]]
				# print 'x%d = %s'%(r*(size_rules+1)+j+1,original_grammar[r][j])
				#print ("69:test ",vars['x%d'%(r*(size_rules+1)+j+1)], " .. ", vars[view_assign[original_grammar[r][j]]])
				s.add(vars['x%d'%(r*(size_rules+1)+j+1)] == vars[view_assign[original_grammar[r][j]]])
				tempP.append(vars['x%d'%(r*(size_rules+1)+j+1)] == vars[view_assign[original_grammar[r][j]]])
				i += 1
    	#print ("tempP", tempP)
	#print "asserting grammar in %s"%str(datetime.timedelta(seconds=(calendar.timegm(time.gmtime()))))


def add_parse_table_constraints(solver,parse_table,view_assign):
	#print "asserting ptable in %s"%str(datetime.timedelta(seconds=(calendar.timegm(time.gmtime()))))

	#print "adding parse table..."
	s = solver["constraints"]
	vars = solver['vars']
	functions = solver['functions']
	constdict = {}#solver["dictconst"]
	consVarH = {}
	# print "parse_table: ",parse_table
	for i in range(len(parse_table)):
		non_terminal = parse_table[i]['non_term']
		for k,t in parse_table[i].items():
			if k == 'non_term':
				continue
			if t:
				pk = Bool("parseTableEntry_%s_%s"%(non_terminal, k))
				consVarH["parseTableEntry_%s_%s"%(non_terminal, k)] = pk
				s.add(Implies(pk, functions['parseTable'](vars[view_assign[non_terminal]],vars[view_assign[k]]) == vars['rule%d'%(t)]))
				constdict['%s %s parse table input'%(non_terminal,k)] = functions['parseTable'](vars[view_assign[non_terminal]],vars[view_assign[k]]) == vars['rule%d'%(t)]
			else:
				pk = Bool("parseTableEntry_%s_%s" % (non_terminal, k))
				consVarH["parseTableEntry_%s_%s" % (non_terminal, k)] = pk
				s.add(Implies(pk, functions['parseTable'](vars[view_assign[non_terminal]],vars[view_assign[k]]) == 0))
				constdict['%s %s parse table input'%(non_terminal,k)] = functions['parseTable'](vars[view_assign[non_terminal]],vars[view_assign[k]]) == 0
	#print "asserting ptable in %s"%str(datetime.timedelta(seconds=(calendar.timegm(time.gmtime()))))
	return consVarH


def add_first_set_constraints(solver, first_set, follow_set, view_assign):
	s = solver["constraints"]
	vars = solver["vars"]
	functions = solver["functions"]
	constdict = {} #solver["dictconst"]
	# print "first set:",first_set
	# print "follow set:",follow_set
	tempF = []
	for i in range(len(first_set)):
		non_terminal = str(first_set[i]['non_term'])
		for k,t in first_set[i].items():
			if k == 'non_term':
				continue;
			if t != 0:
				s.add(functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]]))
				tempF.append(functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]]))
				constdict['first set input %s %s'%(non_terminal,k)] = functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]])
			else:
				s.add(Not(functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]])))
				tempF.append(Not(functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]])))
				constdict['first set input %s %s'%(non_terminal,k)] = Not(functions["first"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]]))
	print("First_tempF",tempF)
	
	for i in range(len(follow_set)):
		non_terminal = str(follow_set[i]['non_term'])
		for k,t in follow_set[i].items():
			if k == 'non_term':
				continue;
			if t != 0:
				s.add(functions["follow"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]]))
				constdict['follow set input %s %s'%(non_terminal, k)] = functions["follow"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]])
			else:
				s.add(Not(functions["follow"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]])))
				constdict['follow set input %s %s'%(non_terminal, str(k))] = Not(functions["follow"](vars[view_assign[non_terminal]], vars[view_assign[str(k)]]))
	

def repair(solver, original_grammar, num_rules, size_rules, input_handle):
	view_assign = {}
	view_assign_t = {}
	view_assign_nt = {}
	non_tokens = discover(input_handle.find_original_grammar())
	tokens = discover_tokens_from_grammar(input_handle)
	i = 1
	for ch in non_tokens:
		view_assign_nt["N%d"%i] = ch
		view_assign[ch] = 'N%d'%(i)
		i += 1

	i = 1
	for ch in tokens:
		view_assign[ch] = 't%d'%(i)
		view_assign_t['t%d'%i] = ch
		i += 1
	view_assign['eps'] = 'eps'
	#print "view_assign",view_assign
	solver["view_assign"] = view_assign
	solver["view_assign_t"] = view_assign_t
	solver["view_assign_nt"] = view_assign_nt
	parse_table = input_handle.get_parse_table()
	#print "PARSE TABLE:", parse_table
        
    
#    	first_set = get_first_set()
#    	print "FIRST SET: ", first_set
#	
#    	follow_set = get_follow_set()
#    	print "FOLLOW SET: ", follow_set
#        """
#	print "Grammer: ", original_grammar
#        """
#
	view_assign['dol'] = 'dol'
	view_assign['$'] = 'dol'
	add_constraints(solver,view_assign,original_grammar,num_rules, size_rules)
	# print view_assign
	return add_parse_table_constraints(solver,parse_table,view_assign)
#	add_first_set_constraints(solver, first_set, follow_set, view_assign)

