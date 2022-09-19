import subprocess


out = subprocess.getoutput("LANG=C git branch")
branches = out.replace(" ", "").splitlines()
for branch in branches:
    if branch.startswith("*"):
        branches.insert(0, branches.pop(branches.index(branch)))
        branches[0] = branch.lstrip("*")
print(branches)
