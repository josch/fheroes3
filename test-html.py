file = open("test2")
objects = [[] for i in range(255)]
for line in file:
    objclass, obj = line.split()
    objects[int(objclass)].append(obj)

file = open("test.html", "w")
for i, objs in enumerate(objects):
    if len(objs) == 0:
        continue
    file.write("<h1>class %d</h1>\n"%i)
    for obj in objs:
        file.write("<img src=\"data/advmap_objects/%s/0.png\" title=\"%s\"/>\n"%(obj, obj))
