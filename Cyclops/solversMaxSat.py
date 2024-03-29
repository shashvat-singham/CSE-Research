from z3 import *

def base_solver(s,InputList,config, parseTableEntry, ptM, ptC, fiM, fiC, foM, foC, graph):

	num_rules = config['num_rules'] #Number of rules
	size_rules = config['size_rules']  #Max number of symbols in RHS
	num_nonterms = config['num_nonterms']  #Number of nonterms
	num_terms = config['num_terms']   #Number of terms
	expansion_constant = config['expansion_constant']  #Determines the max. number of parse actions to take while parsing

	vars = {}
	functions = {}
	x = Int('x')
	y = Int('y')
	z = Int('z')
	w = Int('w')
	################# Maxsatflag #####################################

	#consVar goes to the hard constraints and consVarH goes to the soft constraints
	firstMapFlag = fiM # for depth of the first set in concept map
	firstConsFlag = fiC # 0 for consVar and 1 for consVarH for first set

	followMapFlag = foM # for depth of the follow set in concept map
	followConsFlag = foC # 0 for consVar and 1 for consVarH for follow set

	tableMapFlag = ptM # for depth of the parse table in concept map
	tableConsFlag = ptC # 0 for consVar and 1 for consVarH for parse table

	consVar = {} 	# for hard constraints
	consVarH = {}	# for soft constraints

	######################################################

	# SYMBOLS

	######################################################

	symbol_counter = 0

	nonterms = ['N%d'%i for i in range(1,num_nonterms+1)]
	vars.update({"%s"%nt : Int('%s'%nt) for nt in nonterms})

	terms = ['t%d'%i for i in range(1,num_terms+1)]
	vars.update({"%s"%t : Int('%s'%t) for t in terms})

	vars.update({"eps": Int('eps')})

	for nt in nonterms:
		s.add(vars[nt]==symbol_counter)
		symbol_counter+=1

	for t in terms:
		s.add(vars[t]==symbol_counter)
		symbol_counter+=1

	s.add(vars['eps']==symbol_counter)
	symbol_counter+=1


	######################################################

	# BASIC FUNCTIONS

	######################################################

	#has (second arg) been witnessed to be in first set of (first arg), in template rule number (third arg), according to construction condition number (fourth arg)? if no, return -1 else return the nonterm or term due to which this witness occurred
	firstWitness = Function('firstWitness',IntSort(),IntSort(),IntSort(),IntSort(),IntSort())
	
	#has (second arg) been witnessed to be in follow set of (first arg), in template rule number (third arg), according to construction condition number (fourth arg) ? if no, return -1 else return the nonterm due to which this witness occurred
	followWitness = Function('followWitness',IntSort(),IntSort(),IntSort(),IntSort(),IntSort())

	#Return the existential variable i for first set construction for the given nonterm, term pair
	get_i = Function('get_i',IntSort(),IntSort(),IntSort())

	#Return the existential variable j for first set construction for the given nonterm, term pair
	get_j = Function('get_j',IntSort(),IntSort(),IntSort())

	#Return the existential variable m for follow set construction for the given nonterm, term pair
	get_m = Function('get_m',IntSort(),IntSort(),IntSort())

	#Return the existential variable n for follow set construction for the given nonterm, term pair
	get_n = Function('get_n',IntSort(),IntSort(),IntSort())

	# is eps in the first set of the nonterm second arg after first arg iteration
	epsWitness = Function('epsWitness',IntSort(),IntSort(),BoolSort())

	#is second arg in first of first arg?
	first = Function('first',IntSort(),IntSort(),BoolSort())
	functions["first"] = first
	#is second arg in follow of first arg?
	follow = Function('follow',IntSort(),IntSort(),BoolSort())
	functions["follow"] = follow 
	#returns rule number in the parse table cell corresponding to (first arg) nonterm and (second arg) term
	parseTable = Function('parseTable', IntSort(), IntSort(), IntSort())
	functions["parseTable"] = parseTable
	term = Function('term',IntSort(),BoolSort())
	tempList = []
	for t in terms:
		tempList.append(x==vars[t])
	s.add(ForAll(x,If(Or(tempList),term(x),Not(term(x)))))

	nonterm = Function('nonterm',IntSort(),BoolSort())
	tempList = []
	for nt in nonterms:
		tempList.append(x==vars[nt])
	s.add(ForAll(x,If(Or(tempList),nonterm(x),Not(nonterm(x)))))

	ruleRHS = Function('ruleRHS',IntSort(),BoolSort())

	tempList = []
	for nt in nonterms:
		tempList.append(x==vars[nt])
	for t in terms:
		tempList.append(x==vars[t])
	tempList.append(x==vars['eps'])
	s.add(ForAll(x,If(Or(tempList),ruleRHS(x),Not(ruleRHS(x)))))

	######################################################

	# TEMPLATE CONSTRAINTS

	######################################################

	for r in range(num_rules):
		vars.update({"x%d"%(r*(size_rules+1)+1): Int('x%d'%(r*(size_rules+1)+1))})
		s.add(nonterm(vars["x%d"%(r*(size_rules+1)+1)]))

		for i in range(2,size_rules+2):
			vars.update({"x%d"%(r*(size_rules+1)+i): Int('x%d'%(r*(size_rules+1)+i))})
			s.add(ruleRHS(vars["x%d"%(r*(size_rules+1)+i)]))

	# What is the symbol at (second arg) location in RHS of rule no (first arg)
	symbolInRHS = Function('symbolInRHS', IntSort(), IntSort(), IntSort())

	# What is the symbol in LHS of rule no (first arg)
	symbolInLHS = Function('symbolInLHS', IntSort(), IntSort())

	# Initialize symbolInRHS and symbolInLHS
	for r in range(num_rules):
		for i in range(2,size_rules+2):
			s.add(symbolInRHS(r+1,i-1) == vars["x%d"%(r*(size_rules+1)+i)])
		s.add(symbolInLHS(r+1) == vars["x%d"%(r*(size_rules+1)+1)])

	#Avoid trivial rules
	for r in range(1,num_rules+1):
		for i in range(2,size_rules+1):
			s.add(Implies(symbolInRHS(r,i)==vars["eps"],symbolInRHS(r,i-1)==vars["eps"]))
			s.add(Implies(symbolInRHS(r,size_rules)==symbolInLHS(r),symbolInRHS(r,size_rules-1)!=vars["eps"])) # to prevent left recursion


	######################################################

	# FIRST SET WITNESS CONSTRAINTS

	######################################################

	for r in range(1,num_rules+1):
		vars.update({"rule%d"%r: Int('rule%d'%r)})
		s.add(vars["rule%d"%r]==r)

	num_conds = 1
	for r in range(1,2*size_rules+1):
		vars.update({"cond%d"%r: Int('cond%d'%r)})
		s.add(vars["cond%d"%r]==r)
		num_conds+=1

	# Definition constraint: firstWitness must either return -1 or return nonterm or term
	s.add(ForAll([x,y,z,w], And(firstWitness(x,y,z,w) >= -1, firstWitness(x,y,z,w) < vars['eps'] ) ))

	# Definition constraint: forall terms t, firstWitness(t,t,i_tt,j_tt) = t
	for t in terms:
		var = "%s%s"%(str(vars[t]),str(vars[t]))
		vars["i_%s"%var] = Int('i_%s'%var)
		vars["j_%s"%var] = Int('j_%s'%var)
		s.add(firstWitness(vars[t],vars[t],vars["i_%s"%var],vars["j_%s"%var])==vars[t])
		s.add(get_i(vars[t],vars[t])==vars["i_%s"%var])
		s.add(get_j(vars[t],vars[t])==vars["j_%s"%var])

	# Definition constraint: firstWitness must return -1 for -1 as nonterm arg
	s.add(ForAll([x,y,z],firstWitness(-1,x,y,z) == -1 ))

	# Definition constraint: epsWitness must be true for eps
	s.add(ForAll(x,epsWitness(x,vars["eps"])))

	######################################################

	# FIRST SET WITNESS CONSTRUCTION

	######################################################
	
