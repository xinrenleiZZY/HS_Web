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

import os
import sqlite3
from datetime import datetime, time, timedelta

# 数据库路径
DB_PATH = os.path.join("data", "attendance.db")

def init_shift_tables():
    """初始化班次和打卡规则表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建班次表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,  -- 班次名称：早班、中班、夜班
        department TEXT NOT NULL,   -- 所属部门
        system_rest_time TIME NOT NULL,  -- 系统休息时间
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建详细打卡规则表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shift_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        rule_type TEXT NOT NULL,  -- 上班、午休、下班等
        start_time TIME,
        end_time TIME,
        processing_logic TEXT NOT NULL,  -- 处理逻辑标识
        FOREIGN KEY (shift_id) REFERENCES shifts(id)
    )
    ''')
    
    # 创建生产部早班记录特殊表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS production_morning_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        check_date DATE NOT NULL,
        original_check_times TEXT NOT NULL,  -- 原始打卡时间，分号分隔
        work_start_time TIME,  -- 计算后的上班时间
        work_end_time TIME,    -- 计算后的下班时间
        noon_leave_time TIME,  -- 午休下班时间
        noon_start_time TIME,  -- 午休上班时间
        day_overtime_hours REAL DEFAULT 0,  -- 白天加班时长
        night_overtime_hours REAL DEFAULT 0,  -- 晚上加班时长
        status TEXT,  -- 出勤状态
        status_note TEXT,  -- 状态说明
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("班次相关表初始化完成")

def process_morning_shift(employee_id, check_date, check_times_str):
    """
    处理生产部早班打卡记录
    employee_id: 员工ID
    check_date: 打卡日期
    check_times_str: 打卡时间字符串，分号分隔
    """
    # 系统休息时间：次日05:00
    system_rest_time = time(5, 0)
    
    # 解析打卡时间
    check_times = []
    for time_str in check_times_str.split(';'):
        try:
            # 假设时间格式为HH:MM
            check_time = datetime.strptime(time_str.strip(), "%H:%M").time()
            check_times.append(check_time)
        except ValueError:
            continue  # 跳过无效时间格式
    
    # 排序打卡时间
    check_times.sort()
    
    result = {
        'employee_id': employee_id,
        'check_date': check_date,
        'original_check_times': check_times_str,
        'work_start_time': None,
        'work_end_time': None,
        'noon_leave_time': None,
        'noon_start_time': None,
        'day_overtime_hours': 0,
        'night_overtime_hours': 0,
        'status': '正常',
        'status_note': ''
    }
    
    # 处理上班打卡 (早上8:00)
    morning_checks = [t for t in check_times if is_time_between(t, time(0,0), time(12,0))]
    work_start_processed = False
    
    if morning_checks:
        first_morning = morning_checks[0]
        
        # 系统休息时间到8:00属于上班卡（记为8:00上班卡）
        if is_time_between(first_morning, time(0,0), time(8,0)) or first_morning == time(8,0):
            result['work_start_time'] = time(8, 0)
            work_start_processed = True
        
        # 8:00-12:00属于迟到
        elif is_time_between(first_morning, time(8,0), time(12,0)):
            result['work_start_time'] = first_morning
            late_minutes = (first_morning.hour - 8) * 60 + first_morning.minute
            result['status'] = '迟到'
            result['status_note'] = f"迟到{late_minutes}分钟"
            work_start_processed = True
    
    # 8:00-12:00未打卡属于缺勤
    if not work_start_processed:
        result['status'] = '缺勤'
        result['status_note'] = '未在规定时间内打上班卡'
        # 保存结果到数据库
        save_morning_shift_result(result)
        return result
    
    # 处理中午12:00-13:30打卡
    noon_checks = [t for t in check_times if is_time_between(t, time(12,0), time(13,30))]
    
    if len(noon_checks) == 1:
        # 打卡次数=1，记为12:00下班
        result['noon_leave_time'] = time(12, 0)
    elif len(noon_checks) >= 2:
        # 第一次打卡为12点下班卡
        result['noon_leave_time'] = time(12, 0)
        
        # 第二次打卡为上班卡
        second_check = noon_checks[1]
        if is_time_between(second_check, time(12,0), time(12,30)):
            # 记为12:30上班卡，白天加班时长+1
            result['noon_start_time'] = time(12, 30)
            result['day_overtime_hours'] = 1
        else:
            # 记为13:30上班卡
            result['noon_start_time'] = time(13, 30)
    
    # 处理下午17:30下班打卡
    evening_checks = [t for t in check_times if is_time_between(t, time(13,30), system_rest_time)]
    evening_checks += [t for t in check_times if is_time_between(t, time(0,0), system_rest_time)]  # 跨天的情况
    
    if evening_checks:
        # 取最后一次打卡作为下班时间
        last_evening = evening_checks[-1]
        
        # 打卡时间取整点
        rounded_time = round_time_to_hour(last_evening)
        result['work_end_time'] = rounded_time
        
        # 计算晚上加班时长
        work_end_std = time(17, 30)
        if last_evening > work_end_std:
            # 计算分钟差
            overtime_minutes = (rounded_time.hour - work_end_std.hour) * 60
            overtime_minutes += (rounded_time.minute - work_end_std.minute)
            result['night_overtime_hours'] = round(overtime_minutes / 60, 1)
    else:
        # 未打卡记为缺卡
        result['status'] = '缺卡'
        result['status_note'] += '; 未在规定时间内打下班卡' if result['status_note'] else '未在规定时间内打下班卡'
    
    # 保存结果到数据库
    save_morning_shift_result(result)
    return result

def save_morning_shift_result(result):
    """保存早班处理结果到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO production_morning_records 
    (employee_id, check_date, original_check_times, work_start_time, work_end_time,
     noon_leave_time, noon_start_time, day_overtime_hours, night_overtime_hours,
     status, status_note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result['employee_id'],
        result['check_date'],
        result['original_check_times'],
        result['work_start_time'].strftime("%H:%M") if result['work_start_time'] else None,
        result['work_end_time'].strftime("%H:%M") if result['work_end_time'] else None,
        result['noon_leave_time'].strftime("%H:%M") if result['noon_leave_time'] else None,
        result['noon_start_time'].strftime("%H:%M") if result['noon_start_time'] else None,
        result['day_overtime_hours'],
        result['night_overtime_hours'],
        result['status'],
        result['status_note']
    ))
    
    conn.commit()
    conn.close()

