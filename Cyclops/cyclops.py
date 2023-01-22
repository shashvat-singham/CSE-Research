#!/usr/bin/python2
import importlib

from z3 import *
from helpers import *
from solvers import *
#from input_specs_tiger import *
# from input_specs import *
from test import *
import calendar
import time
import datetime
#import solversTry
import solversMaxSat
import threading
from inspect import currentframe, getframeinfo
import sys

import imp

import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import to_agraph

sys.path.insert(0, '/cyclopsWeb/cyclopes-frontend/')

if len(sys.argv) != 2:
    print("Usage: ./unSynth [file name]")
    exit()

# handle = importlib.import_module(sys.argv[1].replace(".py", "").replace("/","."))
# handle = importlib.import_module(sys.argv[1].replace(".py", "").replace("/","."), package='cyclopes-frontend')
# handle = importlib.import_module( sys.argv[1].split('/')[-1].split('.')[0], package='/cyclopsWeb/cyclopes-frontend/inputs/')
# handle = importlib.import_module("pryadav.input_spec" , package='cyclopes-frontend.inputs')

inputFile = sys.argv[1].replace('.py','')
# print inputFile
packageLink =str(sys.argv[1])
# print packageLink
#handle = imp.load_source('input_specs', '/cyclopsWeb/cyclopes-frontend/inputs/pryadav/input_specs.py')
handle = imp.load_source(inputFile, packageLink)

'''
print(sys.argv[1].split('/')[-1].split('.')[0])
spec =  importlib.util.spec_from_file_location(sys.argv[1].split('/')[-1].split('.')[0] ,sys.argv[1].replace(".py", "").replace("/","."))
handle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handle)
'''

original_grammar = handle.find_original_grammar()
accept_strings,reject_strings,config = handle.specs()
terms = discover_terms(accept_strings)
#print("terms ", terms)
config.update({'num_terms':len(terms)})
assert(config['size_rules']>=2)

def reverseGraph(graph):
    revG = {}
    for i in graph.keys():
        revG[i] = []
        
    for i, j in graph.items():
        for k in range(1,len(j)):
            revG[j[k]].append(i)
    
    return revG

def calculateScore(graph):
    for i in graph.keys():
        if len(graph[i]) == 1:
            continue
        cr = 0
        bl = 0
        tmp = graph[i][0] 
        lst = graph[i]
        for j in range(1, len(lst)):
            if tmp == graph[lst[j]][0]:
                if tmp == 1:
                    cr += 1
                elif tmp == 0:
                    bl += 1

        graph[i].append(float(bl)/ float(cr + bl))
        
    return graph


def calculateScoreDump(graph, node):
    if len(graph[node]) == 1:
        return graph[node][-1]
    else:
        res = 0
        for i in graph[node]:
            if type(i) !=  int:
                res += calculateScore(graph, i)
        graph[node][-1] = res
        return res

def processCons(cons, value, firstFlag, followFlag, assign):
    #print ("process ", cons)
    if "firstSet_rule1_" in cons:
        bug = cons.split('_')
        print("First rule of First set for terminal: %s" %assign[bug[2]])

    if "firstSet_2" in cons:
        bug = cons.split('_')
        if firstFlag == 1:
            print("Second rule of First Set for Rule: %s"% bug[3])
        elif firstFlag == 2:
            print("Second rule of First Set for non terminal: %s, and terminal:  %s"%(assign[bug[3]], assign[bug[4]]))
        elif firstFlag == 3:
            print("Second rule of First Set for non terminal: %s, terminal: %s "%(assign[bug[3]], assign[bug[5]]))

    elif "first_set_cons_5_" in cons:
        bug = cons.split('_')
        print("Third rule of First Set for non terminal: %s"%(assign[bug[4]]))

    elif "Follow_set_rule_1" in cons:
        print("First rule of Follow set")

    elif "Follow_set_rule_2_" in cons:
        bug = cons.split('_')
        if followFlag == 1:
            print("Second rule of Follow Set for Rule %s"% bug[4])
        elif followFlag == 2:
            print("Second rule of Follow Set for rule: %s, and terminal: %s"%(bug[4], assign[bug[5]]))
        elif followFlag == 3:
            print("Second rule of Follow Set for rule: %s, and terminal: %s"%(bug[4], assign[bug[6]]))

    elif "Follow_set_rule_3_" in cons:
        bug = cons.split('_')
        if followFlag == 1:
            print("Third rule of Follow Set for Rule %s"% bug[4])
        elif followFlag == 2:
            print("Third rule of Follow Set for rule: %s, and terminal: %s"%(bug[4], assign[bug[5]]))
        elif followFlag == 3:
            print("Third rule of Follow Set for rule: %s, and terminal: %s"%(bug[4], assign[bug[6]]))




