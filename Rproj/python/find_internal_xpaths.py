import csv

paths = set()
with open("../counts.csv", "rb") as counts:
    for version, path, count in csv.reader(counts):
        paths.add(path)

pathCopy = paths.copy()

for i in paths:
    c = 0
    for j in pathCopy:
        if j.startswith(i + "/"):
            c += 1
    if c > 0:
        print i

