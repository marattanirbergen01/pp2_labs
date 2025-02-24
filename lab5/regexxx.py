import re
file = open("/Users/damirnurmagambetov/Desktop/PP2_Labs/Lab_5/text.txt", "r")
content = file.read()

# Task1
# Write a Python program that matches a string that has an 'a' followed by zero or more 'b''s.
result1 = re.findall(r'ab*', content)

# Task2
# Write a Python program that matches a string that has an 'a' followed by two to three 'b'.
pattern = r'ab{2,3}'
result2 = re.findall(pattern, content)

# Task3
# Write a Python program to find sequences of lowercase letters joined with a underscore.
pattern = r'[a-z]+\_'
result3 = re.findall(pattern, content)

# Task4
# Write a Python program to find the sequences of one upper case letter followed by lower case letters.
pattern = r'[A-Z][a-z]+'
result4 = re.findall(pattern, content)

# Task5
# Write a Python program that matches a string that has an 'a' followed by anything, ending in 'b'.
pattern = r'a.+b$'
result5 = re.search(pattern, content)

# Task6
# Write a Python program to replace all occurrences of space, comma, or dot with a colon.
pattern = r'[ ,.]'
replace = ':'
result6 = re.sub(pattern, replace, content)

# Task7
# Write a python program to convert snake case string to camel case string.
pattern = r'_+(\w)'
def replace(match):
    return match.group(1).upper()
result7 = re.sub(pattern, replace, content)

# Task8
# Write a Python program to split a string at uppercase letters.
pattern = r'([a-z])([A-Z])'
result8 = re.sub(pattern, r'\1 \2', content)

# Task9
# Write a Python program to insert spaces between words starting with capital letters.
pattern = r'([a-z0-9])([A-Z])'
replace = r'\1 \2'
result9 = re.sub(pattern, replace, content)

# Task10
# Write a Python program to convert a given camel case string to snake case.
pattern = r'([a-z0-9])([A-Z])'
replace = r'\1_\2'
result10 = re.sub(pattern, replace, content)
answer10 = result10.lower()

def printing():
    print("Answer for Task 1:", result1)

    print("Answer for Task 2:", result2)

    print("Answer for Task 3:", result3)

    print("Answer for Task 4:", result4)

    print("Answer for Task 5:", result5)

    print("Answer for Task 6:", result6)

    print("Answer for Task 7:", result7)

    print("Answer for Task 8:", result8)

    print("Answer for Task 9:", result9)

    print("Answer for Task 10:", answer10)

printing()