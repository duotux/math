# 创建 create_admin.py 文件
from app import create_app
from app.models import User, db

app = create_app()

with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='teacher')
        admin.set_password('admin123')
        db.session.add(admin)
        
        student = User(username='stu1', role='student', grade='7')
        student.set_password('stu123')
        db.session.add(student)
        
        db.session.commit()
        print("初始用户创建成功！")