import os

path = '/Users/damirnurmagambetov/Desktop/study files'

#Task 1
print("Only directories:")
print([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))])

print("Only files:")
print([name for name in os.listdir(path) if not os.path.isdir(os.path.join(path, name))])

print("All directories and files:")
print([name for name in os.listdir(path)])

#Task 2
print("Existence:", os.access(path, os.F_OK))
print("Readability:", os.access(path, os.R_OK))
print("Writability:", os.access(path, os.W_OK))
print("Executability:", os.access(path, os.X_OK))

#Task3
if os.path.exists(path):
    print("Given path exists.")
    print("Filename:", os.path.basename(path))
    print("Dirname:", os.path.dirname(path))
else:
    print("Given path does not exist.")
#Task 4
def file(name):
    with open(name) as f:
        cnt = sum(1 for line in f)
    return cnt

print("Number of lines:", file("text.txt"))
    
#Task 5
color = ["column", "word", "number", "name", "old", "major", "faculty"]
with open('name.txt', "w") as f:
    for i in color:
        f.write("%s\n"%i)
with open('name.txt', "r") as f:
    content = f.read()
    print(content)

#Task 6
for char in range(ord('A'), ord('Z')+1):
    file_name = chr(char) + ".txt"
    with open(file_name, 'w') as file:
        file.write("".format(file_name))

#Task 7
from shutil import copyfile
copyfile('name.txt', 'copy_of_name.txt')

#Task 8
if os.path.exists("name.txt"):
    os.remove("name.txt")
else:
    print("The file does not exist.")