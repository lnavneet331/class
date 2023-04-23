a = int(input("Enter side 1: "))
b = int(input("Enter side 2: "))
c = int(input("Enter side 3: "))

if a+b>c and b+c>a and c+a>b:
    print("Yes")
else:
    print("No")