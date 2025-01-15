import pygame
import math
import random
import os

# 初始化Pygame
pygame.init()

# 常量定义
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 144
PLAYER_SIZE = 40
ENEMY_SIZE = 30
CROSSHAIR_SIZE = 20
TITLE_FONT_SIZE = 64
BUTTON_FONT_SIZE = 36
TUTORIAL_FONT_SIZE = 24

# 加载资源
GAME_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(GAME_DIR, "assets")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
BULLET_INFO = {
    "normal": {
        "color": WHITE,
        "description": "Normal Bullet (Enemy: -10, Self: -10)"
    },
    "holy": {
        "color": RED,
        "description": "Holy Bullet (Enemy: +40, Self: +10, San: +20)"
    },
    "evil": {
        "color": BLUE,
        "description": "Evil Bullet (Enemy: -20, Self: -20, San: -30)"
    }
}

class Bullet:
    DAMAGE_TABLE = {
        "normal": {"enemy": -10, "player_health": -10, "player_san": 0},
        "holy": {"enemy": 40, "player_health": 10, "player_san": 20},
        "evil": {"enemy": -20, "player_health": -20, "player_san": -30}
    }

    def __init__(self, bullet_type):  # 用于弹夹中的子弹
        self.type = bullet_type
        self.color = {
            "normal": WHITE,
            "holy": RED,
            "evil": BLUE
        }[bullet_type]

    @classmethod
    def create_active(cls, x, y, target_x, target_y, bullet_type):  # 用于发射的子弹
        bullet = cls(bullet_type)
        bullet.x = x
        bullet.y = y
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx * dx + dy * dy)
        bullet.speed = 10
        bullet.dx = (dx/dist) * bullet.speed if dist != 0 else 0
        bullet.dy = (dy/dist) * bullet.speed if dist != 0 else 0
        bullet.radius = 5
        bullet.alive = True
        return bullet

    def update(self):
        self.x += self.dx
        self.y += self.dy
        if (self.x < 0 or self.x > SCREEN_WIDTH or 
            self.y < 0 or self.y > SCREEN_HEIGHT):
            self.alive = False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def get_damage(self, target_type):
        return self.DAMAGE_TABLE[self.type][target_type]

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.health = 100
        self.san = 100
        self.bullets = []  # 初始时无子弹
        self.max_bullets = 6
        self.rect = pygame.Rect(self.x - PLAYER_SIZE//2, 
                              self.y - PLAYER_SIZE//2, 
                              PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 5
        self.alive = True
        self.last_san_decay = pygame.time.get_ticks()
        self.san_decay_rate = 1000  # 每秒减少1点san值
        self.last_collision_time = 0
        self.collision_cooldown = 500  # 碰撞伤害冷却时间（毫秒）
        self.knockback_speed = 10  # 击退速度
        self.reloading = False
        self.reload_start_time = 0
        self.reload_delay = 400  # 增加到400ms每颗子弹
        self.reload_finish_time = 0
        self.reload_display_duration = 1000  # 装填完成后显示1秒
        self.reload_bullets = []  # 用于动画显示的子弹
        self.reload_height = 30  # 装填动画显示在角色上方的距离
        self.empty_mag_hint_time = 0  # 空弹匣提示时间
        self.hint_duration = 1000  # 提示显示时间（毫秒）

    def reload(self):
        self.bullets = []
        bullet_types = ["normal", "holy", "evil"]
        for _ in range(self.max_bullets):
            self.bullets.append(Bullet(random.choice(bullet_types)))

    def shoot(self, target_is_self):
        if self.reloading:  # 装填时不能射击
            return None
        if not self.bullets:
            # 记录提示显示时间
            self.empty_mag_hint_time = pygame.time.get_ticks()
            return None
        bullet = self.bullets.pop(0)
        if target_is_self:
            self.take_damage(bullet.type)
        return bullet

    def move(self, dx, dy):
        self.x = max(PLAYER_SIZE//2, min(SCREEN_WIDTH - PLAYER_SIZE//2, self.x + dx))
        self.y = max(PLAYER_SIZE//2, min(SCREEN_HEIGHT - PLAYER_SIZE//2, self.y + dy))
        self.rect.center = (self.x, self.y)

    def update(self):
        # 处理san值衰减
        current_time = pygame.time.get_ticks()
        if current_time - self.last_san_decay >= self.san_decay_rate:
            self.san -= 1
            self.last_san_decay = current_time
        
        # 检查死亡条件
        if self.health <= 0 or self.san <= 0:
            self.alive = False

    def take_damage(self, bullet_type):
        bullet = Bullet(bullet_type)  # 临时创建子弹对象获取伤害值
        self.health += bullet.get_damage("player_health")
        self.san += bullet.get_damage("player_san")
        self.health = min(100, max(0, self.health))  # 限制在0-100之间
        self.san = min(100, max(0, self.san))

    def take_collision_damage(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_collision_time >= self.collision_cooldown:
            self.health -= 10
            self.last_collision_time = current_time
            self.health = max(0, self.health)

    def apply_knockback(self, other_x, other_y):
        dx = self.x - other_x
        dy = self.y - other_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist != 0:
            self.x += (dx/dist) * self.knockback_speed
            self.y += (dy/dist) * self.knockback_speed
        # 确保不会移出屏幕
        self.x = max(PLAYER_SIZE//2, min(SCREEN_WIDTH - PLAYER_SIZE//2, self.x))
        self.y = max(PLAYER_SIZE//2, min(SCREEN_HEIGHT - PLAYER_SIZE//2, self.y))
        self.rect.center = (self.x, self.y)

    def start_reload(self):
        if not self.reloading:
            self.reloading = True
            self.reload_start_time = pygame.time.get_ticks()
            self.reload_bullets = []
            bullet_types = ["normal", "holy", "evil"]
            # 预生成所有要装填的子弹
            self.bullets_to_reload = [Bullet(random.choice(bullet_types)) 
                                    for _ in range(self.max_bullets)]

    def update_reload(self):
        if not self.reloading:
            return
            
        current_time = pygame.time.get_ticks()
        
        # 如果已经装填完所有子弹
        if len(self.reload_bullets) >= self.max_bullets:
            # 如果还没设置完成时间，设置它
            if self.reload_finish_time == 0:
                self.reload_finish_time = current_time
            # 检查是否显示时间已到
            elif current_time - self.reload_finish_time >= self.reload_display_duration:
                self.bullets = self.reload_bullets.copy()
                self.reload_bullets = []
                self.reloading = False
                self.reload_finish_time = 0
            return

        # 正常装填过程
        bullets_to_load = (current_time - self.reload_start_time) // self.reload_delay
        
        # 装填新子弹
        while len(self.reload_bullets) < bullets_to_load and len(self.reload_bullets) < self.max_bullets:
            self.reload_bullets.append(self.bullets_to_reload[len(self.reload_bullets)])

    def draw_reload_animation(self, screen):
        if not self.reloading:
            return
            
        # 计算第一颗子弹的位置
        start_x = self.x - (self.max_bullets * 20) // 2  # 修改为总是显示最大数量的位置
        y = self.y - self.reload_height
        
        # 先绘制未装填的位置（灰色）
        for i in range(self.max_bullets):
            pygame.draw.circle(screen, (60, 60, 60), 
                             (int(start_x + i * 20), int(y)), 5)
        
        # 再绘制已装填的子弹
        for i, bullet in enumerate(self.reload_bullets):
            pygame.draw.circle(screen, bullet.color, 
                             (int(start_x + i * 20), int(y)), 5)

    def draw_ammo_count(self, screen):
        # 在左上角显示子弹数量，位于血量和san值下方
        font = pygame.font.Font(None, 36)
        ammo_text = font.render(f"Ammo: {len(self.bullets)}/{self.max_bullets}", True, WHITE)
        screen.blit(ammo_text, (10, 90))  # y坐标在san值(50)下方

        # 如果最近尝试空弹射击，显示提示
        current_time = pygame.time.get_ticks()
        if current_time - self.empty_mag_hint_time < self.hint_duration:
            hint_text = font.render("Press R to reload", True, WHITE)
            text_width = hint_text.get_width()
            screen.blit(hint_text, (SCREEN_WIDTH//2 - text_width//2, SCREEN_HEIGHT - 100))

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x - ENEMY_SIZE//2, 
                              y - ENEMY_SIZE//2, 
                              ENEMY_SIZE, ENEMY_SIZE)
        self.max_health = 100
        self.health = self.max_health
        self.speed = 2
        self.last_collision_time = 0
        self.collision_cooldown = 500
        self.knockback_speed = 8  # 击退速度
        
    def move_towards_player(self, player_x, player_y, enemies):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        # 计算移动方向
        move_x = (dx/dist) * self.speed if dist != 0 else 0
        move_y = (dy/dist) * self.speed if dist != 0 else 0
        
        # 临时保存新位置
        new_x = self.x + move_x
        new_y = self.y + move_y
        new_rect = pygame.Rect(new_x - ENEMY_SIZE//2, 
                             new_y - ENEMY_SIZE//2, 
                             ENEMY_SIZE, ENEMY_SIZE)
        
        # 检查与其他敌人的碰撞
        collided = False
        for other in enemies:
            if other != self and new_rect.colliderect(other.rect):
                collided = True
                # 发生碰撞时，双方都会被击退
                self.apply_knockback(other.x, other.y)
                other.apply_knockback(self.x, self.y)
                break
        
        # 如果没有碰撞则正常移动
        if not collided:
            self.x = new_x
            self.y = new_y
            self.rect.center = (self.x, self.y)

    def apply_knockback(self, other_x, other_y):
        dx = self.x - other_x
        dy = self.y - other_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist != 0:
            self.x += (dx/dist) * self.knockback_speed
            self.y += (dy/dist) * self.knockback_speed
        # 确保不会移出屏幕
        self.x = max(ENEMY_SIZE//2, min(SCREEN_WIDTH - ENEMY_SIZE//2, self.x))
        self.y = max(ENEMY_SIZE//2, min(SCREEN_HEIGHT - ENEMY_SIZE//2, self.y))
        self.rect.center = (self.x, self.y)

    def draw(self, screen):
        # 绘制敌人
        pygame.draw.circle(screen, BLUE, (self.x, self.y), ENEMY_SIZE//2)
        
        # 绘制血量条
        bar_width = 40
        bar_height = 5
        bar_pos = (self.x - bar_width//2, self.y - ENEMY_SIZE//2 - 10)
        # 血条背景
        pygame.draw.rect(screen, (60, 60, 60), 
                        (bar_pos[0], bar_pos[1], bar_width, bar_height))
        # 当前血量
        health_width = int(bar_width * (self.health / self.max_health))
        pygame.draw.rect(screen, RED, 
                        (bar_pos[0], bar_pos[1], health_width, bar_height))

    def take_damage(self, bullet_type):
        bullet = Bullet(bullet_type)
        damage = bullet.get_damage("enemy")
        self.health += damage  # 因为damage是负数，所以用加
        return self.health <= 0

    def take_collision_damage(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_collision_time >= self.collision_cooldown:
            self.health -= 10
            self.last_collision_time = current_time
            self.health = max(0, self.health)
            return self.health <= 0
        return False

class DamageNumber:
    def __init__(self, x, y, value, color):
        self.x = x
        self.y = y
        self.value = value
        self.color = color
        self.life = 30  # 持续帧数
        self.speed = 2  # 向上飘动速度
        self.font = pygame.font.Font(None, 24)

    def update(self):
        self.y -= self.speed
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        # 根据生命值计算透明度
        alpha = int(255 * (self.life / 30))
        text = self.font.render(f"{'+' if self.value > 0 else ''}{self.value}", True, self.color)
        # 创建一个临时surface来支持透明度
        temp = pygame.Surface(text.get_size()).convert_alpha()
        temp.fill((0, 0, 0, 0))
        temp.blit(text, (0, 0))
        temp.set_alpha(alpha)
        screen.blit(temp, (self.x, self.y))

class Button:
    def __init__(self, x, y, width, height, text, font_size=BUTTON_FONT_SIZE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.color = WHITE
        self.hover_color = GREEN
        self.is_hovered = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, 2)
        text_surface = self.font.render(self.text, True, color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

def show_menu(screen):
    title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
    tutorial_font = pygame.font.Font(None, TUTORIAL_FONT_SIZE)
    
    start_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50, "Start Game")
    
    tutorial_text = [
        "WASD - Move",
        "Left Click - Shoot enemies",
        "Right Click - Shoot yourself",
        "R - Reload"
        "P - Pause"
    ]
    
    running = True
    while running:
        screen.fill((50, 50, 50))
        
        # 绘制标题
        title = title_font.render("Destiny Demon Gun", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title, title_rect)
        
        # 绘制按钮
        start_button.draw(screen)
        
        # 绘制教程
        for i, text in enumerate(tutorial_text):
            tutorial = tutorial_font.render(text, True, WHITE)
            screen.blit(tutorial, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT*2//3 + i*30))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if start_button.handle_event(event):
                return True
                
        pygame.display.flip()
    return False

def show_game_over(screen, score=0):
    font = pygame.font.Font(None, TITLE_FONT_SIZE)
    menu_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50, 200, 50, "Back to Menu")
    
    running = True
    while running:
        screen.fill((50, 50, 50))
        
        # 绘制游戏结束文本
        game_over = font.render("Game Over", True, RED)
        game_over_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(game_over, game_over_rect)
        
        menu_button.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if menu_button.handle_event(event):
                return True
                
        pygame.display.flip()
    return False

def show_pause_menu(screen):
    font = pygame.font.Font(None, TITLE_FONT_SIZE)
    resume_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50, "Resume Game")
    menu_button = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 70, 200, 50, "Back to Menu")
    
    # 创建半透明遮罩
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    
    while True:
        # 绘制半透明遮罩
        screen.blit(overlay, (0, 0))
        
        # 绘制暂停文本
        pause_text = font.render("Paused", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(pause_text, pause_rect)
        
        # 绘制按钮
        resume_button.draw(screen)
        menu_button.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                return "resume"
            if resume_button.handle_event(event):
                return "resume"
            if menu_button.handle_event(event):
                return "menu"
                
        pygame.display.flip()

def draw_bullet_info(screen):
    font = pygame.font.Font(None, 24)
    x = 200  # 左对齐
    y = 10  # 从顶部开始
    
    # 绘制标题
    title = font.render("Bullet Types:", True, WHITE)
    screen.blit(title, (x, y))
    y += 50  # 标题后的间距
    
    # 竖向绘制每种子弹的信息
    for bullet_type, info in BULLET_INFO.items():
        # 绘制子弹示例
        pygame.draw.circle(screen, info["color"], (x + 10, y + 8), 5)
        # 绘制说明文字
        text = font.render(info["description"], True, WHITE)
        screen.blit(text, (x + 25, y))
        y += 25  # 每行之间的间距

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Destiny Demon Gun")
    
    running = True
    while running:
        # 显示菜单
        if not show_menu(screen):
            break
            
        # 游戏主循环
        clock = pygame.time.Clock()
        player = Player()
        pygame.mouse.set_visible(False)
        enemies = [Enemy(random.randint(0, SCREEN_WIDTH), 
                        random.randint(0, SCREEN_HEIGHT)) 
                  for _ in range(3)]
        active_bullets = []
        damage_numbers = []
        
        game_running = True
        while game_running:
            # 处理输入
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_d] - keys[pygame.K_a]) * player.speed
            dy = (keys[pygame.K_s] - keys[pygame.K_w]) * player.speed
            player.move(dx, dy)
            
            # 更新敌人
            for enemy in enemies:
                enemy.move_towards_player(player.x, player.y, enemies)
            
            # 更新子弹
            for bullet in active_bullets[:]:
                bullet.update()
                if not bullet.alive:
                    active_bullets.remove(bullet)
            
            # 更新伤害数字
            damage_numbers = [num for num in damage_numbers if num.update()]
            
            # 子弹碰撞检测
            for bullet in active_bullets[:]:
                bullet_rect = pygame.Rect(bullet.x - bullet.radius, 
                                        bullet.y - bullet.radius,
                                        bullet.radius * 2, 
                                        bullet.radius * 2)
                
                for enemy in enemies[:]:
                    if enemy.rect.colliderect(bullet_rect):
                        # 获取伤害值
                        damage = bullet.get_damage("enemy")
                        # 造成伤害并显示伤害数字
                        if enemy.take_damage(bullet.type):
                            enemies.remove(enemy)
                        damage_numbers.append(DamageNumber(
                            enemy.x, enemy.y - 20, damage, RED))
                        active_bullets.remove(bullet)
                        break
            
            # 处理玩家和敌人的碰撞
            for enemy in enemies[:]:
                if player.rect.colliderect(enemy.rect):
                    # 造成伤害
                    player.take_collision_damage()
                    if enemy.take_collision_damage():
                        enemies.remove(enemy)
                        continue
                    
                    # 击退效果
                    player.apply_knockback(enemy.x, enemy.y)
                    enemy.apply_knockback(player.x, player.y)
            
            # 更新装填动画
            player.update_reload()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # P键暂停
                        pygame.mouse.set_visible(True)
                        pause_result = show_pause_menu(screen)
                        if pause_result == "quit":
                            game_running = False
                            running = False
                        elif pause_result == "menu":
                            game_running = False
                        elif pause_result == "resume":
                            pygame.mouse.set_visible(False)
                    elif event.key == pygame.K_r:  # R键装填
                        player.start_reload()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if event.button == 1:  # 左键射击敌人
                        bullet = player.shoot(False)
                        if bullet:
                            active_bullets.append(
                                Bullet.create_active(player.x, player.y, 
                                                  mouse_x, mouse_y, 
                                                  bullet.type))
                    elif event.button == 3:  # 右键射击自己
                        bullet = player.shoot(True)
                        if bullet:
                            health_change = bullet.get_damage("player_health")
                            san_change = bullet.get_damage("player_san")
                            # 显示血量变化
                            if health_change != 0:
                                damage_numbers.append(DamageNumber(
                                    player.x + 20, player.y - 20, 
                                    health_change, RED if health_change < 0 else GREEN))
                            # 显示san值变化
                            if san_change != 0:
                                damage_numbers.append(DamageNumber(
                                    player.x - 20, player.y - 20, 
                                    san_change, BLUE))
            
            # 绘制
            screen.fill((50, 50, 50))  # 深灰色背景
            
            # 绘制网格
            for x in range(0, SCREEN_WIDTH, 50):
                pygame.draw.line(screen, (70, 70, 70), (x, 0), (x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, 50):
                pygame.draw.line(screen, (70, 70, 70), (0, y), (SCREEN_WIDTH, y))
            
            # 绘制玩家
            pygame.draw.circle(screen, RED, (player.x, player.y), PLAYER_SIZE//2)
            
            # 绘制敌人
            for enemy in enemies:
                enemy.draw(screen)
            
            # 绘制准星
            mouse_x, mouse_y = pygame.mouse.get_pos()
            pygame.draw.circle(screen, WHITE, (mouse_x, mouse_y), CROSSHAIR_SIZE//2, 2)
            pygame.draw.line(screen, WHITE, 
                            (mouse_x - CROSSHAIR_SIZE//2, mouse_y),
                            (mouse_x + CROSSHAIR_SIZE//2, mouse_y), 2)
            pygame.draw.line(screen, WHITE,
                            (mouse_x, mouse_y - CROSSHAIR_SIZE//2),
                            (mouse_x, mouse_y + CROSSHAIR_SIZE//2), 2)
            
            # 绘制玩家状态
            font = pygame.font.Font(None, 36)
            health_text = font.render(f"Health: {player.health}", True, WHITE)
            san_text = font.render(f"San: {player.san}", True, WHITE)
            screen.blit(health_text, (10, 10))
            screen.blit(san_text, (10, 50))
            
            # 绘制装填动画
            player.draw_reload_animation(screen)
            
            # 显示弹药数量
            player.draw_ammo_count(screen)
            
            # 绘制子弹
            for bullet in active_bullets:
                bullet.draw(screen)
            
            # 绘制伤害数字
            for num in damage_numbers:
                num.draw(screen)
            
            # 绘制子弹信息
            draw_bullet_info(screen)
            
            pygame.display.flip()
            clock.tick(FPS)

            # 更新玩家状态
            player.update()
            if not player.alive:
                pygame.mouse.set_visible(True)
                if not show_game_over(screen):
                    game_running = False
                break
                
            pygame.display.flip()
            clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main() 