#	if firstMapFlag == 3:
#		for r in range(1,num_rules+1):
#			for i in range(1,size_rules+1):
#				for t in terms:	
#					if firstConsVar == 1:
#						consVarH["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
#						consVarH["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t))
#					else:
#						consVar["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
#						consVar["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t)) 

#	if firstMapFlag == 2: 
#		for r in range(1,num_rules+1):
#			for t in terms:	
#				if firstConsVar == 1:
#					consVarH["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
#					consVarH["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
#				else:
#					consVar["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
#					consVar["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
#			consVarH["firstSet_2_B1_%s_%s"%(r,t)] = Bool("firstSet_2_B1_%s_%s"%(r,t))
#			consVarH["firstSet_2_B2_%s_%s"%(r,t)] = Bool("firstSet_2_B2_%s_%s"%(r,t))

	for r in range(1,num_rules+1):
		if firstMapFlag == 1:
			if firstConsFlag == 1:
				if followMapFlag == 1:
					graph['First_Rule2'].append("firstSet_2_A1_%s"%(r))
					graph["firstSet_2_A1_%s"%(r)] = []
				consVarH["firstSet_2_A1_%s"%(r)] = Bool("firstSet_2_A1_%s"%(r))
				consVarH["firstSet_2_A2_%s"%(r)] = Bool("firstSet_2_A2_%s"%(r))
				h1a = consVarH["firstSet_2_A1_%s"%(r)]
				h1b = consVarH["firstSet_2_A2_%s"%(r)]
			else:
				consVar["firstSet_2_A1_%s"%(r)] = Bool("firstSet_2_A1_%s"%(r))
				consVar["firstSet_2_A2_%s"%(r)] = Bool("firstSet_2_A2_%s"%(r))
				h1a = consVar["firstSet_2_A1_%s"%(r)]
				h1b = consVar["firstSet_2_A2_%s"%(r)]

		for i in range(1,size_rules+1):
			for t in terms:
				if firstMapFlag == 2:
					if firstConsFlag == 1:
						if "firstSet_2_A1_%s_%s"%(r,t) not in consVarH:
							#print("here, r, i, t, %s, %s, %s"%(r,i,t))
							consVarH["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
							consVarH["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
							if followMapFlag == 1:
								graph["firstSet_2_A1_%s"%(r)].append("firstSet_2_A1_%s_%s"%(r,t))
								graph["firstSet_2_A1_%s_%s"%(r,t)] = []
						h1a = consVarH["firstSet_2_A1_%s_%s"%(r,t)]
						h1b = consVarH["firstSet_2_A2_%s_%s"%(r,t)]
					else: #if firstConsFlag == 0:
						if "firstSet_2_A1_%s_%s"%(r,t) not in consVar:
							consVar["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
							consVar["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
						h1a = consVar["firstSet_2_A1_%s_%s"%(r,t)]
						h1b = consVar["firstSet_2_A2_%s_%s"%(r,t)]		
				if firstMapFlag == 3:
					if firstConsFlag == 1:
						if "firstSet_2_A1_%s_%s_%s"%(r,i,t) not in consVarH:  #no need.. but still
							consVarH["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
							consVarH["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t))
							if followMapFlag == 1:
								graph["firstSet_2_A1_%s_%s"%(r,t)].append("firstSet_2_A1_%s_%s_%s"%(r,i,t))
								graph["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = []
						h1a = consVarH["firstSet_2_A1_%s_%s_%s"%(r,i,t)]
						h1b = consVarH["firstSet_2_A2_%s_%s_%s"%(r,i,t)]
					else:
						if "firstSet_2_A1_%s_%s_%s"%(r,i,t) not in consVar:
							consVar["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
							consVar["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t))
						h1a = consVar["firstSet_2_A1_%s_%s_%s"%(r,i,t)]
						h1b = consVar["firstSet_2_A2_%s_%s_%s"%(r,i,t)] 
							

				tempList = []
				
				for j in range(1,i):
					tempList.append(symbolInRHS(r,j)==vars["eps"])
				tempList.append(first(symbolInRHS(r,i),vars[t]))  #it looks potential rule for first set #2
				tempList.append(symbolInRHS(r,i)!=symbolInLHS(r)) 

				temp = firstWitness(symbolInRHS(r,i),vars[t],get_i(symbolInRHS(r,i),vars[t]),get_j(symbolInRHS(r,i),vars[t]))
				for j in range(num_rules):
					temp = firstWitness(temp,vars[t],get_i(temp,vars[t]),get_j(temp,vars[t]))
				tempList.append(temp==vars[t])
				condition = Or(Not(h1b), And(h1a, And(tempList)))
				s.add(If(condition, (firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(i)]) == symbolInRHS(r,i)), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(i)]) == -1) ))

				#s.add(If(And(tempList), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(i)]) == symbolInRHS(r,i)), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(i)]) == -1) ))

					
		for i in range(1,size_rules+1):
			for t in terms:

#				h1a = consVarH["firstSet_2_B1_%s_%s"%(r,t)]
#				h1b = consVarH["firstSet_2_B2_%s_%s"%(r,t)]
#				h1a = consVarH["firstSet_2_A1_%s_%s"%(r,t)]
#				h1b = consVarH["firstSet_2_A2_%s_%s"%(r,t)]

				if firstMapFlag == 2:
					if firstConsFlag == 1:
#						consVarH["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
#						consVarH["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
						h1a = consVarH["firstSet_2_A1_%s_%s"%(r,t)]
						h1b = consVarH["firstSet_2_A2_%s_%s"%(r,t)]
					else: #firstConsFlag == 0:
#						consVar["firstSet_2_A1_%s_%s"%(r,t)] = Bool("firstSet_2_A1_%s_%s"%(r,t))
#						consVar["firstSet_2_A2_%s_%s"%(r,t)] = Bool("firstSet_2_A2_%s_%s"%(r,t))
						h1a = consVar["firstSet_2_A1_%s_%s"%(r,t)]
						h1b = consVar["firstSet_2_A2_%s_%s"%(r,t)]	
	
				if firstMapFlag == 3:
					if firstConsFlag == 1:
#						consVarH["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
#						consVarH["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t))
						h1a = consVarH["firstSet_2_A1_%s_%s_%s"%(r,i,t)]
						h1b = consVarH["firstSet_2_A2_%s_%s_%s"%(r,i,t)]
					else:
#						consVar["firstSet_2_A1_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A1_%s_%s_%s"%(r,i,t))
#						consVar["firstSet_2_A2_%s_%s_%s"%(r,i,t)] = Bool("firstSet_2_A2_%s_%s_%s"%(r,i,t))
						h1a = consVar["firstSet_2_A1_%s_%s_%s"%(r,i,t)]
						h1b = consVar["firstSet_2_A2_%s_%s_%s"%(r,i,t)] 
							
	


				tempList = []
				for j in range(1,i):
					tempList.append(first(symbolInRHS(r,j),vars["eps"]))
				tempList.append(first(symbolInRHS(r,i),vars[t]))
				tempList.append(symbolInRHS(r,i)!=symbolInLHS(r))

				temp = firstWitness(symbolInRHS(r,i),vars[t],get_i(symbolInRHS(r,i),vars[t]),get_j(symbolInRHS(r,i),vars[t]))
				for j in range(num_rules):
					temp = firstWitness(temp,vars[t],get_i(temp,vars[t]),get_j(temp,vars[t]))
				tempList.append(temp==vars[t])
	
				condition = Or(Not(h1b), And(h1a, And(tempList)))
				s.add(If(condition, ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(size_rules+i)]) == symbolInRHS(r,i)), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(size_rules+i)]) == -1) ))

