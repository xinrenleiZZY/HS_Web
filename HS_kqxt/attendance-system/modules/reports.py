import sqlite3
import os
from datetime import datetime

# 数据库文件路径（与其他模块保持一致）
DB_PATH = os.path.join("data", "attendance.db")

def init_attendance_records():
    """初始化考勤记录表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建考勤记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        check_in_time TIMESTAMP,
        check_out_time TIMESTAMP,
        work_hours REAL,
        overtime_hours REAL,
        status TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("考勤记录表初始化完成")

def get_today_attendance():
    """获取今日出勤人数"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT employee_id) 
        FROM attendance_records 
        WHERE DATE(check_in_time) = ?
    """, (today,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_late_count():
    """获取今日迟到人数"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取考勤规则中的迟到阈值和上班时间
    cursor.execute("SELECT late_threshold, work_start_time FROM attendance_rules ORDER BY updated_at DESC LIMIT 1")
    rule = cursor.fetchone()
    late_threshold = rule[0] if rule else 15  # 默认15分钟
    work_start_time = rule[1] if rule else '09:00'  # 默认上班时间
    
    # 计算迟到时间阈值（上班时间 + 迟到阈值）
    today_str = today
    work_start_datetime = datetime.strptime(f"{today_str} {work_start_time}", "%Y-%m-%d %H:%M")
    late_cutoff = work_start_datetime.timestamp() + (late_threshold * 60)
    
    # 查询今日迟到的员工
    cursor.execute("""
        SELECT COUNT(DISTINCT employee_id) 
        FROM attendance_records 
        WHERE DATE(check_in_time) = ?
        AND strftime('%s', check_in_time) > ?
    """, (today, late_cutoff))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_overtime_hours():
    """获取今日总加班小时数"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询今日所有记录的加班时长并求和
    cursor.execute("""
        SELECT SUM(overtime_hours) 
        FROM attendance_records 
        WHERE DATE(check_out_time) = ?
        AND overtime_hours IS NOT NULL
    """, (today,))
    
    total_overtime = cursor.fetchone()[0] or 0.0
    conn.close()
    return round(total_overtime, 2)

def get_recent_records(limit=10):
    """获取最近的打卡记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ar.employee_id, e.name, e.department, 
               ar.check_in_time, ar.check_out_time, 
               ar.status, e.avatar
        FROM attendance_records ar
        JOIN employees e ON ar.employee_id = e.employee_id
        ORDER BY ar.created_at DESC LIMIT ?
    """, (limit,))
    records = cursor.fetchall()
    conn.close()
    
    return [
        {
            'avatar': r[6],
            'name': r[1],
            'department': r[2],
            'type': '上班打卡' if r[3] and not r[4] else '下班打卡' if r[4] else '未知',
            'time': r[3].split(' ')[1] if r[3] else r[4].split(' ')[1] if r[4] else '',
            'status': r[5] or '未知',
            'status_class': 'bg-success/10 text-success' if r[5] == '正常' else 
                           'bg-danger/10 text-danger' if r[5] in ['迟到', '早退'] else
                           'bg-warning/10 text-warning'
        } for r in records
    ]