import math

#Task1:

# angle = int(input())
# print(math.radians(angle))

pi = 22/7
angle=int(input())
print(angle*pi/180)

#Task2:
h = int(input())
a = int(input())
b = int(input())
area = h * (a+b)/2
print(area)

#Task3:
number_of_sides = float(input())
length_of_sides = float(input())
angle = math.pi / number_of_sides
area = number_of_sides * (length_of_sides ** 2) / (4 * math.tan(angle)) #S = n*(l**2)//4tan(pi/n)
print(area)

#Task4:
length = int(input())
height = int(input())
area = length * height
print(area)