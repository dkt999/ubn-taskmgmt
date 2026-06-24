import tkinter as tk
from tkinter import ttk
import psutil
import collections
import random
import time
import os
import subprocess
from PIL import Image, ImageTk

# Import đầy đủ các phân hệ view chi tiết hoàn chỉnh từ thư mục dự án
from CpuDetailView import CpuDetailView, CpuGraphCanvas
from RamDetailView import RamDetailView
from DiskDetailView import DiskDetailView 
from ProcessesDetail import ProcessesDetailView

# ==============================================================================
#  SIDEBAR ITEM HOÀN CHỈNH: KHÔI PHỤC MINI GRAPH + HIỆU ỨNG HOVER/ACTIVE
# ==============================================================================
class SidebarItem(tk.Frame):
    def __init__(self, parent, icon_text, title_text, value_text, h, w, click_callback=None, disk_id=None):
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.icon_text = icon_text
        self.title_text = title_text      
        self.disk_id = disk_id            
        self.value_text = value_text
        self.graph_h = h
        self.graph_w = w
        self.click_callback = click_callback 
        
        self.is_active = False            
        self.data_history = [0] * 40      
        
        # 🎨 1. TÍNH TOÁN BỘ MÀU CHUẨN CHO TỪNG LINH KIỆN NGAY KHI KHỞI TẠO
        if "CPU" in self.title_text:
            self.graph_color_outline = "#0078d4" # Xanh dương (Windows)
            self.graph_color_domain = "#e6f0fa"
        elif "RAM" in self.title_text:
            self.graph_color_outline = "#73527E" # Tím bóng bẩy
            self.graph_color_domain = "#FFE9FF"
        elif "Disk" in self.title_text:
            self.graph_color_outline = "#7A9A60" # Xanh lá cây đĩa
            self.graph_color_domain = "#F4F8F1"
        elif "GPU" in self.title_text:
            self.graph_color_outline = "#C4996E" # Vàng hổ phách
            self.graph_color_domain = "#F4E9DD"
        elif "Wi-Fi" in self.title_text or "Ethernet" in self.title_text or "VPN" in self.title_text:
            self.graph_color_outline = "#272727" # Xám đen Network mộc mạc
            self.graph_color_domain = "#F0EFEE"
        else:
            self.graph_color_outline = "#7A9A60"
            self.graph_color_domain = "#F4F8F1"
            
        self.setup_ui()
        
    def setup_ui(self):
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill="x", padx=5, pady=1)
        self.icon_mode_separator = tk.Frame(self, bg="#d9d9d9", height=1)
        self.left_container = tk.Frame(self.container, bg="#ffffff", width=self.graph_w + 10, height=self.graph_h + 6)
        self.left_container.pack(side="left", padx=5, fill="y")
        self.left_container.pack_propagate(False)
        is_network_item = "Wi-Fi" in self.title_text or "Ethernet" in self.title_text or "VPN" in self.title_text
        mini_component = "Network" if is_network_item else "None"
        self.mini_graph = CpuGraphCanvas(
            self.left_container, 
            click_callback=lambda: self.on_click(None), 
            history_data=self.data_history, 
            is_logical=False, 
            width=self.graph_w, 
            height=self.graph_h,
            face_color=self.graph_color_domain,  
            edge_color=self.graph_color_outline,
            component=mini_component,
        )
        self.mini_graph.pack(fill="both", expand=True, padx=2, pady=2)
        self.icon_canvas = tk.Canvas(self.left_container, bg="#ffffff", highlightthickness=0, width=self.graph_w, height=self.graph_h)
        self._draw_generic_icon()
        self.right_container = tk.Frame(self.container, bg="#ffffff")
        self.right_container.pack(side="left", fill="both", expand=True, padx=5)
        self.lbl_title = tk.Label(self.right_container, text=self.title_text, font=("Calibri Bold", 11), bg="#ffffff", fg="#000000", anchor="w")
        self.lbl_title.pack(fill="x", pady=(2, 0))
        self.lbl_value = tk.Label(self.right_container, text=self.value_text, font=("Calibri", 9), bg="#ffffff", fg="#555555", anchor="w")
        self.lbl_value.pack(fill="x")
        for widget in (self, self.container, self.left_container, self.right_container,
                       self.lbl_title, self.lbl_value, self.icon_canvas):
            widget.bind("<Enter>", self.on_hover)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)
    

    def on_hover(self, event):
        if not self.is_active:
            self.set_all_bg("#f2f2f2") 

    def on_leave(self, event):
        if not self.is_active:
            self.set_all_bg("#ffffff") 

    def on_click(self, event):
        if self.click_callback:
            self.click_callback(self)

    def set_active(self, active=True):
        """Hàm đặt trạng thái kích hoạt đổi sang màu xanh nhạt xịn mịn chuẩn Windows"""
        self.is_active = active
        if active:
            self.set_all_bg("#e5f1fb")         
            self.lbl_title.config(fg="#0078d4") 
        else:
            self.set_all_bg("#ffffff")
            self.lbl_title.config(fg="#000000")

    def set_all_bg(self, color):
        """Nhuộm màu nền đồng bộ nhưng chặn không cho cấu hình lại geometry ẩn"""
        self.config(bg=color)
        self.container.config(bg=color)
        self.left_container.config(bg=color)
        self.right_container.config(bg=color)
        self.lbl_title.config(bg=color)
        self.lbl_value.config(bg=color)
        if hasattr(self, 'mini_graph'):
            self.mini_graph.config(bg=color)
        if hasattr(self, 'icon_canvas'):
            self.icon_canvas.config(bg=color)

    # 🛠️ Thư mục chứa icon PNG — tính theo vị trí thật của main.py (không phải cwd lúc chạy app),
    # để dù chạy app từ đâu vẫn luôn tìm đúng thư mục icons/ nằm cùng cấp với main.py.
    ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
    ICON_FILES = {
        "CPU": "cpu.png",
        "RAM": "ram.png",
        "Disk": "disk.png",
        "GPU": "gpu.png",
        "Network": "network.png",
    }

    def _resolve_icon_key(self):
        if "CPU" in self.title_text: return "CPU"
        if "RAM" in self.title_text: return "RAM"
        if "Disk" in self.title_text: return "Disk"
        if "GPU" in self.title_text: return "GPU"
        if "Wi-Fi" in self.title_text or "Ethernet" in self.title_text or "VPN" in self.title_text: return "Network"
        return None

    def _draw_generic_icon(self):
        """Nạp icon PNG thật theo từng hạng mục (cpu.png/ram.png/disk.png/gpu.png/network.png
        trong thư mục ICON_DIR). Nếu không tìm thấy file, fallback vẽ placeholder generic bằng
        Canvas thuần (khung vuông + đường zigzag) để app không bị vỡ giao diện."""
        c = self.icon_canvas
        c.delete("all")
        w, h = self.graph_w, self.graph_h
        icon_key = self._resolve_icon_key()
        filename = self.ICON_FILES.get(icon_key)
        icon_path = os.path.join(self.ICON_DIR, filename) if filename else None

        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).convert("RGBA")
                # Co ảnh vừa khung, chừa lề 6px, giữ tỉ lệ gốc, lọc LANCZOS cho mượt
                img.thumbnail((max(1, 50), max(1, 50)), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(img)  # giữ reference tránh bị GC
                c.create_image(20, 20, image=self._icon_photo)
                return
            except Exception as e:
                print(f"⚠️ Không load được icon '{icon_path}': {e}")  # In ra để fen dễ debug
                pass  # Lỗi đọc file (hỏng/định dạng sai) -> rơi xuống fallback bên dưới

        # --- Fallback: placeholder generic khi chưa có file PNG tương ứng ---
        pad = max(4, min(w, h) // 6)
        c.create_rectangle(pad, pad, w - pad, h - pad, outline=self.graph_color_outline, width=2)
        mid_y = h / 2
        points = [
            (pad + 3, mid_y + 6), (pad + (w - 2*pad) * 0.3, mid_y - 8),
            (pad + (w - 2*pad) * 0.55, mid_y + 4), (pad + (w - 2*pad) * 0.8, mid_y - 10),
            (w - pad - 3, mid_y - 2),
        ]
        c.create_line(points, fill=self.graph_color_outline, width=2, smooth=True)

    def set_compact_icon_mode(self, icon_only):
        """Chuyển đổi giữa mini_graph (đồ thị thật) và icon_canvas (placeholder) khi cửa sổ hẹp.
        Đồng thời hiện/ẩn viền ngăn cách 1px xám giữa các item — chỉ hiện ở chế độ icon."""
        if icon_only:
            self.mini_graph.pack_forget()
            self.icon_canvas.pack(fill="both", expand=True, padx=2, pady=0)
            self.icon_mode_separator.pack(fill="x", side="bottom", pady=(0, 0))
            # 🛠️ Item co lại nhỏ ở chế độ icon, pady=5 (mặc định) trông quá hở -> giảm xuống 1px
            self.pack_configure(pady=0)
        else:
            self.icon_canvas.pack_forget()
            self.mini_graph.pack(fill="both", expand=True, padx=2, pady=2)
            self.icon_mode_separator.pack_forget()
            # Trả lại pady gốc khi hiển thị đầy đủ (đồ thị to, cần khoảng cách thoáng hơn)
            self.pack_configure(pady=5)

    def switch_mode(self, collapsed=False):
        if collapsed:
            self.right_container.pack_forget()
        else:
            self.right_container.pack(side="left", fill="both", expand=True, padx=5)

    def update_real_data(self, usage_val, text_val):
        """Đồng bộ nạp số liệu cuộn và giữ màu viền đặc chủng khi render"""
        self.lbl_value.config(text=text_val)
        self.data_history.pop(0)
        self.data_history.append(usage_val)
        
        if hasattr(self, 'mini_graph'):
            # Đảm bảo các thuộc tính màu sắc trong instance đồ thị không bị ghi đè mất gốc
            self.mini_graph.face_color = self.graph_color_domain
            self.mini_graph.edge_color = self.graph_color_outline
            self.mini_graph.update_graph_only(self.mini_graph.grid_offset)


# ==============================================================================
#  MAIN WINDOW: QUẢN LÝ TAB, PHẦN CỨNG VÀ TRUYỀN THAM SỐ CHUẨN XỊN
# ==============================================================================
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Manager Pro")
        self.geometry("1100x700")
        self.configure(bg="#ffffff")
        
        self.is_collapsed = False
        self.is_icon_mode = False
        self.items = [] 
        
        self.current_offset = 0
        self.last_sync_time = time.time()
        
        # ----------------------------------------------------------------------
        #  1. THANH TAB ĐỈNH HỆ THỐNG
        # ----------------------------------------------------------------------
        self.top_tab_bar = tk.Frame(self, bg="#f3f3f3", height=40, bd=1, relief="groove")
        self.top_tab_bar.pack(side="top", fill="x")
        self.top_tab_bar.pack_propagate(False)
        
        self.btn_tab_proc = tk.Button(self.top_tab_bar, text="Processes", font=("Calibri Bold", 11),
                                      bg="#f3f3f3", fg="#000000", bd=0, activebackground="#ffffff",
                                      padx=20, cursor="hand2", command=self.switch_to_processes_tab)
        self.btn_tab_proc.pack(side="left", fill="y")
        
        self.btn_tab_res = tk.Button(self.top_tab_bar, text="Performance", font=("Calibri Bold", 11),
                                     bg="#ffffff", fg="#0078d4", bd=0, activebackground="#ffffff",
                                     padx=20, cursor="hand2", command=self.switch_to_resource_tab)
        self.btn_tab_res.pack(side="left", fill="y")
        
        # ----------------------------------------------------------------------
        #  2. KHUNG PROCESSES TAB (TẠM ẨN)
        # ----------------------------------------------------------------------
        self.processes_layout_frame = tk.Frame(self, bg="#ffffff")
        self.processes_view = ProcessesDetailView(self.processes_layout_frame)
        self.processes_view.pack(fill="both", expand=True)
        
        # ----------------------------------------------------------------------
        #  3. KHUNG PERFORMANCE/RESOURCE TAB (CHỨA SIDEBAR + ĐỒ THỊ)
        # ----------------------------------------------------------------------
        self.resource_layout_frame = tk.Frame(self, bg="#ffffff")
        self.resource_layout_frame.pack(side="bottom", fill="both", expand=True) 
        
        self.sidebar_frame = tk.Frame(self.resource_layout_frame, bg="#ffffff", width=250, bd=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # 🛠️ Border-right 2px cho sidebar — dùng 1 Frame mỏng riêng (Tkinter Frame không hỗ trợ
        # border từng cạnh như CSS, nên tách hẳn 1 thanh màu xám đặt sát bên phải sidebar_frame).
        self.sidebar_border = tk.Frame(self.resource_layout_frame, bg="#d9d9d9", width=1)
        self.sidebar_border.pack(side="left", fill="y")
        
        self.menu_items_container = tk.Frame(self.sidebar_frame, bg="#ffffff")
        self.menu_items_container.pack(fill="both", expand=True)
        
        self.main_frame = tk.Frame(self.resource_layout_frame, bg="#ffffff")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Khởi tạo CPU và RAM tĩnh lề trái
        self.item_cpu = SidebarItem(self.menu_items_container, "📊", "CPU", "0%", 40, 60, click_callback=self.handle_view_change)
        self.item_cpu.pack(fill="x", pady=5)
        self.items.append(self.item_cpu)
        
        self.item_ram = SidebarItem(self.menu_items_container, "🗲", "RAM", "0%", 40, 60, click_callback=self.handle_view_change)
        self.item_ram.pack(fill="x", pady=5)
        self.items.append(self.item_ram)
        
        self.item_cpu.set_active(True)
        
        self.cpu_view = CpuDetailView(self.main_frame)
        self.ram_view = RamDetailView(self.main_frame)
        self.cpu_view.pack(fill="both", expand=True)
        
        # ----------------------------------------------------------------------
        #  4. KHỞI TẠO PHÂN HỆ ĐĨA (DISK)
        # ----------------------------------------------------------------------
        self.disk_io_keys = []
        self.disk_views = {}
        self.disk_sidebar_items = {}
        self.last_disk_io = psutil.disk_io_counters(perdisk=True)
        
        try:
            disk_idx = 0
            for d_name in sorted(self.last_disk_io.keys()):
                if d_name.startswith("loop") or d_name.startswith("ram"): continue
                if "nvme" in d_name and "p" in d_name: continue
                if d_name.startswith("sd") and d_name[-1].isdigit(): continue
                
                self.disk_io_keys.append(d_name)
                display_label = f"Disk {disk_idx}"
                
                item_disk = SidebarItem(self.menu_items_container, "💽", display_label, "0%", 40, 60, 
                                        click_callback=self.handle_view_change, disk_id=d_name)
                item_disk.pack(fill="x", pady=5)
                
                self.disk_sidebar_items[d_name] = item_disk
                self.items.append(item_disk)
                
                self.disk_views[d_name] = DiskDetailView(self.main_frame, d_name)
                disk_idx += 1
        except Exception as e:
            print(f"Lỗi khởi tạo ổ đĩa ban đầu: {e}")

        # ----------------------------------------------------------------------
        #  5. KHỞI TẠO CARD ĐỒ HỌA (GPU)
        # ----------------------------------------------------------------------
        self.gpu_keys = []          
        self.gpu_views = {}         
        self.gpu_sidebar_items = {} 
        
        detected_gpus = self.detect_all_gpus_on_startup()
        gpu_idx = 0
        for gpu_info in detected_gpus:
            g_id = gpu_info["id"]
            self.gpu_keys.append(g_id)
            display_label = f"GPU {gpu_idx}"
            
            item_gpu = SidebarItem(self.menu_items_container, "📟", display_label, "0%", 40, 60, 
                                   click_callback=self.handle_view_change, disk_id=g_id)
            item_gpu.pack(fill="x", pady=5)
            
            self.gpu_sidebar_items[g_id] = item_gpu
            self.items.append(item_gpu)
            
            from GpuDetailView import GpuDetailView
            new_gpu_view = GpuDetailView(self.main_frame)
            new_gpu_view.lbl_gpu_model.config(text=gpu_info["model"]) 
            self.gpu_views[g_id] = new_gpu_view
            gpu_idx += 1

        # ----------------------------------------------------------------------
        #  6. KHỞI TẠO MẠNG (NETWORK)
        # ----------------------------------------------------------------------
        self.net_keys = []
        self.net_views = {}
        self.net_sidebar_items = {}
        self.last_net_io = psutil.net_io_counters(pernic=True)
        
        active_nets = sorted([k for k in self.last_net_io.keys() if k != 'lo' and not k.startswith('veth')])
        last_anchor = list(self.gpu_sidebar_items.values())[-1] if self.gpu_sidebar_items else self.item_ram
        
        for n_name in active_nets:
            self.net_keys.append(n_name)
            display_label = "Ethernet"
            if "wlan" in n_name or "wlp" in n_name:
                display_label = "Wi-Fi"
            elif "ppp" in n_name or "tailscale" in n_name:
                display_label = "VPN"
            display_label = display_label + " (" + n_name + ")"
            item_net = SidebarItem(self.menu_items_container, "🌐", display_label, "0 Kbps", 40, 60, 
                                   click_callback=self.handle_view_change, disk_id=n_name)
            item_net.pack(fill="x", pady=5, after=last_anchor)
            last_anchor = item_net
            
            self.net_sidebar_items[n_name] = item_net
            self.items.append(item_net)
            
            from NetDetailView import NetDetailView
            self.net_views[n_name] = NetDetailView(self.main_frame, net_name=n_name)

        self.global_sync_loop()
        self.bind("<Configure>", self.on_resize)

    def switch_to_processes_tab(self):
        self.btn_tab_proc.config(bg="#ffffff", fg="#0078d4")
        self.btn_tab_res.config(bg="#f3f3f3", fg="#000000")
        self.resource_layout_frame.pack_forget()
        self.processes_layout_frame.pack(fill="both", expand=True)

    def switch_to_resource_tab(self):
        self.btn_tab_res.config(bg="#ffffff", fg="#0078d4")
        self.btn_tab_proc.config(bg="#f3f3f3", fg="#000000")
        self.processes_layout_frame.pack_forget()
        self.resource_layout_frame.pack(fill="both", expand=True)

    # ----------------------------------------------------------------------
    #  ĐIỀU HƯỚNG CLICK SIDEBAR ĐỒNG BỘ ĐẦY ĐỦ THAM SỐ AN TOÀN
    # ----------------------------------------------------------------------
    def handle_view_change(self, clicked_item):
        for item in self.items:
            item.set_active(False)
        clicked_item.set_active(True)
        
        self.cpu_view.pack_forget()
        self.ram_view.pack_forget()
        for dv in self.disk_views.values(): dv.pack_forget()
        for gv in self.gpu_views.values(): gv.pack_forget()
        for nv in self.net_views.values(): nv.pack_forget()
            
        target_title = clicked_item.title_text
        if target_title == "CPU":
            self.cpu_view.pack(fill="both", expand=True)
        elif "RAM" in target_title:
            self.ram_view.pack(fill="both", expand=True)
        else:
            hw_id = clicked_item.disk_id
            if hw_id in self.disk_views:
                self.disk_views[hw_id].pack(fill="both", expand=True)
            elif hw_id in self.gpu_views:
                self.gpu_views[hw_id].pack(fill="both", expand=True)
            elif hw_id in self.net_views:
                self.net_views[hw_id].pack(fill="both", expand=True)

    # ----------------------------------------------------------------------
    #  LUỒNG ĐỒNG BỘ CHU KỲ NỀN 1S (TỐI ƯU THAM SỐ)
    # ----------------------------------------------------------------------
    def global_sync_loop(self):
        self.current_offset = (self.current_offset + 1) % 10
        now_time = time.time()
        time_delta = now_time - self.last_sync_time
        if time_delta <= 0: time_delta = 1.0
        
        # --- 1. ĐỒNG BỘ CPU ---
        current_cpu_pct = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        current_speed = round(freq.current / 1000, 2) if freq else 3.20
        self.item_cpu.update_real_data(current_cpu_pct, f"{int(current_cpu_pct)}%  {current_speed} GHz")
        self.cpu_view.receive_central_cpu_data(current_cpu_pct, current_speed)
        
        # --- 2. ĐỒNG BỘ RAM ---
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ram_percent = mem.percent
        in_use_gb = mem.used / (1024**3)
        available_gb = mem.available / (1024**3)
        
        total_raw_gb = mem.total / (1024**3)
        standard_sizes = [2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 256]
        hardware_total_gb = min(standard_sizes, key=lambda x: abs(x - total_raw_gb))
        if hardware_total_gb < total_raw_gb: hardware_total_gb = round(total_raw_gb, 1)
        
        ram_type = "DDR4"
        try:
            import os
            if os.getuid() == 0: 
                import subprocess
                proc = subprocess.Popen("dmidecode -t memory".split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                stdout, _ = proc.communicate()
                for line in stdout.split('\n'):
                    if "Type:" in line and "Detail" not in line:
                        type_str = line.split(":")[1].strip()
                        if type_str in ["DDR3", "DDR4", "DDR5", "LPDDR4"]:
                            ram_type = type_str
                            break
        except: pass

        cache_bytes = (mem.buffers + mem.cached) if hasattr(mem, 'buffers') else 0
        pct_cache = (cache_bytes / mem.total) * 100
        cache_gb = cache_bytes / (1024**3)
        committed_str = f"{(mem.used + swap.used)/(1024**3):.1f}/{(mem.total + swap.total)/(1024**3):.1f} GB"
        
        paged_pool_gb, non_paged_pool_gb = "N/A", "N/A"
        try:
            with open("/proc/meminfo", "r") as f:
                s_rec, s_unrec = 0, 0
                for line in f:
                    if line.startswith("SReclaimable:"): s_rec = int(line.split()[1]) * 1024
                    elif line.startswith("SUnreclaim:"): s_unrec = int(line.split()[1]) * 1024
                if s_rec > 0: paged_pool_gb = f"{s_rec / (1024**3):.1f} GB"
                if s_unrec > 0: non_paged_pool_gb = f"{s_unrec / (1024**3):.1f} GB"
        except: pass

        hardware_reserved_mb = int((hardware_total_gb - total_raw_gb) * 1024)
        if hardware_reserved_mb < 0: hardware_reserved_mb = 0
        hardware_reserved_str = f"{hardware_reserved_mb} MB" if hardware_reserved_mb > 0 else "0 MB"

        self.item_ram.update_real_data(ram_percent, f"{in_use_gb:.1f}/{hardware_total_gb:.0f} GB ({int(ram_percent)}%)")
        self.ram_view.receive_central_ram_data(ram_percent, pct_cache, in_use_gb, available_gb, cache_gb, committed_str, paged_pool_gb, non_paged_pool_gb, hardware_total_gb, ram_type, hardware_reserved_str, self.current_offset)
        try:
            current_raw_disks = psutil.disk_io_counters(perdisk=True)
            active_disks = []
            for k in current_raw_disks.keys():
                if k.startswith("loop") or k.startswith("ram"): continue
                if "nvme" in k and "p" in k: continue
                if k.startswith("sd") and k[-1].isdigit(): continue
                active_disks.append(k)
            
            active_disks = sorted(active_disks)
            
            # Nếu phát hiện có sự thay đổi (Cắm thêm hoặc rút ra)
            if active_disks != sorted(self.disk_io_keys):
                
                # TRƯỜNG HỢP 1: RÚT Ổ ĐĨA RA
                for d_name in list(self.disk_io_keys):
                    if d_name not in active_disks:
                        print(f"🔌 Phát hiện ổ đĩa bị rút ra: {d_name}")
                        # Kiểm tra nếu đang xem chính ổ đĩa bị rút này thì chuyển view về CPU chống trắng màn hình
                        if d_name in self.disk_views and self.disk_views[d_name].winfo_manager():
                            self.cpu_view.pack(fill="both", expand=True)
                        
                        # Hủy widget chi tiết bên phải
                        if d_name in self.disk_views:
                            self.disk_views[d_name].destroy()
                            del self.disk_views[d_name]
                        
                        # Hủy mục hiển thị trên Sidebar
                        if d_name in self.disk_sidebar_items:
                            item = self.disk_sidebar_items[d_name]
                            if item in self.items:
                                self.items.remove(item)
                            item.destroy()
                            del self.disk_sidebar_items[d_name]

                # TRƯỜNG HỢP 2: CẮM Ổ ĐĨA VÀO
                for d_name in active_disks:
                    if d_name not in self.disk_io_keys:
                        print(f"🔌 Phát hiện ổ đĩa mới được cắm vào: {d_name}")
                        
                        # Tạo view chi tiết mới găm vào main_frame (ẩn ngầm)
                        from DiskDetailView import DiskDetailView
                        self.disk_views[d_name] = DiskDetailView(self.main_frame, disk_name=d_name)
                        
                        # Khởi tạo item Sidebar mới
                        item_disk = SidebarItem(self.menu_items_container, "💽", "Disk TEMP", "0%", 40, 60, 
                                                click_callback=self.handle_view_change, disk_id=d_name)
                        self.disk_sidebar_items[d_name] = item_disk
                        self.items.append(item_disk)
                        
                        # Đồng bộ trạng thái co giãn của Sidebar
                        item_disk.switch_mode(collapsed=self.is_collapsed)
                        item_disk.set_compact_icon_mode(self.is_icon_mode)

                # CẬP NHẬT LẠI BIẾN QUẢN LÝ ĐĨA HỆ THỐNG
                self.disk_io_keys = active_disks
                
                # SẮP XẾP VÀ ĐỊNH VỊ LẠI VỊ TRÍ HIỂN THỊ TRÊN SIDEBAR (CPU > RAM > DISK 0 > DISK 1 > ...)
                # Đầu tiên gỡ tạm pack của toàn bộ các đĩa hiện có ra
                for d_name in self.disk_io_keys:
                    self.disk_sidebar_items[d_name].pack_forget()
                
                # Tiến hành pack lại theo đúng thứ tự mảng đã sắp xếp, găm ngay sau thanh RAM
                last_anchor = self.item_ram
                for idx, d_name in enumerate(self.disk_io_keys):
                    # Đổi lại tên hiển thị chuẩn số thứ tự tăng dần (Disk 0, Disk 1...)
                    self.disk_sidebar_items[d_name].lbl_title.config(text=f"Disk {idx}")
                    self.disk_sidebar_items[d_name].title_text = f"Disk {idx}"
                    
                    # Chèn khít ngay sau mục trước đó bằng thuộc tính after
                    self.disk_sidebar_items[d_name].pack(fill="x", pady=5, after=last_anchor)
                    last_anchor = self.disk_sidebar_items[d_name] # Dịch mốc neo xuống dưới cho đĩa kế tiếp

                self.menu_items_container.update()
                print("✅ Cập nhật cục bộ danh sách ổ đĩa thành công!")
                
                self.last_sync_time = now_time
                self.after(1000, self.global_sync_loop)
                return
        except Exception as e:
            print(f"Lỗi xử lý tháo lắp cục bộ ổ đĩa: {e}")
        try:
            current_disk_io = psutil.disk_io_counters(perdisk=True)
            
            # Khảo sát nhanh xem phân vùng root "/" đang nằm trên thiết bị nào để tìm System Disk
            root_device = ""
            for part in psutil.disk_partitions():
                if part.mountpoint == '/':
                    root_device = part.device # Ví dụ: /dev/nvme0n1p2 hoặc /dev/sda2
                    break

            for d_name in self.disk_io_keys:
                if d_name in current_disk_io and d_name in self.last_disk_io:
                    io_old = self.last_disk_io[d_name]
                    io_new = current_disk_io[d_name]
                    
                    # Tính toán tốc độ đọc ghi (MB/s) và % Active time
                    read_speed_mbs = ((io_new.read_bytes - io_old.read_bytes) / (1024**2)) / time_delta
                    write_speed_mbs = ((io_new.write_bytes - io_old.write_bytes) / (1024**2)) / time_delta
                    total_speed_mbs = read_speed_mbs + write_speed_mbs
                    
                    busy_delta_ms = io_new.busy_time - io_old.busy_time
                    active_pct = (busy_delta_ms / (time_delta * 1000)) * 100
                    active_pct = min(max(active_pct, 0), 100)
                    
                    ops_delta = (io_new.read_count + io_new.write_count) - (io_old.read_count + io_old.write_count)
                    time_spent_delta = (io_new.read_time + io_new.write_time) - (io_old.read_time + io_old.write_time)
                    avg_response_ms = time_spent_delta / ops_delta if ops_delta > 0 else 0.0
                    
                    # 1. LẤY DUNG LƯỢNG VẬT LÝ (CAPACITY)
                    capacity_str = "N/A"
                    try:
                        sys_path = f"/sys/block/{d_name}/size"
                        if os.path.exists(sys_path):
                            with open(sys_path, "r") as f_sz:
                                sectors = int(f_sz.read().strip())
                                capacity_str = f"{(sectors * 512) / (1024**3):.1f} GB"
                    except: pass
                    
                    # 2. 🛠️ LẤY MODEL Ổ CỨNG THẬT TỪ KERNEL LINUX
                    model_str = d_name.upper() # Fallback mặc định
                    try:
                        model_path = f"/sys/block/{d_name}/device/model"
                        if os.path.exists(model_path):
                            with open(model_path, "r") as f_md:
                                model_str = f_md.read().strip()
                    except: pass

                    # 3. 🛠️ KIỂM TRA SYSTEM DISK THẬT
                    is_system_disk = "No"
                    if root_device and d_name in root_device:
                        is_system_disk = "Yes"

                    # 4. 🛠️ QUÉT DANH SÁCH CÁC PHÂN VÙNG CON
                    sub_parts = []
                    for k in sorted(current_disk_io.keys()):
                        if k == d_name:
                            continue
                        # Lọc phân vùng con: nvme0n1pX thuộc nvme0n1, hoặc sdaX thuộc sda
                        if ("nvme" in d_name and d_name in k and "p" in k) or (d_name.startswith("sd") and k.startswith(d_name)):
                            sub_parts.append(k)
                    partitions_str = ", ".join(sub_parts) if sub_parts else "None"
                    form_factor = "SSD/HDD"
                    if "nvme" in d_name.lower():
                        form_factor = "NVMe"
                    else:
                        try:
                            removable_path = f"/sys/block/{d_name}/removable"
                            if os.path.exists(removable_path):
                                with open(removable_path, "r") as f_rm:
                                    if f_rm.read().strip() == "1":
                                        form_factor = "USB / Removable"
                        except:
                            pass
                    # Cập nhật hiển thị Sidebar
                    sidebar_text = f"{int(active_pct)}%" if active_pct > 0 else "0%"
                    self.disk_sidebar_items[d_name].update_real_data(active_pct, sidebar_text)
                    self.disk_views[d_name].receive_central_disk_data(
                        active_pct=active_pct, 
                        read_speed_mbs=read_speed_mbs, 
                        write_speed_mbs=write_speed_mbs, 
                        total_speed_mbs=total_speed_mbs,
                        avg_response_ms=avg_response_ms,
                        capacity_str=capacity_str,
                        model_str=model_str,
                        is_system_disk=is_system_disk,
                        partitions_str=partitions_str,
                        form_factor_str=form_factor,
                        current_offset=self.current_offset
                    )
            
            self.last_disk_io = current_disk_io
        except Exception as e:
            print(f"Lỗi đồng bộ dữ liệu đĩa: {e}")
        try:
            for g_id in self.gpu_keys:
                # Quét lấy chỉ số sống thời gian thực của GPU tương ứng
                g_data = self.query_live_gpu_data(g_id)
                
                # Cập nhật thông số % tải lên Sidebar Item tương ứng
                sidebar_display_text = f"{int(g_data['util_3d'])}%"
                self.gpu_sidebar_items[g_id].update_real_data(g_data['util_3d'], sidebar_display_text)
                
                # Bắn gói dữ liệu đa đồ thị sang trang chi tiết GpuDetailView.py
                self.gpu_views[g_id].receive_central_gpu_data(
                    util_3d=g_data["util_3d"],
                    util_copy=g_data["util_copy"],
                    util_decode=g_data["util_decode"],
                    util_proc=g_data["util_proc"],
                    ded_used=g_data["ded_used"],
                    ded_total=g_data["ded_total"],
                    shr_used=g_data["shr_used"],
                    shr_total=g_data["shr_total"],
                    temp=g_data["temp"],
                    current_offset=self.current_offset
                )
                # Đổ nốt Driver tĩnh lên giao diện nếu chưa được load
                if hasattr(self.gpu_views[g_id], 'lbl_driver_val'):
                    self.gpu_views[g_id].lbl_driver_val.config(text=g_data["driver"])
        except Exception as e:
            print(f"Lỗi đồng bộ dữ liệu đồ họa GPU: {e}")
        try:
            current_raw_nets = psutil.net_io_counters(pernic=True)
            live_nets = sorted([k for k in current_raw_nets.keys() if k != 'lo' and not k.startswith('veth')])
            
            if live_nets != sorted(self.net_keys):
                # TRƯỜNG HỢP RÚT CARD MẠNG
                for n_name in list(self.net_keys):
                    if n_name not in live_nets:
                        print(f"🔌 Rút card mạng: {n_name}")
                        if n_name in self.net_views and self.net_views[n_name].winfo_manager():
                            # Nếu đang xem card mạng bị rút -> Ưu tiên quay về card mạng còn lại
                            remains = [k for k in live_nets if k in self.net_views]
                            if remains:
                                self.net_views[remains[0]].pack(fill="both", expand=True)
                            elif self.gpu_keys: # Không còn mạng, nhảy về GPU
                                self.gpu_views[self.gpu_keys[-1]].pack(fill="both", expand=True)
                            else: # Không có GPU, nhảy về Disk
                                self.disk_views[self.disk_io_keys[-1]].pack(fill="both", expand=True)
                        
                        if n_name in self.net_views:
                            self.net_views[n_name].destroy()
                            del self.net_views[n_name]
                        if n_name in self.net_sidebar_items:
                            item = self.net_sidebar_items[n_name]
                            if item in self.items: self.items.remove(item)
                            item.destroy()
                            del self.net_sidebar_items[n_name]

                # TRƯỜNG HỢP CẮM THÊM CARD MẠNG (USB Wi-Fi)
                for n_name in live_nets:
                    if n_name not in self.net_keys:
                        print(f"🔌 Cắm thêm card mạng mới: {n_name}")
                        from NetDetailView import NetDetailView
                        self.net_views[n_name] = NetDetailView(self.main_frame, net_name=n_name)
                        
                        display_label = "Ethernet"
                        if "wlan" in n_name or "wlp" in n_name:
                            display_label = "Wi-Fi"
                        elif "ppp" in n_name or "tailscale" in n_name:
                            display_label = "VPN"
                        display_label = display_label + " (" + n_name + ")"
                        item_net = SidebarItem(self.menu_items_container, "🌐", display_label, "0 Kbps", 40, 60, 
                                               click_callback=self.handle_view_change, disk_id=n_name)
                        self.net_sidebar_items[n_name] = item_net
                        self.items.append(item_net)
                        item_net.switch_mode(collapsed=self.is_collapsed)
                        item_net.set_compact_icon_mode(self.is_icon_mode)

                self.net_keys = live_nets
                
                # Định vị sắp xếp lại vị trí neo chuẩn sau GPU
                for n_name in self.net_keys: self.net_sidebar_items[n_name].pack_forget()
                last_anchor = list(self.gpu_sidebar_items.values())[-1] if self.gpu_sidebar_items else self.item_ram
                for n_name in self.net_keys:
                    self.net_sidebar_items[n_name].pack(fill="x", pady=5, after=last_anchor)
                    last_anchor = self.net_sidebar_items[n_name]
                self.menu_items_container.update()

            # --- ĐỒNG BỘ DỮ LIỆU TỐC ĐỘ MẠNG THỜI GIAN THỰC ---
            time_delta = now_time - self.last_sync_time if (now_time - self.last_sync_time) > 0 else 1.0
            for n_name in self.net_keys:
                if n_name in current_raw_nets and n_name in self.last_net_io:
                    net_old = self.last_net_io[n_name]
                    net_new = current_raw_nets[n_name]
                    
                    # Tính toán tốc độ KB/s
                    send_speed_kbs = ((net_new.bytes_sent - net_old.bytes_sent) / 1024) / time_delta
                    recv_speed_kbs = ((net_new.bytes_recv - net_old.bytes_recv) / 1024) / time_delta
                    
                    # Cập nhật thông số tóm tắt lên Sidebar
                    total_bps = (send_speed_kbs + recv_speed_kbs) * 1024 * 8
                    sidebar_text = f"{total_bps/1000000:.1f} Mbps" if total_bps >= 1000000 else f"{total_bps/1000:.0f} Kbps"
                    self.net_sidebar_items[n_name].update_real_data(max(send_speed_kbs, recv_speed_kbs), sidebar_text)
                    
                    # 🛠️ LAZY RENDERING: Chỉ vẽ đồ thị lớn nếu đang mở xem tab mạng này
                    if self.net_views[n_name].winfo_manager():
                        self.net_views[n_name].receive_central_net_data(send_speed_kbs, recv_speed_kbs, self.current_offset)
            
            self.last_net_io = current_raw_nets
        except Exception as e:
            print(f"Lỗi đồng bộ phân hệ Network: {e}")
        self.last_sync_time = now_time
        self.after(1000, self.global_sync_loop)

    def detect_all_gpus_on_startup(self):
        gpus = []
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
            if output:
                for idx, name in enumerate(output.split('\n')): gpus.append({"id": f"NVIDIA_{idx}", "brand": "NVIDIA", "model": name.strip()})
        except: pass
        try:
            if os.path.exists("/sys/class/drm"):
                for card in sorted([d for d in os.listdir("/sys/class/drm") if d.startswith("card") and not "-" in d]):
                    if os.path.exists(f"/sys/class/drm/{card}/device/gpu_busy_percent"):
                        gpus.append({"id": f"AMD_{card}", "brand": "AMD", "model": f"AMD Radeon Graphics ({card.upper()})"})
        except: pass
        if not gpus: gpus.append({"id": "FALLBACK_GPU", "brand": "Generic", "model": "Intel HD Graphics / Generic GPU"})
        return gpus

    def query_live_gpu_data(self, gpu_id):
        data = {"util_3d": 0, "util_copy": 0, "util_decode": 0, "util_proc": 0, "ded_used": 0.0, "ded_total": 0.0, "shr_used": 0.0, "shr_total": 0.0, "temp": 0, "driver": "N/A"}
        data["shr_total"] = (psutil.virtual_memory().total / (1024**3)) * 0.5
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "Shmem:" in line: data["shr_used"] = int(line.split()[1]) / (1024**2); break
        except: data["shr_used"] = 0.05
        if gpu_id.startswith("NVIDIA"):
            try:
                idx = gpu_id.split("_")[1]
                out = subprocess.check_output(["nvidia-smi", f"--id={idx}", "--query-gpu=utilization.gpu,utilization.memory,utilization.decoder,utilization.encoder,memory.used,memory.total,temperature.gpu,driver_version", "--format=csv,noheader,nounits"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
                if out:
                    parts = [p.strip() for p in out.split(",")]
                    data["util_3d"], data["util_copy"], data["util_decode"], data["util_proc"] = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    data["ded_used"], data["ded_total"], data["temp"], data["driver"] = float(parts[4])/1024, float(parts[5])/1024, int(parts[6]), parts[7]
            except: pass
        elif gpu_id.startswith("AMD"):
            try:
                card_name = gpu_id.split("_")[1]
                amd_base = f"/sys/class/drm/{card_name}/device"
                if os.path.exists(amd_base):
                    with open(f"{amd_base}/gpu_busy_percent", "r") as f: gpu_load = int(f.read().strip()); data["util_3d"] = gpu_load
                    with open(f"{amd_base}/mem_info_vram_used", "r") as f: data["ded_used"] = int(f.read().strip()) / (1024**3)
                    with open(f"{amd_base}/mem_info_vram_total", "r") as f: data["ded_total"] = int(f.read().strip()) / (1024**3)
                    data["util_copy"], data["util_decode"], data["util_proc"] = gpu_load//2, gpu_load//4, gpu_load//5
                    try:
                        with open(f"{amd_base}/hwmon/hwmon0/temp1_input", "r") as f: data["temp"] = int(f.read().strip()) // 1000
                    except: pass
                    data["driver"] = "AMD DRM Open Source Driver"
            except: pass
        return data

    def on_resize(self, event):
        if event.widget == self:
            current_width = event.width
            print(current_width)
            SizeCollapse = 950
            if current_width < SizeCollapse and not self.is_collapsed:
                self.sidebar_frame.config(width=60)
                for item in self.items: item.switch_mode(collapsed=True)
                for item in self.items: item.set_compact_icon_mode(True)
                self.is_collapsed = True
                self.is_icon_mode = True
            elif current_width >= SizeCollapse and self.is_collapsed:
                self.sidebar_frame.config(width=250)
                for item in self.items: item.switch_mode(collapsed=False)
                for item in self.items: item.set_compact_icon_mode(False)
                self.is_collapsed = False
                self.is_icon_mode = False

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()