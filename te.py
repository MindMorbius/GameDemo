import pygame
import math
from enum import Enum
import random

# 初始化
pygame.init()
WINDOW_SIZE = (1200, 900)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("音律战境")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

class WaveState(Enum):
    EXPANDING = 1
    CONTRACTING = 2

class NoteEnergy:
    def __init__(self, angle, ring_index):
        self.angle = angle
        self.ring_index = ring_index
        self.value = (5 - ring_index) * 2  # 最外圈2点，每靠近中心+2
        self.collected = False
        print(f"Created note energy at ring {ring_index} with value {self.value}")  # Debug

class Wave:
    def __init__(self):
        self.radius = 0
        self.state = WaveState.EXPANDING
        self.speed = 2  # 降低音波速度
        self.ring_radii = [50, 100, 150, 200, 250, 300]
        self.ring_width = 15  # 增加音波宽度，让音波在圆环上停留更久
        self.absorbed_positions = []
        self.wave_id = 0
        self.note_energies = []
        self.rings_passed = set()
        self.warriors_energized = set()
        
    def is_on_ring(self, ring_index):
        # 检查音波是否在指定圆环上
        ring_radius = self.ring_radii[ring_index]
        return abs(self.radius - ring_radius) <= self.ring_width / 2
        
    def update(self):
        old_radius = self.radius
        
        if self.state == WaveState.EXPANDING:
            self.radius += self.speed
            # 检查是否首次经过某个圆环
            for i, ring_radius in enumerate(self.ring_radii):
                if (old_radius < ring_radius - self.ring_width/2 and 
                    self.radius >= ring_radius - self.ring_width/2):
                    if (self.wave_id, i) not in self.rings_passed:
                        print(f"Wave {self.wave_id} passing ring {i}")  # Debug
                        self.spawn_note_energies(i)
                        self.rings_passed.add((self.wave_id, i))
            
            if self.radius >= max(self.ring_radii):
                self.state = WaveState.CONTRACTING
        else:
            self.radius -= self.speed
            if self.radius <= 0:
                self.state = WaveState.EXPANDING
                self.wave_id += 1
                self.absorbed_positions.clear()
                
    def spawn_note_energies(self, ring_index):
        # 在圆环上随机生成1-2个音符能量
        num_notes = random.randint(1, 2)
        for _ in range(num_notes):
            angle = random.uniform(0, 2 * math.pi)
            note = NoteEnergy(angle, ring_index)
            print(f"Spawned note at ring {ring_index}, angle {angle:.2f} with value {note.value}")  # Debug
            self.note_energies.append(note)
            
    def draw(self, screen):
        # 绘制音波
        pygame.draw.circle(screen, BLUE, (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2), 
                         self.radius, 2)
        # 绘制固定圆环
        for radius in self.ring_radii:
            pygame.draw.circle(screen, WHITE, 
                             (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2), 
                             radius, self.ring_width)
        # 绘制音符能量
        for note in self.note_energies:
            if not note.collected:
                x = (WINDOW_SIZE[0]//2 + math.cos(note.angle) * 
                     self.ring_radii[note.ring_index])
                y = (WINDOW_SIZE[1]//2 + math.sin(note.angle) * 
                     self.ring_radii[note.ring_index])
                pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 6)

    def give_initial_energy(self, warrior):
        # 音波第一次经过战士时给予能量
        warrior_key = (self.wave_id, id(warrior))
        if warrior_key not in self.warriors_energized:
            warrior.note_energy += 2  # 提供2点初始能量
            # 50%进入集体能量池
            collective_gain = 1
            NoteWarrior.collective_energy = min(
                NoteWarrior.collective_energy + collective_gain,
                NoteWarrior.COLLECTIVE_ENERGY_MAX
            )
            self.warriors_energized.add(warrior_key)
            print(f"Wave {self.wave_id} gave warrior initial energy. Warrior energy: {warrior.note_energy}, Added to collective: {collective_gain}")

