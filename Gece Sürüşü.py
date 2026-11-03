import random
import tkinter as tk
import tkinter.font as tkfont

WIDTH, HEIGHT = 800, 600
COLORS = ["#30a8ff", "#ff493d", "#43d17a", "#e4c542", "#b06cff"]
CARS = ["Sedan", "Spor", "SUV"]
TRAFFIC_DENSITIES = ("Az", "Orta", "Yoğun")
TRAFFIC_INTERVAL_MULTIPLIERS = (2.5, 1.7, 1.0)
MISSION_TARGET = 10
TIME_PERIODS = ("Gece", "Gün batımı", "Gündüz")
SCENE_PALETTES = (
    ("#111827", "#101a2b", "#252a31", "#59606a", "#dce8ff"),
    ("#493b68", "#c26b4a", "#37323a", "#70615e", "#ffd6a0"),
    ("#5b9bd5", "#87ceeb", "#555a60", "#85898d", "#ffffff"),
)


class DrivingGame:
    def __init__(self, root):
        self.root = root
        root.title("Gece Sürüşü")
        root.geometry(f"{WIDTH}x{HEIGHT}")
        root.minsize(WIDTH, HEIGHT)
        root.resizable(True, True)
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, background="#131925",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.fullscreen = False
        self.canvas_scale = 1.0
        self.canvas_offset_x = 0.0
        self.canvas_offset_y = 0.0
        self.scaled_fonts = {}
        self.configure_redraw_id = None

        self.car_choice = 0
        self.color_choice = 0
        self.traffic_density = 0
        self.time_period = 0
        self.spoiler = False
        self.neon = False
        self.reset_game()
        self.state = "menu"

        root.bind("<KeyPress>", self.key_down)
        root.bind("<KeyRelease>", self.key_up)
        root.bind("<Button-1>", self.click)
        self.canvas.bind("<Configure>", self.canvas_configured)
        self.keys = set()
        self.draw_menu()
        self.root.after_idle(self.redraw_current_screen)

    def reset_game(self):
        self.speed = 0.35
        self.position = 0.0
        self.steering = 0.0
        self.target_lane = 1
        self.signal = None
        self.signal_blink = 0
        self.headlights = True
        self.score = 0
        self.traffic = []
        self.spawn_timer = 0

    def button(self, x1, y1, x2, y2, text, color="#303b4d"):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#8995a8", width=2)
        self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text,
                                fill="white", font=("Arial", 13, "bold"))

    def fit_canvas(self):
        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        self.canvas_scale = min(canvas_width / WIDTH, canvas_height / HEIGHT)
        self.canvas_offset_x = (canvas_width - WIDTH * self.canvas_scale) / 2
        self.canvas_offset_y = (canvas_height - HEIGHT * self.canvas_scale) / 2
        scale_key = round(self.canvas_scale, 2)
        for item in self.canvas.find_all():
            if self.canvas.type(item) != "text":
                continue
            font_spec = self.canvas.itemcget(item, "font")
            cache_key = (font_spec, scale_key)
            if cache_key not in self.scaled_fonts:
                font_details = tkfont.Font(root=self.root, font=font_spec).actual()
                self.scaled_fonts[cache_key] = tkfont.Font(
                    root=self.root,
                    family=font_details["family"],
                    size=max(1, round(abs(font_details["size"]) * self.canvas_scale)),
                    weight=font_details["weight"],
                    slant=font_details["slant"],
                    underline=font_details["underline"],
                    overstrike=font_details["overstrike"],
                )
            self.canvas.itemconfigure(item, font=self.scaled_fonts[cache_key])
        self.canvas.scale("all", 0, 0, self.canvas_scale, self.canvas_scale)
        self.canvas.move("all", self.canvas_offset_x, self.canvas_offset_y)

    def redraw_current_screen(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "garage":
            self.draw_garage()
        elif self.state == "controls":
            self.draw_controls()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "mode_select":
            self.draw_mode_select()
        elif self.state in ("playing", "gameover", "mission_complete"):
            self.draw_scene()
            if self.state == "gameover":
                self.draw_gameover_overlay()
            elif self.state == "mission_complete":
                self.draw_mission_complete_overlay()
            self.fit_canvas()

    def canvas_configured(self, _event):
        if self.configure_redraw_id is not None:
            self.root.after_cancel(self.configure_redraw_id)
        self.configure_redraw_id = self.root.after_idle(
            self.redraw_after_configure
        )

    def redraw_after_configure(self):
        self.configure_redraw_id = None
        self.redraw_current_screen()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        if self.fullscreen:
            self.root.resizable(True, True)
        else:
            self.root.geometry(f"{WIDTH}x{HEIGHT}")
            self.root.resizable(True, True)
        self.root.after(150, self.redraw_current_screen)

    def draw_menu(self):
        self.state = "menu"
        self.signal = None
        self.headlights = True
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#131925", outline="")
        self.canvas.create_text(WIDTH / 2, 55, text="GECE SÜRÜŞÜ",
                                fill="#42baff", font=("Arial", 32, "bold"))
        self.canvas.create_text(WIDTH / 2, 105, text="SÜRÜŞE HAZIR MISIN?",
                                fill="white", font=("Arial", 14, "bold"))

        self.draw_car(WIDTH / 2, 220, 0.9, COLORS[self.color_choice], player=True)
        self.button(300, 315, 500, 360, "GARAJ")
        self.button(300, 370, 500, 415, "AYARLAR")
        self.button(300, 425, 500, 470, "KONTROLLER")
        self.button(300, 485, 500, 540, "SÜRÜŞE BAŞLA", "#176b9e")
        self.canvas.create_text(
            WIDTH / 2, 587,
            text="Aracını özelleştirmek için GARAJ'a tıkla",
            fill="#c6ccd6", font=("Arial", 11)
        )
        self.fit_canvas()

    def draw_garage(self):
        self.state = "garage"
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#131925", outline="")
        self.canvas.create_text(WIDTH / 2, 60, text="GARAJ",
                                fill="#42baff", font=("Arial", 30, "bold"))
        self.canvas.create_text(260, 135, text="◀", fill="white", font=("Arial", 24))
        self.canvas.create_text(540, 135, text="▶", fill="white", font=("Arial", 24))
        self.canvas.create_text(WIDTH / 2, 135, text=CARS[self.car_choice],
                                fill="#42baff", font=("Arial", 20, "bold"))
        self.draw_car(WIDTH / 2, 255, 1.15, COLORS[self.color_choice], player=True)

        self.button(260, 355, 540, 400,
                    f"Boya: {self.color_choice + 1} / {len(COLORS)}")
        self.button(260, 410, 540, 455,
                    f"Spoiler: {'Açık' if self.spoiler else 'Kapalı'}")
        self.button(260, 465, 540, 510,
                    f"Neon: {'Açık' if self.neon else 'Kapalı'}")
        self.button(300, 530, 500, 575, "ANA MENÜYE DÖN", "#176b9e")
        self.fit_canvas()

    def draw_mode_select(self):
        self.state = "mode_select"
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#131925", outline="")
        self.canvas.create_text(WIDTH / 2, 100, text="SÜRÜŞ MODUNU SEÇ",
                                fill="#42baff", font=("Arial", 30, "bold"))
        self.button(220, 195, 580, 250, "GÖREV")
        self.canvas.create_text(WIDTH / 2, 270, text=f"{MISSION_TARGET} aracı geç",
                                fill="#c6ccd6", font=("Arial", 12))
        self.button(220, 320, 580, 375, "SERBEST SÜRÜŞ", "#176b9e")
        self.canvas.create_text(WIDTH / 2, 395, text="Hedef olmadan sürüş yap",
                                fill="#c6ccd6", font=("Arial", 12))
        self.button(300, 490, 500, 545, "ANA MENÜYE DÖN")
        self.fit_canvas()

    def draw_controls(self):
        self.state = "controls"
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#131925", outline="")
        self.canvas.create_text(WIDTH / 2, 75, text="KONTROLLER",
                                fill="#42baff", font=("Arial", 30, "bold"))

        controls = (
            ("W / S", "Hızı artır / azalt"),
            ("A / D", "Sola / sağa şerit değiştir"),
            ("Q / E", "Sol / sağ sinyali aç-kapat"),
            ("F", "Farları aç-kapat"),
            ("ESC", "Ana menüye dön"),
            ("BOŞLUK", "Kaza sonrası yeniden başlat"),
        )
        for index, (keys, description) in enumerate(controls):
            y = 155 + index * 55
            self.canvas.create_text(250, y, text=keys, anchor="e",
                                    fill="#42baff", font=("Arial", 16, "bold"))
            self.canvas.create_text(280, y, text=description, anchor="w",
                                    fill="white", font=("Arial", 15))

        self.button(300, 510, 500, 560, "MENÜYE DÖN", "#176b9e")
        self.fit_canvas()

    def draw_settings(self):
        self.state = "settings"
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#131925", outline="")
        self.canvas.create_text(WIDTH / 2, 75, text="AYARLAR",
                                fill="#42baff", font=("Arial", 30, "bold"))
        self.button(
            220, 175, 580, 230,
            f"Trafik yoğunluğu: {TRAFFIC_DENSITIES[self.traffic_density]}"
        )
        self.button(
            220, 255, 580, 310,
            f"Günün saati: {TIME_PERIODS[self.time_period]}"
        )
        self.button(
            220, 335, 580, 390,
            f"Tam ekran: {'Açık' if self.fullscreen else 'Kapalı'}"
        )
        self.button(300, 455, 500, 510, "MENÜYE DÖN", "#176b9e")
        self.canvas.create_text(WIDTH / 2, 545, text="ESC: Ana menüye dön",
                                fill="#c6ccd6", font=("Arial", 12))
        self.fit_canvas()

    def draw_gameover_overlay(self):
        self.canvas.create_rectangle(225, 235, 575, 370, fill="#10131b",
                                     outline="#ff596b", width=3)
        self.canvas.create_text(WIDTH / 2, 275, text="KAZA!",
                                fill="#ff596b", font=("Arial", 32, "bold"))
        self.canvas.create_text(WIDTH / 2, 320, text="Tekrar: BOŞLUK   Menü: ESC",
                                fill="white", font=("Arial", 14))

    def draw_mission_complete_overlay(self):
        self.canvas.create_rectangle(200, 235, 600, 370, fill="#10131b",
                                     outline="#43d17a", width=3)
        self.canvas.create_text(WIDTH / 2, 275, text="GÖREV TAMAMLANDI!",
                                fill="#43d17a", font=("Arial", 26, "bold"))
        self.canvas.create_text(WIDTH / 2, 320, text="Tekrar: BOŞLUK   Menü: ESC",
                                fill="white", font=("Arial", 14))

    def start_game(self, mode):
        self.game_mode = mode
        self.reset_game()
        self.state = "playing"
        self.tick()

    def click(self, event):
        x = (event.x - self.canvas_offset_x) / self.canvas_scale
        y = (event.y - self.canvas_offset_y) / self.canvas_scale
        if self.state in ("playing", "gameover", "mission_complete"):
            if 650 <= x <= 790 and 55 <= y <= 95:
                self.draw_menu()
            return
        if self.state == "mode_select":
            if 220 <= x <= 580 and 195 <= y <= 250:
                self.start_game("mission")
            elif 220 <= x <= 580 and 320 <= y <= 375:
                self.start_game("free")
            elif 300 <= x <= 500 and 490 <= y <= 545:
                self.draw_menu()
            return
        if self.state == "settings":
            if 175 <= y <= 230 and 220 <= x <= 580:
                self.traffic_density = (self.traffic_density + 1) % len(TRAFFIC_DENSITIES)
                self.draw_settings()
            elif 255 <= y <= 310 and 220 <= x <= 580:
                self.time_period = (self.time_period + 1) % len(TIME_PERIODS)
                self.draw_settings()
            elif 335 <= y <= 390 and 220 <= x <= 580:
                self.toggle_fullscreen()
            elif 455 <= y <= 510 and 300 <= x <= 500:
                self.draw_menu()
            return
        if self.state == "garage":
            if 105 <= y <= 165 and x < WIDTH / 2:
                self.car_choice = (self.car_choice - 1) % len(CARS)
            elif 105 <= y <= 165 and x >= WIDTH / 2:
                self.car_choice = (self.car_choice + 1) % len(CARS)
            elif 355 <= y <= 400 and 260 <= x <= 540:
                self.color_choice = (self.color_choice + 1) % len(COLORS)
            elif 410 <= y <= 455 and 260 <= x <= 540:
                self.spoiler = not self.spoiler
            elif 465 <= y <= 510 and 260 <= x <= 540:
                self.neon = not self.neon
            elif 530 <= y <= 575 and 300 <= x <= 500:
                self.draw_menu()
                return
            self.draw_garage()
            return
        if self.state == "controls":
            if 510 <= y <= 560 and 300 <= x <= 500:
                self.draw_menu()
            return
        if self.state != "menu":
            return
        if 315 <= y <= 360 and 300 <= x <= 500:
            self.draw_garage()
            return
        elif 370 <= y <= 415 and 300 <= x <= 500:
            self.draw_settings()
            return
        elif 425 <= y <= 470 and 300 <= x <= 500:
            self.draw_controls()
            return
        elif 485 <= y <= 540 and 300 <= x <= 500:
            self.draw_mode_select()
            return
        self.draw_menu()

    def key_down(self, event):
        key = event.keysym.lower()
        already_pressed = key in self.keys
        self.keys.add(key)
        if key == "escape":
            if self.state == "settings":
                self.draw_menu()
            elif self.state == "garage":
                self.draw_menu()
            elif self.state == "controls":
                self.draw_menu()
            elif self.state == "mode_select":
                self.draw_menu()
            else:
                self.draw_menu()
        elif key == "f11" and not already_pressed:
            self.toggle_fullscreen()
        elif key == "space" and self.state in ("gameover", "mission_complete"):
            self.start_game(self.game_mode)
        elif self.state == "playing" and key == "a" and not already_pressed:
            self.target_lane = max(0, self.target_lane - 1)
        elif self.state == "playing" and key == "d" and not already_pressed:
            self.target_lane = min(2, self.target_lane + 1)
        elif self.state == "playing" and not already_pressed:
            if key == "q":
                self.signal = None if self.signal == "left" else "left"
            elif key == "e":
                self.signal = None if self.signal == "right" else "right"
            elif key == "f":
                self.headlights = not self.headlights

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def road_x(self, depth):
        return WIDTH / 2 + (depth - 0.5) * 70

    def road_width(self, depth):
        return 80 + depth * 570

    def draw_car(self, x, y, scale, color, player=False):
        w = (18 + self.car_choice * 3) * scale
        h = (34 + self.car_choice * 3) * scale
        headlights_on = not player or self.headlights

        self.canvas.create_oval(x - w, y - h / 2, x + w, y + h,
                                fill="#080b10", outline="")
        if player and self.neon:
            self.canvas.create_oval(x - w * 1.25, y - h / 2, x + w * 1.25, y + h,
                                    fill="#31dfff", outline="", stipple="gray50")

        self.canvas.create_polygon(
            x - w * 0.65, y - h, x + w * 0.65, y - h,
            x + w, y - h * 0.6, x + w, y + h * 0.65,
            x + w * 0.65, y + h, x - w * 0.65, y + h,
            x - w, y + h * 0.65, x - w, y - h * 0.6,
            fill=color, outline="#d9e0e8", width=max(1, int(scale * 2))
        )
        self.canvas.create_polygon(
            x - w * 0.58, y - h * 0.55, x + w * 0.58, y - h * 0.55,
            x + w * 0.42, y - h * 0.12, x - w * 0.42, y - h * 0.12,
            fill="#182c3d", outline="#9aa8b6"
        )
        for side in (-1, 1):
            self.canvas.create_oval(x + side * w * 0.55 - 3 * scale, y - h,
                                    x + side * w * 0.55 + 3 * scale, y - h + 5 * scale,
                                    fill="#fff1b0" if headlights_on else "#555968",
                                    outline="")
            if player and self.signal == ("left" if side < 0 else "right"):
                if self.signal_blink < 15:
                    self.canvas.create_oval(
                        x + side * w * 0.55 - 4 * scale, y - h - 2 * scale,
                        x + side * w * 0.55 + 4 * scale, y - h + 6 * scale,
                        fill="#ff9d32", outline=""
                    )
            self.canvas.create_rectangle(
                x + side * w * 0.55 - 3 * scale, y + h - 5 * scale,
                x + side * w * 0.55 + 3 * scale, y + h - 2 * scale,
                fill="#ff3548", outline=""
            )
        if player and self.spoiler:
            self.canvas.create_line(x - w * 0.8, y + h * 0.65,
                                    x + w * 0.8, y + h * 0.65,
                                    fill="#11151b", width=max(2, int(scale * 4)))

    def draw_scene(self):
        c = self.canvas
        sky_color, horizon_color, road_color, edge_color, light_color = (
            SCENE_PALETTES[self.time_period]
        )
        c.delete("all")
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill=sky_color, outline="")
        c.create_rectangle(0, 0, WIDTH, 205, fill=horizon_color, outline="")

        # Perspective road
        c.create_polygon(360, 190, 440, 190, 790, HEIGHT, 10, HEIGHT,
                         fill=road_color, outline="")
        c.create_polygon(350, 190, 360, 190, 10, HEIGHT, 0, HEIGHT,
                         fill=edge_color, outline="")
        c.create_polygon(440, 190, 450, 190, WIDTH, HEIGHT, 790, HEIGHT,
                         fill=edge_color, outline="")

        player_x = WIDTH / 2 + self.steering_offset()
        if self.headlights:
            c.create_polygon(
                player_x - 65, 490, player_x + 65, 490,
                player_x + 18, 245, player_x - 18, 245,
                fill="#d5d9a8", outline="", stipple="gray25"
            )

        # Lane markings move with speed.
        for lane in (1, 2):
            for i in range(12):
                depth = ((i / 12 + self.position * 0.22) % 1)
                y = 190 + depth * (HEIGHT - 190)
                half = self.road_width(depth) / 2
                x = WIDTH / 2 - half + (2 * half / 3) * lane
                mark_h = 3 + depth * 20
                c.create_rectangle(x - 2, y, x + 2, y + mark_h,
                                   fill="#d2d3cb", outline="")

        # Distant lights
        if self.time_period == 0:
            for i in range(8):
                x = 35 + (i * 103) % 730
                y = 35 + (i * 47) % 130
                c.create_oval(x, y, x + 3, y + 3, fill=light_color, outline="")

        for car in self.traffic:
            depth = car["depth"]
            y = 190 + depth * 360
            road_left = WIDTH / 2 - self.road_width(depth) / 2
            x = road_left + self.road_width(depth) * (car["lane"] + 0.5) / 3
            self.draw_car(x, y, 0.25 + depth * 0.85, car["color"])

        self.draw_car(player_x, 505, 1.25, COLORS[self.color_choice], player=True)

        c.create_rectangle(12, 12, 210, 77, fill="#11151b", outline="#647083")
        c.create_text(25, 27, anchor="nw", text=f"Hız: {int(self.speed * 220)} km/h",
                      fill="white", font=("Arial", 15, "bold"))
        score_text = (
            f"Görev: {min(self.score, MISSION_TARGET)}/{MISSION_TARGET}"
            if self.game_mode == "mission"
            else f"Puan: {self.score}"
        )
        c.create_text(25, 53, anchor="nw", text=score_text,
                      fill="#c6ccd6", font=("Arial", 12))
        c.create_text(
            WIDTH - 15, 20, anchor="ne",
            text="W/S: Hız  A/D: Şerit  Q/E: Sinyal  F: Far  Esc: Menü",
            fill="white", font=("Arial", 11)
        )
        signal_text = {
            "left": "Sol",
            "right": "Sağ",
            None: "Kapalı",
        }[self.signal]
        c.create_text(
            WIDTH - 15, 40, anchor="ne",
            text=f"Sinyal: {signal_text}   Far: {'Açık' if self.headlights else 'Kapalı'}",
            fill="#c6ccd6", font=("Arial", 10)
        )
        self.button(650, 55, 790, 95, "ANA MENÜ")

    def steering_offset(self):
        lane_width = self.road_width((505 - 190) / 360) / 3
        return self.steering * lane_width

    def tick(self):
        if self.state != "playing":
            return

        self.signal_blink = (self.signal_blink + 1) % 30
        target_steering = self.target_lane - 1
        steering_delta = target_steering - self.steering
        self.steering += max(-0.06, min(0.06, steering_delta))

        if "w" in self.keys:
            self.speed = min(1.0, self.speed + 0.012)
        elif "s" in self.keys:
            self.speed = max(0.08, self.speed - 0.025)
        else:
            self.speed = max(0.25, self.speed - 0.002)

        self.position += self.speed * 0.025
        self.spawn_timer += 1
        spawn_interval = int(
            (75 - self.speed * 45)
            * TRAFFIC_INTERVAL_MULTIPLIERS[self.traffic_density]
        )
        if self.spawn_timer > max(18, spawn_interval):
            self.spawn_timer = 0
            self.traffic.append({
                "lane": random.randrange(3),
                "depth": 0.0,
                "color": random.choice(["#e34b5f", "#e8e8e8", "#e5aa3a", "#597ce8"])
            })

        for car in self.traffic:
            car["depth"] += self.speed * 0.009
            if car["depth"] > 0.86 and abs(car["lane"] - (1 + self.steering)) < 0.48:
                self.state = "gameover"
                self.draw_scene()
                self.draw_gameover_overlay()
                self.fit_canvas()
                return

        passed = [car for car in self.traffic if car["depth"] > 1.1]
        self.score += len(passed)
        self.traffic = [car for car in self.traffic if car["depth"] <= 1.1]
        if self.game_mode == "mission" and self.score >= MISSION_TARGET:
            self.state = "mission_complete"
            self.draw_scene()
            self.draw_mission_complete_overlay()
            self.fit_canvas()
            return
        self.draw_scene()
        self.fit_canvas()
        self.root.after(30, self.tick)


if __name__ == "__main__":
    window = tk.Tk()
    DrivingGame(window)
    window.mainloop()