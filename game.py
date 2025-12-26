from browser import document, html, timer, ajax, window
from random import random

canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")
WIDTH, HEIGHT = 800, 400

# --- 圖片處理 ---
bird_img = html.IMG(src="/static/images/bird.png")
pig_img = html.IMG(src="/static/images/pig.png")

# 遊戲常數
SLING_X, SLING_Y = 120, 300
MAX_SHOTS = 10
NUM_PIGS = 10  # 修改：增加為 10 隻豬

# 遊戲狀態
shots_fired = 0
total_score = 0
mouse_down = False
mouse_pos = (SLING_X, SLING_Y)
projectile = None
sent = False
game_phase = "playing"
game_over_countdown = 0

# ------------------------------------------
# 類別
# ------------------------------------------
class Pig:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.w, self.h = 35, 35  # 稍微調小，避免畫面太擠
        self.alive = True
        self.house_blocks = [
            (0, 35, 100, 12),
            (0, -5, 12, 40),
            (88, -5, 12, 40),
            (0, -20, 100, 12)
        ]

    def draw(self):
        if self.alive:
            ctx.fillStyle = "#8B4513" # 鞍褐色 (木屋)
            for rx, ry, rw, rh in self.house_blocks:
                ctx.fillRect(self.x + rx - 30, self.y + ry, rw, rh)
            if pig_img.complete:
                ctx.drawImage(pig_img, self.x, self.y, self.w, self.h)

    def hit(self, px, py):
        return self.alive and self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def relocate(self, other_pigs):
        # 修改：調整間距讓 10 隻豬能均勻分佈
        MIN_DISTANCE = 65 
        MIN_X, MAX_X = 350, WIDTH - self.w - 50
        MIN_Y, MAX_Y = 150, HEIGHT - self.h - 60
        for _ in range(100): 
            new_x = MIN_X + random() * (MAX_X - MIN_X)
            new_y = MIN_Y + random() * (MAX_Y - MIN_Y)
            too_close = any(abs(new_x - p.x) < MIN_DISTANCE and abs(new_y - p.y) < MIN_DISTANCE 
                            for p in other_pigs if p is not self)
            if not too_close:
                self.x, self.y = new_x, new_y
                break

class Bird:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.w, self.h = 35, 35
        self.active = True

    def update(self):
        global total_score
        if not self.active: return
        self.vy += 0.35 # 重力
        self.x += self.vx
        self.y += self.vy
        if self.y > HEIGHT - self.h or self.x > WIDTH or self.x < 0:
            self.active = False
        for p in pigs:
            if p.hit(self.x + self.w / 2, self.y + self.h / 2):
                p.relocate(pigs)
                total_score += 50
                document["score_display"].text = str(total_score)
                self.active = False
                break

    def draw(self):
        if bird_img.complete:
            ctx.drawImage(bird_img, self.x, self.y, self.w, self.h)

# ------------------------------------------
# 遊戲邏輯與輸入處理
# ------------------------------------------
pigs = []

def init_level():
    global pigs
    pigs = [Pig(0, 0) for _ in range(NUM_PIGS)] # 初始化 10 隻
    for p in pigs: p.relocate(pigs)

def start_new_game():
    global shots_fired, total_score, projectile, sent, game_phase, game_over_countdown
    total_score, shots_fired = 0, 0
    document["score_display"].text = "0"
    projectile, sent = None, False
    game_phase = "playing"
    game_over_countdown = 0
    init_level()
    update_shots_remaining()

def update_shots_remaining():
    document["shots_remaining"].text = str(MAX_SHOTS - shots_fired)

def get_pos(evt):
    rect = canvas.getBoundingClientRect()
    scale_x = canvas.width / rect.width
    scale_y = canvas.height / rect.height
    if hasattr(evt, "touches") and len(evt.touches) > 0:
        cx, cy = evt.touches[0].clientX, evt.touches[0].clientY
    elif hasattr(evt, "changedTouches") and len(evt.changedTouches) > 0:
        cx, cy = evt.changedTouches[0].clientX, evt.changedTouches[0].clientY
    else:
        cx, cy = evt.clientX, evt.clientY
    return (cx - rect.left) * scale_x, (cy - rect.top) * scale_y

def mousedown(evt):
    global mouse_down, mouse_pos
    evt.preventDefault()
    if game_phase == "playing" and projectile is None and shots_fired < MAX_SHOTS:
        mouse_down = True
        mouse_pos = get_pos(evt)

def mousemove(evt):
    global mouse_pos
    evt.preventDefault()
    if mouse_down:
        mouse_pos = get_pos(evt)

def mouseup(evt):
    global mouse_down, projectile, shots_fired
    evt.preventDefault()
    if mouse_down:
        mouse_down = False
        end_pos = get_pos(evt)
        dx, dy = SLING_X - end_pos[0], SLING_Y - end_pos[1]
        projectile = Bird(SLING_X, SLING_Y, dx * 0.25, dy * 0.25)
        shots_fired += 1
        update_shots_remaining()

canvas.bind("mousedown", mousedown)
window.bind("mousemove", mousemove)
window.bind("mouseup", mouseup)
canvas.bind("touchstart", mousedown)
canvas.bind("touchmove", mousemove)
canvas.bind("touchend", mouseup)

# ------------------------------------------
# 繪圖與主迴圈
# ------------------------------------------
def draw_background():
    # 修改：自定義背景繪製
    # 天空
    ctx.fillStyle = "#87CEEB" 
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    # 草地
    ctx.fillStyle = "#228B22" 
    ctx.fillRect(0, HEIGHT - 50, WIDTH, 50)
    # 畫雲
    ctx.fillStyle = "white"
    for cx in [150, 450, 750]:
        ctx.beginPath()
        ctx.arc(cx, 60, 20, 0, 6.28)
        ctx.arc(cx+20, 55, 25, 0, 6.28)
        ctx.arc(cx+40, 60, 20, 0, 6.28)
        ctx.fill()

def draw_sling():
    if game_phase != "playing": return
    ctx.strokeStyle, ctx.lineWidth = "#4A2C2A", 6 
    if mouse_down:
        mx, my = mouse_pos
        ctx.beginPath()
        ctx.moveTo(SLING_X, SLING_Y)
        ctx.lineTo(mx, my)
        ctx.stroke()
        if bird_img.complete:
            ctx.drawImage(bird_img, mx - 17, my - 17, 35, 35)
    elif projectile is None and shots_fired < MAX_SHOTS:
        if bird_img.complete:
            ctx.drawImage(bird_img, SLING_X - 17, SLING_Y - 17, 35, 35)

def loop():
    global projectile, game_phase, game_over_countdown
    # 修改：使用背景繪製取代 clearRect
    draw_background()
    
    for p in pigs: p.draw()
    if projectile:
        projectile.update()
        projectile.draw()
        if not projectile.active: projectile = None

    if game_phase == "playing":
        draw_sling()
        if shots_fired >= MAX_SHOTS and projectile is None:
            game_phase, game_over_countdown = "game_over", 90
    elif game_phase == "game_over":
        ctx.fillStyle = "rgba(0, 0, 0, 0.6)"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)
        ctx.fillStyle, ctx.textAlign = "white", "center"
        ctx.font = "bold 40px Arial"
        ctx.fillText("Game Over", WIDTH // 2, HEIGHT // 2 - 20)
        ctx.fillText(f"Score: {total_score}", WIDTH // 2, HEIGHT // 2 + 30)
        game_over_countdown -= 1
        if game_over_countdown <= 0: start_new_game()

timer.set_interval(loop, 30)
start_new_game()