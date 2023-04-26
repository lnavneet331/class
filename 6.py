num = int(input("Enter year: "))

if num%4==0 and not num%100==0:
    print("Yes")
elif num%400==0:
    print("Yes")
else:
    print("No")