def is_time_between(check_time, start_time, end_time):
    """检查时间是否在指定区间内"""
    if start_time <= end_time:
        return start_time <= check_time <= end_time
    else:
        # 跨天的情况，如23:00到次日05:00
        return check_time >= start_time or check_time <= end_time

def round_time_to_hour(check_time):
    """将时间取整点，如20:31记为20:30，20:11记为20:00"""
    # 30分钟以内的取当前小时的00分，30分钟及以上的取当前小时的30分
    if check_time.minute < 30:
        return time(check_time.hour, 0)
    else:
        return time(check_time.hour, 30)
    
def process_logistics_department(employee_id, check_date, check_times_str):
    """
    处理后勤部打卡记录
    一天只要有一次打卡就是出勤，没有打卡就是休息
    """
    # 检查是否有打卡记录
    has_check_in = len(check_times_str.strip()) > 0 and check_times_str != ";"
    
    status = "出勤" if has_check_in else "休息"
    
    # 保存结果
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 确保有后勤部打卡记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logistics_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        check_date DATE NOT NULL,
        has_check_in INTEGER NOT NULL,  -- 1表示有打卡，0表示无打卡
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    ''')
    
    cursor.execute('''
    INSERT INTO logistics_records 
    (employee_id, check_date, has_check_in, status)
    VALUES (?, ?, ?, ?)
    ''', (
        employee_id,
        check_date,
        1 if has_check_in else 0,
        status
    ))
    
    conn.commit()
    conn.close()
    
    return {
        'employee_id': employee_id,
        'check_date': check_date,
        'status': status,
        'has_check_in': has_check_in
    }