class NoteWarrior:  # 原Enemy类改名
    def __init__(self, angle, strategy, warrior_id):
        self.angle = angle
        self.ring_index = 5
        self.note_energy = 0
        self.move_cooldown = 0
        self.health = 100
        self.angular_speed = 0.05
        self.move_direction = 0
        self.is_moving = False
        self.energy_change_display = []
        self.strategy = strategy
        self.warrior_id = warrior_id  # 存储战士ID
        
    def add_energy_display(self, value):
        # 添加能量变化显示
        self.energy_change_display.append((value, 60))  # 显示60帧
        
    def check_ring_energy(self, wave):
        # 检查当前圆环上是否还有可收集的能量
        for note in wave.note_energies:
            if (not note.collected and note.ring_index == self.ring_index):
                return True
        return False
        
    def estimate_melody_cost(self, target_ring):
        # 估算搭乘冲击波到达目标圆环需要的能量
        total_cost = 0
        current_ring = self.ring_index
        while current_ring > target_ring:
            cost = (5 - current_ring) * 2 * 0.5  # 50%的正常消耗
            total_cost += cost
            current_ring -= 1
        return total_cost
        
    def should_join_melody_wave(self):
        # 只根据能量和策略判断是否加入
        if self.strategy == 'aggressive':
            return self.note_energy >= 30
        elif self.strategy == 'balanced':
            return self.note_energy >= 50
        else:  # conservative
            return self.note_energy >= 80
                
    def calculate_ring_energy(self, wave, ring_index):
        # 计算指定圆环上的可用能量总和
        total_energy = 0
        for note in wave.note_energies:
            if not note.collected and note.ring_index == ring_index:
                total_energy += (5 - ring_index) * 2
        return total_energy
        
    def find_best_ring(self, wave):
        # 寻找能量最丰富的圆环，考虑战略偏好
        best_ring = self.ring_index
        max_value = 0
        
        for i in range(6):  # 检查所有圆环
            ring_energy = self.calculate_ring_energy(wave, i)
            if ring_energy == 0:
                continue
                
            # 根据策略调整圆环价值
            strategic_value = ring_energy
            if self.strategy == 'aggressive':
                # 激进型更看重内圈
                strategic_value *= (6 - i) * 1.2
            elif self.strategy == 'balanced':
                # 平衡型偏好中间层级
                if 2 <= i <= 3:
                    strategic_value *= 1.5
            else:  # conservative
                # 保守型更看重外圈的安全能量
                strategic_value *= (i + 1) * 1.1
                
            # 考虑移动成本
            move_cost = abs(i - self.ring_index) * 2
            strategic_value -= move_cost
            
            if strategic_value > max_value:
                max_value = strategic_value
                best_ring = i
                
        return best_ring, max_value
        
    def move(self, wave):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
            
        # 环形移动（必须在音波上）
        if wave.is_on_ring(self.ring_index):
            # 检查周围是否有音符能量
            nearby_energy = False
            closest_angle_diff = math.pi
            best_direction = 0
            
            # 寻找最近的能量
            for note in wave.note_energies:
                if not note.collected and note.ring_index == self.ring_index:
                    angle_diff = (note.angle - self.angle + math.pi) % (2 * math.pi) - math.pi
                    if abs(angle_diff) < abs(closest_angle_diff):
                        closest_angle_diff = angle_diff
                        best_direction = 1 if angle_diff > 0 else -1
                        nearby_energy = True
            
            if nearby_energy:
                self.move_direction = best_direction
                self.is_moving = True
                print(f"Warrior at ring {self.ring_index} moving towards energy, angle: {self.angle:.2f}")  # Debug
            else:
                self.is_moving = False
                self.move_direction = 0
            
            if self.is_moving:
                old_angle = self.angle
                self.angle = (self.angle + self.angular_speed * self.move_direction) % (2 * math.pi)
                print(f"Warrior moved from {old_angle:.2f} to {self.angle:.2f}")  # Debug
        else:
            self.is_moving = False
            self.move_direction = 0
            
        # 跨环移动时考虑策略
        if not self.check_ring_energy(wave):
            best_ring, max_value = self.find_best_ring(wave)
            
            if best_ring != self.ring_index:
                can_move = (best_ring < self.ring_index and 
                           wave.is_on_ring(best_ring) and 
                           wave.state == WaveState.CONTRACTING) or \
                          (best_ring > self.ring_index and 
                           wave.is_on_ring(best_ring) and 
                           wave.state == WaveState.EXPANDING)
                           
                if can_move:
                    cost = (5 - best_ring) * 2
                    min_reserve = 5 if self.strategy == 'aggressive' else (
                        8 if self.strategy == 'balanced' else 12)
                    if self.note_energy >= cost + min_reserve:
                        print(f"{self.strategy} warrior moving to ring {best_ring} with value {max_value}")
                        self.ring_index = best_ring
                        self.note_energy -= cost
                        self.add_energy_display(-cost)
                        self.move_cooldown = 30
                        self.is_moving = False

    def draw(self, screen, ring_radii):
        x = WINDOW_SIZE[0]//2 + math.cos(self.angle) * ring_radii[self.ring_index]
        y = WINDOW_SIZE[1]//2 + math.sin(self.angle) * ring_radii[self.ring_index]
        # 绘制战士圆球
        pygame.draw.circle(screen, RED, (int(x), int(y)), 10)
        if self.is_moving:
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 12, 1)
            
        # 绘制战士ID
        font = pygame.font.Font(None, 20)
        id_text = str(self.warrior_id)
        text_surface = font.render(id_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(int(x), int(y)))
        screen.blit(text_surface, text_rect)

    def check_wave_collision(self, wave):
        # 检查是否在音波上并收集能量
        if wave.is_on_ring(self.ring_index):
            wave.give_initial_energy(self)  # 检查是否需要给予初始能量
            if self.collect_note_energy(wave):  # 收集音符能量
                print(f"Warrior at ring {self.ring_index} collected energy, now has {self.note_energy}")  # Debug

    def collect_note_energy(self, wave):
        # 检查当前圆环上是否有可收集的能量
        for note in wave.note_energies:
            if (not note.collected and 
                note.ring_index == self.ring_index and
                abs((note.angle - self.angle + math.pi) % (2 * math.pi) - math.pi) < 0.2):  # 修正角度计算
                note.collected = True
                collected_value = (5 - note.ring_index) * 2  # 重新计算能量值
                self.note_energy += collected_value
                self.add_energy_display(collected_value)  # 显示获得的能量
                
                collective_gain = collected_value // 2
                NoteWarrior.collective_energy = min(
                    NoteWarrior.collective_energy + collective_gain,
                    NoteWarrior.COLLECTIVE_ENERGY_MAX
                )
                # 打印调试信息
                print(f"Warrior at angle {self.angle:.2f} collected energy at ring {note.ring_index}")
                print(f"Base value: {collected_value}, Added to warrior: {collected_value}, New warrior energy: {self.note_energy}")
                print(f"Added to collective: {collective_gain}, Total collective: {NoteWarrior.collective_energy}")
                return True
        return False

