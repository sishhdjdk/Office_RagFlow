# 1. 启动前端
cd D:\9_Project\VsStudioProject\Office_RagFlow\frontend
npm run dev
# 2. 启动后端
cd D:\9_Project\VsStudioProject\Office_RagFlow 
python run.py

# 3. 启动work
cd D:\9_Project\VsStudioProject\Office_RagFlow\backend
celery -A api.celery_app worker -l info -P solo

# 4. 启动redis

# 5. 启动minion



# 2. 浏览器打开 http://localhost:3000
# 3. 登录 → admin/admin123
# 4. 左侧菜单 → 知识库管理（确认能看到已创建的知识库）
# 5. 左侧菜单 → 对话管理 → 新建对话
#    → 弹窗里应该能看到知识库多选框
#    → 选中知识库 + 输入名称 → 创建
# 6. 点击进入对话 → 输入问题 → 按 Enter
#    → 右侧应该逐字输出 LLM 回答 + 底部引用卡片