#find the largest among 3 numbers
a = int(input("Enter the first number: "))
b = int(input("Enter the second number: "))
c = int(input("Enter the third number: "))
if a>b and a>c:
    print("The largest number is: ",a)
if b>a and b>c:
    print("The largest number is: ",b)
if c>a and c>b:
    print("The largest number is: ",c)
if a == b and b == c:
    print("All the numbers are equal")
else:
    print("The largest number is: ",c)
