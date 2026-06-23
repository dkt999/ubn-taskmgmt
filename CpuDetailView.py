import tkinter as tk
from tkinter import ttk
import psutil
import time
import json
import os
from PIL import Image, ImageDraw, ImageTk, ImageFont

# 🛠️ ĐÃ BỎ MATPLOTLIB/NUMPY — Dùng Pillow để vẽ đồ thị ra ảnh rồi nhúng vào Canvas, nhẹ và
# nhanh hơn matplotlib rất nhiều (mỗi CpuGraphCanvas trước đây khởi tạo riêng 1 Figure rất nặng
# RAM/CPU khi mở nhiều đồ thị cùng lúc, ví dụ chế độ Logical Cores có thể tới 16-32 đồ thị).
# Để có nét mượt (Tkinter Canvas vector không hỗ trợ antialias, vẽ trực tiếp bị răng cưa),
# ta vẽ ảnh ở độ phân giải cao hơn (supersample) bằng PIL.ImageDraw rồi downscale bằng
# Image.resize(LANCZOS) để có hiệu ứng antialias, sau đó hiển thị qua PhotoImage trên Canvas.

class CpuGraphCanvas(tk.Frame):
    def __init__(self, parent, click_callback, history_data, is_logical=False, width=200, height=120,
                 face_color="#e6f0fa", edge_color="#0078d4", is_disk_transfer=False, component = "None"):
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.click_callback = click_callback
        self.is_logical = is_logical
        self.data_history = history_data
        self.grid_offset = 0
        self.face_color = face_color
        self.edge_color = edge_color
        self.is_disk_transfer = is_disk_transfer
        self.component = component
        self.peak_val = 100  # Dùng cho DiskDetailView đọc nhãn peak bên phải
        self.SS = 3  # Hệ số supersample để vẽ mượt (antialias) qua PIL rồi downscale

        # Canvas chỉ dùng làm khung hiển thị ảnh PIL + bắt sự kiện click
        self.canvas = tk.Canvas(self, bg="#ffffff", highlightthickness=0, width=width, height=height)
        self.canvas.pack(fill="both", expand=True)
        self._photo = None          # Giữ reference PhotoImage để tránh bị GC thu hồi
        self._image_id = None

        self.canvas.bind("<Button-1>", lambda event: self.click_callback())
        self.canvas.bind("<Configure>", self._on_resize)

        self._redraw_job = None
        self._font_size = 12  # cỡ chữ mong muốn, tính theo px thật (chưa nhân SS)
        try:
            self._font = ImageFont.truetype("DejaVuSans.ttf", self._font_size * self.SS)
        except Exception:
            self._font = ImageFont.load_default() 

    def get_nice_scale(self, max_val):
        """Trả về mốc tròn gần nhất phía trên max_val, giống Windows Task Manager."""
        steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000]
        for s in steps:
            if max_val <= s:
                return s
        decade = 10 ** len(str(int(max_val)))
        return decade

    def _on_resize(self, event):
        # Tránh vẽ lại quá dồn dập khi đang kéo giãn cửa sổ
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(10, self.draw_chart)

    def update_graph_only(self, current_offset):
        self.grid_offset = current_offset
        self.draw_chart()

    def _flatten_history(self):
        all_vals = []
        for item in self.data_history:
            if isinstance(item, (list, tuple)):
                all_vals.extend(item)
            else:
                all_vals.append(item)
        return all_vals

    def draw_chart(self):
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 2 or h <= 2:
            return

        SS = self.SS
        img = Image.new("RGB", (w * SS, h * SS), "#ffffff")
        draw = ImageDraw.Draw(img)
        # --- Xác định giới hạn trục Y giống setup_axes() trước đây ---
        if self.is_disk_transfer:
            all_vals = self._flatten_history()
            raw_max = max(all_vals + [0.1])
            nice_max = self.get_nice_scale(raw_max)
            self.peak_val = nice_max
            y_min, y_max = 0.0, nice_max
        elif self.component == "Network":
            # 🛠️ Minigraph Network (sidebar) dùng giá trị Kbps thô (không phải %), nên auto-scale
            # giống disk transfer thay vì cố định 100 — tránh bị kẹp trần khi tốc độ > 100 Kbps.
            all_vals = self._flatten_history()
            raw_max = max(all_vals + [0.1])
            nice_max = self.get_nice_scale(raw_max)
            self.peak_val = nice_max
            y_min, y_max = 0.0, nice_max
        else:
            # CPU/RAM/Disk active%/GPU: luôn là % cố định 0-100, không cần auto-scale
            y_min, y_max = 0.0, 100.0

        pad = SS  # lề 1px (đã nhân SS) để viền không bị cắt
        plot_w = max(1, w * SS - 2 * pad)
        line_w = max(1, SS)  # độ dày nét ~1px sau khi downscale (tính trước để chừa khoảng hở đáy)
        # 🛠️ Chừa 1 khoảng hở = line_w giữa đáy vùng vẽ dữ liệu và viền dưới, để đường line/area
        # không bao giờ đè đúng lên hàng pixel của viền (gây cảm giác cạnh dưới dày/mất nét).
        box_h = max(1, h * SS - 2 * pad)          # chiều cao toàn khung kể cả viền

        plot_h = max(1, box_h - 2)

        def x_to_px(i, n):
            if n <= 1:
                return pad
            return pad + (i / (n - 1)) * plot_w

        def y_to_px(val):
            val = min(max(val, y_min), y_max)
            ratio = (val - y_min) / (y_max - y_min) if y_max > y_min else 0
            return pad + plot_h - ratio * plot_h

        # --- Lưới ngang mờ cố định (25%/50%/75%) ---
        for pct in (0.25, 0.50, 0.75):
            y_px = y_to_px(y_max * pct)
            draw.line([(pad, y_px), (pad + plot_w, y_px)], fill="#f0f0f0", width=SS)

        # --- Lưới dọc cuộn động chạy lùi ---
        step_x = plot_w / 10
        start_x = pad - (self.grid_offset * (step_x / 10))
        while start_x <= pad + plot_w:
            if start_x >= pad:
                draw.line([(start_x, pad), (start_x, pad + plot_h)], fill="#f0f0f0", width=SS)
            start_x += step_x

        n = len(self.data_history)

        if self.is_disk_transfer:
            y_read = [item[0] for item in self.data_history]
            y_write = [item[1] for item in self.data_history]

            read_pts = [(x_to_px(i, n), y_to_px(val)) for i, val in enumerate(y_read)]
            if len(read_pts) >= 2:
                draw.line(read_pts, fill=self.edge_color, width=line_w, joint="curve")

            # PIL không có dash sẵn, tự vẽ nét đứt cho write speed
            write_pts = [(x_to_px(i, n), y_to_px(val)) for i, val in enumerate(y_write)]
            if len(write_pts) >= 2:
                dash_len, gap_len = 5 * SS, 4 * SS
                self._draw_dashed_line(draw, write_pts, self.edge_color, line_w, dash_len, gap_len)

            all_vals = self._flatten_history()
            raw_max = max(all_vals + [0.0])
            if raw_max > 0:
                y_px = y_to_px(raw_max)
                draw.line([(pad, y_px), (pad + plot_w, y_px)], fill=self.edge_color, width=line_w)
                text_val = ""
                if self.component == "None":
                    if raw_max >= 1000.0:
                        text_val = f"{raw_max/1024:.1f} GB/s" if raw_max % 1024 != 0 else f"{int(raw_max/1024)} GB/s"
                    elif raw_max >= 1.0:
                        text_val = f"{raw_max:.1f} MB/s"
                    else:
                        text_val = f"{int(raw_max * 1024)} KB/s"
                else:
                    net_kbps = raw_max * 8
                    if net_kbps >= 1000000: # Lớn hơn hoặc bằng 1 Gbps
                        text_val = f"{net_kbps / 1000000:.1f} Gbps"
                    elif net_kbps >= 1000:  # Lớn hơn hoặc bằng 1 Mbps
                        text_val = f"{net_kbps / 1000:.1f} Mbps"
                    else:
                        text_val = f"{int(net_kbps)} Kbps"
                        if net_kbps == 0: text_val = "0 Kbps"
                near_top = (y_max - raw_max) / y_max < 0.2 if y_max else False
                text_y = y_px + 5 * SS if near_top else y_px - 20 * SS
                try:
                    draw.text((pad + plot_w - 2 * SS, text_y), text_val, fill="#555555",
                            font=self._font, anchor="ra")
                except TypeError:
                    tw = draw.textlength(text_val, font=self._font) if hasattr(draw, "textlength") else len(text_val) * 5 * SS
                    draw.text((pad + plot_w - 2 * SS - tw, text_y), text_val, fill="#555555", font=self._font)
        else:
            # Biểu đồ miền truyền thống cho CPU/RAM (fill_between tương đương polygon)
            y_vals = list(self.data_history)
            poly_pts = [(x_to_px(i, n), y_to_px(val - 0.1)) for i, val in enumerate(y_vals)]
            if len(poly_pts) >= 2:
                closed = poly_pts + [(x_to_px(n + 1, n), pad + box_h), (x_to_px(0, n + 1), pad + box_h)]
                draw.polygon(closed, fill=self.face_color)
                draw.line(poly_pts, fill=self.edge_color, width=line_w, joint="curve")

        # --- Viền hộp đồ thị (spines) ---
        # Vẽ đủ 4 cạnh; nhờ đã chừa khoảng hở (box_h > plot_h) ở bước tính phía trên,
        # cạnh dưới giờ nằm tách biệt hẳn khỏi vùng dữ liệu, không còn bị chồng/mất nét.
        #draw.rectangle([pad, pad, pad + plot_w, pad + box_h], outline=self.edge_color, width=line_w)
        draw.rectangle([pad, pad, pad + plot_w, pad + box_h], outline=self.edge_color, width=4)

        # --- Downscale antialias rồi đẩy vào Canvas ---
        img = img.resize((w, h), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)
        if self._image_id is None:
            self._image_id = c.create_image(0, 0, anchor="nw", image=self._photo)
        else:
            c.itemconfig(self._image_id, image=self._photo)

    @staticmethod
    def _draw_dashed_line(draw, points, fill, width, dash_len, gap_len):
        """Vẽ đường nét đứt thủ công qua một dãy điểm liên tiếp (PIL không hỗ trợ dash sẵn)."""
        if len(points) < 2:
            return
        remaining = dash_len
        drawing = True
        for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
            seg_dx, seg_dy = x1 - x0, y1 - y0
            seg_len = (seg_dx ** 2 + seg_dy ** 2) ** 0.5
            if seg_len == 0:
                continue
            travelled = 0.0
            cx, cy = x0, y0
            while travelled < seg_len:
                step = min(remaining, seg_len - travelled)
                nx = cx + seg_dx * (step / seg_len)
                ny = cy + seg_dy * (step / seg_len)
                if drawing:
                    draw.line([(cx, cy), (nx, ny)], fill=fill, width=width)
                cx, cy = nx, ny
                travelled += step
                remaining -= step
                if remaining <= 0:
                    drawing = not drawing
                    remaining = dash_len if drawing else gap_len

    def on_destroy(self, event=None):
        """Giữ lại cho tương thích API cũ — không còn Figure matplotlib cần dọn dẹp."""
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
        self.grid_rowconfigure(0, weight=0)  # Header giữ nguyên
        self.grid_rowconfigure(1, weight=0)  # Header giữ nguyên
        self.grid_rowconfigure(2, weight=1)  # Graph container chiếm trọn không gian trống còn lại
        self.grid_rowconfigure(3, weight=0)  # Thông số dưới đáy giữ nguyên

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
        # 1. Hủy Widget cũ (không còn Figure matplotlib cần plt.close)
        for g in self.graphs:
            g.destroy()
        self.graphs.clear()

        if self.view_mode == "overall":
            # 🛠️ BƯỚC KHÔI PHỤC QUAN TRỌNG: Xóa sạch cấu hình Grid nhiều ô của Logical cũ
            for c in range(12):
                self.graph_container.grid_columnconfigure(c, weight=1 if c == 0 else 0)
            for r in range(12):
                self.graph_container.grid_rowconfigure(r, weight=1 if r == 0 else 0)

            g = CpuGraphCanvas(self.graph_container, click_callback=self.toggle_view_mode, history_data=self.overall_history, is_logical=False)

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