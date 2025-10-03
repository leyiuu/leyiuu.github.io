import time
import json
import os
import schedule
from datetime import datetime, timedelta
from pynput import mouse, keyboard
from collections import defaultdict
import git
from pathlib import Path
import threading

class ActivityTracker:
    def __init__(self, repo_path="./leyiuu.github.io"):
        self.last_activity = datetime.now()
        self.cursor_positions = defaultdict(int)
        self.active_periods = []
        self.current_active_start = datetime.now()
        self.idle_threshold = 300  # 5分钟无活动视为空闲
        self.repo_path = Path(repo_path)
        self.last_save_date = datetime.now().date()
        
        # 初始化Git仓库
        self._init_git_repo()
        
        # 设置定时任务
        self._setup_schedule()
        
    def _init_git_repo(self):
        """初始化或连接到Git仓库"""
        if not self.repo_path.exists():
            print(f"⚠️  仓库目录不存在: {self.repo_path}")
            print("请先执行以下命令:")
            print(f"  git clone https://github.com/leyiuu/leyiuu.github.io.git")
            exit(1)
        
        try:
            self.repo = git.Repo(self.repo_path)
            print(f"✅ 已连接到Git仓库: {self.repo_path}")
        except git.exc.InvalidGitRepositoryError:
            print(f"❌ {self.repo_path} 不是有效的Git仓库")
            exit(1)
    
    def _setup_schedule(self):
        """设置定时任务"""
        # 每天23:55自动保存当天数据
        schedule.every().day.at("23:55").do(self.auto_save_daily)
        
        # 每小时自动上传一次（可选）
        schedule.every().hour.do(self.auto_upload_current)
        
        print("⏰ 定时任务已设置:")
        print("   - 每天 23:55 自动保存当日数据")
        print("   - 每小时自动上传最新状态")
    
    def on_move(self, x, y):
        grid_x = x // 100
        grid_y = y // 100
        self.cursor_positions[(grid_x, grid_y)] += 1
        self.update_activity()
    
    def on_click(self, x, y, button, pressed):
        self.update_activity()
    
    def on_key(self, key):
        self.update_activity()
    
    def update_activity(self):
        now = datetime.now()
        
        # 检查是否跨天，如果跨天则保存昨天的数据
        if now.date() > self.last_save_date:
            print("\n🌅 检测到新的一天，保存昨日数据...")
            self.save_daily_report(auto=True)
            # 重置数据
            self.cursor_positions = defaultdict(int)
            self.active_periods = []
            self.current_active_start = now
            self.last_save_date = now.date()
        
        # 检查是否从空闲状态恢复
        if (now - self.last_activity).seconds > self.idle_threshold:
            self.active_periods.append({
                'start': self.current_active_start.isoformat(),
                'end': self.last_activity.isoformat(),
                'duration': (self.last_activity - self.current_active_start).seconds
            })
            self.current_active_start = now
        
        self.last_activity = now
    
    def _calculate_weekly_total(self):
        """计算本周总活动时间"""
        data_dir = self.repo_path / 'data'
        if not data_dir.exists():
            return 0
        
        week_ago = datetime.now() - timedelta(days=7)
        weekly_total = 0
        
        for json_file in data_dir.glob('activity_*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_date = datetime.fromisoformat(data['last_activity'])
                    if file_date >= week_ago:
                        weekly_total += data['total_active_time']
            except:
                continue
        
        return weekly_total
    
    def _count_total_records(self):
        """统计总记录数"""
        data_dir = self.repo_path / 'data'
        if not data_dir.exists():
            return 0
        return len(list(data_dir.glob('activity_*.json')))
    
    def _get_recent_history(self, days=7):
        """获取最近N天的历史数据"""
        data_dir = self.repo_path / 'data'
        if not data_dir.exists():
            return []
        
        history = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for json_file in sorted(data_dir.glob('activity_*.json'), reverse=True)[:days]:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_date = datetime.fromisoformat(data['last_activity'])
                    if file_date >= cutoff_date:
                        history.append({
                            'date': data['date'],
                            'total_time': data['total_active_time'],
                            'formatted_time': data['total_active_time_formatted'],
                            'periods': len(data.get('active_periods', []))
                        })
            except:
                continue
        
        return history
    
    def auto_save_daily(self):
        """每日自动保存"""
        print("\n⏰ 执行每日自动保存...")
        self.save_daily_report(auto=True)
    
    def auto_upload_current(self):
        """每小时自动上传当前状态"""
        print("\n🔄 自动更新最新状态...")
        self._save_latest_only()
    
    def _save_latest_only(self):
        """只保存latest_activity.json（每小时更新）"""
        total_active_time = sum(p['duration'] for p in self.active_periods)
        if self.current_active_start and self.last_activity:
            current_duration = (self.last_activity - self.current_active_start).seconds
            total_active_time += current_duration
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'last_activity': self.last_activity.isoformat(),
            'total_active_time': total_active_time,
            'total_active_time_formatted': self._format_duration(total_active_time),
            'weekly_total': self._calculate_weekly_total() + total_active_time,
            'total_records': self._count_total_records(),
            'recent_history': self._get_recent_history(7)
        }
        
        data_dir = self.repo_path / 'data'
        data_dir.mkdir(exist_ok=True)
        
        latest_filepath = data_dir / 'latest_activity.json'
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 上传到GitHub
        try:
            self.repo.index.add([str(latest_filepath.relative_to(self.repo_path))])
            self.repo.index.commit(f"Update latest activity: {datetime.now().strftime('%H:%M')}")
            origin = self.repo.remote(name='origin')
            origin.push()
            print(f"✅ 最新状态已上传 ({datetime.now().strftime('%H:%M')})")
        except:
            pass
    
    def save_daily_report(self, auto=False):
        """保存每日报告并上传到GitHub"""
        # 保存当前活动时段
        if self.current_active_start and self.last_activity:
            current_duration = (self.last_activity - self.current_active_start).seconds
            if current_duration > 0:
                self.active_periods.append({
                    'start': self.current_active_start.isoformat(),
                    'end': self.last_activity.isoformat(),
                    'duration': current_duration
                })
        
        # 生成报告
        total_active_time = sum(p['duration'] for p in self.active_periods)
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'last_activity': self.last_activity.isoformat(),
            'active_periods': self.active_periods,
            'total_active_time': total_active_time,
            'total_active_time_formatted': self._format_duration(total_active_time),
            'cursor_heatmap': {f"{k[0]},{k[1]}": v for k, v in self.cursor_positions.items()},
            'cursor_total_moves': sum(self.cursor_positions.values()),
            'weekly_total': self._calculate_weekly_total() + total_active_time,
            'total_records': self._count_total_records() + 1,
            'recent_history': self._get_recent_history(7)
        }
        
        # 保存到仓库目录
        data_dir = self.repo_path / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # 保存详细报告
        filename = f"activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存最新数据（供网页读取）
        latest_filepath = data_dir / 'latest_activity.json'
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        if not auto:
            print(f"\n{'='*50}")
            print(f"📊 活动报告已保存: {filename}")
            print(f"{'='*50}")
            print(f"📅 日期: {report['date']}")
            print(f"⏰ 最后活动时间: {report['last_activity']}")
            print(f"⏱️  总活动时间: {report['total_active_time_formatted']}")
            print(f"🖱️  鼠标移动次数: {report['cursor_total_moves']}")
            print(f"📍 活动时段数: {len(self.active_periods)}")
            print(f"📊 本周总时长: {self._format_duration(report['weekly_total'])}")
            print(f"📁 历史记录数: {report['total_records']}")
            print(f"{'='*50}\n")
        
        # 上传到GitHub
        self._upload_to_github([filepath, latest_filepath], filename)
    
    def _upload_to_github(self, filepaths, filename):
        """上传文件到GitHub"""
        try:
            if not filepaths:
                return
                
            print("📤 正在上传到GitHub...")
            
            # 添加文件到Git
            for filepath in filepaths:
                self.repo.index.add([str(filepath.relative_to(self.repo_path))])
            
            # 提交
            commit_message = f"Update activity log: {filename}"
            self.repo.index.commit(commit_message)
            
            # 推送到远程仓库
            origin = self.repo.remote(name='origin')
            origin.push()
            
            print(f"✅ 已上传到GitHub!")
            print(f"🌐 网页将在1-2分钟内自动更新")
            print(f"🔗 访问: https://leyiuu.github.io/#activity")
            
        except Exception as e:
            print(f"⚠️  上传失败: {e}")
    
    def _format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _run_schedule(self):
        """后台运行定时任务"""
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def start(self):
        mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click
        )
        keyboard_listener = keyboard.Listener(
            on_press=self.on_key
        )
        
        mouse_listener.start()
        keyboard_listener.start()
        
        # 启动定时任务线程
        schedule_thread = threading.Thread(target=self._run_schedule, daemon=True)
        schedule_thread.start()
        
        print("\n" + "="*50)
        print("🚀 活动跟踪已启动...")
        print("="*50)
        print("📝 记录内容:")
        print("   - 实际工作时间分布")
        print("   - 最后一次键鼠活动时刻")
        print("   - 光标位置分布热力图")
        print(f"⏳ 空闲阈值: {self.idle_threshold}秒")
        print(f"🌐 数据将上传到: https://leyiuu.github.io")
        print("💡 网页会自动读取最新数据并实时显示")
        print("🔄 每天23:55自动保存，每小时自动更新")
        print("⚠️  按 Ctrl+C 手动停止并保存")
        print("="*50 + "\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在保存并上传报告...")
            self.save_daily_report()
            mouse_listener.stop()
            keyboard_listener.stop()
            print("✅ 完成!")

if __name__ == "__main__":
    # 修改为你的仓库路径
    tracker = ActivityTracker(repo_path=r"D:\OneDrive\文档\GitHub\leyiuu.github.io")
    tracker.start()