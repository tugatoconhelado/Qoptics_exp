import dataclasses
from typing import List, Tuple, Union
from functools import wraps

@dataclasses.dataclass
class Test:
    a: tuple
    b: tuple
    c: tuple


def receive_dataclass(function) -> None:
    
    @wraps(function)
    def accept_dataclass(param_data, *args):
        if not args and dataclasses.is_dataclass(param_data):
            # If 1 argument is given, use the dataclass as a tuple
            return function(*dataclasses.astuple(param_data))
        return function(param_data, *args)
    return accept_dataclass

@receive_dataclass
def my_function(a, b, c):

    print('-' * 9)
    print(a)
    print(b)
    print(c)
    print('-' * 9)

if __name__ == '__main__':
    test = Test((1, 2, 3), (4, 5, 6), (7, 8, 9))
    test2 = [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
    print(dataclasses.astuple(test))
    my_function((1, 2, 3), (4, 5, 6), (7, 8, 9))
    my_function(test)  # Example usage with 3 arguments
