import streamlit as st
from streamlit.components.v1 import html
import os
import json
from modules import auth, employees, rules, reports

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

# 初始化数据库表
def init_all_tables():
    """初始化所有数据库表结构"""
    auth.init_users_table()
    employees.init_employees_table()
    rules.init_attendance_rules()
    reports.init_attendance_records()

# 读取前端HTML文件
def load_frontend_html():
    """加载前端HTML模板文件"""
    try:
        with open(os.path.join("frontend", "index.html"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error("前端模板文件未找到，请确保frontend/index.html存在")
        return "<h1>前端资源加载失败</h1>"

# 准备后端数据
def get_backend_data():
    """获取需要传递给前端的后端数据"""
    attendance_rules = rules.get_attendance_rules()
    # 调试：打印获取到的考勤规则
    print("考勤规则数据:", attendance_rules)
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
    # 设置页面配置
    st.set_page_config(
        layout="wide",  # 宽屏布局
        initial_sidebar_state="collapsed",  # 折叠侧边栏
        menu_items={"Get help": None, "Report a bug": None, "About": None}
    )
    # 初始化数据库
    init_all_tables()
    
    # 检查登录状态
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        # 显示登录页面
        auth.login_page()
    else:
        # 获取后端数据
        backend_data = get_backend_data()
        # 将后端数据转换为JavaScript变量
        data_script = f"window.backendData = {json.dumps(backend_data)};"
        
        # 加载并修改HTML内容
        html_content = load_frontend_html()
        # 将数据脚本插入到HTML头部
        html_content = html_content.replace("</head>", f"<script>{data_script}</script></head>")
        
        # 添加前后端交互脚本
        interaction_script = """
        <script>
            const rules = window.backendData.attendance_rules;
            if (rules) {
                document.querySelector('input[value="09:00"]').value = rules.work_start_time;
                document.querySelector('input[value="18:00"]').value = rules.work_end_time;
                document.querySelector('input[value="15"][min="0"][max="60"]').value = rules.late_threshold;
                document.querySelector('input[value="12:00"]').value = rules.lunch_start_time;
            }
            // 填充统计数据
            if (window.backendData) {
                // 更新用户信息
                document.querySelector('.font-medium.text-sm').textContent = window.backendData.current_user;
                
                // 更新统计卡片
                const stats = window.backendData.stats;
                document.querySelector('.stats-total-employees').textContent = stats.total_employees;
                document.querySelector('.stats-today-attendance').textContent = stats.today_attendance;
                document.querySelector('.stats-late-count').textContent = stats.late_count;
                document.querySelector('.stats-overtime-hours').textContent = stats.overtime_hours + 'h';
                // 更新最近打卡记录
                updateRecentRecords(window.backendData.recent_records);
            }
            
            // 更新打卡记录表格
            function updateRecentRecords(records) {
                const tableBody = document.querySelector('#recent-records-table tbody');
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
        
        # 将交互脚本插入到HTML底部
        html_content = html_content.replace("</body>", f"{interaction_script}</body>")
        
        # 自定义Streamlit样式，移除默认边距和限制
        st.markdown("""
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                .reportview-container .main .block-container,
                .reportview-container .main 
                #app-container ,
                main.flex-1,
                .horizontal-container {
                    max-width: 100% !important;
                    width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .reportview-container {
                    padding: 0 !important;
                    margin: 0 !important;
                }
                html, body {
                    overflow: auto !important;
                    width: 100% !important;
                    height: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                #app-container {
                    display: flex !important;
                    height: 100vh !important;
                    overflow: hidden !important;
                }
                #sidebar {
                    margin: 0 !important;
                    padding: 0 !important;
                    flex-shrink: 0 !important;
                }
                #app-container main.flex-1 {
                    margin-left: 0 !important;
                    padding-left: 0 !important;
                    overflow-y: auto !important;
                    flex: 1 1 auto !important;
                }
                iframe {
                    width: 100% !important;
                    height: 100vh !important;
                    overflow: hidden !important; 
                    border: none !important;
                }
                #MainMenu, .stDeployButton, footer {
                    display: none !important;
                }
                #page-content {
                    height: 100% !important;
                    overflow-y: auto !important;
                }
            </style>
        """, unsafe_allow_html=True)
        # 渲染完整页面
        html(html_content, height=0, scrolling=True)

if __name__ == "__main__":
    main()