#				s.add(If(And(tempList), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(size_rules+i)]) == symbolInRHS(r,i)), ( firstWitness(symbolInLHS(r),vars[t],vars["rule%d"%(r)],vars["cond%d"%(size_rules+i)]) == -1) ))


	for n in nonterms:
		OrList = []

		for r in range(1,num_rules+1):
			tempList = []
			tempList.append(symbolInLHS(r)==vars[n])
			for i in range(1,size_rules+1):
				tempList.append(symbolInRHS(r,i)==vars["eps"])
			OrList.append(And(tempList))

		s.add(Or(OrList)==epsWitness(0,vars[n]))

	for i in range(1,num_rules+1):

		for n in nonterms:
			OrList = []

			OrList.append(epsWitness(i-1,vars[n]))

			for r in range(1,num_rules+1):
				tempList = []
				tempList.append(symbolInLHS(r)==vars[n])
				for j in range(1,size_rules+1):
					tempList.append(epsWitness(i-1,symbolInRHS(r,j)))
				OrList.append(And(tempList))

			s.add(Or(OrList)==epsWitness(i,vars[n]))

	######################################################

	# FIRST SET CONSTRAINTS

	######################################################

	# Definition constraint: no invalid symbol in first sets
		

	for t in nonterms+terms+["eps"]:
		pk = Bool("first_set_0_%s"%t)
		consVar["first_set_0_%s"%t] = pk
		s.add(Implies(pk, ForAll(y,Implies(Or(y>symbol_counter-1,y<0),Not(first(vars[t],y))))))

	# Definition constraint: no nonterm in first sets
	for n in nonterms:
		pk = Bool("first_set_1_%s"%n)
		consVar["first_set_1_%s"%n] = pk
		s.add(Implies(pk, ForAll(y,Not(first(y,vars[n])))))

	# Definition constraint: first(eps) = {eps}
	pk = Bool("firstSet_3")
	consVar["firstSet_3"] = pk
	s.add(Implies(pk, ForAll(y,Implies(y!=vars["eps"],And(first(vars["eps"],vars["eps"]),Not(first(vars["eps"],y)))))))

	# Definition constraint: first(term) = {term}
	for t in terms:
		if followMapFlag == 1 and firstMapFlag == 1:
			graph["First_Rule1"].append("firstSet_rule1_%s"%t)
			graph["firstSet_rule1_%s"%t] = []
		pk = Bool("firstSet_rule1_%s"%t)
		consVarH["firstSet_rule1_%s"%t] = pk
#		pk1 = Bool("firstSet_1B_%s"%t)
#		consVarH["firstSet_1B_%s"%t] = pk1
		s.add(Implies(pk, ForAll(y,Implies(y!=vars[t],And(first(vars[t],vars[t]),Not(first(vars[t],y)))))))
		
