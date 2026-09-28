import sys
walls=set("│─┌┐└┘├┤┬┴┼")
x0=int(sys.argv[1]); x1=int(sys.argv[2])
for l in sys.stdin.read().split("\n"):
    if len(l)>3 and l[:2].isdigit() and 10<=int(l[:2])<=31:
        body=l[3:]
        seg=body[x0:x1+1]
        print(l[:2], "".join("#" if c in walls else "." if c=="·" else c for c in seg))
