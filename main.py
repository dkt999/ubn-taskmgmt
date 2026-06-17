import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib
import matplotlib.font_manager as fm
matplotlib.font_manager = fm  # Gán lại thuộc tính để tránh lỗi các chỗ khác gọi ngầm
fm._load_fontmanager(try_read_cache=False)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
import random
import time
from CpuDetailView import CpuDetailView

# ==========================================
# COMPONENT BASE: HỖ TRỢ ĐỔI CHẾ ĐỘ VIEW ĐỘNG
# ==========================================
class BaseMetricsView(ttk.Frame):
    def __init__(self, parent, title_name, line_color, max_points=40):
        super().__init__(parent)
        self.title_name = title_name
        self.line_color = line_color
        self.max_points = max_points
        self.data_history = collections.deque([0] * self.max_points, maxlen=self.max_points)
        self.view_mode = "graph" 
        self.active = False
        
        self.columnconfigure(0, weight=3) 
        self.columnconfigure(1, weight=1) 
        self.rowconfigure(0, weight=1)

        self.frame_stats = ttk.Frame(self)
        self.frame_stats.grid(row=0, column=1, sticky="nsew", padx=20, pady=40)
        
        self.lbl_title = ttk.Label(self.frame_stats, text=self.title_name, font=("Helvetica", 16, "bold"), foreground="#00a3e0")
        self.lbl_title.pack(anchor="w", pady=(0, 10))
        
        self.lbl_value = ttk.Label(self.frame_stats, text="0%", font=("Helvetica", 32, "bold"), foreground="white")
        self.lbl_value.pack(anchor="w", pady=(0, 5))
        
        self.lbl_subtext = ttk.Label(self.frame_stats, text="", font=("Helvetica", 10), foreground="#aaaaaa")
        self.lbl_subtext.pack(anchor="w")

        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor('#2e2e2e')
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self.max_points - 1)
        self.ax.set_facecolor('#1a1a1a')
        self.ax.grid(True, color='#444444', linestyle=':', linewidth=0.5)
        self.ax.tick_params(axis='both', which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
        
        self.line, = self.ax.plot(list(self.data_history), color=self.line_color, linewidth=2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)

        self.render_layout()

    def set_view_mode(self, mode):
        if self.view_mode != mode:
            self.view_mode = mode
            self.render_layout()

    def render_layout(self):
        if self.view_mode == "graph":
            self.columnconfigure(0, weight=3)
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
            self.frame_stats.grid(row=0, column=1, sticky="nsew", padx=20, pady=40)
        else:
            self.canvas.get_tk_widget().grid_forget()
            self.columnconfigure(0, weight=0) 
            self.frame_stats.grid(row=0, column=0, columnspan=2, sticky="center", padx=20, pady=40)

    def start_update(self):
        self.active = True
        self.update_loop()

    def stop_update(self):
        self.active = False

    def update_loop(self):
        pass


class SidebarItem(tk.Frame):
    def __init__(self, parent, icon_text, title_text, value_text, h, w):
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.icon_text = icon_text
        self.title_text = title_text
        self.value_text = value_text
        self.graph_h = h
        self.graph_w = w
        
        # Lịch sử lưu dữ liệu (CPU sẽ tham chiếu hoặc đồng bộ chung mảng 40 điểm cho gọn)
        self.data_history = [0] * 40
        self.setup_ui()
        
    def setup_ui(self):
        self.left_container = tk.Frame(self, bg="#ffffff", width=self.graph_w+10, height=self.graph_h+5)
        self.left_container.pack(side="left", padx=5, fill="y")
        self.left_container.pack_propagate(False)
        
        self.lbl_icon = tk.Label(self.left_container, text=self.icon_text, bg="#ffffff", fg="#363636", font=("Calibri", 14))
        self.lbl_icon.pack(expand=True)
        
        if "CPU" in self.title_text:
            self.graph_color_outline = "#0078d4"
            self.graph_color_domain = "#e6f0fa"
            self.graph_color_line = "#0078d4"
        elif "RAM" in self.title_text:
            self.graph_color_outline = "#73527E"
            self.graph_color_domain = "#FFE9FF"
            self.graph_color_line = "#73527E"
        else:
            self.graph_color_outline = "#8DAA60"
            self.graph_color_domain = "#F0FFE7"
            self.graph_color_line = "#8DAA60"
            
        self.canvas = tk.Canvas(self.left_container, bg="#ffffff", highlightthickness=1, highlightbackground=self.graph_color_outline, width=self.graph_w, height=self.graph_h)
        
        self.text_container = tk.Frame(self, bg="#ffffff")
        self.lbl_title = tk.Label(self.text_container, text=self.title_text, bg="#ffffff", fg="#000000", font=("Calibri Light", 12), anchor="w")
        self.lbl_title.pack(fill="x")
        
        self.lbl_value = tk.Label(self.text_container, text=self.value_text, bg="#ffffff", fg="#555555", font=("Calibri", 9), anchor="w")
        self.lbl_value.pack(fill="x")
        
        self.bind("<Enter>", lambda e: self.set_hover_color("#f3f3f3"))
        self.bind("<Leave>", lambda e: self.set_hover_color("#ffffff"))
        
        # BỎ HÀM TỰ UPDATE RANDOM: Hàm update_real_data sẽ được gọi từ lớp MainWindow
        self.draw_mini_graph()

    def set_hover_color(self, color):
        self.config(bg=color)
        self.left_container.config(bg=color)
        self.text_container.config(bg=color)
        self.lbl_icon.config(bg=color)
        self.lbl_title.config(bg=color)
        self.lbl_value.config(bg=color)

    def update_real_data(self, new_val, display_text):
        """Hàm nhận dữ liệu thật được đẩy từ MainWindow"""
        self.data_history.pop(0)
        self.data_history.append(new_val)
        self.lbl_value.config(text=display_text)
        self.draw_mini_graph()

    def draw_mini_graph(self):
        """Chỉ lo vẽ lại biểu đồ mini dựa trên mảng data_history hiện tại"""
        self.canvas.delete("all")
        points = []
        w, h = self.graph_w, self.graph_h
        padding_top = 2
        padding_bottom = 2
        usable_h = h - padding_top - padding_bottom
        step = w / (len(self.data_history) - 1)
        
        for i, val in enumerate(self.data_history):
            x = i * step
            y = padding_top + (usable_h - (val / 100 * usable_h))
            points.append((x, y))  
            
        if len(points) > 1:
            polygon_points = [(0, h)] + points + [(w, h)]
            self.canvas.create_polygon(polygon_points, fill=self.graph_color_domain, outline="")
            self.canvas.create_line(points, fill=self.graph_color_line, width=1.0)

    def switch_mode(self, collapsed):
        if collapsed:
            self.text_container.pack_forget()
            self.canvas.pack_forget()
            self.lbl_icon.pack(expand=True)
            self.left_container.config(width=30)
        else:
            self.lbl_icon.pack_forget()
            self.left_container.config(width=self.graph_w)
            self.canvas.pack(pady=5, padx=2, expand=True)
            self.text_container.pack(side="left", fill="both", expand=True, padx=5)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Custom Task Manager Pro")
        self.geometry("1000x600")
        self.minsize(625, 400)
        self.h = 40  # Thu nhỏ chiều cao đồ thị sidebar tí cho đẹp cân đối
        self.w = 60  # Thu nhỏ độ rộng đồ thị sidebar
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Cột bên trái (Sidebar) ----
        self.sidebar_frame = tk.Frame(self, bg="#ffffff")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.config(width=250)
        self.sidebar_frame.pack_propagate(False)
        self.sidebar_frame.grid_propagate(False)

        self.lbl_menu = tk.Label(self.sidebar_frame, text="☰  Hiệu năng", bg="#ffffff", fg="#363636", font=("Arial", 12, "bold"), anchor="w")
        self.lbl_menu.pack(pady=15, padx=10, fill="x")

        self.menu_items_container = tk.Frame(self.sidebar_frame, bg="#ffffff")
        self.menu_items_container.pack(fill="both", expand=True, padx=5)
        
        # Khởi tạo các item sidebar
        self.items = []
        self.item_cpu = SidebarItem(self.menu_items_container, "⚙", "CPU", "0% 0.00 GHz", self.h, self.w)
        self.item_cpu.pack(fill="x", pady=5)
        self.items.append(self.item_cpu)
        
        self.item_ram = SidebarItem(self.menu_items_container, "📊", "RAM", "5.9/15.9 GB (37%)", self.h, self.w)
        self.item_ram.pack(fill="x", pady=5)
        self.items.append(self.item_ram)

        self.item_disk0 = SidebarItem(self.menu_items_container, "📊", "Disk 0", "0%", self.h, self.w)
        self.item_disk0.pack(fill="x", pady=5)
        self.items.append(self.item_disk0)

        # ---- Cột chứa border 1px ----
        self.right_border = tk.Frame(self, bg="#CCCCCC", width=1)
        self.right_border.grid(row=0, column=1, sticky="nsew")

        # ---- Cột bên phải (Main Content) ----
        self.main_frame = tk.Frame(self, bg="#f3f3f3")
        self.main_frame.grid(row=0, column=2, sticky="nsew")

        # Tạo View chi tiết và truyền quyền tham chiếu MainWindow vào
        self.cpu_view = CpuDetailView(self.main_frame)
        self.cpu_view.pack(fill="both", expand=True)

        self.is_collapsed = False
        
        for item in self.items:
            item.switch_mode(collapsed=False)
            
        self.bind("<Configure>", self.on_resize)
        
        # KÍCH HOẠT VÒNG LẶP ĐỒNG BỘ DỮ LIỆU TỪ MẸ CHÍNH (MAINWINDOW)
        self.global_sync_loop()

    def global_sync_loop(self):
        """Hàm trung tâm lấy dữ liệu CPU thật để phân phát đồng bộ cho các phân hệ"""
        # 1. Đọc dữ liệu thô từ hệ thống
        current_cpu_pct = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        current_speed = round(freq.current / 1000, 2) if freq else 3.20
        
        # 2. Cập nhật trực tiếp cho Sidebar CPU Item bên trái
        cpu_display_text = f"{int(current_cpu_pct)}%  {current_speed} GHz"
        self.item_cpu.update_real_data(current_cpu_pct, cpu_display_text)
        
        # 3. Ra lệnh cho khung chi tiết CpuDetailView nhận dữ liệu và vẽ lại biểu đồ chính
        # Truyền giá trị hiện tại cùng tốc độ xung nhịp thật sang cho con xử lý tiếp
        self.cpu_view.receive_central_cpu_data(current_cpu_pct, current_speed)
        
        # Giả lập tạm dữ liệu cho RAM/Disk để ngày mai fen code tiếp không bị lỗi
        self.item_ram.update_real_data(random.randint(30, 40), "5.8/16.0 GB (36%)")
        self.item_disk0.update_real_data(random.randint(1, 5), "2%")

        # Lặp lại đều đặn sau 1000 mili-giây (1 giây)
        self.after(1000, self.global_sync_loop)

    def on_resize(self, event):
        if event.widget == self:
            current_width = event.width
            #print(current_width)
            SizeCollapse = 840
            if current_width < SizeCollapse and not self.is_collapsed:
                self.sidebar_frame.config(width=40)
                self.lbl_menu.config(text="☰", anchor="center")
                for item in self.items:
                    item.switch_mode(collapsed=True)
                self.is_collapsed = True
            elif current_width >= SizeCollapse and self.is_collapsed:
                self.sidebar_frame.config(width=250)
                self.lbl_menu.config(text="☰  Hiệu năng", anchor="w")
                for item in self.items:
                    item.switch_mode(collapsed=False)
                self.is_collapsed = False

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()