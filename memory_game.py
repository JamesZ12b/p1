
import tkinter as tk
import random
from PIL import Image, ImageTk

# 仅在 Windows 上可用，且只能播放 .wav 格式
import winsound

# Pillow 兼容性处理
try:
    from PIL import ImageResampling
    LANCZOS = ImageResampling.LANCZOS
except ImportError:
    if hasattr(Image, "LANCZOS"):
        LANCZOS = Image.LANCZOS
    else:
        LANCZOS = Image.ANTIALIAS


class MemoryGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Game with Sound Effect")

        # 蔬菜名称列表
        self.vegetables = ["Eggplant", "Pepper", "Carrot", "Tomato", "Cucumber", "Onion"]

        # 读取背面图片
        # 确保 images/back.png 存在
        self.original_back = Image.open("images/back.png")

        # 读取每个蔬菜的原始图
        self.original_images = {}
        for veg in self.vegetables:
            self.original_images[veg] = Image.open(f"images/{veg.lower()}.png")

        # 生成卡牌并打乱
        self.cards = self.vegetables * 2
        random.shuffle(self.cards)

        # 行列数、配对情况
        self.rows = 3
        self.cols = 4
        self.total_pairs = len(self.vegetables)
        self.matched_pairs = 0

        # 记录翻牌信息
        self.first_card_idx = None
        self.first_card_name = None
        # face_up[i] == True 表示第i张卡是正面
        self.face_up = [False] * (self.rows * self.cols)

        # 创建卡牌按钮
        self.buttons = []
        for i in range(self.rows * self.cols):
            # 设置一个初始大小
            init_w, init_h = 100, 100
            init_resized = self.original_back.resize((init_w, init_h), LANCZOS)
            init_photo = ImageTk.PhotoImage(init_resized)

            btn = tk.Button(
                self.root,
                image=init_photo,
                bd=2,
                relief=tk.RAISED,
                command=lambda idx=i: self.on_card_click(idx)
            )
            # 保存对图像的引用，避免被垃圾回收
            btn.image = init_photo

            # 网格布局
            btn.grid(row=i // self.cols, column=i % self.cols, padx=5, pady=5, sticky="nsew")

            # 监听大小变化事件，用于动态缩放图片
            btn.bind("<Configure>", lambda e, idx=i: self.on_resize_button(e, idx))
            self.buttons.append(btn)

        # 让所有列和行在窗口拉伸时可自动扩展
        for c in range(self.cols):
            self.root.columnconfigure(c, weight=1)
        for r in range(self.rows):
            self.root.rowconfigure(r, weight=1)

        # 记分区
        score_frame = tk.Frame(self.root)
        score_frame.grid(row=self.rows, column=0, columnspan=self.cols, pady=10, sticky="ew")
        tk.Label(score_frame, text="Score:").pack(side=tk.LEFT, padx=5)
        self.score_label = tk.Label(score_frame, text="0")
        self.score_label.pack(side=tk.LEFT)

    def on_card_click(self, idx):
        # 播放翻牌音效（.wav 格式文件必须存在于 sounds/flip.wav）
        winsound.PlaySound("sounds/flip.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

        # 若牌已是正面或已禁用，忽略点击
        if self.face_up[idx] or self.buttons[idx].cget("state") == "disabled":
            return

        # 翻开该卡
        self.face_up[idx] = True
        self.update_card_image(idx)

        veg_name = self.cards[idx]

        # 如果没有已经翻开的第一张，记录这张
        if self.first_card_idx is None:
            self.first_card_idx = idx
            self.first_card_name = veg_name
        else:
            # 第二张牌，判断是否匹配
            if veg_name == self.first_card_name:
                # 成功配对
                self.buttons[idx].configure(state="disabled", bg="#c5fdb5")
                self.buttons[self.first_card_idx].configure(state="disabled", bg="#c5fdb5")
                self.matched_pairs += 1
                self.score_label.configure(text=str(self.matched_pairs))
                winsound.PlaySound("sounds/correct.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

                # 判断是否全部完成
                if self.matched_pairs == self.total_pairs:
                    winsound.PlaySound("sounds/win.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                    win_label = tk.Label(self.root, text="All matched! Congratulations!", fg="green")
                    win_label.grid(row=self.rows+1, column=0, columnspan=self.cols, pady=10)

            else:
                # 没匹配，延迟翻回背面
                self.root.after(700, self.flip_back, idx, self.first_card_idx)

            # 重置翻牌记录
            self.first_card_idx = None
            self.first_card_name = None

    def flip_back(self, idx1, idx2):
        """翻回背面。"""
        self.face_up[idx1] = False
        self.face_up[idx2] = False
        self.update_card_image(idx1)
        self.update_card_image(idx2)

    def on_resize_button(self, event, idx):
        """按钮尺寸发生变化时, 自动缩放卡面图。"""
        new_w = event.width
        new_h = event.height

        # 设置最小 / 最大尺寸
        min_w, min_h = 80, 80
        max_w, max_h = 150, 150

        if new_w < min_w:
            new_w = min_w
        elif new_w > max_w:
            new_w = max_w

        if new_h < min_h:
            new_h = min_h
        elif new_h > max_h:
            new_h = max_h

        self.do_resize(idx, new_w, new_h)

    def update_card_image(self, idx):
        """刷新卡片的图像(翻开或翻回)。"""
        w = self.buttons[idx].winfo_width()
        h = self.buttons[idx].winfo_height()

        if w < 1 or h < 1:
            # 若尚未布局完成, 稍后重试
            self.root.after(50, lambda: self.update_card_image(idx))
        else:
            self.do_resize(idx, w, h)

    def do_resize(self, idx, width, height):
        """根据当前 face_up 决定使用正面或背面图进行 resize 并渲染。"""
        if self.face_up[idx]:
            veg_name = self.cards[idx]
            original_pil = self.original_images[veg_name]
        else:
            original_pil = self.original_back

        if width < 1 or height < 1:
            return

        resized = original_pil.resize((width, height), LANCZOS)
        new_photo = ImageTk.PhotoImage(resized)

        self.buttons[idx].configure(image=new_photo)
        self.buttons[idx].image = new_photo

def main():
    root = tk.Tk()
    MemoryGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()




















