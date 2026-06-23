import tkinter as tk
from tkinter import ttk
import psutil
import time
import json
import os

# Import thư viện đồ họa Matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class CpuGraphCanvas(tk.Frame):
    def __init__(self, parent, click_callback, history_data, is_logical=False, width=200, height=120, 
                 face_color="#e6f0fa", edge_color="#0078d4", is_disk_transfer=False): # 🛠️ Thêm flag nhận diện ổ đĩa
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.click_callback = click_callback
        self.is_logical = is_logical 
        self.data_history = history_data 
        self.grid_offset = 0        
        self.face_color = face_color
        self.edge_color = edge_color
        self.is_disk_transfer = is_disk_transfer # Lưu cấu hình ổ đĩa

        # 1. Khởi tạo Figure Matplotlib nền
        self.fig, self.ax = plt.subplots(dpi=140)
        self.fig.patch.set_facecolor('#ffffff') 
        self.bind("<Destroy>", self.on_destroy)
        if self.is_logical:
            self.fig.subplots_adjust(left=0.015, right=0.985, bottom=0.01, top=0.98)
        else:
            #self.fig.subplots_adjust(left=0.001, right=0.999, bottom=0.01, top=1.0)
            self.fig.subplots_adjust(left=0.001, right=0.990, top=1.0, bottom=0.01)
        
        # 2. Nhúng vào Tkinter
        self.canvas_matplotlib = FigureCanvasTkAgg(self.fig, master=self)
        self.widget = self.canvas_matplotlib.get_tk_widget()
        self.widget.pack(fill="both", expand=True)
        
        self.widget.bind("<Button-1>", lambda event: self.click_callback())
        self.setup_axes()
    def get_nice_scale(self, max_val):
        """Trả về mốc tròn gần nhất phía trên max_val, giống Windows Task Manager."""
        steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]
        for s in steps:
            if max_val <= s:
                return s
        decade = 10 ** len(str(int(max_val)))
        return decade
    def setup_axes(self):
        self.ax.set_facecolor('#ffffff')
        self.ax.set_xlim(0, 49)
        
        # 🛠️ CẢI TIẾN TỰ ĐỘNG SCALE TRỤC Y:
        if self.is_disk_transfer:
            # Thu thập tất cả các giá trị đọc và ghi hiện có trong lịch sử để tìm đỉnh cao nhất
            all_vals = []
            for item in self.data_history:
                if isinstance(item, (list, tuple)):
                    all_vals.extend(item)
                else:
                    all_vals.append(item)
            
            raw_max = max(all_vals + [0.1]) # Đặt chặn dưới siêu nhỏ để tránh mảng trống hoàn toàn
            
            # Tính mốc trần tròn thông minh theo hàm fen cấp
            nice_max = self.get_nice_scale(raw_max)
            self.peak_val = nice_max  # Lưu lại để DiskDetailView gọi hiển thị label bên phải
            
            # 🛠️ ĐIỀU CHỈNH CHUẨN: Để hẳn từ 0 để khi tốc độ về 0, đường vẽ chạm khít sàn đáy không bị hụt pixel
            self.ax.set_ylim(0.1, nice_max)
        else:
            # CPU và RAM giữ nguyên mốc cố định lún nhẹ chống dày viền đáy
            self.ax.set_ylim(0.1, 100)
            
        self.ax.set_aspect('auto')
        
        # Đặt cấu hình viền hộp đồ thị màu xám nhạt tinh tế giống Task Manager thật
        for spine_name, spine in self.ax.spines.items():
            spine.set_visible(True)
            spine.set_color(self.edge_color)  
            spine.set_linewidth(0.5)    
            
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

    def update_graph_only(self, current_offset):
        self.grid_offset = current_offset
        self.draw_chart()
        
    def draw_chart(self):
        # 🛠️ SỬA TẠI ĐÂY: Phải xóa đồ thị cũ TRƯỚC, rồi mới gọi setup_axes() để dựng lại khung viền
        self.ax.clear()
        self.setup_axes()
        
        w_width = 49 
        
        # Lưới ngang cố định mờ (Hệ thống lưới giữ nguyên của fen)
        y_limits = self.ax.get_ylim()
        y_max = y_limits[1]
        for pct in [0.25, 0.50, 0.75]:
            self.ax.axhline(y=y_max * pct, color="#f5f5f5", linestyle="-", linewidth=0.5, zorder=1)
            
        # Đường lưới dọc cuộn động chạy lùi
        step_x = w_width / 10
        start_x = 0 - (self.grid_offset * (step_x / 10))
        while start_x <= w_width:
            if start_x >= 0:
                self.ax.axvline(x=start_x, color="#f5f5f5", linestyle="-", linewidth=0.5, zorder=1)
            start_x += step_x

        # Tiến trình vẽ đường phân tách độc lập và đường đỉnh di động
        x = np.arange(len(self.data_history))
        
        if self.is_disk_transfer:
            y_read = np.array([item[0] for item in self.data_history])
            y_write = np.array([item[1] for item in self.data_history])
            
            self.ax.plot(x, y_read, color=self.edge_color, linestyle="-", linewidth=0.8, antialiased=True, zorder=2)
            self.ax.plot(x, y_write, color=self.edge_color, linestyle="--", linewidth=0.8, antialiased=True, zorder=2)
            
            # Tính toán đường đỏ di động
            all_vals = []
            for item in self.data_history:
                if isinstance(item, (list, tuple)):
                    all_vals.extend(item)
                else:
                    all_vals.append(item)
            raw_max = max(all_vals + [0.0])
            
            if raw_max > 0:
                self.ax.axhline(y=raw_max + 0.01, color=self.edge_color, linestyle="-", linewidth=0.6, zorder=3)
                
                # Định dạng chữ raw_max và logic lật hướng nhãn
                if raw_max >= 1000.0:
                    text_val = f"{raw_max/1024:.1f} GB/s" if raw_max % 1024 != 0 else f"{int(raw_max/1024)} GB/s"
                elif raw_max >= 1.0:
                    text_val = f"{raw_max:.1f} MB/s"
                else:
                    text_val = f"{int(raw_max * 1024)} KB/s"
                
                if (y_max - raw_max) / y_max < 0.2:
                    v_align = 'top'
                    y_offset = - (y_max * 0.01)
                else:
                    v_align = 'bottom'
                    y_offset = + (y_max * 0.01)
                self.ax.text(
                    x=0.99, 
                    y=raw_max + y_offset, 
                    s=text_val, 
                    color="#555555", 
                    fontsize=8,
                    horizontalalignment='right',  
                    verticalalignment=v_align,     
                    transform=self.ax.get_yaxis_transform(),
                    zorder=4
                )
        else:
            # Biểu đồ miền truyền thống dành cho CPU và RAM
            y = np.array(self.data_history)
            self.ax.fill_between(x, y, 0, facecolor=self.face_color, edgecolor=self.edge_color, linewidth=0.5, antialiased=True, zorder=2)
        
        self.canvas_matplotlib.draw_idle()
    def on_destroy(self, event):
        """Hàm dọn dẹp và đóng Figure Matplotlib một cách tường minh để giải phóng RAM"""
        if hasattr(self, 'fig') and self.fig:
            import matplotlib.pyplot as plt
            try:
                plt.close(self.fig)  # Đóng hẳn Figure khỏi bộ quản lý ngầm của pyplot
                # print("🧹 Đã giải phóng RAM cho 1 Figure Matplotlib thành công!")
            except:
                pass