#		for yy in nonterms+terms+["eps"]:
#			condition = Or(Not(pk1), And(pk, vars[yy]!=vars[t]))
#			s.add(Implies(condition,And(first(vars[t],vars[t]),Not(first(vars[t],vars[yy])))))
#			s.add(Implies(pk, Implies(vars[yy]!=vars[t],And(first(vars[t],vars[t]),Not(first(vars[t],vars[yy]))))))


	######################################################

	# FIRST SET CONSTRUCTION

	######################################################

	for n in nonterms:
		for t in terms:
			var = "%(nonterm)s%(term)s"%{"nonterm":n, "term":t}
			
			vars["i_%s"%var] = Int("i_%s"%var)
			vars["j_%s"%var] = Int("j_%s"%var)
			s.add(get_i(vars[n],vars[t])==vars["i_%s%s"%(n,t)])
			s.add(get_j(vars[n],vars[t])==vars["j_%s%s"%(n,t)])

			tempList = []
			for i in range(1,num_rules+1):
				tempList.append(vars["i_%s"%var]==vars["rule%d"%(i)])
			pk = Bool("first_set_cons_0_%s"%var)
			consVar["first_set_cons_0_%s"%var] = pk
			s.add(Implies(pk, Or(tempList)))

			tempList = []
			for i in range(1,2*size_rules+1):
				tempList.append(vars["j_%s"%var]==vars["cond%d"%(i)])
			pk = Bool("first_set_cons_1_%s"%var)
			consVar["first_set_cons_1_%s"%var] = pk
			s.add(Implies(pk, Or(tempList)))

			
			for i in range(1,num_rules+1):
				pk = Bool("first_set_cons_2_%s_%s"%(var,i))
				consVar["first_set_cons_2_%s_%s"%(var,i)] = pk
				s.add(Implies(pk, Implies(And(first(vars[n],vars[t]),vars["i_%s"%var]==vars["rule%d"%(i)]),vars[n]==symbolInLHS(i)) ))

			pk = Bool("first_set_cons_3_%s"%var)
			consVar["first_set_cons_3_%s"%var] = pk
			s.add(Implies(pk, Implies(first(vars[n],vars[t]),( firstWitness(vars[n],vars[t],vars["i_%s"%var],vars["j_%s"%var]) != -1))))

			tempList = []
			for i in range(1,num_rules+1):
				for j in range(1,2*size_rules+1):
					tempList.append( (firstWitness(vars[n],vars[t],vars["rule%d"%i],vars["cond%d"%j])) == -1)
			
			pk = Bool("first_set_cons_4_%s"%var)
			consVar["first_set_cons_4_%s"%var] = pk 
			s.add(Implies(pk, Implies(Not(first(vars[n],vars[t])),And(tempList))))

		pk = Bool("first_set_cons_5_%s"%n)
		if followMapFlag == 1 and firstMapFlag == 1:
			graph["First_Rule3"].append("first_set_cons_5_%s"%n)
			graph["first_set_cons_5_%s"%n] = []
		if firstConsFlag == 0:
    			consVar["first_set_cons_5_%s"%n] = pk
		if firstConsFlag == 1:
    			consVarH["first_set_cons_5_%s"%n] = pk
		s.add(Implies(pk, first(vars[n],vars["eps"])==epsWitness(num_rules,vars[n])))

	######################################################

	# FOLLOW SET WITNESS CONSTRAINTS

	######################################################

	vars.update({"dol": Int('dol')})
	s.add(vars["dol"]==symbol_counter)
	
	while (num_conds <= (size_rules*(size_rules+1))/2):
		#print ("309",num_conds, type(num_conds), (size_rules*(size_rules+1))/2, vars["cond8"])
		vars.update({"cond%s"%num_conds: Int('cond%d'%num_conds)})
		num_conds+=1
	
	# Definition constraint: forall terms and dol t, followWitness(t,t,m_tt,n_tt) = t
	for t in terms+["dol"]:
		var = "%s%s"%(str(vars[t]),str(vars[t]))
		vars["m_%s"%var] = Int('m_%s'%var)
		vars["n_%s"%var] = Int('n_%s'%var)
		s.add(followWitness(vars[t],vars[t],vars["m_%s"%var],vars["n_%s"%var])==vars[t])
		s.add(get_m(vars[t],vars[t])==vars["m_%s"%var])
		s.add(get_n(vars[t],vars[t])==vars["n_%s"%var])

	# Definition constraint: followWitness must return -1 for -1 as nonterm arg
	s.add(ForAll([x,y,z],followWitness(-1,x,y,z) == -1 ))

	# Definition constraint: dol has been witnessed to be in follow(N1)
	# NOTE: N1 is the starting nonterm
	vars["m_N1dol"] = Int('m_N1dol')
	vars["n_N1dol"] = Int('n_N1dol')
	s.add(get_m(vars["N1"],vars["dol"])==vars["m_N1dol"])
	s.add(get_n(vars["N1"],vars["dol"])==vars["n_N1dol"])
	s.add(followWitness(vars["N1"],vars["dol"],vars["m_N1dol"],vars["n_N1dol"])==vars["dol"])

	######################################################

	# FOLLOW SET WITNESS CONSTRUCTION

	######################################################

	for r in range(1,num_rules+1):
		if followMapFlag == 1:
			if followConsFlag == 1:
				if firstMapFlag == 1:
					graph["Follow_Rule2"].append("Follow_set_rule_2_%s"%(r))
					graph["Follow_set_rule_2_%s"%(r)] = []

					graph["Follow_Rule3"].append("Follow_set_rule_3_%s"%(r))
					graph["Follow_set_rule_3_%s"%(r)] = []

				implyFlagFollowA = Bool("Follow_set_rule_2_%s"%(r))
				consVarH["Follow_set_rule_2_%s"%(r)] = implyFlagFollowA

				implyFlagFollowB = Bool("Follow_set_rule_3_%s"%(r))
				consVarH["Follow_set_rule_3_%s"%(r)] = implyFlagFollowB
			else:
				implyFlagFollowA = Bool("Follow_set_rule_2_%s"%(r))
				consVar["Follow_set_rule_2_%s"%(r)] = implyFlagFollowA

				implyFlagFollowB = Bool("Follow_set_rule_3_%s"%(r))
				consVar["Follow_set_rule_3_%s"%(r)] = implyFlagFollowB

		condNo = 1

		for i in range(1,size_rules):
			for j in range(i+1,size_rules+1):
				for t in terms:
					if followMapFlag == 2:
						if followConsFlag == 1:
							if "Follow_set_rule_2_%s_%s"%(r,t) not in consVarH:
								implyFlagFollowA = Bool("Follow_set_rule_2_%s_%s"%(r,t))
								consVarH["Follow_set_rule_2_%s_%s"%(r,t)] = implyFlagFollowA
								if firstMapFlag == 1:
									graph["Follow_set_rule_2_%s"%(r)].append("Follow_set_rule_2_%s_%s"%(r,t))
									graph["Follow_set_rule_2_%s_%s"%(r,t)] = []

							else:	
								implyFlagFollowA = consVarH["Follow_set_rule_2_%s_%s"%(r,t)]

