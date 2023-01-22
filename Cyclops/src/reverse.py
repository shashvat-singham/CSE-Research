from timeit import repeat


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

print(reverse_grammar([['S','a','S','a','a'],['S','a','S','eps','eps'],['S','eps','eps','eps','eps']]))