from z3 import *

def discover_terms(strings):
	terms = []
	for s in strings:
		l = s.split(' ')
		for t in l:
			if t not in terms:
				terms.append(t)

	return terms

def list_from_strings(in_strings,terms):
	in_terms = [in_strings[i].split(' ') for i in range(len(in_strings))]
	return [["t%s"%(terms.index(i)+1) for i in in_terms[j]] for j in range(len(in_terms))]

def req_rules(config,m,m_vars):
	num_rules = config['num_rules']
	num_nonterms = config['num_nonterms']
	num_terms = config['num_terms']
	size_rules = config['size_rules']

	#check distinct rules
	seen_rules = set()
	distinct_rules = [False for i in range(num_rules)]
	for i in range(num_rules):
		rule = ()
		rule += (int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+1)]))),)
		for j in range(size_rules):
			rule += (int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+2+j)]))),)
		if rule not in seen_rules:
			seen_rules.add(rule)
			distinct_rules[i] = True
		else:
			distinct_rules[i] = False


	#check reachable rules
	reached_rules = [False for i in range(num_rules)]
	reached_nonterms = [False for i in range(num_nonterms)]

	reached_nonterms[0] = True
	changed = True

	while changed:
		changed = False
		for j in range(num_rules):
			if not reached_rules[j] and reached_nonterms[int(str(m.evaluate(m_vars['x%d'%(j*(size_rules+1)+1)])))]:
				reached_rules[j] = True
				changed = True
				for k in range(size_rules):
					symbolValue = int(str(m.evaluate(m_vars['x%d'%(j*(size_rules+1)+2+k)])))
					if symbolValue < num_nonterms:
						if not reached_nonterms[symbolValue]:
							reached_nonterms[symbolValue] = True

	#check producing rules (producing a term or eps)
	producing_rules = [False for i in range(num_rules)]
	producing_nonterms = [False for i in range(num_nonterms)]

	for i in range(num_rules):
		goodrule = False
		for j in range(size_rules):
			symbolValue = int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+2+j)])))
			if symbolValue >= num_nonterms:
				goodrule = True
			else:
				goodrule = False
				break
		if goodrule:
			producing_nonterms[int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+1)])))] = True
			producing_rules[i]= True

	changed = True

	while changed:
		changed = False
		for j in range(num_rules):
			if not producing_rules[j]:
				producing_rules[j] = True
				for k in range(size_rules):
					symbolValue = int(str(m.evaluate(m_vars['x%d'%(j*(size_rules+1)+2+k)])))
					if symbolValue < num_nonterms:
						if not producing_nonterms[symbolValue]:
							producing_rules[j] = False
							break
				if producing_rules[j] == True:
					producing_nonterms[int(str(m.evaluate(m_vars['x%d'%(j*(size_rules+1)+1)])))] = True
					changed = True 

	return [(i and j and k) for (i,j,k) in zip(distinct_rules,reached_rules,producing_rules)]


def print_grammar(config,terms,m,m_vars):
	num_rules = config['num_rules']
	num_nonterms = config['num_nonterms']
	num_terms = config['num_terms']
	size_rules = config['size_rules']

	rules = req_rules(config,m,m_vars)

	for i in range(num_rules):
		if rules[i]:
			symbolValue = int(str(m.evaluate(m_vars["x%d"%(i*(size_rules+1)+1)])))
			print ("N%d\t->\t"%(symbolValue+1),)
			for j in range(size_rules):
				symbolValue = int(str(m.evaluate(m_vars["x%d"%(i*(size_rules+1)+2+j)])))
				if symbolValue < num_nonterms:
					print ("N%d\t"%(symbolValue+1),)
				elif symbolValue < num_nonterms + num_terms:
					print ("%s\t"%(terms[symbolValue-num_nonterms]),)
				elif symbolValue == num_nonterms + num_terms:
					print ("eps\t",)
			print ("")

def assert_grammar(config,s,s_vars,m,m_vars):
	num_rules = config['num_rules']
	num_nonterms = config['num_nonterms']
	num_terms = config['num_terms']
	size_rules = config['size_rules']

	for i in range(num_rules*(size_rules+1)):
		s.add(s_vars['x%d'%(i+1)]==int(str(m.evaluate(m_vars['x%d'%(i+1)]))))

def add_bad_grammar(config,m,m_vars,s,s_vars,derivedBy,iterationNo):
	num_rules = config['num_rules']
	num_nonterms = config['num_nonterms']
	num_terms = config['num_terms']
	size_rules = config['size_rules']

	#create distinct vars
	tempList = []
	for i in range(num_nonterms):
		s_vars.update({'k_%d%d'%(iterationNo,i) : Int('k_%d%d'%(iterationNo,i))})
		tempList.append(s_vars['k_%d%d'%(iterationNo,i)])
		s.add(s_vars['k_%d%d'%(iterationNo,i)]>=0)
		s.add(s_vars['k_%d%d'%(iterationNo,i)]<num_nonterms)

	s.add(Distinct(tempList))

	#check reachable rules
	rules = req_rules(config,m,m_vars)

	#add the derivedBy constraint for reachable rules
	AndList = []
	for i in range(num_rules):
		if rules[i]:
			lhsSymbol = int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+1)])))
			tempList = []
			for j in range(size_rules):
				symbolValue = int(str(m.evaluate(m_vars['x%d'%(i*(size_rules+1)+2+j)])))
				if symbolValue < num_nonterms:
					tempList.append(s_vars['k_%d%d'%(iterationNo,symbolValue)])
				else:
					tempList.append(symbolValue)
			AndList.append(derivedBy(tempList)==s_vars['k_%d%d'%(iterationNo,lhsSymbol)])
	s.add(Not(And(AndList)))

def assert_req_grammar(config,s,s_vars,m,m_vars):
	num_rules = config['num_rules']
	num_nonterms = config['num_nonterms']
	num_terms = config['num_terms']
	size_rules = config['size_rules']

	reqrules = req_rules(config,m,m_vars)
	
	for r in range(num_rules):
		if reqrules[r]:
			for i in range(r*(size_rules+1),(r+1)*(size_rules+1)):
				s.add(s_vars['x%d'%(i+1)]==int(str(m.evaluate(m_vars['x%d'%(i+1)]))))