#								implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s"%(r,t))
#								consVarH["Follow_set_rule_3_%s_%s"%(r,t)] = implyFlagFollowB
						else:
							if "Follow_set_rule_2_%s_%s"%(r,t) not in consVar:
								implyFlagFollowA = Bool("Follow_set_rule_2_%s_%s"%(r,t))
								consVar["Follow_set_rule_2_%s_%s"%(r,t)] = implyFlagFollowA
							else:
								implyFlagFollowA = consVar["Follow_set_rule_2_%s_%s"%(r,t)]

#								implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s"%(r,t))
#								consVar["Follow_set_rule_3_%s_%s"%(r,t)] = implyFlagFollowB
					
					if followMapFlag == 3:
						if followConsFlag == 1:
							if "Follow_set_rule_2_%s_%s_%s"%(r,i,t) not in consVarH:
								implyFlagFollowA = Bool("Follow_set_rule_2_%s_%s_%s"%(r,i,t))
								consVarH["Follow_set_rule_2_%s_%s_%s"%(r,i,t)] = implyFlagFollowA
								if firstMapFlag == 1:
									graph["Follow_set_rule_2_%s_%s"%(r,t)].append("Follow_set_rule_2_%s_%s_%s"%(r,i,t))
									graph["Follow_set_rule_2_%s_%s_%s"%(r,i,t)] = []
							else:
								implyFlagFollowA = consVarH["Follow_set_rule_2_%s_%s_%s"%(r,i,t)]