def calculateUnsatCore(maxSat, coreCons, assign, graph, consVarH):
    coreStr = [str(k) for k in coreCons]
    for i in range(len(coreCons)):
        maxSat.push()
        
        for name, val in consVarH.items():
            maxSat.assert_and_track(val, name)
        
        maxSat.add(coreCons[i] == False)  #relax that particular unsat core
        for j in range(len(coreCons)):
            if j == i:
                continue
            maxSat.assert_and_track(coreCons[j], str(coreCons[j]))
        if maxSat.check() == unsat:
            tempCore = maxSat.unsat_core()
            for i in tempCore:
                if str(i) not in coreStr:
                    coreCons.append(i)
                    coreStr.append(str(i))
                    del consVarH[str(i)]

        else:
            print ("In sat for the loop")
        maxSat.pop()
    print("coreCons", coreCons)
       
    for key, val in graph.items():
        if key in coreStr:
            if len(val) > 0:
                if type(val[0]) != int:
                    graph[key].insert(0, int(0))
                else:
                    if val[0] == 1:
                        graph[key][0] = 0
                    #elif val[0] == 0:
                    #    continue
            else:
                graph[key].append(int(0))

        else:   #not in the unsatcore
            if len(val) > 0:
                if type(val[0]) != int:
                    graph[key].insert(0, int(1))
            
            else: #len(val) > 0
                graph[key].append(int(1))

            

    #print ("track", track)
    for i in coreStr:
        processCons(i, 1, 1, 1, assign)


'''
    to calculate list of cores  
'''
def calculatePotentialCore(opt, coreList,  consVarH, falseCoreList, listOfCores, currCell):
    # listOfCores = []
    # for j in parseTableCore:
    #     calculatePotentialCore(opt, j, parseTableCore, consVarH, listOfCores)

    # print(currentframe().f_lineno, "potential core", coreList)

    if len(coreList) == 0:
        # print("Corelist size is ZERO")
        return

    for cons in coreList:
        # opt.add(consVarH[coreList[0]] == False)
        opt.push()
        #
        # print("Cons started : %s"%cons)
        # print("Total cons %s"%str(coreList))
        falseCoreList.append(cons)

        for name, val in consVarH.items():
            # if name == coreList[0]:
            if "parseTableEntry" in name :
                # print("currcell found %s"%name)
                continue

            if name in falseCoreList:
                opt.add(consVarH[cons] == False)
                # print("in name == cons -> %s" %name)
                continue
                # opt.add(consVarH[name] == False)
            else:
                # print("name: %s"%name)
                opt.assert_and_track(val, name)

        res = opt.check()
        if res == sat:
            # print("Corelist gave SAT for " + str(coreList))
            opt.pop()
            return
        elif res == unsat:
            # print("touched Here")
            opt.pop()
            core = opt.unsat_core()
            newCore = [str(i) for i in core]
            newCoreSet = set(newCore)
            # oldCoreSet = set(coreList)

            for ls in listOfCores:
                # if newCoreSet.issubset(oldCoreSet):
                if newCoreSet.issubset(ls):
                    listOfCores.remove(ls)
            listOfCores.append(newCoreSet)

            newOldCoreList = list(coreList)
            newOldCoreList.remove(cons)
            # newOldCoreList.remove(coreList[0])
            newFalseCoreList = list(falseCoreList)
            calculatePotentialCore(opt, newOldCoreList, consVarH, newFalseCoreList, listOfCores,currCell)
        else:
            opt.pop()
            return

'''
    :return the rule number of the core
'''
def getLabel(cons):
    if "firstSet_rule1_" in cons:
        return "First_1"

    elif "firstSet_2" in cons:
        return "First_2"

    elif "first_set_cons_5_" in cons:
        return "First_3"

    elif "Follow_set_rule_1" in cons:
        return "Follow_1"

    elif "Follow_set_rule_2_" in cons:
        return "Follow_2"

    elif "Follow_set_rule_3_" in cons:
        return "Follow_3"

    elif "parseTableEntry_" in cons:
        return "ParseTable_1"

    elif "parse_table_cons_1" in cons:
        return "ParseTable_2"

    else:
        return "Unknown"

