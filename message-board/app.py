# -*- coding: utf-8 -*-
import os
import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# 分别从 flask_wtf 和 wtforms 导入需要的模块
# Form 作为所有我们定义的 Form 的基类
from flask_wtf import FlaskForm as Form
from wtforms.fields import StringField
from wtforms.validators import Required, Length
from werkzeug.datastructures import MultiDict

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(dict(
    # 主要是为了关闭一些不必要的提示
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    # 使用 sqlite 数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'data.sqlite')
))
db = SQLAlchemy(app)


class Message(db.Model):
     # 在数据库中创建表时的表名称
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    # index 创建索引，nullable 表示不能为空
    name = db.Column(db.String(64), index=True, nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    # 设置了 default 值，所以前端不需要传创建时间过来
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {'name': self.name,
                'text': self.text,
                'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')}

class MessageForm(Form):
    """
    根据 Message Model 定义相应的 Form
    """
    name = StringField(validators=[Required(), Length(1, 64)])
    text = StringField(validators=[Required(), Length(1, 1000)])

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """获取所有 message, 按创建时间倒序排列"""
    messages = Message.query.order_by('created_at desc').all()
    return jsonify([message.to_dict() for message in messages])


@app.route('/api/messages', methods=['POST'])
def create_message():
    # 由于 wtforms 实际上是用来验证表单数据的，当我们想用它来验证 Ajax 传的 JSON
    # 数据时，需要我们自己去初始化这个 form 
    formdata = MultiDict(request.get_json())
    form = MessageForm(formdata=formdata, obj=None, csrf=False)
    if not form.validate():
          # 数据验证失败时直接返回
          # form.error 是一个字典，包含 form 字段的所有错误信息，类似：
          # {'name': ['error1', ...], 'text': ['error1', ...]}
          # 需要注意的是字段的错误信息都是一个列表
          # 422 表示 请求是正确的，但服务器处理不了请求的数据
        return jsonify(ok=False, errors=form.errors), 422
    # 请求数据无误创建 Message
    msg = Message(name=formdata['name'], text=formdata['text'])
    db.session.add(msg)
    db.session.commit()
    # 201 表示资源创建成功
    return jsonify(ok=True), 201


if __name__ == '__main__':
    app.run(debug=True)