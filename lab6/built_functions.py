#Task1
array = [int(x) for x in input().split()]
def multiply(array):
    total = 1
    for x in array:
        total *= x
    return total
print(multiply(array))

#Task2
word = input()
def up_low(word):
    up = 0
    low = 0
    for x in word:
        if x >= 'A' and x <= 'Z':
            up += 1
        if x >= 'a' and x <= 'z':
            low += 1

    print("Upper case letters:", up)
    print("Lower case letters:", low)
up_low(word)

#Task3
word = input()
def isPalindrome(word):
    word = word.lower().replace(" ", "") #to convert chars to lower and remove whitespace 
    return word==word[::-1]
if(isPalindrome(word)==1):
    print("Palindrome")
else:
    print("Not palindrome")

#Task4
from time import sleep
import math
def delay(function, miliesec, *arguments):
  sleep(miliesec / 1000)
  return function(*arguments)
print("Square root after specific miliseconds:")
miliesec = int(input()) 
arguments = int(input())
print(delay(lambda x: math.sqrt(x), miliesec, arguments))

#Task5
x = (True, True, False)
y = (True, True, True)
print(all(x))
print(all(y))