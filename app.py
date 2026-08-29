import os
import sys

import win32con
import win32gui
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow


class CustomWebEngineView(QWebEngineView):
    def contextMenuEvent(self, event):
        # 禁用右键菜单
        pass

    def createWindow(self, window_type):
        #让网页请求的新窗口在当前视图中打开。
        return self

class CalendarViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置无边框、不可拖动
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |  # Tool 窗口通常不出现在任务栏
            Qt.WindowType.WindowStaysOnBottomHint # Qt 级别的置底提示
        )
        self.setFixedSize(600, 640)  # 可改为你需要的尺寸
        self.move(80, 90) # 移动到屏幕左上角
        self.setWindowTitle("Google Calendar")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.set_always_on_bottom() # 修正方法调用

        # 配置持久化存储
        # 判断程序是否被打包
        if getattr(sys, 'frozen', False):
            # 如果是打包状态，则基路径是可执行文件所在目录
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是正常运行状态，则基路径是脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))

        persistent_dir = os.path.join(base_path, "app_data", "google_profile")
        if not os.path.exists(persistent_dir):
            os.makedirs(persistent_dir, exist_ok=True)

        self.profile = QWebEngineProfile("google_storage", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setPersistentStoragePath(persistent_dir)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        # 加载Google Calendar网页
        self.browser = CustomWebEngineView(self.profile, self) # 使用自定义 profile
        self.browser.page().settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        self.browser.setUrl(QUrl("https://calendar.google.com/calendar/u/0/r"))
        self.browser.setGeometry(0, 0, 673, 670) # WebEngineView相对于QMainWindow的位置
        self.browser.loadFinished.connect(self.apply_multiply_effect)


    def apply_multiply_effect(self, ok):
        if ok:
            script = """
                // 强制覆盖 XPath /html/body/div[2] 对应元素的背景色
                const style = document.createElement('style');
                style.id = 'tasks-widget-background-override';
                style.textContent = `
                    html > body > div:nth-of-type(2) {
                        background-color: #FFFFFF !important;
                    }

                    html > body > div:nth-of-type(2) > div > div:nth-child(1) > header > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div > div > div > div:nth-child(2) {
                        display: none !important;
                    }
                `;
                document.head.appendChild(style);

                // Add event listener to prevent Tab key default action
                document.addEventListener('keydown', function(event) {
                    // Check for Tab key (event.key === 'Tab' or event.keyCode === 9 for older browsers)
                    if (event.key === 'Tab' || event.keyCode === 9) {
                        event.preventDefault();
                    }
                });
            """
            self.browser.page().runJavaScript(script)
        else:
            # 加载失败（如断网），5秒后尝试重新加载
            QTimer.singleShot(5000, self.browser.reload)

    def set_always_on_bottom(self):
        hwnd = int(self.winId())
        if hwnd == 0: # 确保 hwnd 有效
            # print("Error: Could not get window handle on time.") # 可选的调试信息
            QTimer.singleShot(200, self.set_always_on_bottom) # 如果第一次失败，稍后再试
            return

        # 设置窗口扩展样式，使其不被激活 (WS_EX_NOACTIVATE)
        # 这有助于防止窗口在点击时被带到前景
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_NOACTIVATE)


    def mousePressEvent(self, _):
        pass  # 禁用拖动
 
    def mouseMoveEvent(self, _):
        pass

    def closeEvent(self, event):
        # 忽略关闭事件，防止 Alt+F4 关闭
        event.ignore()
 
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-frame-rate-limit"
if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = CalendarViewer()
    viewer.show()
    sys.exit(app.exec())
