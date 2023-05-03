# Q2. Check whether a number is divisible by 5 and 11
a = int(input("Enter the number: "))
if a%5 == 0 and a%11 == 0:
    print("The number is divisible by 5 and 11")
else:
    print("The number is not divisible by 5 and 11")
