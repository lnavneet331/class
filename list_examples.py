accepted_denomination = [5, 10, 25]
price = 50
amount_due = 50
amount_inserted = 0

while amount_due > 0:
    print(f"Amount Due: {amount_due}")
    a = int(input("Insert Coin: "))
    if a in accepted_denomination:
        amount_due -= a
        amount_inserted += a
    
print(f"Change Owed: {amount_inserted - price}")