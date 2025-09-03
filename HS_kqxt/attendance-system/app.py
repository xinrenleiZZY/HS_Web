import streamlit as st
from streamlit.components.v1 import html
import os
import json
from modules import auth, employees, rules, reports

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

# 初始化数据库表
def init_all_tables():
    auth.init_users_table()
    employees.init_employees_table()
    rules.init_attendance_rules()
    reports.init_attendance_records()

# 读取前端HTML文件
def load_frontend_html():
    with open(os.path.join("frontend", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# 准备后端数据
def get_backend_data():
    return {
        "current_user": st.session_state.get("username", "管理员"),
        "user_role": st.session_state.get("role", "admin"),
        "stats": {
            "total_employees": employees.get_total_count(),
            "today_attendance": reports.get_today_attendance(),
            "late_count": reports.get_late_count(),
            "overtime_hours": reports.get_overtime_hours()
        },
        "attendance_rules": rules.get_attendance_rules(),
        "recent_records": reports.get_recent_records()
    }

# 主应用
def main():
    # 初始化数据库
    init_all_tables()
    
    # 检查登录状态
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        auth.login_page()
    else:
        # 获取后端数据
        backend_data = get_backend_data()
        data_script = f"window.backendData = {json.dumps(backend_data)};"
        
        # 加载并修改HTML内容
        html_content = load_frontend_html()
        html_content = html_content.replace("</head>", f"<script>{data_script}</script></head>")
        
        # 添加前后端交互脚本
        interaction_script = """
        <script>
            // 填充统计数据
            if (window.backendData) {
                // 更新用户信息
                document.querySelector('.font-medium.text-sm').textContent = window.backendData.current_user;
                
                // 更新统计卡片
                const stats = window.backendData.stats;
                document.querySelectorAll('.card h3')[0].textContent = stats.total_employees;
                document.querySelectorAll('.card h3')[1].textContent = stats.today_attendance;
                document.querySelectorAll('.card h3')[2].textContent = stats.late_count;
                document.querySelectorAll('.card h3')[3].textContent = stats.overtime_hours + 'h';
                
                // 更新最近打卡记录
                updateRecentRecords(window.backendData.recent_records);
            }
            
            // 更新打卡记录表格
            function updateRecentRecords(records) {
                const tableBody = document.querySelector('#dashboard-page table tbody');
                if (!tableBody) return;
                
                tableBody.innerHTML = '';
                records.forEach(record => {
                    const row = document.createElement('tr');
                    row.className = 'hover:bg-light-1/50 transition-colors';
                    row.innerHTML = `
                        <td class="px-6 py-4">
                            <div class="flex items-center gap-3">
                                <img src="${record.avatar}" alt="员工头像" class="w-8 h-8 rounded-full">
                                <span>${record.name}</span>
                            </div>
                        </td>
                        <td class="px-6 py-4">${record.department}</td>
                        <td class="px-6 py-4">${record.type}</td>
                        <td class="px-6 py-4">${record.time}</td>
                        <td class="px-6 py-4">
                            <span class="px-2 py-1 ${record.status_class} text-xs rounded-full">${record.status}</span>
                        </td>
                        <td class="px-6 py-4">
                            <button class="text-primary hover:text-primary/80">详情</button>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        </script>
        """
        
        html_content = html_content.replace("</body>", f"{interaction_script}</body>")
        
        # 渲染页面
        html(html_content, height="100vh", scrolling=True)

if __name__ == "__main__":
    main()
