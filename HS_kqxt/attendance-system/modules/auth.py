import sqlite3
import os
from hashlib import sha256
import streamlit as st

# 数据库文件路径
DB_PATH = os.path.join("data", "attendance.db")

def init_users_table():
    """初始化用户表，创建管理员默认账户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 检查是否存在管理员账户，不存在则创建
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # 默认密码是 'admin123'，已加密
        admin_password = sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', admin_password, 'admin')
        )
        print("已创建默认管理员账户: 用户名 admin, 密码 admin123")
    
    conn.commit()
    conn.close()

def hash_password(password):
    """对密码进行SHA256加密"""
    return sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """验证用户名和密码是否正确"""
    hashed_pw = hash_password(password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed_pw)
    )
    
    user = cursor.fetchone()
    conn.close()
    
    return user

def login_page():
    """显示登录页面并处理登录逻辑"""
    st.title("员工考勤管理系统")
    
    # 创建登录表单
    with st.form("login_form"):
        st.subheader("用户登录")
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        submit = st.form_submit_button("登录", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("请输入用户名和密码")
            else:
                user = verify_credentials(username, password)
                if user:
                    # 登录成功，保存会话状态
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user[0]
                    st.session_state["username"] = user[1]
                    st.session_state["role"] = user[2]
                    
                    st.success(f"登录成功，欢迎回来 {user[1]}!")
                    st.rerun()  # 重新加载页面
                else:
                    st.error("用户名或密码错误")
    
    # 显示默认登录信息提示
    with st.expander("默认登录信息"):
        st.info("""
        用户名: admin  
        密码: admin123  
        建议登录后修改密码
        """)

def logout():
    """注销用户"""
    st.session_state.clear()
    st.success("已成功注销")
    st.experimental_rerun()

def change_password(username, old_password, new_password):
    """修改密码"""
    # 先验证旧密码
    if not verify_credentials(username, old_password):
        return False, "原密码不正确"
    
    # 加密新密码并更新
    hashed_new_pw = hash_password(new_password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET password = ? WHERE username = ?",
        (hashed_new_pw, username)
    )
    
    conn.commit()
    conn.close()
    
    return True, "密码修改成功"
