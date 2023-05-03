#check whether a given year is leap year or not
a = int(input("Enter the year: "))
if a%4 == 0 and a%100 != 0 or a%400 == 0:
    print("The year is leap year")
else:
    print("This is not a leap year")

if a % 4 == 0: 
    if a % 400 == 0: 
        print("This is a leap year")
    elif a % 100 == 0:
        print("This is not a leap year")
    else:
        print("This is a leap year")
else:
    print("This is not a leap year")