#								implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s"%(r,t))
#								consVarH["Follow_set_rule_3_%s_%s"%(r,t)] = implyFlagFollowB
						else:
							if "Follow_set_rule_2_%s_%s_%s"%(r,i,t) not in consVar:
								implyFlagFollowA = Bool("Follow_set_rule_2_%s_%s_%s"%(r,i,t))
								consVar["Follow_set_rule_2_%s_%s_%s"%(r,i,t)] = implyFlagFollowA
							else:
								implyFlagFollowA = consVar["Follow_set_rule_2_%s_%s_%s"%(r,i,t)]


					tempList = []
					for k in range(i+1,j):
						tempList.append(first(symbolInRHS(r,k),vars["eps"]))
					tempList.append(first(symbolInRHS(r,j),vars[t]))

					s.add(Implies(implyFlagFollowA, (followWitness(symbolInRHS(r,i),vars[t],vars["rule%d"%(r)],vars["cond%d"%condNo])==vars[t]) == And(tempList)))

				condNo += 1

		followCondMid = condNo

		for i in range(1,size_rules+1):
			for t in terms+['dol']:
	
				if followMapFlag == 3:
					if followConsFlag == 1:
						if "Follow_set_rule_3_%s_%s_%s"%(r,i,t) not in consVarH:
							implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s_%s"%(r,i,t))
							consVarH["Follow_set_rule_3_%s_%s_%s"%(r,i,t)] = implyFlagFollowB
							if firstMapFlag == 1:
								graph["Follow_set_rule_3_%s_%s"%(r,t)].append("Follow_set_rule_3_%s_%s_%s"%(r,i,t))
								graph["Follow_set_rule_3_%s_%s_%s"%(r,i,t)] = []

						else:
							implyFlagFollowB = consVarH["Follow_set_rule_3_%s_%s_%s"%(r,i,t)]
					else:
						if "Follow_set_rule_3_%s_%s_%s"%(r,i,t) not in consVar:
							implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s_%s"%(r,i,t))
							consVar["Follow_set_rule_3_%s_%s_%s"%(r,i,t)] = implyFlagFollowB
						else:
							implyFlagFollowB = consVar["Follow_set_rule_3_%s_%s_%s"%(r,i,t)]

				if followMapFlag == 2:
					if followConsFlag == 1:
						if "Follow_set_rule_3_%s_%s"%(r,t) not in consVarH:
							implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s"%(r,t))
							consVarH["Follow_set_rule_3_%s_%s"%(r,t)] = implyFlagFollowB
							if firstMapFlag == 1:
								graph["Follow_set_rule_3_%s"%(r)].append("Follow_set_rule_3_%s_%s"%(r,t))
								graph["Follow_set_rule_3_%s_%s"%(r,t)] = []
						else:
							implyFlagFollowB = consVarH["Follow_set_rule_3_%s_%s"%(r,t)]
					else:
						if "Follow_set_rule_3_%s_%s"%(r,t) not in consVar:
							implyFlagFollowB = Bool("Follow_set_rule_3_%s_%s"%(r,t))
							consVar["Follow_set_rule_3_%s_%s"%(r,t)] = implyFlagFollowB
						else:
							implyFlagFollowB = consVar["Follow_set_rule_3_%s_%s"%(r,t)]

				tempList = []
				for k in range(i+1,size_rules+1):
					tempList.append(first(symbolInRHS(r,k),vars["eps"]))
				tempList.append(follow(symbolInLHS(r),vars[t]))
				tempList.append(symbolInRHS(r,i)!=symbolInLHS(r))

				temp = followWitness(symbolInLHS(r),vars[t],get_i(symbolInLHS(r),vars[t]),get_j(symbolInLHS(r),vars[t]))
				for j in range(num_rules):
					temp = followWitness(temp,vars[t],get_m(temp,vars[t]),get_n(temp,vars[t]))
				tempList.append(temp==vars[t])

				

				s.add(Implies(implyFlagFollowB,(followWitness(symbolInRHS(r,i),vars[t],vars["rule%d"%(r)],vars["cond%d"%condNo])==symbolInLHS(r)) == And(tempList)))

			condNo += 1

		followCondEnd = condNo

	######################################################

	# FOLLOW SET CONSTRAINTS

	######################################################

	# Definition constraints: no nonterm and eps in follow sets
	for n in nonterms+["eps"]:
		pk = Bool("follow_set_0_%s"%n)
		consVar["follow_set_0_%s"%n] = pk
		s.add(Implies(pk, ForAll([x],Implies(Not(term(x)),Not(follow(x,vars[n]))))))

	# s.add(ForAll([x,y],Implies(term(x), follow(x,y)) ))
	# Definition constraint: no invalid symbol in follow sets
	pk = Bool("follow_set_1")
	consVar["follow_set_1"] = pk
	s.add(Implies(pk, ForAll([x,y],Implies(Or(y>symbol_counter,y<0),Not(follow(x,y))))))

	# Definition constraint: dol is in follow(N1)
	# NOTE: N1 is the starting nonterm
	if firstMapFlag == 1 and followMapFlag == 1:	
		graph["Follow_Rule1"].append("Follow_set_rule_1")
		graph["Follow_set_rule_1"] = []
	pk = Bool("Follow_set_rule_1")
	if firstConsFlag == 0:
	    	consVar["Follow_set_rule_1"] = pk
	else:
        	consVarH["Follow_set_rule_1"] = pk


	s.add(Implies(pk, follow(vars["N1"],vars["dol"])))

	######################################################

	# FOLLOW SET CONSTRUCTION

	######################################################

	for n in nonterms:
		for t in terms:
			var = "%(nonterm)s%(term)s"%{"nonterm":n, "term":t}
			vars["m_%s"%var] = Int("m_%s"%var)
			vars["n_%s"%var] = Int("n_%s"%var)
			s.add(get_m(vars[n],vars[t])==vars["m_%s"%(var)])
			s.add(get_n(vars[n],vars[t])==vars["n_%s"%(var)])

			tempList = []
			for i in range(1,num_rules+1):
				tempList.append(vars["m_%s"%var]==vars["rule%d"%(i)])

			pk = Bool("follow_set_cons_0_%s"%var)
			consVar["follow_set_cons_0_%s"%var] = pk
			s.add(Implies(pk, Or(tempList)))

			tempList = []
			for i in range(1,followCondEnd):
				tempList.append(vars["n_%s"%var]==vars["cond%d"%i])

			pk = Bool("follow_set_cons_1_%s"%var)
			consVar["follow_set_cons_1_%s"%var] = pk
			s.add(Implies(pk, Or(tempList)))

			for r in range(1,num_rules+1):
				condNo = 1
				for i in range(1,size_rules):
					for j in range(i+1,size_rules+1): ## edited in 28/1/22 (changed j+1 to i+1)
						pk = Bool("follow_set_cons_2_%s_%s_%s_%s"%(var,r,i,j))
						consVar["follow_set_cons_2_%s_%s_%s_%s"%(var,r,i,j)] = pk
						s.add(Implies(pk, Implies(And(follow(vars[n],vars[t]),vars["m_%s"%var]==vars["rule%d"%(r)],vars["n_%s"%var]==vars["cond%d"%(condNo)]),vars[n]==symbolInRHS(r,i))))
						condNo += 1

				for i in range(1,size_rules+1):
					pk = Bool("follow_set_cons_3_%s_%s_%s"%(var,r,i))
					consVar["follow_set_cons_3_%s_%s_%s"%(var,r,i)] = pk
					s.add(Implies(pk, Implies(And(follow(vars[n],vars[t]),vars["m_%s"%var]==vars["rule%d"%(r)],vars["n_%s"%var]==vars["cond%d"%(condNo)]),vars[n]==symbolInRHS(r,i))))
					condNo += 1
			
			pk = Bool("follow_set_cons_4_%s"%var)
			consVar["follow_set_cons_4_%s"%var] = pk
			s.add(Implies(pk, Implies(follow(vars[n],vars[t]),followWitness(vars[n],vars[t],vars["m_%s"%var],vars["n_%s"%var])!=-1)))

			tempList = []
			for i in range(1,num_rules+1):
				for j in range(1,followCondEnd):
					tempList.append(followWitness(vars[n],vars[t],vars["rule%d"%i],vars["cond%d"%j])==-1)
			pk = Bool("follow_set_cons_5_%s"%(var))
			consVar["follow_set_cons_5_%s"%(var)] = pk
			s.add(Implies(pk, Implies(Not(follow(vars[n],vars[t])),And(tempList))))

		t = "dol"
		if n != "N1":
			var = "%(nonterm)s%(dol)s"%{"nonterm":n,"dol":t}
			vars["m_%s"%var] = Int("m_%s"%var)
			vars["n_%s"%var] = Int("n_%s"%var)
			s.add(get_m(vars[n],vars[t])==vars["m_%s"%(var)])
			s.add(get_n(vars[n],vars[t])==vars["n_%s"%(var)])


			tempList = []
			for r in range(1,num_rules+1):
				tempList.append(vars["m_%s"%var]==vars["rule%d"%(r)])
			pk = Bool("follow_set_cons_6_%s"%(n))
			consVar["follow_set_cons_6_%s"%(n)] = pk
			s.add(Implies(pk, Or(tempList)))

			tempList = []
			for i in range(followCondMid,followCondEnd):
				tempList.append(vars["n_%s"%var]==vars["cond%d"%i])
			
			pk = Bool("follow_set_cons_7_%s"%(n))
			consVar["follow_set_cons_7_%s"%(n)] = pk
			s.add(Implies(pk, Or(tempList)))

			for r in range(1,num_rules+1):
				condNo = followCondMid
				for i in range(1,size_rules+1):
					pk = Bool("follow_set_cons_8_%s_%s_%s"%(n,r,i))
					consVar["follow_set_cons_8_%s_%s_%s"%(n,r,i)] = pk
					s.add(Implies(pk, Implies(And(follow(vars[n],vars[t]),vars["m_%s"%var]==vars["rule%d"%(r)],vars["n_%s"%var]==vars["cond%d"%(condNo)]),vars[n]==symbolInRHS(r,i))))
					condNo += 1

			pk = Bool("follow_set_cons_9_%s"%(n))
			consVar["follow_set_cons_9_%s"%(n)] = pk
			s.add(Implies(pk, Implies(follow(vars[n],vars[t]),followWitness(vars[n],vars[t],vars["m_%s"%var],vars["n_%s"%var])!=-1)))

			tempList = []
			for i in range(1,num_rules+1):
				for j in range(followCondMid,followCondEnd):
					tempList.append(followWitness(vars[n],vars[t],vars["rule%d"%i],vars["cond%d"%j])==-1)

			pk = Bool("follow_set_cons_10_%s"%(n))
			consVar["follow_set_cons_10_%s"%(n)] = pk
			s.add(Implies(pk, Implies(Not(follow(vars[n],vars[t])),And(tempList))))

	######################################################

	# PARSE TABLE CONSTRAINTS

	######################################################

	for n in nonterms:
		for t in terms+['dol']:
			pk = Bool("parse_table_0_%s_%s"%(n,t))
			consVarH["parse_table_0_%s_%s"%(n,t)] = pk
			s.add(Implies(pk, And(parseTable(vars[n],vars[t])<=num_rules,parseTable(vars[n],vars[t])>=0)))

	######################################################

	# PARSE TABLE CONSTRUCTION

	######################################################
	
