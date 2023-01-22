import sys
import json


gt2pt = {2: {1: u"input_specs2_PT_2_B.py"}}


grammar = 2 #sys.argv[1]
task = 1 #sys.argv[2]


def getNullProd(G):
    nullSet = []
    for i in G:
        if i[-1] == 'eps':
            nullSet.append(i[0])
    return nullSet

def cleanUp(G, nullSet):
    newG = []
    for prod in G:
        ts = set(prod[1:])
        if 'eps' in ts and len(ts) == 1:
            newG.append([prod[0], 'eps'])
        else:
            temp = list(prod)
            try:
                while True:
                    temp.remove('eps')
            except ValueError:
                pass
            newG.append(temp)
    return newG


# require a grammar after applying cleanUp()
def convertG2Str(G):
    gStr = []
    for prod in G:
        ts = prod[1:]
        gStr.append(prod[0] + " -> " + ' '.join([ele for ele in ts]))
    return gStr



def getBetterPt(pt, G):

    newPt = list(pt)
    for row in range(len(newPt)):
        for k, v in newPt[row].items():
            if k == "non_term":
                continue
            elif v == 0:
                newPt[row][k] = ""
            else:
                newPt[row][k]= G[int(newPt[row][k]) - 1]
    return newPt


def cleanerFeedback(fdbk):
    nFdbk = []
    for i in fdbk:
        if "First_1" in i:
            nFdbk.append("First Set Rule 1")
        elif "First_2" in i:
            nFdbk.append("First Set Rule 2")
        elif "First_3" in i:
            nFdbk.append("First Set Rule 3")
        if "Follow_1" in i:
            nFdbk.append("Follow Set Rule 1")
        elif "Follow_2" in i:
            nFdbk.append("Follow Set Rule 2")
        elif "Follow_3" in i:
            nFdbk.append("Follow Set Rule 3")
        if "PT_1" in i:
            nFdbk.append("Parse Table Rule 1")
        if "PT_2" in i:
            nFdbk.append("Parse Table Rule 2")
    return nFdbk

f = open("JSONdata.txt")
data = json.load(f)["data"]


def addingEpsHtml(G):
    for i in range(len(G)):
        if "eps" in G[i]:
            # print("&#949;", G[i])
            G[i] = G[i].replace("eps","<Latex>$\epsilon$</Latex>")
    return G

response = {}
#print("ga", grammar, task, gt2pt[int(grammar)][int(task)])
for d in data:
    if d["Filename"] == gt2pt[int(grammar)][int(task)]:
        pt = d["ParseTable"]
        G = d["Grammar"]

        newPt = getBetterPt(pt, G)
        #fdbk = cleanerFeedback(d["Feedback"])
        fdbk = d["Feedback"]
        
        response = { "Grammar" : G, "ParseTable" : newPt, "Feedback": fdbk}
        break

print(json.dumps(response))
