from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager  # 确保导入 login_manager
from app.models import User, Problem, AnswerRecord
from app.utils import generate_problem
from datetime import datetime, timezone
from fractions import Fraction

bp = Blueprint('main', __name__)

# 必须添加的用户加载器
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # 使用新版查询方式

@bp.route('/')
def index():
    if current_user.is_authenticated:
        # 修改重定向逻辑，避免嵌套 redirect
        return redirect(url_for('main.student') if current_user.role == 'student' else url_for('main.teacher'))
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_active = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for('main.index'))
        flash('无效的用户名或密码', 'danger')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# 在 app/routes.py 中
import logging

@bp.route('/student')
@login_required
def student():
    expr, answer = generate_problem()  # 调用更新后的函数生成题目
    logging.info(f"Generated expression: {expr}")  # 添加日志输出
    problem = Problem(expression=expr, answer=answer)
    db.session.add(problem)
    db.session.commit()
    session['current_problem'] = problem.id

    history = AnswerRecord.query.filter_by(user_id=current_user.id) \
        .join(Problem) \
        .order_by(AnswerRecord.timestamp.desc()) \
        .limit(5).all()

    return render_template('student.html',
                           problem=expr,
                           history=history)






@bp.route('/submit', methods=['POST'])
@login_required
def submit_answer():
    problem = Problem.query.get(session.get('current_problem'))
    try:
        user_answer_input = request.form.get('answer')
        # 尝试将输入解析为分数或浮点数
        try:
            user_answer = float(Fraction(user_answer_input))
        except ValueError:
            user_answer = float(user_answer_input)
        # 直接比较四舍五入后的答案
        is_correct = round(user_answer, 2) == round(problem.answer, 2)
    except:
        is_correct = False
    
    record = AnswerRecord(
        user_id=current_user.id,
        problem_id=problem.id,
        user_answer=user_answer,
        is_correct=is_correct
    )
    db.session.add(record)
    current_user.last_active = datetime.now(timezone.utc)
    db.session.commit()
    
    # 生成新的题目
    expr, answer = generate_problem()
    new_problem = Problem(expression=expr, answer=answer)
    db.session.add(new_problem)
    db.session.commit()
    session['current_problem'] = new_problem.id

    history = AnswerRecord.query.filter_by(user_id=current_user.id) \
        .join(Problem) \
        .order_by(AnswerRecord.timestamp.desc()) \
        .limit(5).all()

    return render_template('student.html',
                           problem=expr,
                           history=history,
                           last_problem_answer=problem.answer,
                           last_answer_correct=is_correct)

@bp.route('/teacher')
@login_required
def teacher():
    if current_user.role != 'teacher':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))
    
    students = User.query.filter_by(role='student').all()
    accuracy = db.session.query(
        db.func.avg(db.cast(AnswerRecord.is_correct, db.Float)) * 100
    ).scalar() or 0.0
    
    common_errors = db.session.query(
        Problem.expression,
        db.func.count(AnswerRecord.id)
    ).join(AnswerRecord)\
     .filter(AnswerRecord.is_correct == False)\
     .group_by(Problem.expression)\
     .order_by(db.func.count(AnswerRecord.id).desc())\
     .limit(3).all()
    
    # 查询每个学生的答题总题数和正确率
    student_stats = []
    for student in students:
        total_answers = AnswerRecord.query.filter_by(user_id=student.id).count()
        correct_answers = AnswerRecord.query.filter_by(user_id=student.id, is_correct=True).count()
        if total_answers > 0:
            student_accuracy = (correct_answers / total_answers) * 100
        else:
            student_accuracy = 0
        student_stats.append({
            'student': student,
            'total_answers': total_answers,
            'accuracy': student_accuracy
        })
    
    return render_template('teacher.html',
                         students=students,
                         accuracy=round(accuracy, 2),
                         common_errors=common_errors,
                         student_stats=student_stats)

@bp.route('/teacher/create_student', methods=['GET', 'POST'])
@login_required
def create_student():
    if current_user.role != 'teacher':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not User.query.filter_by(username=username).first():
            student = User(username=username, role='student')
            student.set_password(password)
            db.session.add(student)
            db.session.commit()
            flash('学生账号创建成功', 'success')
            return redirect(url_for('main.teacher'))
        else:
            flash('用户名已存在', 'danger')
    
    return render_template('create_student.html')

@bp.route('/teacher/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    if current_user.role != 'teacher':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))
    
    student = User.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
        flash('学生账号删除成功', 'success')
    else:
        flash('未找到该学生账号', 'danger')
    
    return redirect(url_for('main.teacher'))

@bp.route('/teacher/change_password/<int:student_id>', methods=['GET', 'POST'])
@login_required
def change_password(student_id):
    if current_user.role != 'teacher':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))
    
    student = User.query.get(student_id)
    if not student:
        flash('未找到该学生账号', 'danger')
        return redirect(url_for('main.teacher'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        student.set_password(new_password)
        db.session.commit()
        flash('学生账号密码修改成功', 'success')
        return redirect(url_for('main.teacher'))
    
    return render_template('change_password.html', student=student)

@bp.route('/teacher/clear_records/<int:student_id>')
@login_required
def clear_records(student_id):
    if current_user.role != 'teacher':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))

    student = User.query.get(student_id)
    if student:
        # 删除该学生的所有答题记录
        AnswerRecord.query.filter_by(user_id=student.id).delete()
        db.session.commit()
        flash('学生答题记录清除成功', 'success')
    else:
        flash('未找到该学生账号', 'danger')

    return redirect(url_for('main.teacher'))


@bp.route('/student/change_password', methods=['GET', 'POST'])
@login_required
def student_change_password():
    if current_user.role != 'student':
        flash('权限不足', 'danger')
        return redirect(url_for('main.student'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('当前密码不正确', 'danger')
        elif new_password != confirm_password:
            flash('新密码和确认密码不一致', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('main.student'))
    
    return render_template('student_change_password.html')