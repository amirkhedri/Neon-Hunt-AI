import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from pathlib import Path

try:
    from PIL import Image, ImageTk
except Exception:  # Pillow fallback
    Image = None
    ImageTk = None

from neon_hunt.config import CELL_SIZE, GRID_PADDING, WINDOW_WIDTH, WINDOW_HEIGHT, AGENT_PLAYER, AGENT_MONSTER
from neon_hunt.levels import LEVELS
from neon_hunt.state import GameState
from neon_hunt.engine import (
    legal_moves_basic,
    transition_basic,
    terminal_result,
    bfs_distance,
    escape_routes,
)
from neon_hunt.ai import instructor_monster_ai
from neon_hunt.ai import student_player_ai

BG = "#050714"
PANEL = "#0a1023"
PANEL_SOFT = "#0d1430"
SECTION = "#0c1329"
CARD_INNER = "#09101f"
BORDER = "#203763"
DIVIDER = "#1b2d52"
AMBER = "#ffad24"
CYAN = "#00f5ff"
PINK = "#ff2bd6"
PURPLE = "#8b5cf6"
GOLD = "#ffd166"
RED = "#ff3864"
GREEN = "#56f39a"
WHITE = "#ecfbff"
MUTED = "#8ea4cf"
MUTED2 = "#607299"


class NeonHuntEscapeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Neon Hunt: Escape Agent Challenge — Instructor Edition")

        # V26: fixed 1100px width, restored 840px height.
        # Centering is done later using Windows work area, so taskbar is ignored.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        target_w = 1100
        target_h = 840
        self.window_width = min(target_w, max(1020, screen_w - 80))
        self.window_height = min(target_h, max(760, screen_h - 120))
        self.geometry(f"{self.window_width}x{self.window_height}")
        self.configure(bg=BG)
        self.resizable(False, False)

        max_rows = max(level["rows"] for level in LEVELS)
        max_cols = max(level["cols"] for level in LEVELS)
        margin_x = 16
        right_panel_w = 430
        gap = 12
        header_h = 58
        action_h = 52
        spare_h = 44
        left_available = self.window_width - right_panel_w - gap - 2 * margin_x
        board_height_available = self.window_height - header_h - action_h - spare_h
        # Prefer 54px cells for a rich Level 4 board, but shrink safely on smaller screens.
        self.cell_size = int(
            max(
                42,
                min(
                    54,
                    (left_available - GRID_PADDING - 10) // max_cols,
                    (board_height_available - GRID_PADDING - 10) // max_rows,
                ),
            )
        )

        self.level_index = 0
        self.state = GameState.from_level(LEVELS[self.level_index])
        self.player_control = tk.StringVar(value="Human")
        self.player_depth = tk.IntVar(value=4)
        self.player_alpha_beta = tk.BooleanVar(value=True)
        self.monster_difficulty = tk.StringVar(value="Easy")
        self.show_heatmap = tk.BooleanVar(value=False)
        self.show_ghost = tk.BooleanVar(value=True)
        self.autoplay_running = False
        self.speed_levels = [1, 2, 4]
        self.speed_index = 1
        self.speed_label = tk.StringVar(value="2x")
        self.speed_buttons = {}

        self.message = "Goal: escape or survive."
        self.game_over = False
        self.overlay = None
        self.player_info = {}
        self.monster_info = {}
        self.ghost_path = []
        self.heat_scores = {}
        self.position_history = [self.state.player]
        self.loop_warning = None
        self.loop_cells = []
        self.animating = False
        self.player_facing = "DOWN"
        self.monster_facing = "DOWN"
        self.character_images = {}
        self.ui_images = {}

        self._load_fonts()
        self._load_character_images()
        self._load_visual_assets()
        self._build_ui()

        self.bind("<Up>", lambda e: self.human_player_move("UP"))
        self.bind("<Down>", lambda e: self.human_player_move("DOWN"))
        self.bind("<Left>", lambda e: self.human_player_move("LEFT"))
        self.bind("<Right>", lambda e: self.human_player_move("RIGHT"))
        self.monster_difficulty.set("Easy")
        self._center_window()
        self.after(80, self._center_window)
        self.after(250, self.render)

    def _center_window(self):
        """Center the fixed-size window in the usable desktop area.

        Uses Windows work area when available so taskbar is not counted. A small
        upward nudge prevents the window from visually feeling attached to the
        taskbar on Windows laptops.
        """
        try:
            self.update_idletasks()
            actual_w = max(self.window_width, self.winfo_width())
            actual_h = max(self.window_height, self.winfo_height())

            left = top = 0
            right = self.winfo_screenwidth()
            bottom = self.winfo_screenheight()

            try:
                import ctypes
                from ctypes import wintypes
                rect = wintypes.RECT()
                SPI_GETWORKAREA = 0x0030
                ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
                if ok:
                    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
            except Exception:
                pass

            work_w = max(1, right - left)
            work_h = max(1, bottom - top)
            x = left + max(0, (work_w - actual_w) // 2)
            y = top + max(0, (work_h - actual_h) // 2)
            y = max(top, y - 10)
            self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
            self.lift()
        except Exception:
            pass

    def _load_fonts(self):
        available = set(tkfont.families())

        def choose(candidates, size, weight="normal"):
            for name in candidates:
                if name in available:
                    return (name, size, weight)
            return ("Consolas", size, weight)

        self.font_title = choose(["Orbitron", "Eurostile", "Consolas"], 28, "bold")
        self.font_subtitle = choose(["Consolas", "Courier New"], 12, "normal")
        self.font_header = choose(["Orbitron", "Consolas"], 19, "bold")
        self.font_section = choose(["Orbitron", "Consolas"], 10, "bold")
        self.font_label = choose(["Consolas", "Courier New"], 10, "bold")
        self.font_body = choose(["Consolas", "Courier New"], 10, "normal")
        self.font_small = choose(["Consolas", "Courier New"], 8, "normal")
        self.font_pixel = choose(["Press Start 2P", "VT323", "Fixedsys", "Terminal", "Courier New", "Consolas"], 10, "bold")
        self.font_pixel_small = choose(["Press Start 2P", "VT323", "Fixedsys", "Terminal", "Courier New", "Consolas"], 9, "bold")
        self.font_button = choose(["Press Start 2P", "VT323", "Fixedsys", "Terminal", "Courier New", "Consolas"], 9, "bold")

    def _load_png(self, path, size=None):
        """Load a PNG as a Tk image, optionally resized.

        Tkinter's native PhotoImage cannot do smooth arbitrary resizing. Pillow is
        used when available so board assets can scale with self.cell_size. If Pillow is
        unavailable, the original PNG is loaded as a fallback.
        """
        try:
            if Image is not None and ImageTk is not None:
                img = Image.open(path).convert("RGBA")
                if size is not None:
                    img = img.resize(size, Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            return tk.PhotoImage(file=str(path))
        except Exception:
            return None

    def _load_centered_sprite(self, path):
        """Crop transparent padding and center the visible character in one cell.

        Some generated sprites have uneven transparent margins, so resizing the
        whole PNG makes the character appear off-center. This method crops the
        alpha bounding box, scales the visible body to fit, then pastes it into a
        transparent cell-sized canvas centered on both axes.
        """
        try:
            if Image is None or ImageTk is None:
                return tk.PhotoImage(file=str(path))

            src = Image.open(path).convert("RGBA")
            alpha = src.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                src = src.crop(bbox)

            target = max(28, self.cell_size - 10)
            scale = min(target / max(1, src.width), target / max(1, src.height))
            new_size = (max(1, int(src.width * scale)), max(1, int(src.height * scale)))
            src = src.resize(new_size, Image.LANCZOS)

            cell = Image.new("RGBA", (self.cell_size, self.cell_size), (0, 0, 0, 0))
            x = (self.cell_size - src.width) // 2
            y = (self.cell_size - src.height) // 2
            cell.alpha_composite(src, (x, y))
            return ImageTk.PhotoImage(cell)
        except Exception:
            return None

    def _load_character_images(self):
        asset_dir = Path(__file__).resolve().parent / "assets" / "characters"
        mapping = {
            ("player", "UP"): "hacker_up.png",
            ("player", "DOWN"): "hacker_down.png",
            ("player", "LEFT"): "hacker_left.png",
            ("player", "RIGHT"): "hacker_right.png",
            ("monster", "UP"): "beast_up.png",
            ("monster", "DOWN"): "beast_down.png",
            ("monster", "LEFT"): "beast_left.png",
            ("monster", "RIGHT"): "beast_right.png",
        }
        for key, filename in mapping.items():
            path = asset_dir / filename
            self.character_images[key] = self._load_centered_sprite(path)

    def _load_visual_assets(self):
        asset_dir = Path(__file__).resolve().parent / "assets"
        mapping = {
            "tile_walkable": asset_dir / "tiles" / "tile_walkable.png",
            "tile_blocked": asset_dir / "tiles" / "tile_blocked.png",
            "tile_danger": asset_dir / "tiles" / "tile_danger.png",
            "halo_player": asset_dir / "effects" / "halo_player_cyan.png",
            "halo_monster": asset_dir / "effects" / "halo_monster_red.png",
            "wall_block": asset_dir / "obstacles" / "cyber_block.png",
            "wall_gate": asset_dir / "obstacles" / "electric_gate.png",
            "wall_holo": asset_dir / "obstacles" / "holographic_barrier.png",
            "wall_fire_h": asset_dir / "obstacles" / "neon_firewall_horizontal.png",
            "wall_fire_v": asset_dir / "obstacles" / "neon_firewall_vertical.png",
            "action_bar": asset_dir / "ui" / "action_bar_wide.png",
            "action_button_a": asset_dir / "ui" / "button_frame_a.png",
            "action_button_b": asset_dir / "ui" / "button_frame_b.png",
            "action_button_c": asset_dir / "ui" / "button_frame_c.png",
        }
        for key, path in mapping.items():
            if key.startswith("tile_") or key.startswith("wall_"):
                size = (self.cell_size, self.cell_size)
            elif key.startswith("halo_"):
                size = (self.cell_size + 18, self.cell_size + 18)
            elif key.startswith("action_button_"):
                size = (122, 50)
            else:
                size = None
            self.ui_images[key] = self._load_png(path, size)

    def _image_or_none(self, key):
        return self.ui_images.get(key)

    def _draw_tile_image(self, key, x, y):
        img = self._image_or_none(key)
        if img:
            self.canvas.create_image(x, y, image=img, anchor="nw")
            return True
        return False

    def _wall_asset_key(self, pos):
        r, c = pos
        walls = self.state.walls
        vertical = ((r - 1, c) in walls) or ((r + 1, c) in walls)
        horizontal = ((r, c - 1) in walls) or ((r, c + 1) in walls)
        if vertical and not horizontal:
            return "wall_fire_v"
        if horizontal and not vertical:
            return "wall_fire_h"
        if vertical and horizontal:
            return "wall_holo"
        return "wall_block"

    def _configure_ttk_style(self):
        try:
            style = ttk.Style(self)
            style.theme_use("clam")
            style.configure(
                "Neon.TCombobox",
                fieldbackground="#071024",
                background="#111936",
                foreground=WHITE,
                arrowcolor=CYAN,
                bordercolor=BORDER,
                lightcolor=BORDER,
                darkcolor="#040712",
                padding=4,
            )
            style.map(
                "Neon.TCombobox",
                fieldbackground=[("readonly", "#071024")],
                foreground=[("readonly", WHITE)],
                selectbackground=[("readonly", "#15234a")],
                selectforeground=[("readonly", WHITE)],
            )
        except Exception:
            pass

    def _button_colors(self, role):
        palette = {
            "primary": ("#0b3446", CYAN, "#15475c"),
            "secondary": ("#24174c", PURPLE, "#34216e"),
            "auto": ("#421347", PINK, "#5a195f"),
            "pause": ("#50310c", AMBER, "#6b4312"),
            "utility": ("#132248", "#3dd7ff", "#1d3165"),
            "danger": ("#421526", RED, "#5a1c32"),
        }
        return palette.get(role, palette["utility"])

    def _neon_button(self, parent, text, command, role="utility"):
        bg, border, hover = self._button_colors(role)
        holder = tk.Frame(parent, bg=border)
        btn = tk.Button(
            holder,
            text=text,
            command=command,
            bg=bg,
            fg=WHITE,
            activebackground=hover,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            padx=6,
            pady=5,
            font=self.font_button,
            cursor="hand2",
            highlightthickness=0,
        )
        btn.pack(fill="both", expand=True, padx=1, pady=1)

        def enter(_):
            btn.configure(bg=hover)

        def leave(_):
            btn.configure(bg=bg)

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        btn._neon_holder = holder
        btn._neon_role = role
        btn._base_bg = bg
        btn._hover_bg = hover
        return holder, btn

    def _set_button_role(self, btn, role, text=None):
        if getattr(btn, "_image_button", False):
            colors = {
                "primary": CYAN,
                "secondary": "#d6c2ff",
                "auto": PINK,
                "pause": AMBER,
                "utility": "#d7e8ff",
                "danger": RED,
            }
            fg = colors.get(role, WHITE)
            if text is not None:
                btn.configure(text=text)
            btn.configure(fg=fg, activeforeground=WHITE)
            btn._role = role
            btn._base_fg = fg
            btn._hover_fg = WHITE
            btn.bind("<Enter>", lambda e: btn.configure(fg=WHITE))
            btn.bind("<Leave>", lambda e: btn.configure(fg=fg))
            return
        bg, border, hover = self._button_colors(role)
        if text is not None:
            btn.configure(text=text)
        btn.configure(bg=bg, activebackground=hover)
        if hasattr(btn, "_neon_holder"):
            btn._neon_holder.configure(bg=border)
        btn._neon_role = role
        btn._base_bg = bg
        btn._hover_bg = hover
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))

    def _action_button_image(self, index):
        cycle = ["action_button_a", "action_button_b", "action_button_c", "action_button_a", "action_button_b"]
        return self._image_or_none(cycle[index % len(cycle)])

    def _make_action_button(self, parent, text, command, role, index):
        image = self._action_button_image(index)
        text_colors = {
            "primary": CYAN,
            "secondary": "#d6c2ff",
            "auto": PINK,
            "pause": AMBER,
            "utility": "#d7e8ff",
            "danger": RED,
        }
        fg = text_colors.get(role, WHITE)
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            image=image,
            compound="center",
            bg=BG,
            activebackground=BG,
            fg=fg,
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            cursor="hand2",
            font=self.font_button,
            borderwidth=0,
        )
        btn._image_button = True
        btn._image_index = index
        btn._role = role
        btn._base_fg = fg
        btn._hover_fg = WHITE

        def enter(_):
            btn.configure(fg=btn._hover_fg)

        def leave(_):
            btn.configure(fg=btn._base_fg)

        btn.bind("<Enter>", enter)
        btn.bind("<Leave>", leave)
        return btn

    def _apply_level_layout(self):
        """Resize and center the board according to the current level.

        Small maps use a smaller canvas. Large maps use a larger canvas.
        The board and buttons are centered together inside the left play region.
        """
        if not hasattr(self, "canvas"):
            return

        grid_w = GRID_PADDING + self.state.cols * self.cell_size + 4
        grid_h = GRID_PADDING + self.state.rows * self.cell_size + 4

        left_region_w = max(1, self.right_x - self.left_x - self.layout_gap)
        max_board_h = max(1, self.action_bar_y - self.main_top - 10)

        self.board_canvas_width = min(grid_w, left_region_w)
        self.board_canvas_height = min(grid_h + 6, max_board_h)

        self.board_x = self.left_x + max(0, (left_region_w - self.board_canvas_width) // 2)
        self.board_y = self.main_top

        self.grid_offset_x = max(0, (self.board_canvas_width - grid_w) // 2)
        self.grid_offset_y = max(0, (self.board_canvas_height - grid_h) // 2)

        self.canvas.configure(width=self.board_canvas_width, height=self.board_canvas_height)
        self.canvas.place(x=self.board_x, y=self.board_y)

    def _position_action_bar(self):
        """Place action buttons directly under the current board."""
        if not hasattr(self, "action_bar_frame"):
            return

        y = self.board_y + self.board_canvas_height + 8
        y = min(y, self.window_height - self.action_bar_height - 22)

        self.action_bar_frame.place(
            x=self.board_x,
            y=y,
            width=self.board_canvas_width,
            height=self.action_bar_height,
        )
        self._position_credit_footer()

    def _position_credit_footer(self):
        """Place the small design credit below the action buttons."""
        if not hasattr(self, "credit_label"):
            return
        footer_y = min(
            self.action_bar_y + self.action_bar_height + 2,
            self.window_height - 16,
        )
        self.credit_label.place(
            x=self.board_x + self.board_canvas_width // 2,
            y=footer_y,
            anchor="n",
        )

    def _make_section(self, parent, title, accent=CYAN, inner_pad=12):
        outer = tk.Frame(parent, bg=BORDER)
        outer.pack(fill="x", padx=18, pady=(0, 12))
        frame = tk.Frame(outer, bg=SECTION)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        head = tk.Frame(frame, bg=SECTION)
        head.pack(fill="x", padx=12, pady=(10, 8))
        tk.Label(head, text=title, fg=accent, bg=SECTION, font=self.font_section).pack(anchor="w")
        tk.Frame(frame, bg=DIVIDER, height=1).pack(fill="x", padx=12)
        body = tk.Frame(frame, bg=SECTION)
        body.pack(fill="both", expand=True, padx=inner_pad, pady=(10, 12))
        return body

    def _make_stat_chip(self, parent, title, value="--", accent=CYAN):
        holder = tk.Frame(parent, bg=BORDER)
        inner = tk.Frame(holder, bg=CARD_INNER)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=title.upper(), fg=MUTED2, bg=CARD_INNER, font=self.font_small).pack(anchor="w", padx=8, pady=(4, 1))
        val = tk.Label(inner, text=str(value), fg=accent, bg=CARD_INNER, font=self.font_pixel)
        val.pack(anchor="w", padx=8, pady=(0, 5))
        return holder, val

    def _set_depth(self, delta):
        self.player_depth.set(max(1, min(6, self.player_depth.get() + delta)))
        if hasattr(self, "depth_value_label"):
            self.depth_value_label.configure(text=str(self.player_depth.get()))
        self.render()

    def _cycle_choice(self, var, choices, delta):
        try:
            idx = choices.index(var.get())
        except ValueError:
            idx = 0
        var.set(choices[(idx + delta) % len(choices)])
        self.render()

    def _cycle_control(self, parent, label, var, choices, row, column=0):
        tk.Label(parent, text=label, fg=WHITE, bg=SECTION, font=self.font_label).grid(row=row, column=column, sticky="w", pady=4)
        box = tk.Frame(parent, bg=SECTION)
        box.grid(row=row, column=column + 1, sticky="w", padx=(10, 18), pady=4)
        left, _ = self._neon_button(box, "‹", lambda: self._cycle_choice(var, choices, -1), "utility")
        left.pack(side="left")
        value = tk.Label(
            box,
            textvariable=var,
            fg=WHITE,
            bg="#071024",
            width=11,
            font=self.font_label,
            highlightbackground=BORDER,
            highlightcolor=CYAN,
            highlightthickness=1,
            padx=6,
            pady=6,
        )
        value.pack(side="left", padx=6)
        right, _ = self._neon_button(box, "›", lambda: self._cycle_choice(var, choices, 1), "utility")
        right.pack(side="left")
        return value

    def _build_ui(self):
        self._configure_ttk_style()
        self.monster_difficulty.set("Easy")

        # Two-column layout:
        # left  = board + action buttons
        # right = compact scanner panel
        margin_x = 16
        margin_top = 8
        header_h = 64
        gap = 12
        self.layout_gap = gap

        max_rows = max(level["rows"] for level in LEVELS)
        max_cols = max(level["cols"] for level in LEVELS)

        self.main_top = margin_top + header_h
        self.main_bottom = self.window_height - 18
        self.main_h = self.main_bottom - self.main_top

        self.grid_visible_w = GRID_PADDING + max_cols * self.cell_size + 4
        self.grid_visible_h = GRID_PADDING + max_rows * self.cell_size + 4

        self.left_x = margin_x
        # Left play area is exactly the size of the largest map. The right panel
        # starts right after it and stretches to the right edge, so the board is
        # no longer floating with empty horizontal space.
        self.left_w = self.grid_visible_w
        # Compact right panel attached to the right edge. This prevents the HUD
        # from becoming too wide on larger windows.
        self.right_w = 390
        self.right_x = self.window_width - self.right_w - margin_x

        self.board_x = self.left_x
        self.board_y = self.main_top
        self.board_canvas_width = self.left_w

        self.action_bar_height = 52
        self.action_bar_y = self.window_height - self.action_bar_height - 24
        self.board_canvas_height = self.action_bar_y - self.board_y - 10

        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self._apply_level_layout()

        self.action_button_gap = 10

        tk.Label(self, text="NEON HUNT", fg=CYAN, bg=BG, font=self.font_title).place(x=self.left_x, y=margin_top)
        tk.Label(
            self,
            text="Escape the grid. Beat the beast.",
            fg=MUTED,
            bg=BG,
            font=self.font_subtitle,
        ).place(x=self.left_x + 2, y=margin_top + 40)

        self.canvas = tk.Canvas(
            self,
            width=self.board_canvas_width,
            height=self.board_canvas_height,
            bg="#050613",
            highlightthickness=0,
        )
        self.canvas.place(x=self.board_x, y=self.board_y)

        self.action_bar_frame = tk.Frame(self, bg=BG)
        self._position_action_bar()
        for i in range(5):
            self.action_bar_frame.grid_columnconfigure(i, weight=1, uniform="action")

        specs = [
            ("STEP", self.player_step, "primary", "action_player"),
            ("ROUND", self.auto_round, "secondary", "action_round"),
            ("AUTO", self.toggle_autoplay, "auto", "autoplay_button"),
            ("RESET", self.restart, "danger", "action_restart"),
            ("NEXT", self.next_level, "utility", "action_next"),
        ]
        for i, (text_value, cmd, role, attr) in enumerate(specs):
            btn = self._make_action_button(self.action_bar_frame, text_value, cmd, role, i)
            btn.grid(row=0, column=i, sticky="nsew", padx=2, pady=0)
            setattr(self, attr, btn)

        self.credit_label = tk.Label(
            self,
            text="Designed By Fatemeh",
            fg=MUTED2,
            bg=BG,
            font=self.font_small,
        )

        self._apply_level_layout()
        self._position_action_bar()
        self._refresh_speed_buttons()

        # Thin vertical divider between board/action area and scanner panel.
        self.vertical_divider = tk.Frame(self, bg="#18365f")
        self.vertical_divider.place(x=self.right_x - 15, y=54, width=1, height=self.window_height - 86)

        panel_outer = tk.Frame(self, bg=BORDER)
        panel_outer.place(x=self.right_x, y=44, width=self.right_w, height=self.window_height - 72)
        panel = tk.Frame(panel_outer, bg=PANEL)
        panel.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(panel, bg=PANEL)
        header.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(header, text="ESCAPE SCANNER", fg=PINK, bg=PANEL, font=self.font_header).pack(anchor="w")
        tk.Frame(panel, bg=PINK, height=1).pack(fill="x", padx=16, pady=(4, 8))

        setup = self._make_section(panel, "AGENT SETUP", accent=CYAN, inner_pad=10)
        self._cycle_control(setup, "Player", self.player_control, ["Human", "Student AI"], row=0, column=0)
        self._cycle_control(setup, "Monster", self.monster_difficulty, ["Easy", "Normal", "Hard", "Boss"], row=1, column=0)

        tk.Label(setup, text="Depth", fg=WHITE, bg=SECTION, font=self.font_label).grid(row=2, column=0, sticky="w", pady=(8, 2))
        depth_box = tk.Frame(setup, bg=SECTION)
        depth_box.grid(row=2, column=1, columnspan=3, sticky="w", pady=(8, 2))
        minus_holder, _ = self._neon_button(depth_box, "−", lambda: self._set_depth(-1), "utility")
        minus_holder.pack(side="left")
        self.depth_value_label = tk.Label(
            depth_box,
            text=str(self.player_depth.get()),
            fg=CYAN,
            bg="#071024",
            width=4,
            font=self.font_pixel,
            highlightbackground=CYAN,
            highlightthickness=1,
            pady=4,
        )
        self.depth_value_label.pack(side="left", padx=7)
        plus_holder, _ = self._neon_button(depth_box, "+", lambda: self._set_depth(1), "utility")
        plus_holder.pack(side="left")

        tk.Label(setup, text="Speed", fg=WHITE, bg=SECTION, font=self.font_label).grid(row=3, column=0, sticky="w", pady=(8, 2))
        speed_box = tk.Frame(setup, bg=SECTION)
        speed_box.grid(row=3, column=1, columnspan=3, sticky="w", pady=(8, 2))
        self.speed_buttons = {}
        for speed in self.speed_levels:
            holder, btn = self._neon_button(speed_box, f"{speed}x", lambda s=speed: self._set_speed(s), "primary" if speed == self.speed_levels[self.speed_index] else "utility")
            holder.pack(side="left", padx=(0, 5))
            self.speed_buttons[speed] = btn

        toggles = tk.Frame(setup, bg=SECTION)
        toggles.grid(row=4, column=0, columnspan=4, sticky="w", pady=(10, 0))
        for i, (txt, var) in enumerate([
            ("Alpha-Beta", self.player_alpha_beta),
            ("Ghost Trail", self.show_ghost),
        ]):
            tk.Checkbutton(
                toggles,
                text=txt,
                variable=var,
                command=self.render,
                fg=WHITE,
                bg=SECTION,
                selectcolor="#071024",
                activebackground=SECTION,
                activeforeground=CYAN,
                font=self.font_label,
                highlightthickness=0,
                bd=0,
            ).grid(row=0, column=i, sticky="w", padx=(0, 22))

        status_sec = self._make_section(panel, "LEVEL STATUS", accent=CYAN, inner_pad=10)
        top = tk.Frame(status_sec, bg=SECTION)
        top.pack(fill="x")
        self.level_title_label = tk.Label(top, text="", fg=WHITE, bg=SECTION, font=self.font_label)
        self.level_title_label.pack(side="left")
        self.status_badge = tk.Label(top, text="ONGOING", fg=BG, bg=AMBER, font=self.font_pixel_small, padx=7, pady=3)
        self.status_badge.pack(side="right")

        chip_row = tk.Frame(status_sec, bg=SECTION)
        chip_row.pack(fill="x", pady=(8, 6))
        self.exit_chip_holder, self.exit_chip = self._make_stat_chip(chip_row, "Exit", "--", accent=GREEN)
        self.threat_chip_holder, self.threat_chip = self._make_stat_chip(chip_row, "Threat", "--", accent=RED)
        self.routes_chip_holder, self.routes_chip = self._make_stat_chip(chip_row, "Routes", "--", accent=CYAN)
        self.depth_chip_holder, self.depth_chip = self._make_stat_chip(chip_row, "Depth", "--", accent=PURPLE)
        for holder in [self.exit_chip_holder, self.threat_chip_holder, self.routes_chip_holder, self.depth_chip_holder]:
            holder.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.status_meta_label = tk.Label(status_sec, text="", fg=MUTED, bg=SECTION, justify="left", anchor="w", font=self.font_small)
        self.status_meta_label.pack(fill="x", pady=(2, 2))
        self.status_message_label = tk.Label(status_sec, text="", fg=WHITE, bg=SECTION, justify="left", anchor="w", font=self.font_small, wraplength=max(300, self.right_w - 70))
        self.status_message_label.pack(fill="x")

        analysis_sec = self._make_section(panel, "AI ANALYSIS", accent=PINK, inner_pad=8)
        analysis_box = tk.Frame(analysis_sec, bg="#070b1a", highlightthickness=1, highlightbackground="#132a4a")
        analysis_box.pack(fill="both", expand=True)
        self.scanner_text = tk.Text(
            analysis_box,
            height=6,
            bg="#070b1a",
            fg=CYAN,
            insertbackground=CYAN,
            relief="flat",
            font=self.font_small,
            wrap="word",
            padx=8,
            pady=6,
            highlightthickness=0,
            bd=0,
        )
        self.scanner_text.pack(side="left", fill="both", expand=True)
        self.scanner_scroll = tk.Scrollbar(analysis_box, command=self.scanner_text.yview, bg="#0b1024", troughcolor="#050714")
        self.scanner_scroll.pack(side="right", fill="y")
        self.scanner_text.configure(yscrollcommand=self.scanner_scroll.set)

    def restart(self):
        self.autoplay_running = False
        if hasattr(self, "autoplay_button"):
            self._set_button_role(self.autoplay_button, "auto", text="AUTO")
        self.state = GameState.from_level(LEVELS[self.level_index])
        self.message = "Level restarted."
        self.game_over = False
        self.player_info = {}
        self.monster_info = {}
        self.ghost_path = []
        self.heat_scores = {}
        self.position_history = [self.state.player]
        self.loop_warning = None
        self.loop_cells = []
        self.render()

    def next_level(self):
        self.level_index = (self.level_index + 1) % len(LEVELS)
        self.restart()

    def human_player_move(self, move):
        if self.player_control.get() != "Human":
            return
        self._apply_player_move(move, trigger_monster=True)

    def _record_player_position(self):
        """Record player positions for loop detection.

        This is diagnostic only. It never changes the student's selected move.
        """
        self.position_history.append(self.state.player)
        if len(self.position_history) > 14:
            self.position_history = self.position_history[-14:]
        self._detect_loop()

    def _detect_loop(self):
        """Detect repeated-position behavior without correcting it."""
        self.loop_warning = None
        self.loop_cells = []
        hist = list(self.position_history)
        if len(hist) < 4:
            return False

        # A-B-A-B oscillation.
        if hist[-1] == hist[-3] and hist[-2] == hist[-4] and hist[-1] != hist[-2]:
            self.loop_cells = [hist[-1], hist[-2]]
            self.loop_warning = "LOOP DETECTED: AI is oscillating between two cells."
            return True

        # Longer repeated local cycle: many moves but too few unique positions.
        recent = hist[-8:]
        unique = list(dict.fromkeys(recent))
        if len(recent) >= 8 and len(set(recent)) <= 3:
            self.loop_cells = unique
            self.loop_warning = "LOOP DETECTED: repeated local path."
            return True

        return False

    def _decide_player_move(self):
        control = self.player_control.get()
        if control not in {"Human", "Student AI"}:
            self.player_control.set("Human")
            control = "Human"
        move = None
        self.player_info = {"control": control}
        try:
            if control == "Human":
                self.message = "Human mode: use arrow keys."
                self.render()
                return None
            if control == "Student AI":
                result = student_player_ai.choose_player_move(self.state, self.player_depth.get(), self.player_alpha_beta.get())
                self.player_info = result if isinstance(result, dict) else {"best_move": result}
                self.player_info["control"] = control
                move = self.player_info.get("best_move")
        except NotImplementedError as e:
            self.message = f"Student Player AI incomplete: {e}"
            self.render()
            return None
        except Exception as e:
            self.message = f"Player AI error: {type(e).__name__}: {e}"
            self.render()
            return None
        return move

    def _set_speed(self, speed):
        if speed not in self.speed_levels:
            return
        self.speed_index = self.speed_levels.index(speed)
        self.speed_label.set(f"{speed}x")
        self._refresh_speed_buttons()
        self.message = f"Playback speed: {self.speed_label.get()}"
        self.render()

    def _refresh_speed_buttons(self):
        if not hasattr(self, "speed_buttons"):
            return
        active_speed = self.speed_levels[self.speed_index]
        for speed, btn in self.speed_buttons.items():
            role = "primary" if speed == active_speed else "utility"
            self._set_button_role(btn, role)

    def _delay(self, base_ms):
        speed = self.speed_levels[self.speed_index]
        return max(45, int(base_ms / speed))

    def player_step(self):
        if self.game_over or self.animating:
            return
        move = self._decide_player_move()
        if move:
            self._apply_player_move(move, trigger_monster=False)

    def _apply_player_move(self, move, trigger_monster=False):
        if self.game_over or self.animating:
            return
        if not move:
            self.message = "Player has no legal move."
            self.render()
            return
        if move not in legal_moves_basic(self.state, AGENT_PLAYER):
            self.message = f"Invalid player move: {move}"
            self.render()
            return
        self.player_facing = move
        self._build_player_visual_aids(move)
        self.state = transition_basic(self.state, move, AGENT_PLAYER)
        self._record_player_position()
        self.message = f"Player moved {move}."
        if self.loop_warning:
            self.message = self.loop_warning
        self.check_end()
        self.render()
        if trigger_monster and not self.game_over:
            self.after(self._delay(180), self.monster_turn)

    def monster_turn(self):
        if self.game_over or self.animating:
            return
        try:
            result = instructor_monster_ai.choose_monster_move(self.state, self.monster_difficulty.get())
            self.monster_info = result
            move = result.get("best_move")
        except Exception as e:
            self.message = f"Instructor monster error: {type(e).__name__}: {e}"
            self.render()
            return
        if move:
            self.monster_facing = move
            self._extend_ghosts(result.get("principal_variation", []))
            self.state = transition_basic(self.state, move, AGENT_MONSTER)
            self.message = f"Monster moved {move}."
        else:
            self.message = "Monster has no legal move."
        self.check_end()
        self.render()
        if self.autoplay_running and not self.game_over and self.player_control.get() != "Human":
            self.after(self._delay(350), self._autoplay_tick)

    def auto_round(self):
        if self.game_over or self.animating:
            return
        if self.player_control.get() == "Human":
            self.message = "Switch Player to Student AI for Auto Round."
            self.render()
            return
        move = self._decide_player_move()
        if move:
            self._apply_player_move(move, trigger_monster=True)

    def toggle_autoplay(self):
        if self.game_over:
            return
        if self.player_control.get() == "Human":
            self.message = "Auto Play works with Student AI, not Human."
            self.render()
            return
        self.autoplay_running = not self.autoplay_running
        self._set_button_role(
            self.autoplay_button,
            "pause" if self.autoplay_running else "auto",
            text="PAUSE" if self.autoplay_running else "AUTO",
        )
        if self.autoplay_running:
            self._autoplay_tick()

    def _autoplay_tick(self):
        if not self.autoplay_running or self.game_over:
            self.autoplay_running = False
            self._set_button_role(self.autoplay_button, "auto", text="AUTO")
            return
        self.auto_round()

    def check_end(self):
        result = terminal_result(self.state)
        if result == "PLAYER_WIN":
            self.game_over = True
            self.message = "VICTORY — Hacker escaped through the neon portal."
        elif result == "MONSTER_WIN":
            self.game_over = True
            self.message = "CAPTURED — Cyber Beast caught the Hacker."

    def _build_player_visual_aids(self, best_move):
        self.ghost_path = []
        if best_move:
            try:
                ns = transition_basic(self.state, best_move, AGENT_PLAYER)
                self.ghost_path.append(("player", ns.player))
                self._extend_ghosts(self.player_info.get("principal_variation", []))
            except Exception:
                pass
        self.heat_scores = {}
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                pos = (r, c)
                if pos in self.state.walls:
                    continue
                danger = 16 - bfs_distance(self.state, self.state.monster, pos) + 0.85 * bfs_distance(self.state, pos, self.state.exit)
                self.heat_scores[pos] = danger

    def _extend_ghosts(self, pv):
        for item in pv[:8]:
            try:
                self.ghost_path.append((item.get("agent"), tuple(item.get("position"))))
            except Exception:
                pass

    def render(self):
        self._apply_level_layout()
        self._position_action_bar()
        self.canvas.delete("all")
        self._draw_background()
        self._draw_grid()
        self._draw_walls()
        self._draw_loop_warning()
        self._draw_exit()
        if self.show_ghost.get():
            self._draw_ghosts()
        self._draw_player()
        self._draw_monster()
        self._draw_status()
        self._draw_scanner()
        if self.game_over:
            self._show_game_over_modal()
        else:
            self._hide_game_over_modal()

    def cell_xy(self, pos):
        r, c = pos
        return (
            self.grid_offset_x + GRID_PADDING + c * self.cell_size,
            self.grid_offset_y + GRID_PADDING + r * self.cell_size,
        )

    def _draw_background(self):
        w = int(self.canvas.cget("width"))
        h = int(self.canvas.cget("height"))
        self.canvas.create_rectangle(0, 0, w, h, fill="#050613", outline="")
        for i in range(0, w + 24, 24):
            self.canvas.create_line(i, 0, i - 240, h, fill="#0b1430")

    def _draw_grid(self):
        for r in range(self.state.rows):
            for c in range(self.state.cols):
                pos = (r, c)
                x, y = self.cell_xy(pos)
                key = "tile_blocked" if pos in self.state.walls else "tile_walkable"
                if not self._draw_tile_image(key, x, y):
                    fill = "#111632" if pos in self.state.walls else "#071024"
                    outline = PURPLE if pos in self.state.walls else "#16315f"
                    self.canvas.create_rectangle(x, y, x + self.cell_size - 4, y + self.cell_size - 4, outline=outline, fill=fill, width=1)
                self.canvas.create_rectangle(x, y, x + self.cell_size - 4, y + self.cell_size - 4, outline="#0d2c53", width=1)

    def _draw_heatmap(self):
        vals = list(self.heat_scores.values())
        if not vals:
            for r in range(self.state.rows):
                for c in range(self.state.cols):
                    pos = (r, c)
                    if pos not in self.state.walls:
                        self.heat_scores[pos] = 16 - bfs_distance(self.state, self.state.monster, pos) + 0.85 * bfs_distance(self.state, pos, self.state.exit)
            vals = list(self.heat_scores.values())
        if not vals:
            return
        mn, mx = min(vals), max(vals)
        danger_img = self._image_or_none("tile_danger")
        for pos, val in self.heat_scores.items():
            if pos in self.state.walls or pos in (self.state.player, self.state.monster, self.state.exit):
                continue
            t = 0 if mx == mn else (val - mn) / (mx - mn)
            x, y = self.cell_xy(pos)
            if danger_img and t >= 0.84:
                self.canvas.create_image(x, y, image=danger_img, anchor="nw")
                self.canvas.create_rectangle(x + 3, y + 3, x + self.cell_size - 7, y + self.cell_size - 7, outline="#ff3864", width=1)
            elif t >= 0.58:
                self.canvas.create_rectangle(x + 5, y + 5, x + self.cell_size - 9, y + self.cell_size - 9, outline="#ff3864", width=1)
                self.canvas.create_line(x + 10, y + self.cell_size - 14, x + self.cell_size - 14, y + 10, fill="#7a174a", width=1)
            elif t >= 0.42:
                self.canvas.create_rectangle(x + 7, y + 7, x + self.cell_size - 11, y + self.cell_size - 11, outline="#5a2a65", width=1)

    def _draw_walls(self):
        for pos in self.state.walls:
            x, y = self.cell_xy(pos)
            key = self._wall_asset_key(pos)
            img = self._image_or_none(key) or self._image_or_none("wall_block")
            if img:
                self.canvas.create_image(x, y, image=img, anchor="nw")
            else:
                self.canvas.create_rectangle(x + 2, y + 2, x + self.cell_size - 6, y + self.cell_size - 6, fill="#161a36", outline=PURPLE, width=2)
                self.canvas.create_line(x + 8, y + self.cell_size // 2, x + self.cell_size - 12, y + self.cell_size // 2, fill=PINK, width=1)
            self.canvas.create_rectangle(x + 1, y + 1, x + self.cell_size - 5, y + self.cell_size - 5, outline="#a855f7", width=1)

    def _draw_loop_warning(self):
        if not self.loop_warning or not self.loop_cells:
            return
        for pos in self.loop_cells:
            if not pos or pos in self.state.walls:
                continue
            x, y = self.cell_xy(pos)
            self.canvas.create_rectangle(
                x + 2, y + 2, x + self.cell_size - 6, y + self.cell_size - 6,
                outline=GOLD, width=4
            )
            self.canvas.create_rectangle(
                x + 6, y + 6, x + self.cell_size - 10, y + self.cell_size - 10,
                outline=AMBER, width=1
            )

    def _draw_exit(self):
        x, y = self.cell_xy(self.state.exit)
        pulse = 2 + (self.state.turn_count % 3)
        self.canvas.create_oval(x + 4 - pulse, y + 4 - pulse, x + self.cell_size - 8 + pulse, y + self.cell_size - 8 + pulse, outline="#164f47", width=1)
        self.canvas.create_oval(x + 7, y + 7, x + self.cell_size - 11, y + self.cell_size - 11, outline=GREEN, width=4)
        self.canvas.create_oval(x + 18, y + 18, x + self.cell_size - 22, y + self.cell_size - 22, outline=CYAN, width=2)
        self.canvas.create_text(x + self.cell_size // 2 - 2, y + self.cell_size // 2 - 2, text="EXIT", fill=GREEN, font=self.font_small)

    def _draw_player(self):
        x, y = self.cell_xy(self.state.player)
        cx = x + self.cell_size // 2
        cy = y + self.cell_size // 2

        # Neon selection style instead of a flat bright backplate:
        # keep the original tile visible, then add only a clear neon border.
        self.canvas.create_rectangle(
            x + 2, y + 2, x + self.cell_size - 6, y + self.cell_size - 6,
            outline=CYAN, width=3
        )
        self.canvas.create_rectangle(
            x + 6, y + 6, x + self.cell_size - 10, y + self.cell_size - 10,
            outline="#69ffff", width=1
        )
        img = self.character_images.get(("player", self.player_facing))
        if img:
            self.canvas.create_image(cx, cy, image=img)
        else:
            self.canvas.create_oval(x + 9, y + 9, x + self.cell_size - 13, y + self.cell_size - 13, fill="#063b4a", outline=CYAN, width=2)
            self.canvas.create_text(cx, cy, text="H", fill=WHITE, font=self.font_header)

    def _draw_monster(self):
        x, y = self.cell_xy(self.state.monster)
        cx = x + self.cell_size // 2
        cy = y + self.cell_size // 2

        # Monster marker: preserve the tile, use only a red warning border.
        self.canvas.create_rectangle(
            x + 2, y + 2, x + self.cell_size - 6, y + self.cell_size - 6,
            outline=RED, width=3
        )
        self.canvas.create_rectangle(
            x + 6, y + 6, x + self.cell_size - 10, y + self.cell_size - 10,
            outline="#ff8aa0", width=1
        )
        img = self.character_images.get(("monster", self.monster_facing))
        if img:
            self.canvas.create_image(cx, cy, image=img)
        else:
            self.canvas.create_polygon(cx, y + 5, x + self.cell_size - 8, cy, cx, y + self.cell_size - 10, x + 6, cy, fill="#3b0924", outline=RED, width=2)
            self.canvas.create_text(cx, cy, text="M", fill=WHITE, font=self.font_header)

    def _draw_ghosts(self):
        for i, (agent, pos) in enumerate(self.ghost_path[:10], start=1):
            if not pos or pos in self.state.walls:
                continue
            x, y = self.cell_xy(pos)
            col = CYAN if agent == "player" else RED
            self.canvas.create_oval(x + 13, y + 13, x + self.cell_size - 17, y + self.cell_size - 17, outline=col, width=2)
            self.canvas.create_oval(x + 18, y + 18, x + self.cell_size - 22, y + self.cell_size - 22, fill="#070914", outline="#11182d")
            self.canvas.create_text(x + self.cell_size // 2 - 1, y + self.cell_size // 2, text=str(i), fill="#02030a", font=self.font_pixel)
            self.canvas.create_text(x + self.cell_size // 2 - 2, y + self.cell_size // 2 - 1, text=str(i), fill=GOLD, font=self.font_pixel)

    def _draw_status(self):
        level = LEVELS[self.level_index]["name"]
        result = terminal_result(self.state)
        if hasattr(self, "level_title_label"):
            self.level_title_label.configure(text=level)
        if hasattr(self, "status_badge"):
            colors = {
                "ONGOING": (BG, AMBER),
                "PLAYER_WIN": (BG, GREEN),
                "MONSTER_WIN": (WHITE, RED),
            }
            key = result if result in ("PLAYER_WIN", "MONSTER_WIN") else "ONGOING"
            fg, bg = colors.get(key, (BG, AMBER))
            label = "VICTORY" if result == "PLAYER_WIN" else "CAPTURED" if result == "MONSTER_WIN" else "ONGOING"
            self.status_badge.configure(text=label, fg=fg, bg=bg)

        d_exit = bfs_distance(self.state, self.state.player, self.state.exit)
        d_threat = bfs_distance(self.state, self.state.player, self.state.monster)
        routes = escape_routes(self.state)
        if hasattr(self, "exit_chip"):
            self.exit_chip.configure(text=str(d_exit))
            self.threat_chip.configure(text=str(d_threat), fg=RED if d_threat <= 2 else AMBER if d_threat <= 4 else GREEN)
            self.routes_chip.configure(text=str(routes), fg=RED if routes <= 1 else CYAN)
            self.depth_chip.configure(text=str(self.player_depth.get()))
        meta = f"CTRL {self.player_control.get()}  |  MONSTER {self.monster_difficulty.get()}  |  AB {'ON' if self.player_alpha_beta.get() else 'OFF'}"
        self.status_meta_label.configure(text=meta)
        self.status_message_label.configure(text=self.message)

    def _score_tag(self, score, best=False):
        if best:
            return "best"
        if score <= -5000:
            return "danger"
        return "normal"

    def _insert_score_row(self, move, score, best_move, monster=False):
        best = move == best_move
        tag = "monster_best" if (monster and best) else self._score_tag(score, best)
        label = "BEST" if best else "DANGER" if score <= -5000 else ""
        line = f"  {move:<6} {score:>9.2f}  {label}\n"
        self.scanner_text.insert("end", line, tag)

    def _draw_scanner(self):
        self.scanner_text.configure(state="normal")
        self.scanner_text.delete("1.0", "end")
        self.scanner_text.tag_configure("heading", foreground=PINK, font=self.font_label)
        self.scanner_text.tag_configure("normal", foreground="#c7dbff", font=self.font_small)
        self.scanner_text.tag_configure("best", foreground=GOLD, font=self.font_small)
        self.scanner_text.tag_configure("monster_best", foreground=RED, font=self.font_small)
        self.scanner_text.tag_configure("danger", foreground=RED, font=self.font_small)
        self.scanner_text.tag_configure("muted", foreground=MUTED, font=self.font_small)

        if self.loop_warning:
            self.scanner_text.insert("end", "⚠ LOOP DETECTED\n", "danger")
            self.scanner_text.insert("end", "Improve evaluation: add progress / visited penalties.\n\n", "muted")

        self.scanner_text.insert("end", "PLAYER\n", "heading")
        if self.player_info and self.player_info.get("scores"):
            for move, score in sorted(self.player_info.get("scores", {}).items(), key=lambda item: item[1], reverse=True)[:4]:
                self._insert_score_row(move, score, self.player_info.get("best_move"), monster=False)
            self.scanner_text.insert("end", f"states {self.player_info.get('states_explored', 0)} | pruned {self.player_info.get('pruned_branches', 0)}\n", "muted")
        else:
            self.scanner_text.insert("end", "No player AI decision yet.\n", "muted")

        self.scanner_text.insert("end", "\nMONSTER\n", "heading")
        if self.monster_info and self.monster_info.get("scores"):
            self.scanner_text.insert("end", f"{self.monster_info.get('mode')} d={self.monster_info.get('depth')}\n", "muted")
            for move, score in sorted(self.monster_info.get("scores", {}).items(), key=lambda item: item[1], reverse=True)[:4]:
                self._insert_score_row(move, score, self.monster_info.get("best_move"), monster=True)
            self.scanner_text.insert("end", f"states {self.monster_info.get('states_explored', 0)} | pruned {self.monster_info.get('pruned_branches', 0)}\n", "muted")
        else:
            self.scanner_text.insert("end", "Monster has not moved yet.\n", "muted")

        self.scanner_text.configure(state="disabled")

    def _hide_game_over_modal(self):
        if getattr(self, "modal_overlay", None) is not None:
            try:
                self.modal_overlay.destroy()
            except Exception:
                pass
        self.modal_overlay = None
        self.modal_canvas = None

    def _show_game_over_modal(self):
        """Full-window game-over modal.

        The old overlay lived inside the board canvas, so only the board was
        dimmed. V23 places a modal layer over the entire app: board, buttons,
        and right HUD are all muted behind the popup.
        """
        if getattr(self, "modal_overlay", None) is not None:
            try:
                self.modal_overlay.lift()
            except Exception:
                pass
            return

        result = terminal_result(self.state)
        title = "VICTORY" if result == "PLAYER_WIN" else "CAPTURED"
        subtitle = "Escaped the maze." if result == "PLAYER_WIN" else "Caught by the beast."
        color = GREEN if result == "PLAYER_WIN" else RED

        overlay = tk.Frame(self, bg=BG)
        overlay.place(x=0, y=0, width=self.window_width, height=self.window_height)
        overlay.lift()
        self.modal_overlay = overlay

        canvas = tk.Canvas(
            overlay,
            width=self.window_width,
            height=self.window_height,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        canvas.place(x=0, y=0)
        self.modal_canvas = canvas

        # Simulated blur/frost layer over the whole UI.
        canvas.create_rectangle(0, 0, self.window_width, self.window_height, fill="#02030a", outline="")
        canvas.create_rectangle(0, 0, self.window_width, self.window_height, fill="#101735", outline="", stipple="gray50")
        canvas.create_rectangle(0, 0, self.window_width, self.window_height, fill="#050613", outline="", stipple="gray75")

        # Subtle scan lines to make the modal feel intentional rather than flat.
        for y in range(0, self.window_height, 18):
            canvas.create_line(0, y, self.window_width, y, fill="#0c1734")

        cx, cy = self.window_width // 2, self.window_height // 2
        panel_w, panel_h = 460, 250
        x1, y1 = cx - panel_w // 2, cy - panel_h // 2
        x2, y2 = cx + panel_w // 2, cy + panel_h // 2

        canvas.create_rectangle(x1 - 10, y1 - 10, x2 + 10, y2 + 10, fill="#02030a", outline="")
        canvas.create_rectangle(x1, y1, x2, y2, fill="#080b1d", outline=color, width=4)
        canvas.create_rectangle(x1 + 14, y1 + 14, x2 - 14, y2 - 14, outline=CYAN, width=1)
        canvas.create_text(cx, y1 + 62, text=title, fill=color, font=(self.font_header[0], 32, "bold"))
        canvas.create_text(cx, y1 + 107, text=subtitle, fill=WHITE, font=self.font_label)
        canvas.create_text(cx, y1 + 138, text=f"Turns: {self.state.turn_count}", fill=GOLD, font=self.font_label)

        btn_y = y2 - 66
        reset_holder, reset_btn = self._neon_button(overlay, "RESET", self.restart, "primary")
        next_holder, next_btn = self._neon_button(overlay, "NEXT", self.next_level, "secondary")
        reset_holder.place(x=cx - 168, y=btn_y, width=140, height=42)
        next_holder.place(x=cx + 28, y=btn_y, width=140, height=42)



def run_app():
    app = NeonHuntEscapeApp()
    app.mainloop()
