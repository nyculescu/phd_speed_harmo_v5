# Node arithmetic of corridor.build (c1c 4dfefca, corridor.py:24-25, 48, 62-67), typed in from the source; no netconvert.
import math
N={"n1":(0,0),"n2":(3000,0),"m":(3500,0),"ae":(3800,0),"d":(5000,0),"b":(6000,0),"x":(6500,0),"r0":(3080,-40),"rm":(3470,-4)}
R2={"e2":(5300,0),"b":(6300,0),"x":(6800,0),"r02":(4580,-40),"rm2":(4970,-4)}
def pos(al,a2):
    p={n:(x+(al-300 if x>=N["ae"][0] else 0),y) for n,(x,y) in N.items()}
    for n,(x,y) in R2.items(): p[n]=(x+(a2-300 if n in("e2","b","x") else 0),y)
    return p
E={"3a":("m","ae"),"3":("ae","d"),"4a":("d","e2"),"4":("e2","b"),"5":("b","x"),"rj2":("rm2","d"),"rj":("rm","m"),"gore1_to_gore2":("m","d")}
for al,a2 in ((300,300),(600,300),(600,600),(300,600)):
    p=pos(al,a2); print(al,a2,{e:round(math.dist(p[a],p[b]),1) for e,(a,b) in E.items()})
