from sympy.physics.units import *
import sympy as sp
import inspect
import re
import ast
import numpy as np

convertunits = {
    "second":"s",
    "meter":"m",
    "kilogram":"kg",
    "ampere":"A",
    "kelvin":"K",
    "mol":"mol",
    "candela":"cd",
    "radian":"rad",
    "steradian":"sr",
    "bequerel":"Bq",
    "celculs": "°C",
    "coloumb": "C",
    "farad":"F",
    "gray":"Gy",
    "henry":"H",
    "hertz":"Hz",
    "joule":"J",
    "lumen":"lu",
    "lux":"lx",
    "newton":"N",
    "pascal":"Pa",
    "simens":"S",
    "sievert":"Sv",
    "Tesla":"T",
    "volt":"V",
    "watt":"W",
    "ohm":"Ω",
    "weber":"wb",
    "liter":"l",
    "minute":"min",
    "hour":"h",
    "days":"d",
    "year":"a",
    "tonne":"t",
    "bar":"bar",
    "electronvolt":"eV",
    "ångström":"Ã…",
    "astronomicunit":"au",
    "lightyear":"ly",
    "grad":"°",
    "lightspeed":"c",
    "gram": "g"}


class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = set()

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            self.variables.add(node.id)

class VariableUsageCollector(ast.NodeVisitor):
    def __init__(self):
        self.used_variables = set()

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_variables.add(node.id)

def get_unused_variables(script: str):
    tree = ast.parse(script)

    var_collector = VariableCollector()
    var_collector.visit(tree)
    all_variables = var_collector.variables

    usage_collector = VariableUsageCollector()
    usage_collector.visit(tree)
    used_variables = usage_collector.used_variables

    unused_variables = all_variables - used_variables
    return unused_variables

def unit(expr):
    if type(expr) in [int, float, np.float64]:
        return 1
    return expr.subs({x: 1 for x in expr.args if not x.has(Quantity)})

def sin(n):
    x = convert_to(n, radian)
    units = unit(x)
    return sp.N(sp.sin(x/units))*units/radian

def cos(n):
    x = convert_to(n, radian)
    units = unit(x)
    return sp.N(sp.cos(x/units))*units/radian

def arccos(n):
    return np.arccos(np.float64(n))

def arcsin(n):
    return np.arcsin(np.float64(n))

def sqrt(n):
    return sp.sqrt(n)

pi = np.pi

def Bu(func):

    def replace_dict(string_word:str):
        temp = []
        # get pos of all "*"
        # get pos of all "/"
        starpos = list(filter(lambda i: i[1] == "*", enumerate(string_word)))
        starpos = [j[0] for j in starpos]
        slashpos = list(filter(lambda i: i[1] == "/", enumerate(string_word)))
        slashpos = [j[0] for j in slashpos]
        for word in re.split(r"[\*/^]", string_word):
            temp.append(convertunits.get(word, word))
        new_str = ""
        for word in temp:
            new_str += word
            if len(starpos) > 0 and len(slashpos)>0:
                if starpos[0] <slashpos[0]:
                    new_str+="*"
                    del starpos[0]
                elif starpos[0] >slashpos[0]:
                    new_str+="/"
                    del slashpos[0]
            else:
                if len(starpos) > 0:
                    new_str+="*"
                    del starpos[0]
                elif len(slashpos) > 0:
                    new_str+="/"
                    del slashpos[0]
        return new_str


    def remove_unit(number_with_unit):
        number_without_unit = re.split(r"[\*/]", number_with_unit)[0]
        number_without_unit = "".join(number_without_unit.split("."))
        if float(number_without_unit) % 1 == 0:
            number_without_unit = str(int(float(number_without_unit)))
        segnificant_numbers = 0
        check = False
        for i in number_without_unit:
            if not i in ("0", ".") or check or len(number_without_unit) == 1:
                check = True
                segnificant_numbers += 1 
        return segnificant_numbers 
    
    def check_const(string_int):
        try:
            exec("val = " + string_int)
            return True
        except:
            return False
 
    def roughtlog10(number):
        number = abs(number)
        count = 0
        if number < 1:
            while number < 1:
                count -= 1
                number = number * 10
        elif number > 1:
            while count > 1:
                count += 1
                number = number / 10
        return count

    def significant_output(number, significant_length):
        #remember the sign of number
        sign = ""
        if number < 0:
            sign = "-"
        #remove the sign
        number = abs(number)
        #get dot placement
        dotplacement = roughtlog10(number)
        str_number = "".join(str(number).split(".")) # number *10**(length number)
        number = round(int(str_number), -len(str_number) - dotplacement + significant_length)
        str_number = "0"*-dotplacement + str(number)
        str_number = str_number[:significant_length-dotplacement]
        str_number = str_number[:1] + "," + str_number[1:]
        str_number = sign+(str_number[:-1] if str_number[-1] =="," else str_number)
        return str_number

    def wrapper(*args, **kwargs):
        script = inspect.getsource(func)
        lines = list(script.split("\n"))[2:]
        #lines.insert(0, "from sympy.physics.units import *\nimport sympy as sp")
        lines[-1] = lines[-1].replace("return", "print(")
        script2 = "\n".join(line.lstrip() for line in lines)
        is_unused = get_unused_variables(script2)
        lines = lines[:-1]
        #remove whitespace
        lines = ["".join([j if not j.isspace() else "" for j in i]) for i in lines]
        #get lines that set varable
        variables = set(func.__code__.co_varnames)

        variables = variables-is_unused
        lines = list(filter(lambda x: len(x.split("="))==2, lines))
        lines = list(filter(lambda x: x.split("=")[0] in variables, lines))        
        lines = list(filter(lambda x: not any([x1 in re.split(r"[\*/]",x.split("=")[1]) for x1 in variables]), lines))        
        lines = list(filter(lambda x: not "(" in x.split("=")[1], lines))        
        lines = list(filter(lambda x: check_const(x.split("=")[1]), lines))

        #get the number of segnificant numbers
        värdsifror = [remove_unit(i.split("=")[1]) for i in lines]
        significant = min(värdsifror)
        
        try:
            value_ans = func(*args, **kwargs)
        except Exception as inst:
            if "Float which has no callable" in str(inst):
                print("Exception: In " + func.__name__+ " When using numpy function remember:\n\tconvert argument to type np.float64: \n\tExample: foo = np.arccos(np.float64(bar))")
            else:
                print(inst)
            exit()
        #handle weird exeptions
        try:
            units = unit(value_ans)
        except:
            if type(value_ans) == type(None):
                print("Exception: In " + func.__name__ + " Remember to return a value from your function")
            else:
                print("Exception: return of type: \"" + str(type(value_ans)) + "\" is unexpected")
            exit()
        



        number = value_ans/units
        units = replace_dict(str(units)).replace("**", "^")
        print("_______________________________________________________")
        print("\nBU of function : " + func.__name__ +"\nOutput:")
        if "1" in units:
            print("Note:\n\tWithin \"unit\" observe: \"1\" may be radians (rad)\n")
        print(">>\t" + significant_output(number, significant) + " " +str(units))
        print("Unchanged awnser:\n>>\t" + str(value_ans))
        print("_______________________________________________________")
        return value_ans 
    return wrapper
    
#@Bu
#def u1():
#    x = 1001*volt
#    y = 2223*meter*second
#    return x*y
#
#print(u1())