#	tableMapFlag = 1
	
	if tableMapFlag == 0:
		implyFlag1 = Bool("implyFirst")
		consVarH["implyFirst"] = implyFlag1
		implyFlag2 = Bool("implyFollow")
		consVarH["implyFollow"] = implyFlag2
#		implyFlag3 = Bool("parse_table_3")
#		consVarH["parse_table_3"] = implyFlag3

	if tableMapFlag == 1:
		implyFlag1 = True #Bool("aa")
		implyFlag2 = True #Bool("bb")
	

	for n in nonterms:
			
		if tableMapFlag == 2:
			if tableConsFlag == 1:
				implyFlag1 = Bool("implyFirst_%s"%(n))
				consVarH["implyFirst_%s"%(n)] = implyFlag1

				implyFlag2 = Bool("implyFollow_%s"%(n))
				consVarH["implyFollow_%s"%(n)] = implyFlag2

			if tableConsFlag == 0:
				implyFlag1 = Bool("implyFirst_%s"%(n))
				consVar["implyFirst_%s"%(n)] = implyFlag1

				implyFlag2 = Bool("implyFollow_%s"%(n))
				consVar["implyFollow_%s"%(n)] = implyFlag2

		for t in terms:

			if tableMapFlag == 3:
				if tableConsFlag == 1:
					implyFlag1 = Bool("implyFirst_%s_%s"%(n,t))
					consVarH["implyFirst_%s_%s"%(n,t)] = implyFlag1

					implyFlag2 = Bool("implyFollow_%s_%s"%(n,t))
					consVarH["implyFollow_%s_%s"%(n,t)] = implyFlag2
			
				if tableConsFlag == 0:
					implyFlag1 = Bool("implyFirst_%s_%s"%(n,t))
					consVar["implyFirst_%s_%s"%(n,t)] = implyFlag1

					implyFlag2 = Bool("implyFollow_%s_%s"%(n,t))
					consVar["implyFollow_%s_%s"%(n,t)] = implyFlag2

			for r in range(1,num_rules+1):
			#if True:
				skip = "parse_table_cons_0_%s_%s_%s"%(n,t,r)
			
#				if skip not in parseTableEntry:
#					continue
#				print ("in maxsat", skip)

				tempAnd = []
				for i in range(1,size_rules+1):
					tempList = []
					for j in range(1,i):
						tempList.append(first(symbolInRHS(r,j),vars["eps"]))
					tempList.append(first(symbolInRHS(r,i),vars[t]))
					tempAnd.append(And(tempList))
#					tempImplyVar = Bool("parse_table_cons_2_%s_%s_%s_%s"%(n,t,r,i))
#					consVar["parse_table_cons_2_%s_%s_%s_%s"%(n,t,r,i)] = tempImplyVar
#					tempAnd.append(( And(tempList)))
#					tempAnd.append(Implies(tempImplyVar, And(tempList)))

#				tempImplyVar = Bool("parse_table_cons_2_%s_%s_%s"%(n,t,r))
#				consVar["parse_table_cons_2_%s_%s_%s"%(n,t,r)] = tempImplyVar

				tempList = []	
				for i in range(1,size_rules+1):
					tempList.append(first(symbolInRHS(r,i),vars["eps"]))
				tempList.append(follow(symbolInLHS(r),vars[t]))

#				pk1 = Bool("parse_table_cons_3_%s_%s_%s"%(n,t,r))
#				consVar["parse_table_cons_3_%s_%s_%s"%(n,t,r)] = pk1

#				tempAnd.append(Implies(pk,And(tempList)))

#				pk = Bool("parse_table_cons_0_%s_%s_%s"%(n,t,r))
#				consVar["parse_table_cons_0_%s_%s_%s"%(n,t,r)] = pk
#				print("in 588")
#				print ("in 589 ", vars["N2"], vars["t1"], vars["rule2"])
				
#				s.assert_and_track( (parseTable(vars[n],vars[t])==vars["rule%d"%r]) == (symbolInLHS(r)==vars[n]), "line_589_%s_%s_%s"%(n,t,r))
#				s.add(( (parseTable(vars[n],vars[t])==vars["rule%d"%r])==And(symbolInLHS(r)==vars[n],Or((Or(tempAnd)), Implies(pk1, And(tempList) )))))

#				s.add(( (parseTable(vars[n],vars[t])==vars["rule%d"%r]) == Implies(Or(Implies(implyFlag1,Or(tempAnd)), Implies(implyFlag2, And(tempList) )), symbolInLHS(r)==vars[n] )))

#				s.add(( (parseTable(vars[n],vars[t])==vars["rule%d"%r])==And(symbolInLHS(r)==vars[n],Or(Implies(implyFlag1,Or(tempAnd)), Implies(implyFlag2, And(tempList) ))))) 

				s.add(( (parseTable(vars[n],vars[t])==vars["rule%d"%r]) == And(symbolInLHS(r)==vars[n], Or(And(implyFlag1,Or(tempAnd)), And(implyFlag2, And(tempList) ))))) #working
				#implyFlagFirst_vars[n]_vars[t]

