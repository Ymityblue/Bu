# Bu
#Helper tool for Bu assignments when using python as a calculator

#How to use:

#import the Bonus file:
import sys
sys.path.insert(1, 'path/to/file/folder)
from Bonus import *
from sympy.physics.units import *

#Make a function:

def Foo():
  #code here
  return bar
Foo()

#add the @Bu decorator:
@Bu
def Foo():
  #mathstuff
  #cosntants on their own:
  bar = 123*meter #etc
  return bar
Foo()
