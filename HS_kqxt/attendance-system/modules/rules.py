import sqlite3
import os
from datetime import datetime, time

# 数据库文件路径（与其他模块保持一致）
DB_PATH = os.path.join("data", "attendance.db")

def init_attendance_rules():
    """初始化考勤规则表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建考勤规则表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_start_time TIME NOT NULL DEFAULT '09:00',  -- 上班时间
        work_end_time TIME NOT NULL DEFAULT '18:00',    -- 下班时间
        late_threshold INTEGER NOT NULL DEFAULT 15,     -- 迟到阈值(分钟)
        early_leave_threshold INTEGER NOT NULL DEFAULT 15,  -- 早退阈值(分钟)
        lunch_start_time TIME NOT NULL DEFAULT '12:00', -- 午休开始时间
        lunch_end_time TIME NOT NULL DEFAULT '13:00',   -- 午休结束时间
        overtime_start_time TIME NOT NULL DEFAULT '19:00',  -- 加班开始时间
        daily_standard_hours REAL NOT NULL DEFAULT 8.0,  -- 每日标准工时(小时)
        work_days TEXT NOT NULL DEFAULT '1,2,3,4,5',    -- 工作日(1-周一, 7-周日)
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 最后更新时间
    )
    ''')
    
    # 检查是否存在默认规则，不存在则创建
    cursor.execute("SELECT id FROM attendance_rules LIMIT 1")
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO attendance_rules DEFAULT VALUES
        ''')
        print("已创建默认考勤规则")
    
    conn.commit()
    conn.close()
    print("考勤规则表初始化完成")

def get_attendance_rules():
    """获取当前考勤规则"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM attendance_rules ORDER BY updated_at DESC LIMIT 1
    ''')
    
    rule = cursor.fetchone()
    if not rule:
        conn.close()
        return None
    
    # 转换为字典
    columns = [desc[0] for desc in cursor.description]
    result = dict(zip(columns, rule))
    
    conn.close()
    return result

def update_attendance_rules(rule_data):
    """更新考勤规则"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 构建更新语句
        update_fields = []
        values = []
        
        valid_fields = [
            'work_start_time', 'work_end_time', 'late_threshold',
            'early_leave_threshold', 'lunch_start_time', 'lunch_end_time',
            'overtime_start_time', 'daily_standard_hours', 'work_days'
        ]
        
        for key, value in rule_data.items():
            if key in valid_fields:
                update_fields.append(f"{key} = ?")
                values.append(value)
        
        if not update_fields:
            conn.close()
            return True, "没有需要更新的字段"
        
        # 获取最新的规则ID（假设我们只维护一条规则记录）
        cursor.execute("SELECT id FROM attendance_rules ORDER BY updated_at DESC LIMIT 1")
        rule_id = cursor.fetchone()[0]
        
        values.append(rule_id)
        query = f"UPDATE attendance_rules SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        cursor.execute(query, tuple(values))
        conn.commit()
        conn.close()
        return True, "考勤规则更新成功"
    
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"更新失败: {str(e)}"

def is_work_day(weekday):
    """
    检查指定星期是否为工作日
    weekday: 0-6（0是周一，6是周日），需要转换为1-7格式
    """
    # 转换为1-7格式（1=周一，7=周日）
    converted_weekday = weekday + 1
    
    rules = get_attendance_rules()
    if not rules:
        return False
        
    work_days = rules.get('work_days', '1,2,3,4,5')
    return str(converted_weekday) in work_days.split(',')

def calculate_work_hours(check_in, check_out, lunch_start, lunch_end):
    """
    计算实际工作时长（扣除午休时间）
    check_in: 上班打卡时间 (datetime)
    check_out: 下班打卡时间 (datetime)
    lunch_start: 午休开始时间 (time)
    lunch_end: 午休结束时间 (time)
    """
    if not check_in or not check_out:
        return 0.0
        
    # 转换为同一天的datetime进行比较
    lunch_start_dt = datetime.combine(check_in.date(), lunch_start)
    lunch_end_dt = datetime.combine(check_in.date(), lunch_end)
    
    # 计算总时长（分钟）
    total_minutes = (check_out - check_in).total_seconds() / 60
    
    # 计算重叠的午休时间
    overlap_start = max(check_in, lunch_start_dt)
    overlap_end = min(check_out, lunch_end_dt)
    lunch_overlap = max(0, (overlap_end - overlap_start).total_seconds() / 60)
    
    # 实际工作时长（小时）
    work_hours = (total_minutes - lunch_overlap) / 60
    return round(work_hours, 2)

def calculate_overtime(check_out, work_end, lunch_end, overtime_start):
    """
    计算加班时长
    check_out: 下班打卡时间 (datetime)
    work_end: 规定下班时间 (time)
    lunch_end: 午休结束时间 (time)
    overtime_start: 规定加班开始时间 (time)
    """
    if not check_out:
        return 0.0
        
    # 转换为同一天的datetime
    work_end_dt = datetime.combine(check_out.date(), work_end)
    lunch_end_dt = datetime.combine(check_out.date(), lunch_end)
    overtime_start_dt = datetime.combine(check_out.date(), overtime_start)
    
    # 确定计算加班的起始时间（取下班时间和午休结束时间的较晚者）
    base_time = max(work_end_dt, lunch_end_dt)
    
    if check_out <= base_time:
        return 0.0
        
    # 确定加班计算的实际开始时间（如果晚于规定加班开始时间，则从规定时间开始算）
    overtime_calc_start = max(base_time, overtime_start_dt)
    
    if check_out <= overtime_calc_start:
        return 0.0
        
    # 计算加班时长（小时）
    overtime_hours = (check_out - overtime_calc_start).total_seconds() / 3600
    return round(overtime_hours, 2)

def check_attendance_status(check_in, check_out, rules):
    """
    检查考勤状态（正常/迟到/早退）
    check_in: 上班打卡时间 (datetime)
    check_out: 下班打卡时间 (datetime)
    rules: 考勤规则字典
    """
    status = {
        'check_in': '正常',
        'check_out': '正常',
        'is_late': False,
        'is_early_leave': False
    }
    
    if not rules:
        return status
        
    # 检查上班打卡状态
    if check_in:
        work_start = datetime.combine(check_in.date(), 
                                    datetime.strptime(rules['work_start_time'], '%H:%M').time())
        late_threshold = rules['late_threshold']
        
        # 计算迟到分钟数
        if check_in > work_start:
            late_minutes = (check_in - work_start).total_seconds() / 60
            if late_minutes > late_threshold:
                status['check_in'] = f"迟到 {int(late_minutes)}分钟"
                status['is_late'] = True
    
    # 检查下班打卡状态
    if check_out:
        work_end = datetime.combine(check_out.date(), 
                                   datetime.strptime(rules['work_end_time'], '%H:%M').time())
        early_threshold = rules['early_leave_threshold']
        
        # 计算早退分钟数
        if check_out < work_end:
            early_minutes = (work_end - check_out).total_seconds() / 60
            if early_minutes > early_threshold:
                status['check_out'] = f"早退 {int(early_minutes)}分钟"
                status['is_early_leave'] = True
    
    return status