class CpuDetailView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")
        self.config_file = "config.json"
        self.cpu_name = self.get_cpu_name()
        self.logical_cores = psutil.cpu_count(logical=True)
        self.physical_cores = psutil.cpu_count(logical=False)
        self.start_time = time.time()
        self.overall_history = [0] * 50
        self.logical_history = [[0] * 50 for _ in range(self.logical_cores)]
        self.global_grid_offset = 0
        self.view_mode = self.load_config() 
        self.graphs = []
        
        # 🛠️ CẢI TIẾN CHIỀU CAO: Chia Grid cho CpuDetailView để ép giãn đồ thị theo chiều dọc
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header giữ nguyên
        self.grid_rowconfigure(1, weight=0) # Header giữ nguyên
        self.grid_rowconfigure(2, weight=1) # Graph container chiếm trọn không gian trống còn lại
        self.grid_rowconfigure(3, weight=0) # Thông số dưới đáy giữ nguyên
        
        self.setup_ui()
        
    def get_cpu_name(self):
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        except:
            pass
        return "Generic CPU"

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("cpu_view_mode", "overall")
            except:
                pass
        return "overall"

    def save_config(self):
        data = {"cpu_view_mode": self.view_mode}
        try:
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Lỗi lưu cấu hình: {e}")

    def setup_ui(self):
        # Hàng 0: Tiêu đề CPU
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        lbl_cpu_title = tk.Label(header_frame, text="CPU", font=("Calibri Light", 28), bg="#ffffff", fg="#000000")
        lbl_cpu_title.pack(side="left", anchor="s")
        
        lbl_cpu_model = tk.Label(header_frame, text=self.cpu_name, font=("Calibri Light", 11), bg="#ffffff", fg="#555555")
        lbl_cpu_model.pack(side="right", anchor="s", pady=5)
        
        # Hàng 1: Dòng phụ
        self.lbl_sub_title = tk.Label(self, text="% Utilization over 60 seconds", font=("Calibri", 8), bg="#ffffff", fg="#555555")
        self.lbl_sub_title.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 0))
        # Hàng 2: Vùng chứa biểu đồ (Dùng grid thay pack để ăn theo weight=1)
        self.graph_container = tk.Frame(self, bg="#ffffff")
        self.graph_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        self.render_graphs()

        # Hàng 2: Thông số chi tiết phía dưới đáy
        self.stats_frame = tk.Frame(self, bg="#ffffff")
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=(24, 0), pady=(0, 15))
        
        # Khóa cứng độ rộng các cột thông số
        self.stats_frame.grid_columnconfigure(0, minsize=110, weight=0)
        self.stats_frame.grid_columnconfigure(1, minsize=110, weight=0)
        self.stats_frame.grid_columnconfigure(2, minsize=110, weight=0)
        self.stats_frame.grid_columnconfigure(3, minsize=150, weight=1)
        
        self.lbl_usage_title = tk.Label(self.stats_frame, text="Utilization", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_usage_title.grid(row=0, column=0, sticky="sw") 
        self.lbl_usage = tk.Label(self.stats_frame, text="0%", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_usage.grid(row=1, column=0, sticky="nw")
        self.lbl_proc_title = tk.Label(self.stats_frame, text="Processes", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_proc_title.grid(row=2, column=0, sticky="sw") 
        self.lbl_proc = tk.Label(self.stats_frame, text="0", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_proc.grid(row=3, column=0, sticky="nw")
        self.lbl_system_uptime_title = tk.Label(self.stats_frame, text="Up time", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_system_uptime_title.grid(row=4, column=0, sticky="sw") 
        self.lbl_system_uptime = tk.Label(self.stats_frame, text="0:00:00:00", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_system_uptime.grid(row=5, column=0, sticky="nw")

        self.lbl_speed_title = tk.Label(self.stats_frame, text="Speed", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_speed_title.grid(row=0, column=1, sticky="sw") 
        self.lbl_speed = tk.Label(self.stats_frame, text="0.00 GHz", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_speed.grid(row=1, column=1, sticky="nw")
        self.lbl_threads_title = tk.Label(self.stats_frame, text="Threads", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_threads_title.grid(row=2, column=1, sticky="sw") 
        self.lbl_threads = tk.Label(self.stats_frame, text="0", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_threads.grid(row=3, column=1, sticky="nw")
        
        self.lbl_handles_title = tk.Label(self.stats_frame, text="Handles", font=("Calibri", 8), bg="#ffffff", fg="#555555", justify="left", anchor="w")
        self.lbl_handles_title.grid(row=2, column=2, sticky="sw") 
        self.lbl_handles = tk.Label(self.stats_frame, text="0", font=("Calibri", 14), bg="#ffffff", justify="left", anchor="w")
        self.lbl_handles.grid(row=3, column=2, sticky="nw")

        # Khung phụ Cột 4 chứa thông tin Cache và Base Speed
        self.col4_sub_frame = tk.Frame(self.stats_frame, bg="#ffffff")
        self.col4_sub_frame.grid(row=0, column=3, rowspan=6, sticky="nw", padx=(20, 0))

        lbl_base_speed_title = tk.Label(self.col4_sub_frame, text="Base speed:", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_base_speed_title.grid(row=0, column=0, sticky="w")
        lbl_base_speed_val = tk.Label(self.col4_sub_frame, text=f"{round(psutil.cpu_freq().current/1000 if psutil.cpu_freq() else 3.2, 2)} GHz", font=("Calibri", 9), bg="#ffffff", fg="#000000")
        lbl_base_speed_val.grid(row=0, column=1, sticky="w", padx=(10, 0))

        lbl_cores_title = tk.Label(self.col4_sub_frame, text="Cores:", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_cores_title.grid(row=1, column=0, sticky="w")
        lbl_cores_val = tk.Label(self.col4_sub_frame, text=f"{self.physical_cores}", font=("Calibri", 9), bg="#ffffff", fg="#000000")
        lbl_cores_val.grid(row=1, column=1, sticky="w", padx=(10, 0))

        lbl_logical_title = tk.Label(self.col4_sub_frame, text="Logical processors:", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_logical_title.grid(row=2, column=0, sticky="w")
        lbl_logical_val = tk.Label(self.col4_sub_frame, text=f"{self.logical_cores}", font=("Calibri", 9), bg="#ffffff", fg="#000000")
        lbl_logical_val.grid(row=2, column=1, sticky="w", padx=(10, 0))

        lbl_virt_title = tk.Label(self.col4_sub_frame, text="Virtualization:", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_virt_title.grid(row=3, column=0, sticky="w")
        has_kvm = "Enabled" if os.path.exists("/dev/kvm") else "Disabled"
        lbl_virt_val = tk.Label(self.col4_sub_frame, text=has_kvm, font=("Calibri", 9), bg="#ffffff", fg="#000000")
        lbl_virt_val.grid(row=3, column=1, sticky="w", padx=(10, 0))

        def format_cache_size(raw_size):
            if not raw_size or raw_size == "N/A": return "N/A"
            raw_size = raw_size.strip()
            num_part = "".join([c for c in raw_size if c.isdigit()])
            unit_part = "".join([c for c in raw_size if c.isalpha()]).upper()
            if num_part:
                num = int(num_part)
                if "K" in unit_part and num >= 1024: return f"{round(num / 1024, 1)} MB"
                formatted_num = f"{num:,}"
                if "K" in unit_part: return f"{formatted_num} KB"
                elif "M" in unit_part: return f"{formatted_num} MB"
                else: return f"{formatted_num} {unit_part}B"
            return raw_size

        cache_info = {"L1": "N/A", "L2": "N/A", "L3": "N/A"}
        try:
            l1_data = 0
            for i in range(4): 
                base_path = f"/sys/devices/system/cpu/cpu0/cache/index{i}"
                if os.path.exists(base_path):
                    with open(f"{base_path}/level", "r") as f: level = f.read().strip()
                    with open(f"{base_path}/size", "r") as f: size = f.read().strip()
                    with open(f"{base_path}/type", "r") as f: ctype = f.read().strip()
                    if level == "1" and "Data" in ctype: l1_data = size
                    elif level == "2": cache_info["L2"] = size
                    elif level == "3": cache_info["L3"] = size
            if l1_data: cache_info["L1"] = l1_data
        except: pass

        tk.Label(self.col4_sub_frame, text="L1 cache:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=4, column=0, sticky="w")
        tk.Label(self.col4_sub_frame, text=format_cache_size(cache_info["L1"]), font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=4, column=1, sticky="w", padx=(10, 0))
        tk.Label(self.col4_sub_frame, text="L2 cache:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=5, column=0, sticky="w")
        tk.Label(self.col4_sub_frame, text=format_cache_size(cache_info["L2"]), font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=5, column=1, sticky="w", padx=(10, 0))
        tk.Label(self.col4_sub_frame, text="L3 cache:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=6, column=0, sticky="w")
        tk.Label(self.col4_sub_frame, text=format_cache_size(cache_info["L3"]), font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=6, column=1, sticky="w", padx=(10, 0))

    def toggle_view_mode(self):
        if self.view_mode == "overall": self.view_mode = "logical"
        else: self.view_mode = "overall"
        self.save_config()
        for widget in self.graph_container.winfo_children():
            widget.pack_forget()
            widget.grid_forget()
        self.render_graphs()

    def render_graphs(self):
        # 1. Giải phóng bộ nhớ Matplotlib và hủy Widget cũ
        for g in self.graphs: 
            if hasattr(g, 'fig'): plt.close(g.fig)
            g.destroy()
        self.graphs.clear()
        
        if self.view_mode == "overall":
            # 🛠️ BƯỚC KHÔI PHỤC QUAN TRỌNG: Xóa sạch cấu hình Grid nhiều ô của Logical cũ
            # Ép cột 0 và hàng 0 nhận weight=1, đồng thời hủy bỏ hoàn toàn cấu hình dính hàng/cột của các ô từ 1 đến 8
            for c in range(12):  # Quét qua tối đa số cột có thể có
                self.graph_container.grid_columnconfigure(c, weight=1 if c == 0 else 0)
            for r in range(12):  # Quét qua tối đa số hàng có thể có
                self.graph_container.grid_rowconfigure(r, weight=1 if r == 0 else 0)
            
            # Khởi tạo đồ thị tổng thể
            g = CpuGraphCanvas(self.graph_container, click_callback=self.toggle_view_mode, history_data=self.overall_history, is_logical=False)
            
            # Sử dụng Grid tràn viền, bám chắc 4 cạnh sticky="nsew"
            g.grid(row=0, column=0, sticky="nsew")
            self.graphs.append(g)
        else:
            # Chế độ xem theo từng nhân (Logical Cores)
            cores = self.logical_cores
            if cores <= 2:   cols, rows = 2, 1
            elif cores <= 4: cols, rows = 2, 2
            elif cores <= 8: cols, rows = 4, 2
            elif cores <= 12: cols, rows = 4, 3
            elif cores <= 16: cols, rows = 4, 4
            else:            cols, rows = 8, int(cores/8)
            
            # Thiết lập Grid nhiều ô cho chế độ Logical
            for c in range(cols): self.graph_container.grid_columnconfigure(c, weight=1)
            for r in range(rows): self.graph_container.grid_rowconfigure(r, weight=1)
            
            for i in range(cores):
                r = i // cols
                c = i % cols
                g = CpuGraphCanvas(self.graph_container, click_callback=self.toggle_view_mode, history_data=self.logical_history[i], is_logical=True, width=100, height=60)
                g.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
                self.graphs.append(g)
                
        # Ra lệnh làm mới nhịp cuộn lưới động
        for g in self.graphs:
            g.update_graph_only(self.global_grid_offset)

    def receive_central_cpu_data(self, current_overall_pct, current_speed):
        self.overall_history.pop(0)
        self.overall_history.append(current_overall_pct)
        
        current_percpu_pcts = psutil.cpu_percent(interval=None, percpu=True)
        for i, val in enumerate(current_percpu_pcts):
            if i < len(self.logical_history):
                self.logical_history[i].pop(0)
                self.logical_history[i].append(val)
                
        self.global_grid_offset = (self.global_grid_offset + 1) % 10

        for g in self.graphs:
            g.update_graph_only(self.global_grid_offset)
                
        handles_count = 0
        try:
            with open("/proc/sys/fs/file-nr", "r") as f:
                parts = f.read().split()
                if parts: handles_count = int(parts[0])
        except: pass
            
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = int(float(f.readline().split()[0]))
        except:
            uptime_seconds = int(time.time() - psutil.boot_time())
            
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        uptime_str = f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        proc_count = len(psutil.pids())
        thread_count = sum([p.info['num_threads'] or 0 for p in psutil.process_iter(attrs=['num_threads'])])
        
        self.lbl_usage.config(text=f"{int(current_overall_pct)}%")
        self.lbl_speed.config(text=f"{current_speed} GHz")
        self.lbl_proc.config(text=f"{proc_count}")
        self.lbl_threads.config(text=f"{thread_count}")
        self.lbl_handles.config(text=f"{handles_count:,}")
        self.lbl_system_uptime.config(text=uptime_str)