#				s.add(If(tempImplyVar,1,0) + If(pk1,1,0) <= 1)
		for r in range(1,num_rules+1):
			tempList = []
			for i in range(1,size_rules+1):
				tempList.append(first(symbolInRHS(r,i),vars["eps"]))
			tempList.append(follow(symbolInLHS(r),vars["dol"]))   # for A->BCD, is B,C,D->eps then follow of A is $

			pk = Bool("parse_table_cons_1_%s_%s"%(n,r))
			consVarH["parse_table_cons_1_%s_%s"%(n,r)] =  pk # added on 28 Jan 2022 -> changed consVar to consVarH (hard to soft constraints)
			s.add(Implies(pk, (parseTable(vars[n],vars["dol"])==vars["rule%d"%r])==And(symbolInLHS(r)==vars[n],And(tempList)))) # this is saying parsetable entry for N,$ will be rule%d and symbol in LHS of the rule will be the current nonterminal.
	
	"""
	######################################################

	# PARSING FUNCTIONS

	######################################################

	#We take an 'array' of parse actions and use that to process the input, using the following functions

	#The following functions are defined for parsing the (first arg) input string
	# Lookup and constraint application was successful on step (second arg) in parse action array
	step = Function('step', IntSort(), IntSort(), BoolSort())

	# True if parsing was completed on or before step (second arg)
	success = Function('success', IntSort(), IntSort(), BoolSort())

	# The symbol being expanded at location (second arg) in the parse action array - can be term or nonterm
	symbolAt = Function('symbolAt', IntSort(), IntSort(), IntSort())

	# The symbol at location (arg) in the input string
	ip_str = Function('ip_str', IntSort(), IntSort(), IntSort())

	# Index in the input string for the lookAhead symbol for the expansion at location (second arg) in the parse action array
	lookAheadIndex = Function('lookAheadIndex', IntSort(), IntSort(), IntSort())

	# Where does the (second arg) symbol in RHS of the rule getting expanded at (third arg) step in parse action array, start expanding
	startPosition = Function('startPosition', IntSort(), IntSort(), IntSort(), IntSort())

	# The ending index in the parse action array of the expansion of the symbolAt(second arg)
	end=Function('end', IntSort(), IntSort(), IntSort())

	# Take input and construct the ip_str function
	for i in range(len(InputList)):
		for j in range(len(InputList[i])):
			s.add(ip_str(i,j) == vars[InputList[i][j]])
		s.add(ip_str(i,len(InputList[i]))==vars["dol"])

	# Start parsing with N1 as the first symbol
	for i in range(len(InputList)):
		s.add(symbolAt(i,1) == vars["N1"])

	# Starting lookAheadIndex
	for i in range(len(InputList)):
		s.add(lookAheadIndex(i,1) == 0)

	# Starting step
	for i in range(len(InputList)):
		s.add(step(i,0))
	
	# Incremental parsing step number i to constrain the parse action array for the input string strNum
	def Step(s,strNum,i,config):

		num_rules = config['num_rules'] #Number of rules
		size_rules = config['size_rules']  #Max number of symbols in RHS
		num_nonterms = config['num_nonterms']  #Number of nonterms
		num_terms = config['num_terms']   #Number of terms

		# Termination condition
		s.add(Implies(And(end(strNum,1) == (i-1), step(strNum,i-1)), If(ip_str(strNum,lookAheadIndex(strNum,i)) == vars["dol"], And(Not(step(strNum,i)),ForAll(x,Implies(x>=i,success(strNum,x)))), And(Not(step(strNum,i)),ForAll(x,Not(success(strNum,x))) ) ) ))

		# For consuming term
		AndList=[]
		AndList.append(lookAheadIndex(strNum,i+1) == lookAheadIndex(strNum,i) + 1)
		AndList.append(step(strNum,i))
		AndList.append(Not(success(strNum,i)))
		AndList.append(end(strNum,i)==i)
		s.add(Implies(And(term(symbolAt(strNum,i)),step(strNum,i-1)), If(symbolAt(strNum,i)==ip_str(strNum,lookAheadIndex(strNum,i)), And(AndList), And(Not(step(strNum,i)), ForAll(x,Not(success(strNum,x))) )) ))

		# For expanding nonterm
		for k in range(1,size_rules+2):
			RHSList=[]
			AndList=[]
			for j in range(1,k):
				RHSList.append(symbolInRHS(parseTable(symbolAt(strNum,i),ip_str(strNum,lookAheadIndex(strNum,i))), j) == vars["eps"])
				AndList.append(startPosition(strNum,j,i) == i)
				
				
			for j in range(k, size_rules + 1):
				RHSList.append(symbolInRHS(parseTable(symbolAt(strNum,i),ip_str(strNum,lookAheadIndex(strNum,i))), j) != vars["eps"])
				if j != k :
					AndList.append(startPosition(strNum,j,i) == end(strNum,startPosition(strNum,j-1,i)) + 1)	
				else:
					AndList.append(startPosition(strNum,j,i) == i+1)	
				AndList.append(symbolAt(strNum,startPosition(strNum,j,i)) == symbolInRHS(parseTable(symbolAt(strNum,i),ip_str(strNum,lookAheadIndex(strNum,i))), j))
			
			AndList.append(lookAheadIndex(strNum,i+1) == lookAheadIndex(strNum,i))
			
			if k!=size_rules+1:
				AndList.append(end(strNum,i) == end(strNum,startPosition(strNum,size_rules,i)))
			else:
				AndList.append(end(strNum,i) == i)
			
			AndList.append(step(strNum,i))
			AndList.append( Not(success(strNum,i))  )
			s.add(Implies(And(nonterm(symbolAt(strNum,i)),step(strNum,i-1)),If(parseTable(symbolAt(strNum,i),ip_str(strNum,lookAheadIndex(strNum,i))) != 0, Implies(And(RHSList),And(AndList)), And(Not(step(strNum,i)),ForAll(x,Not(success(strNum,x))) ) )))

	######################################################

	# PARSING ALGORITHM

	######################################################

	SuccessList = []
	# Do required number of steps
	for strNum in range(len(InputList)):
		for i in range(expansion_constant*len(InputList[strNum])):
			Step(s,strNum,i+1,config)
		SuccessList.append(success(strNum,expansion_constant*len(InputList[strNum])))
    	"""
	functions["symbolInLHS"] = symbolInLHS
	solver = {}
	solver["constraints"] = s
	solver["vars"] = vars
	solver["functions"] = functions
	solver["terms"] = terms
	solver["nonterms"] = nonterms
#	solver["symbolInLHS"] = symbolInLHS
	
	return True,vars,solver, consVar, consVarH

def SP(s,InputList,config, parseTableEntry, ptM, ptC, fiM, fiC, foM, foC, graph):
    
    	# print ("in solversMaxsat.SP")
	num_rules = config['num_rules'] #Number of rules
	size_rules = config['size_rules']  #Max number of symbols in RHS

	SuccessList,vars,solver, consVar, consVarH = base_solver(s,InputList,config, parseTableEntry, ptM, ptC, fiM, fiC, foM, foC, graph)
	

	s.add(SuccessList)

	######################################################

	# SYNTHESIZER CONSTRAINTS

	######################################################
	"""
	functionArgs = [IntSort() for i in range(size_rules+1)]
	derivedBy = Function('derivedBy',functionArgs)

	for i in range(num_rules):
		tempList = []
		for j in range(size_rules):
			tempList.append(vars['x%d'%(i*(size_rules+1)+2+j)])
		s.add(derivedBy(tempList)==vars['x%d'%(i*(size_rules+1)+1)])
	"""
	derivedBy = []
	return vars,derivedBy,solver, consVar, consVarH

def SN(s,InputList,config):

	SuccessList,vars = base_solver(s,InputList,config)

	s.add(Or(SuccessList))

	return vars
