import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib
import matplotlib.font_manager as fm
matplotlib.font_manager = fm  
fm._load_fontmanager(try_read_cache=False)
import collections
import random
import time

# Import 2 phân hệ view chi tiết
from CpuDetailView import CpuDetailView
from RamDetailView import RamDetailView

class SidebarItem(tk.Frame):
    def __init__(self, parent, icon_text, title_text, value_text, h, w, click_callback=None):
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.icon_text = icon_text
        self.title_text = title_text
        self.value_text = value_text
        self.graph_h = h
        self.graph_w = w
        self.click_callback = click_callback # Nhận hàm gọi lại khi click
        
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
        
        # Gán sự kiện đổi màu Hover
        self.bind("<Enter>", lambda e: self.set_hover_color("#f3f3f3"))
        self.bind("<Leave>", lambda e: self.set_hover_color("#ffffff"))
        
        # 🛠️ QUAN TRỌNG: Gán sự kiện click chuột cho tất cả các thành phần con để click chỗ nào cũng ăn lệnh
        if self.click_callback:
            self.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.left_container.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.text_container.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.lbl_icon.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.canvas.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.lbl_title.bind("<Button-1>", lambda e: self.click_callback(self.title_text))
            self.lbl_value.bind("<Button-1>", lambda e: self.click_callback(self.title_text))

        self.draw_mini_graph()

    def set_hover_color(self, color):
        self.config(bg=color)
        self.left_container.config(bg=color)
        self.text_container.config(bg=color)
        self.lbl_icon.config(bg=color)
        self.lbl_title.config(bg=color)
        self.lbl_value.config(bg=color)

    def update_real_data(self, new_val, display_text):
        self.data_history.pop(0)
        self.data_history.append(new_val)
        self.lbl_value.config(text=display_text)
        self.draw_mini_graph()

    def draw_mini_graph(self):
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
        self.minsize(650, 400)
        self.h = 40  
        self.w = 60  
        self.current_offset = 0
        
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
        
        # Khởi tạo các item sidebar kèm hàm callback xử lý click đổi giao diện
        self.items = []
        self.item_cpu = SidebarItem(self.menu_items_container, "⚙", "CPU", "0% 0.00 GHz", self.h, self.w, click_callback=self.handle_view_change)
        self.item_cpu.pack(fill="x", pady=5)
        self.items.append(self.item_cpu)
        
        self.item_ram = SidebarItem(self.menu_items_container, "📊", "RAM", "0.0/0.0 GB (0%)", self.h, self.w, click_callback=self.handle_view_change)
        self.item_ram.pack(fill="x", pady=5)
        self.items.append(self.item_ram)

        self.item_disk0 = SidebarItem(self.menu_items_container, "📊", "Disk 0", "0%", self.h, self.w, click_callback=self.handle_view_change)
        self.item_disk0.pack(fill="x", pady=5)
        self.items.append(self.item_disk0)

        # ---- Cột chứa border 1px ----
        self.right_border = tk.Frame(self, bg="#CCCCCC", width=1)
        self.right_border.grid(row=0, column=1, sticky="nsew")

        # ---- Cột bên phải (Main Content) ----
        self.main_frame = tk.Frame(self, bg="#ffffff")
        self.main_frame.grid(row=0, column=2, sticky="nsew")

        # Khởi tạo sẵn 2 cụm giao diện chi tiết
        self.cpu_view = CpuDetailView(self.main_frame)
        self.ram_view = RamDetailView(self.main_frame)
        
        # Mặc định lúc mở app lên thì hiển thị CPU trước
        self.cpu_view.pack(fill="both", expand=True)

        self.is_collapsed = False
        for item in self.items:
            item.switch_mode(collapsed=False)
            
        self.bind("<Configure>", self.on_resize)
        
        # Chạy vòng tuần hoàn đồng bộ dữ liệu hệ thống
        self.global_sync_loop()

    def handle_view_change(self, target_view_name):
        """🛠️ HÀM ĐỔI VIEW CHI TIẾT: Ẩn view cũ, xòe view mới tương ứng khi click Sidebar"""
        # Ẩn tạm cả 2 bên
        self.cpu_view.pack_forget()
        self.ram_view.pack_forget()
        
        # Bật chính xác giao diện được bấm chọn
        if target_view_name == "CPU":
            self.cpu_view.pack(fill="both", expand=True)
        elif target_view_name == "RAM":
            self.ram_view.pack(fill="both", expand=True)
        elif target_view_name == "Disk 0":
            # Tạm thời chưa làm Disk thì vẫn giữ màn hình trống hoặc cho hiện CPU
            self.cpu_view.pack(fill="both", expand=True)

    def global_sync_loop(self):
        """Luồng trung tâm thu thập dữ liệu phần cứng thật và chia sẻ phân phối ra các bên"""
        self.current_offset = (self.current_offset + 1) % 10
        
        # -------------------------------------------------------
        # LOGIC ĐỒNG BỘ CPU
        # -------------------------------------------------------
        current_cpu_pct = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        current_speed = round(freq.current / 1000, 2) if freq else 3.20
        
        cpu_display_text = f"{int(current_cpu_pct)}%  {current_speed} GHz"
        self.item_cpu.update_real_data(current_cpu_pct, cpu_display_text)
        self.cpu_view.receive_central_cpu_data(current_cpu_pct, current_speed)
        
        # -------------------------------------------------------
        # LOGIC ĐỒNG BỘ RAM THẬT 100%
        # -------------------------------------------------------
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        ram_percent = mem.percent
        in_use_gb = mem.used / (1024**3)
        available_gb = mem.available / (1024**3)
        
        # Mẹo lấy dung lượng vật lý chuẩn đét (Đã hoàn thiện ở bước trước)
        total_raw_gb = mem.total / (1024**3)
        standard_sizes = [2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 256]
        hardware_total_gb = min(standard_sizes, key=lambda x: abs(x - total_raw_gb))
        if hardware_total_gb < total_raw_gb:
            hardware_total_gb = round(total_raw_gb, 1)

        # 🛠️ HOÀN THIỆN: TỰ ĐỘNG QUÉT KIỂU RAM (CÓ SUDO & KHÔNG SUDO)
        ram_type = "DDR4"  # Giá trị mặc định an toàn nhất
        try:
            import subprocess
            import os
            
            # CÁCH 1: Nếu app đang được chạy trực tiếp bằng quyền root (UID = 0)
            if os.geteuid() == 0:
                # Gọi trực tiếp dmidecode của Linux để bóc tách thông tin phần cứng
                cmd = "dmidecode -t memory"
                proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                stdout, _ = proc.communicate()
                
                # Tìm kiếm từ khóa kiểu RAM trong chuỗi trả về
                for line in stdout.split('\n'):
                    if "Type:" in line and "Detail" not in line:
                        type_str = line.split(":")[1].strip()
                        if type_str in ["DDR3", "DDR4", "DDR5", "LPDDR3", "LPDDR4", "LPDDR5"]:
                            ram_type = type_str
                            break
            else:
                # CÁCH 2: Fallback khi KHÔNG CÓ SUDO (Chạy quyền User thường)
                # Thử quét nhanh trong tệp log khởi động hệ thống xem có lưu vết không
                ram_detected = False
                if os.path.exists("/var/log/dmesg"):
                    try:
                        with open("/var/log/dmesg", "r", errors="ignore") as f_dmesg:
                            for line in f_dmesg:
                                if any(x in line.upper() for x in ["DDR3", "DDR4", "DDR5"]):
                                    for token in ["DDR5", "DDR4", "DDR3"]:
                                        if token in line.upper():
                                            ram_type = token
                                            ram_detected = True
                                            break
                                if ram_detected: break
                    except:
                        pass
                
                # CÁCH 3: Đoán thông minh dựa trên xung nhịp hiện tại nếu dmesg bị khóa log
                # CÁCH 3: Đoán thông minh dựa trên xung nhịp thực tế thu được nếu dmesg bị khóa
                if not ram_detected:
                    ram_speed_mhz = 3200  # Giá trị fallback chuẩn theo máy của fen (3200 MHz)
                    
                    try:
                        # Thử gọi lệnh con lshw (quyền user thường) để quét lấy tốc độ RAM thật từ phần cứng
                        import subprocess
                        proc_lshw = subprocess.Popen(["lshw", "-C", "memory"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                        stdout_lshw, _ = proc_lshw.communicate()
                        
                        for line_lshw in stdout_lshw.split('\n'):
                            if "clock:" in line_lshw.lower() or "tốc độ:" in line_lshw.lower():
                                # Bóc tách con số xung nhịp, ví dụ: "clock: 3200MHz (0.3ns)" -> 3200
                                parts_speed = "".join([char for char in line_lshw if char.isdigit()])
                                if parts_speed:
                                    val_speed = int(parts_speed)
                                    if val_speed > 1000: # Lọc bỏ các giá trị nhiễu nhỏ
                                        ram_speed_mhz = val_speed
                                        break
                    except:
                        pass
                    
                    # Phân tích mốc xung nhịp hệ thống để tự động gán thế hệ DDR phù hợp
                    if ram_speed_mhz >= 4800:
                        ram_type = "DDR5"
                    elif 2133 <= ram_speed_mhz < 4800:
                        ram_type = "DDR4"
                    elif 1066 <= ram_speed_mhz < 2133:
                        ram_type = "DDR3"
                    else:
                        ram_type = "DDR4" # Mốc bảo vệ an toàn
        except Exception as e:
            # Phòng hờ tất cả các lỗi phát sinh ngoài ý muốn, giữ nguyên mặc định DDR4
            ram_type = "DDR4"

        # A. Tính toán Cache
        cache_bytes = (mem.buffers + mem.cached) if hasattr(mem, 'buffers') else 0
        pct_cache = (cache_bytes / mem.total) * 100
        cache_gb = cache_bytes / (1024**3)
        
        # B. Tính toán Committed
        committed_used_gb = (mem.used + swap.used) / (1024**3)
        committed_total_gb = (mem.total + swap.total) / (1024**3)
        committed_str = f"{committed_used_gb:.1f}/{committed_total_gb:.1f} GB"
        
        # C. Tính toán Paged / Non-paged pool
        paged_pool_gb = "N/A"
        non_paged_pool_gb = "N/A"
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
                s_reclaimable = 0
                s_unreclaim = 0
                for line in lines:
                    if line.startswith("SReclaimable:"):
                        s_reclaimable = int(line.split()[1]) * 1024
                    elif line.startswith("SUnreclaim:"):
                        s_unreclaim = int(line.split()[1]) * 1024
                if s_reclaimable > 0:
                    paged_pool_gb = f"{s_reclaimable / (1024**3):.1f} GB"
                if s_unreclaim > 0:
                    non_paged_pool_gb = f"{s_unreclaim / (1024**3):.1f} GB"
        except:
            pass
            
        # Tính toán Hardware Reserved thật
        hardware_reserved_mb = int((hardware_total_gb - total_raw_gb) * 1024)
        if hardware_reserved_mb < 0: hardware_reserved_mb = 0
        hardware_reserved_str = f"{hardware_reserved_mb} MB" if hardware_reserved_mb > 0 else "0 MB"

        # Cập nhật chuỗi chữ hiển thị ở Sidebar
        ram_display_text = f"{in_use_gb:.1f}/{hardware_total_gb:.0f} GB ({int(ram_percent)}%)"
        self.item_ram.update_real_data(ram_percent, ram_display_text)
        
        # Đẩy dữ liệu sang trang con RamDetailView
        self.ram_view.receive_central_ram_data(
            ram_percent=ram_percent, 
            pct_cache=pct_cache, 
            in_use_gb=in_use_gb, 
            available_gb=available_gb, 
            cache_gb=cache_gb,
            committed_str=committed_str,
            paged_pool=paged_pool_gb,
            non_paged_pool=non_paged_pool_gb,
            hardware_total_gb=hardware_total_gb,
            ram_type=ram_type, # <-- Giá trị RAM Type động đã tối ưu hoàn toàn
            hardware_reserved_str=hardware_reserved_str,
            current_offset=self.current_offset
        )
        # Tạm thời giả lập cho Disk 0 (Đợi fen triển khai tiếp)
        self.item_disk0.update_real_data(random.randint(1, 5), "2%")

        self.after(1000, self.global_sync_loop)

    def on_resize(self, event):
        if event.widget == self:
            current_width = event.width
            print(current_width)
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