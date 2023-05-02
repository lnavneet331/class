def shorten(a):
    vowels = "AEIOUaeiou"
    output = ""
    for i in a:
        if i not in vowels:
            output += i
    return output