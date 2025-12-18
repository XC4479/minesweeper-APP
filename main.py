import flet as ft
import random
import asyncio


# 1. 邏輯 
class MinesweeperLogic:
    def __init__(self, rows, cols, mines, lives):
        self.rows = rows
        self.cols = cols
        self.total_mines = mines
        self.lives = lives
        self.max_lives = lives
        self.grid = None
        self.revealed = set()
        self.flags = set()
        self.game_over = False
    #佈雷
    def initialize_board(self, safe_r, safe_c):
        self.grid = [[0 for i in range(self.cols)] for i in range(self.rows)]
        candidates = []
        #可佈雷區
        for r in range(self.rows):
            for c in range(self.cols):
                if abs(r - safe_r) <= 1 and abs(c - safe_c) <= 1:
                    continue
                candidates.append((r, c))
        #隨機佈雷
        mine_positions = random.sample(candidates, self.total_mines)
        for (r, c) in mine_positions:
            self.grid[r][c] = -1
        #周圍有幾顆雷
        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1: continue
                count = 0
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == -1:
                        count += 1
                self.grid[r][c] = count

    def get_cell_value(self, r, c):
        return self.grid[r][c]


#主程式
class GameApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Flet 手機版踩地雷"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 5
        self.page.scroll = "adaptive" # 如果內容太多，允許捲動
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.logic = None
        self.timer_task = None
        self.time_left = 0
        self.buttons_grid = []
        self.timer_running = False 

        self.text_colors = {
            1: ft.Colors.BLUE, 2: ft.Colors.GREEN, 3: ft.Colors.RED,
            4: ft.Colors.INDIGO, 5: ft.Colors.BROWN, 6: ft.Colors.TEAL,
            7: ft.Colors.BLACK, 8: ft.Colors.GREY
        }
        
        # UI 元件
        self.header_text = ft.Text("💣 手機版踩地雷", size=24, weight=ft.FontWeight.BOLD)
        self.status_text = ft.Text("請選擇難度", size=18, color=ft.Colors.BLUE)
        self.lives_text = ft.Text("", size=18, color=ft.Colors.RED)
        self.game_container = ft.Container() #格子

        self.show_menu()

    def show_menu(self):
        self.cancel_timer()
        self.page.clean()
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        # 建立 async handler 執行各級按鈕
        def create_start_handler(rows, cols, mines, limit, lives):
            async def handler(e):
                self.start_game(rows, cols, mines, limit, lives)
            return handler

        self.page.add(
            ft.Column([
                self.header_text,
                ft.Text("操作說明：點擊挖掘，長按插旗", color=ft.Colors.GREY),
                ft.Container(height=20),
                
                ft.ElevatedButton("簡單 (6x6, 5雷) ❤️1", 
                                  on_click=create_start_handler(6, 6, 5, 60, 1), 
                                  width=250, height=50),
                ft.Container(height=10),
                ft.ElevatedButton("中等 (10x10, 15雷) ❤️2", 
                                  on_click=create_start_handler(10, 10, 15, 180, 2), 
                                  width=250, height=50),
                ft.Container(height=10),
                ft.ElevatedButton("困難 (16x16, 40雷) ❤️3", 
                                  on_click=create_start_handler(16, 16, 40, 400, 3), 
                                  width=250, height=50),
                                  
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def start_game(self, rows, cols, mines, limit, lives):
        #畫格子
        self.logic = MinesweeperLogic(rows, cols, mines, lives)
        self.time_left = limit
        self.status_text.value = f"⏳ {self.time_left} (點擊開始)"
        self.lives_text.value = f"❤️ {self.logic.lives}"
        self.timer_running = False 

        #for按鈕
        self.buttons_grid = [[None for _ in range(cols)] for _ in range(rows)]
        cell_size = 35 if cols < 10 else 25 
        
        controls = [] #暫存
        for r in range(rows):
            row_controls = []
            for c in range(cols):
                #handler
                def make_click_handler(row, col):
                    async def handler(e):
                        await self.on_click(row, col)
                    return handler

                def make_long_press_handler(row, col):
                    def handler(e):
                        self.on_long_press(row, col)
                    return handler

                btn_content = ft.Container(
                    width=cell_size, height=cell_size,
                    bgcolor=ft.Colors.GREY_300,
                    border=ft.border.all(1, ft.Colors.GREY_500),
                    alignment=ft.alignment.center,
                    border_radius=4,
                    content=ft.Text("", weight=ft.FontWeight.BOLD),
                    ink=True, 
                    on_click=make_click_handler(r, c),
                    on_long_press=make_long_press_handler(r, c)
                )
                
                self.buttons_grid[r][c] = btn_content
                row_controls.append(btn_content)
            
            controls.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=2))

        self.game_container.content = ft.Column(controls=controls, spacing=2, alignment=ft.MainAxisAlignment.CENTER)
        
        self.page.clean()
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.add(
            ft.Row([
                ft.ElevatedButton("🔙 返回", on_click=lambda e: self.show_menu()),
                self.status_text,
                self.lives_text
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            self.game_container
        )

    def start_timer(self):
        if self.timer_task: 
            self.timer_task.cancel()
        self.timer_running = True
        self.timer_task = asyncio.create_task(self.timer_loop())
        #背景讀秒

    def cancel_timer(self):
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
        self.timer_running = False

    async def timer_loop(self):
        try:
            while self.time_left > 0 and not self.logic.game_over:
                await asyncio.sleep(1)
                self.time_left -= 1
                self.status_text.value = f"⏳ {self.time_left}"
                self.page.update()
            
            if self.time_left == 0 and not self.logic.game_over:
                await self.game_over_sequence(win=False, reason="時間耗盡")
        except asyncio.CancelledError:
            pass

    async def on_click(self, r, c):
        if self.logic.game_over or (r, c) in self.logic.flags: return
        
        # 第一次點擊開始計時
        if self.logic.grid is None:
            self.logic.initialize_board(r, c)
            self.start_timer() 
            
        val = self.logic.get_cell_value(r, c)
        
        if val == -1:
            if self.logic.lives > 0:
                self.logic.lives -= 1
                self.lives_text.value = f"❤️ {self.logic.lives}"
                self.lives_text.update()
                
                btn = self.buttons_grid[r][c]
                btn.bgcolor = ft.Colors.ORANGE
                btn.content.value = "💣"
                btn.update()
                
                # SnackBar
                snack = ft.SnackBar(ft.Text(f"💥 踩到地雷！剩餘命數: {self.logic.lives}"), bgcolor=ft.Colors.RED)
                self.page.open(snack) 
                self.page.update()
                return
            else:
                self.logic.game_over = True
                await self.animate_explosion(r, c)
                return

        self.reveal_recursive(r, c)
        self.page.update()
        
        target = self.logic.rows * self.logic.cols - self.logic.total_mines
        if len(self.logic.revealed) == target:
            await self.game_over_sequence(win=True)

    def on_long_press(self, r, c):
        if self.logic.game_over or (r, c) in self.logic.revealed: return
        
        btn = self.buttons_grid[r][c]
        if (r, c) in self.logic.flags:
            self.logic.flags.remove((r, c))
            btn.content.value = ""
            btn.content.color = ft.Colors.BLACK
            btn.bgcolor = ft.Colors.GREY_300
        else:
            self.logic.flags.add((r, c))
            btn.content.value = "🚩"
            btn.content.color = ft.Colors.RED
            btn.bgcolor = ft.Colors.YELLOW_100
        btn.update()

    def reveal_recursive(self, r, c):
        if not (0 <= r < self.logic.rows and 0 <= c < self.logic.cols): return
        if (r, c) in self.logic.revealed or (r, c) in self.logic.flags: return
        
        self.logic.revealed.add((r, c))
        val = self.logic.grid[r][c]
        btn = self.buttons_grid[r][c]
        
        btn.bgcolor = ft.Colors.WHITE
        if val > 0:
            btn.content.value = str(val)
            btn.content.color = self.text_colors.get(val, ft.Colors.BLACK)
        #掀開0周圍8格
        if val == 0:
            directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for dr, dc in directions:
                self.reveal_recursive(r + dr, c + dc)

    async def animate_explosion(self, r, c):
        """爆炸動畫"""
        colors = [ft.Colors.RED, ft.Colors.ORANGE, ft.Colors.YELLOW, ft.Colors.WHITE]
        texts = ['💥', '🔥', '☠️', '☠️']
        
        btn = self.buttons_grid[r][c]
        
        for i in range(len(colors)):
            btn.bgcolor = colors[i]
            btn.content.value = texts[i]
            btn.update()
            
            if i % 2 == 0:
                affected = []
                directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.logic.rows and 0 <= nc < self.logic.cols:
                        n_btn = self.buttons_grid[nr][nc]
                        if (nr, nc) not in self.logic.revealed:
                            n_btn.bgcolor = ft.Colors.ORANGE_200
                            n_btn.update()
                            affected.append(n_btn)
                
                await asyncio.sleep(0.1)
                for b in affected:
                    b.bgcolor = ft.Colors.GREY_300
                    b.update()
            else:
                await asyncio.sleep(0.1)
        
        await self.game_over_sequence(win=False, explode_pos=(r, c), reason="踩到地雷")

    async def game_over_sequence(self, win, explode_pos=None, reason=""):
        self.logic.game_over = True
        self.cancel_timer()
        
        if self.logic.grid:
            for r in range(self.logic.rows):
                for c in range(self.logic.cols):
                    if self.logic.grid[r][c] == -1:
                        btn = self.buttons_grid[r][c]
                        if btn.bgcolor != ft.Colors.ORANGE:
                            btn.content.value = "💣"
                            btn.bgcolor = ft.Colors.RED_100
                        if explode_pos and r == explode_pos[0] and c == explode_pos[1]:
                            btn.bgcolor = ft.Colors.BLACK
                            btn.content.value = "☠️"
                            btn.content.color = ft.Colors.WHITE
            self.page.update()

        
        title_color = ft.Colors.GREEN if win else ft.Colors.RED
        title_text = "🎉 恭喜獲勝！" if win else "💀 遊戲結束"
        
        content_column = ft.Column([
            ft.Text(f"結果: {reason}", size=18),
            ft.Text(f"剩餘命數: {self.logic.lives}", size=16),
            ft.Text(f"剩餘時間: {self.time_left} 秒", size=16),
        ], height=100, tight=True)

        async def on_return_click(e):
            await self.close_dlg_and_menu(dlg)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title_text, color=title_color, weight=ft.FontWeight.BOLD),
            content=content_column,
            actions=[
                ft.TextButton("回到選單", on_click=on_return_click),
                #ft.TextButton("回到選單", on_click=self.close_dlg_and_menu),
                    ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

    async def close_dlg_and_menu(self, dlg):
        self.page.close(dlg)
        await asyncio.sleep(0.1)
        self.show_menu()

#開始
async def main(page: ft.Page):
    app = GameApp(page)

if __name__ == "__main__":  
    ft.app(target=main)
