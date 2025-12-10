import os
import sys
import locale

# 修复控制台编码问题
if sys.platform == 'win32':
    try:
        # 设置控制台编码
        locale.setlocale(locale.LC_ALL, '')
        encoding = locale.getpreferredencoding()
        # 尝试设置为UTF-8
        os.system('chcp 65001 > nul 2>&1')
    except:
        pass
    
    # 尝试修复输出流
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import pygame
import random
import time
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32api

# 初始化pygame
pygame.init()

# 获取屏幕尺寸
user32 = ctypes.windll.user32
SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)

# 创建控制窗口
control_width = 400
control_height = 450
screen = pygame.display.set_mode((control_width, control_height))
pygame.display.set_caption("Snake Control Center")
clock = pygame.time.Clock()

# 控制窗口位置
control_x = SCREEN_WIDTH - control_width - 20
control_y = SCREEN_HEIGHT - control_height - 20
control_hwnd = pygame.display.get_wm_info()["window"]
win32gui.MoveWindow(control_hwnd, control_x, control_y, control_width, control_height, True)

# 游戏设置
CELL_SIZE = 40
SNAKE_SPEED = 0.15
INITIAL_LENGTH = 4  # 增加初始长度以便更容易看到

# 颜色定义
SNAKE_HEAD_COLOR = (0, 255, 0)    # 蛇头
SNAKE_BODY_COLOR = (0, 200, 0)    # 蛇身
FOOD_COLOR = (255, 0, 0)          # 食物
BG_COLOR = (30, 30, 50)           # 背景
TEXT_COLOR = (255, 255, 255)      # 文本
HIGHLIGHT_COLOR = (100, 255, 100) # 高亮文本
ERROR_COLOR = (255, 100, 100)     # 错误文本
INFO_COLOR = (200, 200, 255)      # 信息文本

# 方向
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class SnakeWindow:
    def __init__(self, x, y, window_id, is_head=False, is_food=False):
        self.x = x
        self.y = y
        self.window_id = window_id
        self.is_head = is_head
        self.is_food = is_food
        self.hwnd = None
        self.color = SNAKE_HEAD_COLOR if is_head else (FOOD_COLOR if is_food else SNAKE_BODY_COLOR)
        self.create_window()
        
    def create_window(self):
        """Create window"""
        try:
            class_name = f"SnakeWin_{random.randint(10000, 99999)}"
            
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.window_proc
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.hbrBackground = win32gui.CreateSolidBrush(
                win32api.RGB(self.color[0], self.color[1], self.color[2])
            )
            wc.lpszClassName = class_name
            
            class_atom = win32gui.RegisterClass(wc)
            
            title = "Snake Head" if self.is_head else ("Food" if self.is_food else f"Snake Body {self.window_id}")
            
            self.hwnd = win32gui.CreateWindowEx(
                win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_NOACTIVATE,
                class_name,
                title,
                win32con.WS_POPUP | win32con.WS_VISIBLE | win32con.WS_BORDER,
                self.x, self.y, CELL_SIZE, CELL_SIZE,
                0, 0, win32api.GetModuleHandle(None), None
            )
            
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)
            print(f"Window created: {title} at ({self.x},{self.y})")
            
        except Exception as e:
            print(f"Failed to create window: {e}")
            
    def window_proc(self, hwnd, msg, wparam, lparam):
        """Window message handler"""
        if msg == win32con.WM_PAINT:
            hdc, paintstruct = win32gui.BeginPaint(hwnd)
            rect = win32gui.GetClientRect(hwnd)
            
            brush = win32gui.CreateSolidBrush(
                win32api.RGB(self.color[0], self.color[1], self.color[2])
            )
            win32gui.FillRect(hdc, rect, brush)
            win32gui.FrameRect(hdc, rect, win32gui.GetStockObject(win32con.BLACK_BRUSH))
            
            win32gui.EndPaint(hwnd, paintstruct)
            win32gui.DeleteObject(brush)
            return 0
            
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        
    def move(self, x, y, is_head=False):
        """Move window"""
        if not self.hwnd:
            return
            
        self.x = x
        self.y = y
        self.is_head = is_head
        
        if is_head:
            self.color = SNAKE_HEAD_COLOR
        elif self.is_food:
            self.color = FOOD_COLOR
        else:
            self.color = SNAKE_BODY_COLOR
            
        try:
            win32gui.MoveWindow(self.hwnd, x, y, CELL_SIZE, CELL_SIZE, True)
        except:
            pass
            
    def close(self):
        """Close window"""
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except:
                pass

