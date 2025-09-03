import sqlite3
import os
from datetime import datetime
import streamlit as st

# 数据库文件路径（与auth.py保持一致）
DB_PATH = os.path.join("data", "attendance.db")

def init_employees_table():
    """初始化员工表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建员工表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL, 
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        position TEXT NOT NULL,
        hire_date DATE NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        avatar TEXT DEFAULT 'https://picsum.photos/id/237/40/40'
    )
    ''')
    
    conn.commit()
    conn.close()
    print("员工表初始化完成")

def get_total_count():
    """获取员工总数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_all_employees():
    """获取所有员工列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, employee_id, name, department, position, hire_date, status 
        FROM employees 
        ORDER BY created_at DESC
    """)
    employees = cursor.fetchall()
    
    # 转换为字典列表
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in employees]
    
    conn.close()
    return result

def get_employee_by_id(employee_id):
    """通过员工编号获取员工信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, employee_id, name, department, position, hire_date, status, avatar 
        FROM employees 
        WHERE employee_id = ?
    """, (employee_id,))
    
    employee = cursor.fetchone()
    if not employee:
        conn.close()
        return None
    
    # 转换为字典
    columns = [desc[0] for desc in cursor.description]
    result = dict(zip(columns, employee))
    
    conn.close()
    return result

def add_employee(employee_data):
    """添加新员工"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查员工编号是否已存在
        cursor.execute("SELECT id FROM employees WHERE employee_id = ?", 
                      (employee_data['employee_id'],))
        if cursor.fetchone():
            conn.close()
            return False, "员工编号已存在"
        
        # 插入新员工
        cursor.execute("""
            INSERT INTO employees 
            (employee_id, name, department, position, hire_date, status, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_data['employee_id'],
            employee_data['name'],
            employee_data['department'],
            employee_data['position'],
            employee_data['hire_date'],
            employee_data.get('status', 'active'),
            employee_data.get('avatar', 'https://picsum.photos/id/237/40/40')
        ))
        
        conn.commit()
        conn.close()
        return True, "员工添加成功"
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"添加失败: {str(e)}"

def update_employee(employee_id, update_data):
    """更新员工信息"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查员工是否存在
        cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (employee_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "员工不存在"
        
        # 构建更新语句
        update_fields = []
        values = []
        
        for key, value in update_data.items():
            if key in ['name', 'department', 'position', 'hire_date', 'status', 'avatar']:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            conn.close()
            return True, "没有需要更新的字段"
        
        values.append(employee_id)
        query = f"UPDATE employees SET {', '.join(update_fields)} WHERE employee_id = ?"
        
        cursor.execute(query, tuple(values))
        conn.commit()
        conn.close()
        return True, "员工信息更新成功"
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"更新失败: {str(e)}"

def delete_employee(employee_id):
    """删除员工"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查员工是否存在
        cursor.execute("SELECT id FROM employees WHERE employee_id = ?", (employee_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "员工不存在"
        
        cursor.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        conn.commit()
        conn.close()
        return True, "员工删除成功"
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"删除失败: {str(e)}"

def get_employees_by_department(department):
    """按部门获取员工"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT employee_id, name, position 
        FROM employees 
        WHERE department = ? AND status = 'active'
        ORDER BY name
    """, (department,))
    
    employees = cursor.fetchall()
    conn.close()
    return employees

def search_employees(keyword):
    """搜索员工（支持员工编号、姓名、部门搜索）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT id, employee_id, name, department, position, hire_date, status 
        FROM employees 
        WHERE 
            employee_id LIKE ? OR 
            name LIKE ? OR 
            department LIKE ?
        ORDER BY created_at DESC
    """
    search_term = f"%{keyword}%"
    cursor.execute(query, (search_term, search_term, search_term))
    
    employees = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in employees]
    
    conn.close()
    return result