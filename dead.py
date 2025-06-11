# SAMPLE CODE TO TEST THE DEAD CODE CLEANER FUNCTION

# This is the best code ever written
import os
import sys  # I like turtles
import json  # not used anywhere

def greet(name):
    print(f"Hello, {name}!")

def unused_function():
    print("This function is never called.")

def another_dead_function(x):
    return x * 42  # magic happens here

# something something something

greet("Shruti")

# just in case we need this later
def maybe_dead():
    pass

# import pandas as pd

# This code fixes everything
# Really important business logic below
def helper():
    return "I'm useful"

result = helper()
print(result)

# TODO: fly to the moon