def normalizeMap(sMap):
    severityMap = {"First": {"1": 0, "2": 0, "3": 0}, "Follow": {"1": 0, "2": 0, "3": 0}, "ParseTable": {"1": 0, "2": 0}}
    sum = 0
    for key, value in sMap.items():
        for k, v in value.items():
            sum += v

    if sum == 0:
        temp = [20, 0, 20, 0, 20, 20, 0, 20]
        return str(temp).replace('[','').replace(']','')
        # return {"First": {"1": 20, "2": 0, "3": 20}, "Follow": {"1": 0, "2": 20, "3": 20}, "ParseTable": {"1": 0, "2": 20}}

    for key, value in sMap.items():
        for k in value.keys():
            severityMap[key][k] = int((float(sMap[key][k]) / sum) * 100)

    severityList = []
    severityList.append(severityMap["First"]["1"])
    severityList.append(severityMap["First"]["2"])
    severityList.append(severityMap["First"]["3"])
    severityList.append(severityMap["Follow"]["1"])
    severityList.append(severityMap["Follow"]["2"])
    severityList.append(severityMap["Follow"]["3"])
    severityList.append(severityMap["ParseTable"]["1"])
    severityList.append(severityMap["ParseTable"]["2"])

    print(str(severityList).replace('[','').replace(']',''))
    return severityMap
'''
    :return severity map
    its implementation is very clumsy
    will figure out a way to optimize it
'''
def returnSeverity(unsatCoreMap):
    severityMap = {"First": {"1": 0, "2": 0, "3": 0}, "Follow": {"1": 0, "2": 0, "3": 0}, "ParseTable": {"1": 0, "2": 0}}
    for key, value in unsatCoreMap.items():
        tempList = []
        for uc in value:
            for i in uc:
                tempList.append(str(i))

        for j in tempList:
            label = getLabel(j)
            if label == "Unknown":
                continue
                # print("Undefined label found in severityMap with key: %s, core: %s" %(str(key), str(j)))
                # exit()
            label = label.split('_')
            severityMap[label[0]][label[1]] += 1

    return normalizeMap(severityMap)



'''
    New naive ranking algorithm 
'''
def naiveRanking(opt, assign, graph, consVarH):

    opt.push()

    #### for  constraints with labels ####
    for name, val in consVarH.items():
        opt.assert_and_track(val, name)

    initialCore = []
    if opt.check() == unsat:
        core = opt.unsat_core()
        initialCore = [str(i) for i in core]
        opt.pop()
    # print(initialCore)
    parseTableCore = []
    ## find the cores related to parse table
    for i in initialCore:
        if "parseTableEntry" in i:
            parseTableCore.append(str(i))
            initialCore.remove(i)

    # print("total parsetable %s"%parseTableCore)
    # allPTCoreMap is a map from parese entry to the list of the unsatcore set
    allPTCoreMap = {}
    for j in parseTableCore:
        # print("parse table cell initiated %s"% j)
        opt.push()
        for k in parseTableCore:
            if k == j:
                opt.add(consVarH[k] == True)
            else:
                opt.add(consVarH[k] == False)

        if opt.check() == unsat:
            core = opt.unsat_core()
            initialCore = [str(i) for i in core]
	    # print("initial core: ", initialCore)
	    if len(initialCore) == 0:
                allPTCoreMap[j] = []
                allPTCoreMap[j].append(set([j]))
		continue

            # opt.pop()
            allPTCoreMap[j] = []
            allPTCoreMap[j].append(set(initialCore))
            calculatePotentialCore(opt, initialCore, consVarH, [], allPTCoreMap[j], j)
	else:
	    allPTCoreMap[j] = []
            allPTCoreMap[j].append(set(initialCore))
            calculatePotentialCore(opt, initialCore, consVarH, [], allPTCoreMap[j], j)
        opt.pop()

    # print(currentframe().f_lineno, allPTCoreMap)
    return returnSeverity(allPTCoreMap)



    