# 添加集体能量池
NoteWarrior.collective_energy = 0
NoteWarrior.COLLECTIVE_ENERGY_MAX = 20  # 满能量值

class Boss:  # 原Player类改名
    def __init__(self):
        self.x = WINDOW_SIZE[0] // 2
        self.y = WINDOW_SIZE[1] // 2
        self.health = 200
        self.energy = 0
        
    def draw(self, screen):
        # 绘制Boss主体
        pygame.draw.circle(screen, RED, (self.x, self.y), 20)
        
        # 绘制朝向鼠标的光标
        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - self.y, mx - self.x)
        cursor_x = self.x + math.cos(angle) * 30
        cursor_y = self.y + math.sin(angle) * 30
        pygame.draw.circle(screen, WHITE, (int(cursor_x), int(cursor_y)), 3)
        pygame.draw.line(screen, WHITE, (self.x, self.y), (cursor_x, cursor_y), 2)

class Missile:
    def __init__(self, angle):
        self.x = WINDOW_SIZE[0] // 2
        self.y = WINDOW_SIZE[1] // 2
        self.angle = angle
        self.speed = 5
        self.active = True
    
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        # 超出屏幕边界时销毁
        if (self.x < 0 or self.x > WINDOW_SIZE[0] or 
            self.y < 0 or self.y > WINDOW_SIZE[1]):
            self.active = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 5)
    
    def check_enemy_collision(self, enemy, ring_radii):
        enemy_x = WINDOW_SIZE[0]//2 + math.cos(enemy.angle) * ring_radii[enemy.ring_index]
        enemy_y = WINDOW_SIZE[1]//2 + math.sin(enemy.angle) * ring_radii[enemy.ring_index]
        distance = math.sqrt((self.x - enemy_x)**2 + (self.y - enemy_y)**2)
        if distance < 15:  # 碰撞半径
            enemy.health -= 20
            enemy.ring_index = min(5, enemy.ring_index + 1)  # 击中后向外移动
            self.active = False
            return True
        return False

