// frontend/js/charts.js
function initDepartmentChart() {
  const ctx = document.getElementById('department-chart');
  if (ctx) {
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['技术部', '市场部', '人事部'],
        datasets: [{
          data: [30, 20, 10],
          backgroundColor: ['#165DFF', '#36CFC9', '#52C41A']
        }]
      }
    });
  }
}

function initWorkingHoursChart() {
  const ctx = document.getElementById('working-hours-chart');
  if (ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['周一', '周二', '周三', '周四', '周五'],
        datasets: [{
          label: '工时',
          data: [8, 7.5, 8.5, 9, 7],
          backgroundColor: '#165DFF'
        }]
      }
    });
  }
}