class SnakeGame:
    def __init__(self):
        self.windows = []
        self.positions = []
        self.direction = RIGHT
        self.score = 0
        self.length = INITIAL_LENGTH
        self.game_over = False
        self.paused = False
        self.last_move_time = 0
        self.food_window = None
        self.food_position = None
        self.window_counter = 0
        
        print("\n" + "="*60)
        print("Snake Game - Fixed Movement Issue Version")
        print("="*60)
        print("Fixed: Initial positions overlapping causing immediate collision")
        print("="*60)
        
        # Initialize snake
        self.init_snake()
        
        # Create food
        self.create_food()
        
    def init_snake(self):
        """Initialize snake - ensure no overlapping initial positions"""
        print("Initializing snake...")
        
        # Key fix: Arrange from right to left to prevent overlap
        start_x = 300
        start_y = 300
        
        for i in range(self.length):
            x = start_x - i * CELL_SIZE
            y = start_y
            
            if x < 0:
                x = 100
            if y < 0:
                y = 100
                
            self.positions.append((x, y))
            print(f"Snake part {i} initial position: ({x}, {y})")
            
            window = SnakeWindow(x, y, self.window_counter, is_head=(i==0))
            self.windows.append(window)
            self.window_counter += 1
            
            time.sleep(0.05)
        
        print(f"Snake initialization complete!")
        print(f"Length: {self.length}")
        print(f"Position list: {self.positions}")
        print(f"Check overlap: positions={len(self.positions)}, unique={len(set(self.positions))}")
        
        if len(self.positions) != len(set(self.positions)):
            print("ERROR: Initial positions overlap!")
            self.positions = []
            for i in range(self.length):
                x = 300 - i * CELL_SIZE
                y = 300
                self.positions.append((x, y))
            print(f"Fixed positions: {self.positions}")
        
    def create_food(self):
        """Create food"""
        print("\nCreating food...")
        
        for attempt in range(100):
            x = random.randint(100, SCREEN_WIDTH - CELL_SIZE - 100)
            y = random.randint(100, SCREEN_HEIGHT - CELL_SIZE - 100)
            
            overlap = False
            for pos in self.positions:
                if pos[0] == x and pos[1] == y:
                    overlap = True
                    break
                    
            if not overlap:
                self.food_position = (x, y)
                if self.food_window:
                    self.food_window.close()
                self.food_window = SnakeWindow(x, y, 999, is_food=True)
                print(f"Food position: ({x}, {y})")
                return
                
        x = 500
        y = 500
        self.food_position = (x, y)
        if self.food_window:
            self.food_window.close()
        self.food_window = SnakeWindow(x, y, 999, is_food=True)
        print(f"Food backup position: ({x}, {y})")
        
    def move(self):
        """Move the snake"""
        if time.time() - self.last_move_time < SNAKE_SPEED:
            return
            
        self.last_move_time = time.time()
        
        if self.game_over or self.paused:
            return
            
        head_x, head_y = self.positions[0]
        new_x = head_x + self.direction[0] * CELL_SIZE
        new_y = head_y + self.direction[1] * CELL_SIZE
        
        # Boundary - wrap around
        if new_x < 0:
            new_x = SCREEN_WIDTH - CELL_SIZE
        elif new_x >= SCREEN_WIDTH:
            new_x = 0
            
        if new_y < 0:
            new_y = SCREEN_HEIGHT - CELL_SIZE
        elif new_y >= SCREEN_HEIGHT:
            new_y = 0
            
        new_head = (new_x, new_y)
        
        print(f"Move: head from ({head_x},{head_y}) to ({new_x},{new_y})")
        
        # Check collision with self
        collision = False
        for i, pos in enumerate(self.positions[1:], 1):
            if new_head == pos:
                collision = True
                print(f"Collision detected: with body part {i} at {pos}!")
                break
                
        if collision:
            self.game_over = True
            print("GAME OVER: Collided with self!")
            return
            
        # Move to new position
        self.positions.insert(0, new_head)
        
        # Check if food eaten
        ate_food = False
        if self.food_position:
            fx, fy = self.food_position
            if (abs(new_x - fx) < CELL_SIZE and abs(new_y - fy) < CELL_SIZE):
                ate_food = True
                self.eat_food()
        
        # Remove tail if no food eaten
        if not ate_food and len(self.positions) > self.length:
            removed = self.positions.pop()
            print(f"Remove tail: {removed}")
                    
        # Update window positions
        for i, window in enumerate(self.windows):
            if i < len(self.positions):
                x, y = self.positions[i]
                window.move(x, y, is_head=(i==0))
            elif i < 10:  # Limit max windows
                x, y = self.positions[-1]
                new_window = SnakeWindow(x, y, self.window_counter)
                self.windows.append(new_window)
                self.window_counter += 1
                print(f"Add new snake body window {self.window_counter}")
                
    def eat_food(self):
        """Eat food"""
        self.score += 10
        self.length += 1
        
        print(f"Food eaten! Score: {self.score}, New length: {self.length}")
        
        # Create new food
        self.create_food()
        
        # Add new snake body part
        if self.positions:
            tail_x, tail_y = self.positions[-1]
            new_window = SnakeWindow(tail_x, tail_y, self.window_counter)
            self.windows.append(new_window)
            self.window_counter += 1
            
    def change_direction(self, new_direction):
        """Change direction"""
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction
            print(f"Direction changed: {self.direction}")
            
    def draw_control_panel(self):
        """Draw control panel"""
        screen.fill(BG_COLOR)
        
        # 使用系统字体
        try:
            font = pygame.font.SysFont("Arial", 24)
        except:
            font = pygame.font.SysFont(None, 24)
        
        # Title
        title = font.render("Snake Game Control Center", True, (0, 255, 0))
        screen.blit(title, (20, 20))
        
        # Status info
        info_y = 60
        score_text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
        length_text = font.render(f"Length: {self.length}", True, TEXT_COLOR)
        
        screen.blit(score_text, (20, info_y))
        screen.blit(length_text, (20, info_y + 25))
        
        # Game status
        status_y = info_y + 70
        if self.game_over:
            status_text = font.render("GAME OVER! Press R to restart", True, ERROR_COLOR)
        elif self.paused:
            status_text = font.render("PAUSED - Press P to continue", True, (255, 200, 0))
        else:
            status_text = font.render("PLAYING...", True, (0, 255, 0))
        screen.blit(status_text, (20, status_y))
        
        # Controls
        controls_y = status_y + 40
        controls = [
            "Controls:",
            "Arrow Keys - Move Snake",
            "P - Pause/Continue",
            "R - Restart Game", 
            "ESC - Quit Game"
        ]
        
        for i, text in enumerate(controls):
            control_text = font.render(text, True, TEXT_COLOR)
            screen.blit(control_text, (20, controls_y + i*25))
            
        # Snake head position
        if self.positions:
            head_x, head_y = self.positions[0]
            pos_text = font.render(f"Head Position: ({head_x}, {head_y})", True, HIGHLIGHT_COLOR)
            screen.blit(pos_text, (20, controls_y + len(controls)*25 + 10))
            
        # Direction display
        direction_names = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}
        dir_text = font.render(f"Direction: {direction_names.get(self.direction, 'UNKNOWN')}", 
                             True, TEXT_COLOR)
        screen.blit(dir_text, (20, controls_y + len(controls)*25 + 40))
        
        # Debug info
        debug_y = controls_y + len(controls)*25 + 70
        debug_text = font.render(f"Segments: {len(self.positions)}", True, INFO_COLOR)
        screen.blit(debug_text, (20, debug_y))
        
        # Fix info
        fix_y = debug_y + 30
        fix_text = font.render("FIXED: No initial position overlap", True, (0, 255, 255))
        screen.blit(fix_text, (20, fix_y))
        
        # Instructions
        instructions_y = fix_y + 30
        instructions = font.render("Click on this window first, then use arrow keys", True, (255, 255, 0))
        screen.blit(instructions, (20, instructions_y))
        
        # 版本信息
        version_text = font.render("Multi-Window Snake v1.1", True, (150, 150, 150))
        screen.blit(version_text, (control_width - 200, control_height - 30))
        
        pygame.display.flip()
        
    def restart(self):
        """Restart game"""
        print("\nRestarting game...")
        
        # Close all windows
        for window in self.windows:
            window.close()
        if self.food_window:
            self.food_window.close()
            
        # Reset state
        self.windows = []
        self.positions = []
        self.direction = RIGHT
        self.score = 0
        self.length = INITIAL_LENGTH
        self.game_over = False
        self.paused = False
        self.last_move_time = 0
        self.food_window = None
        self.food_position = None
        self.window_counter = 0
        
        # Reinitialize
        self.init_snake()
        self.create_food()
        print("Game restarted!")
        
    def close(self):
        """Close all windows"""
        for window in self.windows:
            window.close()
        if self.food_window:
            self.food_window.close()

def main():
    """Main game function"""
    print("Starting Snake Game...")
    
    # Create game
    game = SnakeGame()
    running = True
    
    # Wait for windows to create
    time.sleep(1)
    
    print("\n" + "="*50)
    print("Game ready!")
    print("Click on the control window first")
    print("Then use arrow keys to control the snake")
    print("Check console output to confirm movement")
    print("="*50)
    
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.restart()
                elif event.key == pygame.K_p:
                    game.paused = not game.paused
                elif not game.game_over and not game.paused:
                    if event.key == pygame.K_UP:
                        game.change_direction(UP)
                    elif event.key == pygame.K_DOWN:
                        game.change_direction(DOWN)
                    elif event.key == pygame.K_LEFT:
                        game.change_direction(LEFT)
                    elif event.key == pygame.K_RIGHT:
                        game.change_direction(RIGHT)
        
        # Update game
        if not game.game_over and not game.paused:
            game.move()
            
        # Draw control panel
        game.draw_control_panel()
        
        # Control frame rate
        clock.tick(60)
    
    # Cleanup
    print("\nExiting game...")
    game.close()
    pygame.quit()
    print("Game exited successfully")
    sys.exit()

if __name__ == "__main__":
    main()