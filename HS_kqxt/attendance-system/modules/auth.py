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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
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
    
    # 如果验证成功，更新最后登录时间
    if user:
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user[0],)
        )
        conn.commit()
    
    conn.close()
    
    return user

def login_page():
    """显示登录页面并处理登录逻辑"""
    # 自定义登录页面样式，确保响应式显示
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            width: 100%;
            margin: 50px auto;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        .login-title {
            text-align: center;
            margin-bottom: 2rem;
            color: #1D2129;
        }
        .stButton > button {
            width: 100%;
            background-color: #165DFF;
            color: white;
            padding: 0.6rem;
            border-radius: 8px;
            border: none;
            font-weight: 500;
        }
        .stButton > button:hover {
            background-color: #0E42D2;
        }
        .stTextInput > div > input {
            padding: 0.6rem;
            border-radius: 8px;
            border: 1px solid #E5E6EB;
        }
        .expander-content {
            background-color: #F2F3F5;
            border-radius: 8px;
        }
        @media (max-width: 640px) {
            .login-container {
                margin: 20px;
                padding: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 创建响应式布局容器
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-title">员工考勤管理系统</h1>', unsafe_allow_html=True)
        
        # 创建登录表单
        with st.form("login_form"):
            st.subheader("用户登录")
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submit = st.form_submit_button("登录")
            
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
        with st.expander("默认登录信息", expanded=False):
            st.info("""
            用户名: admin  
            密码: admin123  
            建议登录后修改密码
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

def logout():
    """注销用户"""
    st.session_state.clear()
    st.success("已成功注销")
    st.rerun()

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