from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager  # 确保导入 login_manager
from app.models import User, Problem, AnswerRecord
from app.utils import generate_problem
from datetime import datetime, timezone

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

@bp.route('/student')
@login_required
def student():
    expr, answer = generate_problem()
    problem = Problem(expression=expr, answer=answer)
    db.session.add(problem)
    db.session.commit()
    session['current_problem'] = problem.id
    
    history = AnswerRecord.query.filter_by(user_id=current_user.id)\
                .join(Problem)\
                .order_by(AnswerRecord.timestamp.desc())\
                .limit(5).all()
    
    return render_template('student.html',
                         problem=expr,
                         history=history)

@bp.route('/submit', methods=['POST'])
@login_required
def submit_answer():
    problem = Problem.query.get(session.get('current_problem'))
    try:
        user_answer = float(request.form.get('answer'))
        is_correct = math.isclose(user_answer, problem.answer, abs_tol=0.01)
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
    return redirect(url_for('main.student'))

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
    
    return render_template('teacher.html',
                         students=students,
                         accuracy=round(accuracy, 2),
                         common_errors=common_errors)