def checkGrammar(purpose, parseTableEntry, ptMapFlag, ptConsFlag, fiMapFlag, fiConsFlag, foMapFlag, foConsFlag, graph):

    #start_time = calendar.timegm(time.gmtime())

    opt = Solver()

    opt.set("timeout", 10000)  #timeout 20 sec

    #SP_vars,SP_derivedBy, solver, consVar, consVarH = solversMaxSat.SP(maxSat,acceptList,config, parseTableEntry, ptMapFlag, ptConsFlag, fiMapFlag, fiConsFlag, foMapFlag, foConsFlag)
    SP_vars,SP_derivedBy, solver, consVar, consVarH = solversMaxSat.SP(opt, [], config, parseTableEntry, ptMapFlag, ptConsFlag, fiMapFlag, fiConsFlag, foMapFlag, foConsFlag, graph)

    parseLabel = repair(solver, original_grammar, config['num_rules'], config['size_rules'], handle)

    consVarH.update(parseLabel)

    assignT = solver["view_assign"]
    assign =  dict([(value, key) for key, value in assignT.items()])

    #print("CONSVARH in %s"%purpose)
    #print(len(consVarH))
    
    # for hard constraints ##

    for name, val in consVar.items():
        opt.add(val)

    something = naiveRanking(opt, assign, graph, consVarH)
    return something

    '''
        Following piece of code is not reachable
    '''
    opt.push()

    #### for soft constraints ####

    for name, val in consVarH.items():
        # print(name)
        opt.assert_and_track(val, name)



    if opt.check() == unsat:
        core = opt.unsat_core()
        core1 = [str(i) for i in core]
        #print (core)
        #print (core1)
        opt.pop()
        coreCons = []
        track = []


        for name, val in consVarH.items():
            #maxSat.add(val)
            if name in core1:
                coreCons.append(val)
                #print ("consVarH", consVarH[name])
                del consVarH[name]
            '''
            else:
                opt.assert_and_track(val, name)
                if name == "firstSet_rule1_t2":
                    print("firstSet_rule1_t2")
                #opt.add(val)
            '''
        
        opt.set("timeout", 20000)
        calculateUnsatCore(opt, coreCons, assign, graph, consVarH)        
    else:
        print ("Max sat for %s is SAT" %purpose)
        '''
        for j,i in maxSatHandle.items():
            #print(j, i.value())
            if str(i.value()) == '1':
                processCons(j, str(i.value()), fiMapFlag, foMapFlag, assign)
        '''

    #end_time = calendar.timegm(time.gmtime())

    #print "Time taken for getting max sat for %s : %s"%(purpose,str(datetime.timedelta(seconds=(end_time-start_time))))


def dumpGraph(conceptGraph):
    g = nx.Graph()
    for j, k in conceptGraph.items():
        for i in k:
            g.add_edge(j, i)
    A = to_agraph(g)
    A.layout('dot')
    A.draw("conceptGraph.png")
    # nx.draw(g, with_labels=True)
    # plt.savefig("conceptGraph.png")


conceptGraph = {}
conceptGraph['parseTable'] = ['First', 'Follow']

conceptGraph['First'] = ['First_Rule1', 'First_Rule2', 'First_Rule3']
conceptGraph['Follow'] = ['Follow_Rule1', 'Follow_Rule2', 'Follow_Rule3']
conceptGraph['First_Rule1'] = []
conceptGraph['First_Rule2'] = []
conceptGraph['First_Rule3'] = []
conceptGraph['Follow_Rule1'] = []
conceptGraph['Follow_Rule2'] = []
conceptGraph['Follow_Rule3'] = []



start_time = calendar.timegm(time.gmtime())

for i in range(1,4):
    for j in range(1,4):
        # print("for flag, first: %s and follow: %s"%(i,j))
        severityMap = checkGrammar("unsat checking", [], 1, 1, i, 1, j, 1, conceptGraph)
        # checkGrammar("unsat checking", [], 1, 1, -1, 1, -1, 1, conceptGraph)
        break # added on 28/1/2022
    break # added on 28/1/2022

end_time = calendar.timegm(time.gmtime())

##print(conceptGraph)

# dumpGraph(conceptGraph)

# graphScore = calculateScore(conceptGraph)

##print(graphScore)
#
# fileT =  open("result", "a")
# fileT.write("%s:  %s"%(sys.argv[1],str(datetime.timedelta(seconds=(end_time-start_time)))))
# fileT.write('\n')
# print ("Total Time taken %s"%(str(datetime.timedelta(seconds=(end_time-start_time)))))
