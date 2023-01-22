# import csv
# import sys
import time


# if len(sys.argv) != 2:
#     print("Porvide an argument as file name")
#     sys.exit(0)

# #get the filename passed as command line argument
# fileName = sys.argv[1]

# with open(fileName, 'r') as f1:
#     #values = csv.reader(file)
#     values = f1.readlines()
#     for line in values:
#         print(line.strip())
#         #time.sleep(1)


import subprocess
import sys
# time.sleep(10)
fileName = sys.argv[1]
import os
tmp="python2 generate_parsetable.py " + fileName
try:
    # process = subprocess.Popen(tmp.split(), stdout=subprocess.PIPE)
    # output, error = process.communicate()
    output,error=os.system(tmp)
    print(output)
except:
    print("Execution Failed")
