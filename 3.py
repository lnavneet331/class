# Check whether a triangle is valid or not with given sides
a = int(input("Enter the first side: "))
b = int(input("Enter the second side: "))
c = int(input("Enter the third side: "))
if a+b>c and b+c>a and c+a>b:
    print("The triangle is valid")
else:
    print("The triangle is not valid")
    