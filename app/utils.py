import random
import math
from fractions import Fraction

def generate_rational_number():
    """生成有理数，可能是整数、小数或分数"""
    choice = random.choice([1, 2, 3])
    if choice == 1:
        # 生成整数
        return random.randint(-10, 10)
    elif choice == 2:
        # 生成小数
        return round(random.uniform(-10, 10), 2)
    else:
        # 生成分数
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        return Fraction(numerator, denominator)

def generate_problem():
    """生成包含四个有理数的计算题，包含加减乘除和平方运算"""
    # 生成四个有理数
    numbers = [generate_rational_number() for _ in range(4)]
    # 定义运算符列表，包含加减乘除和平方
    operators = ['+', '-', '*', '/', '**2']

    # 随机选择三个运算符
    op1, op2, op3 = random.choices(operators, k=3)

    # 构建表达式
    if op1 == '**2':
        expr = f"({numbers[0]}{op1}) {random.choice(['+', '-', '*', '/'])} ({numbers[1]}) {op2} ({numbers[2]}) {op3} ({numbers[3]})"
    elif op2 == '**2':
        expr = f"({numbers[0]}) {op1} ({numbers[1]}{op2}) {random.choice(['+', '-', '*', '/'])} ({numbers[2]}) {op3} ({numbers[3]})"
    elif op3 == '**2':
        expr = f"({numbers[0]}) {op1} ({numbers[1]}) {op2} ({numbers[2]}{op3}) {random.choice(['+', '-', '*', '/'])} ({numbers[3]})"
    else:
        expr = f"({numbers[0]}) {op1} ({numbers[1]}) {op2} ({numbers[2]}) {op3} ({numbers[3]})"

    # 将分数转换为字符串形式
    def convert_fraction(num):
        if isinstance(num, Fraction):
            return f"{num.numerator}/{num.denominator}"
        return str(num)

    # 处理表达式中的数字和运算符
    new_expr = []
    tokens = expr.split()
    for token in tokens:
        if token.replace('.', '', 1).isdigit() or ('/' in token and token.replace('/', '', 1).replace('-', '', 1).isdigit()):
            num = eval(token) if '/' in token else float(token)
            new_expr.append(convert_fraction(num))
        elif token == '**2':
            new_expr.append('<sup>2</sup>')
        elif token == '*':
            new_expr.append('×')
        else:
            new_expr.append(token)
    expr = " ".join(new_expr)

    try:
        # 计算答案并保留两位小数
        # 先将 <sup>2</sup> 替换回 **2 再计算
        safe_expr = expr.replace('<sup>2</sup>', '**2')
        # 使用 eval 计算表达式
        answer = round(eval(safe_expr), 2)
    except ZeroDivisionError:
        # 如果出现除零错误，重新生成题目
        return generate_problem()
    except SyntaxError:
        # 如果出现语法错误，重新生成题目
        return generate_problem()
    except TypeError:
        # 如果出现类型错误（如将整数当作函数调用），重新生成题目
        return generate_problem()
    return expr, answer