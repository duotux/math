import random
import math

def generate_problem():
    """生成有理数计算题"""
    operators = ['+', '-', '*', '/']
    a = random.randint(-10, 10)
    b = random.randint(1, 10)
    op = random.choice(operators)
    c = random.randint(-5, 5)
    d = random.randint(1, 5)
    
    expr = f"({a}/{b}) {op} ({c}/{d})"
    try:
        answer = round(eval(expr), 2)
    except ZeroDivisionError:
        return generate_problem()
    return expr, answer