class MelodyWave:
    def __init__(self, boss, enemies):  # 添加 enemies 参数
        self.radius = max(Wave().ring_radii)
        self.speed = 2
        self.active = True
        self.warriors = []
        self.ring_width = 10
        self.boss = boss
        self.enemies = enemies  # 存储 enemies 引用

    def add_warrior(self, warrior):  # 添加缺失的方法
        self.warriors.append(warrior)
        
    def attack_boss(self):
        total_damage = sum(w.note_energy for w in self.warriors)
        self.boss.health -= total_damage  # 使用存储的boss引用
        
    def return_warriors(self):
        for warrior in self.warriors:
            warrior.ring_index = 5  # 返回最外圈
            warrior.note_energy = 0  # 消耗所有能量
            
    def update(self):
        old_radius = self.radius
        self.radius -= self.speed
        
        ring_radii = Wave().ring_radii
        for i, radius in enumerate(ring_radii):
            if old_radius > radius and self.radius <= radius:
                for warrior in [w for w in self.warriors if w.ring_index == i]:
                    warrior.note_energy += 10
                # 使用实例变量 self.enemies
                for warrior in [w for w in self.enemies if w.ring_index == i and w not in self.warriors]:
                    if warrior.should_join_melody_wave():
                        self.add_warrior(warrior)
                        print(f"Warrior {warrior.warrior_id} joined melody wave at ring {i}")
        
        if self.radius <= 20:
            self.active = False
            self.attack_boss()
            self.return_warriors()

    def draw(self, screen):
        # 绘制旋律冲击波
        pygame.draw.circle(screen, RED, 
                         (WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2), 
                         int(self.radius), 3)
        # 绘制搭载的战士
        for warrior in self.warriors:
            x = (WINDOW_SIZE[0]//2 + math.cos(warrior.angle) * self.radius)
            y = (WINDOW_SIZE[1]//2 + math.sin(warrior.angle) * self.radius)
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 10)
            
            # 绘制能量变化
            for value, timer in warrior.energy_change_display:
                if timer > 0:
                    color = GREEN if value > 0 else RED
                    text = f"+{value}" if value > 0 else str(value)
                    text_surface = pygame.font.Font(None, 24).render(text, True, color)
                    screen.blit(text_surface, (int(x) + 15, int(y) - 10))

class SpeedButton:
    def __init__(self, x, y, speed):
        self.rect = pygame.Rect(x, y, 50, 30)
        self.speed = speed
        self.selected = speed == 1
        
    def draw(self, screen):
        color = GREEN if self.selected else WHITE
        pygame.draw.rect(screen, color, self.rect, 2)
        font = pygame.font.Font(None, 24)
        text = f"x{self.speed}"
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_click(self, pos):
        return self.rect.collidepoint(pos)

def draw_ui(screen, player, enemies):
    font = pygame.font.Font(None, 36)
    
    # Boss信息
    health_text = f"Boss HP: {player.health}"
    text_surface = font.render(health_text, True, WHITE)
    screen.blit(text_surface, (10, 10))
    
    energy_text = f"Boss Energy: {player.energy}"
    text_surface = font.render(energy_text, True, WHITE)
    screen.blit(text_surface, (10, 50))
    
    # 集体能量
    collective_text = f"Collective: {NoteWarrior.collective_energy}/{NoteWarrior.COLLECTIVE_ENERGY_MAX}"
    text_surface = font.render(collective_text, True, WHITE)
    screen.blit(text_surface, (10, 90))
    
    # 战士信息 - 显示更多细节
    for i, warrior in enumerate(enemies):
        # 根据策略获取标识
        strategy_tag = {
            'aggressive': 'A',
            'balanced': 'B',
            'conservative': 'C'
        }[warrior.strategy]
        
        warrior_text = f"W{i+1}[{strategy_tag}] [{warrior.ring_index}]: HP {warrior.health} E {warrior.note_energy}"
        text_surface = font.render(warrior_text, True, WHITE)
        screen.blit(text_surface, (10, 130 + i * 40))

def main():
    clock = pygame.time.Clock()
    wave = Wave()
    boss = Boss()
    
    # 固定分配策略，添加ID
    enemies = [
        NoteWarrior(0, 'aggressive', 1),
        NoteWarrior(math.pi/2, 'balanced', 2),
        NoteWarrior(math.pi, 'balanced', 3),
        NoteWarrior(3*math.pi/2, 'conservative', 4)
    ]
    
    # 添加速度控制按钮
    speed_buttons = [
        SpeedButton(WINDOW_SIZE[0] - 220, 10, 1),
        SpeedButton(WINDOW_SIZE[0] - 160, 10, 2),
        SpeedButton(WINDOW_SIZE[0] - 100, 10, 4),
        SpeedButton(WINDOW_SIZE[0] - 40, 10, 8)
    ]
    game_speed = 1
    
    missiles = []
    melody_waves = []
    font = pygame.font.Font(None, 36)
    
    running = True
    game_over = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 处理速度按钮点击
                for button in speed_buttons:
                    if button.handle_click(event.pos):
                        game_speed = button.speed
                        for b in speed_buttons:
                            b.selected = (b.speed == game_speed)
        
        # 根据游戏速度更新多次
        for _ in range(game_speed):
            # 更新游戏状态
            wave.update()
            for missile in missiles[:]:
                missile.update()
            for melody_wave in melody_waves[:]:
                melody_wave.update()
            for enemy in enemies[:]:
                if not any(enemy in wave.warriors for wave in melody_waves):
                    enemy.check_wave_collision(wave)
                    enemy.move(wave)
        
        # 绘制
        screen.fill(BLACK)
        wave.draw(screen)
        boss.draw(screen)
        
        # 检查是否发动旋律冲击波
        if (NoteWarrior.collective_energy >= NoteWarrior.COLLECTIVE_ENERGY_MAX and 
            not any(wave.active for wave in melody_waves)):
            melody_wave = MelodyWave(boss, enemies)  # 传入 enemies 参数
            melody_waves.append(melody_wave)
            NoteWarrior.collective_energy = 0
        
        # 更新敌人
        for enemy in enemies[:]:
            if not any(enemy in wave.warriors for wave in melody_waves):
                # 只有不在旋律冲击波上的战士才检查普通音波碰撞
                enemy.check_wave_collision(wave)
                enemy.move(wave)
            enemy.draw(screen, wave.ring_radii)
            if enemy.health <= 0:
                enemies.remove(enemy)
        
        # 更新和绘制旋律冲击波
        for melody_wave in melody_waves[:]:
            melody_wave.update()
            melody_wave.draw(screen)
            if not melody_wave.active:
                melody_waves.remove(melody_wave)
        
        # 显示被吸收的能量位置并累积boss能量
        if wave.state == WaveState.CONTRACTING:
            for pos in wave.absorbed_positions:
                angle, ring_idx = pos
                x = WINDOW_SIZE[0]//2 + math.cos(angle) * wave.radius
                y = WINDOW_SIZE[1]//2 + math.sin(angle) * wave.radius
                pygame.draw.circle(screen, YELLOW, (int(x), int(y)), 4)
                if wave.radius < 20:  # 音波返回中心时给boss能量
                    boss.energy += 1
        
        # 更新和绘制飞弹
        for missile in missiles[:]:
            missile.update()
            for enemy in enemies:
                missile.check_enemy_collision(enemy, wave.ring_radii)
            if missile.active:
                missile.draw(screen)
            else:
                missiles.remove(missile)
        
        # 绘制UI
        draw_ui(screen, boss, enemies)
        
        # 绘制速度控制按钮
        for button in speed_buttons:
            button.draw(screen)
        
        if not game_over:
            # 检查游戏结束条件
            if len(enemies) == 0:
                game_over = True
                game_result = "BOSS WINS!"
            elif boss.health <= 0:
                game_over = True
                game_result = "WARRIORS WIN!"
        else:
            # 显示游戏结果
            font = pygame.font.Font(None, 72)
            text_surface = font.render(game_result, True, WHITE)
            text_rect = text_surface.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2))
            screen.blit(text_surface, text_rect)
            
            # 显示重启提示
            font = pygame.font.Font(None, 36)
            restart_text = font.render("按R键重新开始", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 + 50))
            screen.blit(restart_text, restart_rect)
            
            # 检查重启游戏
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                wave = Wave()
                enemies = [
                    NoteWarrior(0, 'aggressive', 1),
                    NoteWarrior(math.pi/2, 'balanced', 2),
                    NoteWarrior(math.pi, 'balanced', 3),
                    NoteWarrior(3*math.pi/2, 'conservative', 4)
                ]
                missiles = []
                boss.energy = 0
                game_over = False
        
        pygame.display.flip()
        clock.tick(60)  # 保持60FPS的基础刷新率
        
    pygame.quit()

if __name__ == "__main__":
    main() 