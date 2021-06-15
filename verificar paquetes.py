
import pkg_resources

dists = [str(d).replace(" ","==") for d in pkg_resources.working_set]
for i in dists:
    print(i)