# coding:utf-8


from geek_house import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# 创建flask的应用对象
app = create_app("develop")

# 第一步：python3 bootstrap.py db init  --->多出来一个migrations文件
# 第二步：python3 bootstrap.py db migrate -m 'init tables'
# 第二步：python3 bootstrap.py db upgrade

manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    manager.run()
