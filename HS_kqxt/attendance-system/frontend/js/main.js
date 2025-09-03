// frontend/js/main.js
document.addEventListener('DOMContentLoaded', () => {
  // 页面切换逻辑
  const navLinks = document.querySelectorAll('#sidebar a');
  const pages = document.querySelectorAll('[id$="-page"]');
  
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetPage = link.getAttribute('data-target');
      
      // 隐藏所有页面
      pages.forEach(page => page.classList.add('hidden'));
      // 显示目标页面
      document.getElementById(targetPage).classList.remove('hidden');
    });
  });
});