import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import collections

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def resource_path(relative_path):
    """Resolve a path that works both when running the .py directly and when
    running as a PyInstaller-built .exe (where bundled files are extracted
    to a temporary folder referenced by sys._MEIPASS)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# Folder where item images live (chicken_bucket.png, yumburger.png, etc.)
IMAGE_DIR = resource_path("image")
ICON_SIZE = (90, 90)

# Category -> (background color, emoji) used when auto-generating placeholder icons
CATEGORY_STYLE = {
    "Chickenjoy": ("#F57C00", "🍗"),
    "Yumburger": ("#8D6E63", "🍔"),
    "Jolly Spaghetti": ("#C62828", "🍝"),
    "Burger Steak": ("#5D4037", "🍔"),
    "Summer Treats": ("#EC407A", "🍨"),
}


class JollibeeKioskGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jollibee Self-Order Kiosk")

        # 1. TALL KIOSK DIMENSIONS (Vertical Aspect Ratio)
        self.root.geometry("520x920")
        self.root.configure(bg="#1A1A1A")

        # 2. DATA STRUCTURES
        self.categories = {
            "Chickenjoy": [
                {"name": "6pc Chickenjoy Bucket", "price": 430.00, "code": 101, "image": "chicken_bucket.png"},
                {"name": "8pc Chickenjoy Bucket", "price": 549.00, "code": 102, "image": "chicken_bucket.png"},
                {"name": "1pc Chickenjoy w/ Rice", "price": 95.00, "code": 103, "image": "chicken_rice.png"},
                {"name": "1pc Spicy Chickenjoy", "price": 100.00, "code": 104, "image": "chicken_spicy.png"},
                {"name": "1pc Chickenjoy Perfect Pair", "price": 175.00, "code": 105, "image": "chicken_rice.png"},
                {"name": "2pc Chickenjoy Combo", "price": 180.00, "code": 106, "image": "chicken_rice.png"}
            ],
            "Yumburger": [
                {"name": "Yumburger Solo", "price": 40.00, "code": 201, "image": "yumburger.png"},
                {"name": "Cheesy Yumburger", "price": 65.00, "code": 202, "image": "yumburger.png"},
                {"name": "Bacon Cheese Yumburger", "price": 99.00, "code": 203, "image": "yumburger.png"},
                {"name": "Champ Burger", "price": 175.00, "code": 204, "image": "yumburger.png"}
            ],
            "Jolly Spaghetti": [
                {"name": "Jolly Spaghetti Solo", "price": 60.00, "code": 301, "image": "spaghetti.png"},
                {"name": "Jolly Spaghetti w/ Yumburger", "price": 115.00, "code": 302, "image": "spaghetti.png"},
                {"name": "Jolly Spaghetti Family Pan", "price": 240.00, "code": 303, "image": "spaghetti.png"}
            ],
            "Burger Steak": [
                {"name": "1pc Burger Steak Solo", "price": 60.00, "code": 401, "image": "burger_steak.png"},
                {"name": "2pc Burger Steak Solo", "price": 115.00, "code": 402, "image": "burger_steak.png"}
            ],
            "Summer Treats": [
                {"name": "Peach Mango Pie", "price": 45.00, "code": 501, "image": "peach_mango.png"},
                {"name": "Halo-Halo Sundae", "price": 49.00, "code": 502, "image": "peach_mango.png"},
                {"name": "Royal Float", "price": 45.00, "code": 503, "image": "peach_mango.png"}
            ]
        }

        self.photo_references = []  # keeps PhotoImage objects alive (prevents blank icons)
        self.cart_stack = []
        self.kitchen_queue = collections.deque()
        self.next_order_id = 1001

        self.current_category = "Chickenjoy"

        self.print_image_diagnostics()

        self.setup_ui()
        self.open_kitchen_display_system()

    def print_image_diagnostics(self):
        """Print, at startup, exactly which expected image files are found/missing."""
        print("=" * 60)
        print(f"Looking for images in: {IMAGE_DIR}")
        if not os.path.isdir(IMAGE_DIR):
            print(f"  ! Folder does not exist at that path.")
        else:
            actual_files = set(os.listdir(IMAGE_DIR))
            print(f"  Files found in folder: {sorted(actual_files) if actual_files else '(empty)'}")

            expected = set()
            for items in self.categories.values():
                for item in items:
                    expected.add(item["image"])

            for filename in sorted(expected):
                status = "FOUND" if filename in actual_files else "MISSING (will use placeholder)"
                print(f"  {filename:30s} -> {status}")

            extra = actual_files - expected
            if extra:
                print(f"  Note: these files exist but aren't referenced by any menu item: {sorted(extra)}")
        print("=" * 60)

    # --- IMAGE LOADING / GENERATION ---------------------------------------
    def make_placeholder_image(self, filename, category):
        """Create (and cache to disk) a simple colored icon so something always shows."""
        color, emoji = CATEGORY_STYLE.get(category, ("#455A64", "🍽"))
        img = Image.new("RGBA", ICON_SIZE, color)
        draw = ImageDraw.Draw(img)

        font = None
        for font_name in ("seguiemj.ttf", "AppleColorEmoji.ttf", "NotoColorEmoji.ttf"):
            try:
                font = ImageFont.truetype(font_name, 40)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        try:
            bbox = draw.textbbox((0, 0), emoji, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((ICON_SIZE[0] - w) / 2, (ICON_SIZE[1] - h) / 2), emoji, font=font, fill="white")
        except Exception:
            pass  # if the emoji glyph can't render, we still return a solid color icon

        os.makedirs(IMAGE_DIR, exist_ok=True)
        try:
            img.save(os.path.join(IMAGE_DIR, filename))
        except Exception:
            pass  # if saving fails (e.g. read-only folder), still return the in-memory image

        return img

    def load_item_image(self, filename, category):
        """Return a PhotoImage for filename, using a real file if present, else a generated placeholder."""
        if not PIL_AVAILABLE:
            return None

        path = os.path.join(IMAGE_DIR, filename)
        try:
            if os.path.isfile(path):
                img = Image.open(path).convert("RGBA")
            else:
                img = self.make_placeholder_image(filename, category)
            img = img.resize(ICON_SIZE, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_references.append(photo)  # prevent garbage collection
            return photo
        except Exception as e:
            print(f"Could not load/generate image '{path}': {e}")
            return None

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#D32F2F", height=70)
        header_frame.pack(fill=tk.X)

        header_title = tk.Label(
            header_frame,
            text="🐝 Jollibee Summer Treats",
            font=("Arial", 16, "bold"),
            bg="#D32F2F",
            fg="#FFC107",
            pady=12
        )
        header_title.pack()

        self.category_header = tk.Label(
            self.root,
            text="Chickenjoy",
            font=("Arial", 14, "bold"),
            bg="#0D47A1",
            fg="white",
            pady=6
        )
        self.category_header.pack(fill=tk.X)

        main_body = tk.Frame(self.root, bg="#E1F5FE")
        main_body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main_body, bg="#81D4FA", width=120)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(sidebar, text="Menu", font=("Arial", 11, "bold"), bg="#0288D1", fg="white", pady=6).pack(fill=tk.X)

        for cat_name in self.categories.keys():
            btn = tk.Button(
                sidebar,
                text=cat_name,
                font=("Arial", 9, "bold"),
                bg="#E0F7FA",
                fg="#0277BD",
                activebackground="#0288D1",
                activeforeground="white",
                bd=0,
                pady=10,
                cursor="hand2",
                command=lambda c=cat_name: self.switch_category(c)
            )
            btn.pack(fill=tk.X, pady=1)

        self.grid_frame = tk.Frame(main_body, bg="#B3E5FC")
        self.grid_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.render_menu_grid()

        cart_summary_frame = tk.Frame(self.root, bg="#0288D1", pady=5)
        cart_summary_frame.pack(fill=tk.X)

        tk.Label(cart_summary_frame, text="Your Order:", font=("Arial", 11, "bold"), bg="#0288D1", fg="white").pack(anchor="w", padx=10)

        self.cart_preview_label = tk.Label(
            cart_summary_frame,
            text="Cart is empty",
            font=("Arial", 9),
            bg="#0288D1",
            fg="#E0F7FA",
            wraplength=480,
            justify="left"
        )
        self.cart_preview_label.pack(anchor="w", padx=10, pady=2)

        action_bar = tk.Frame(self.root, bg="#D32F2F", height=60, padx=5, pady=5)
        action_bar.pack(fill=tk.X)

        btn_cancel = tk.Button(
            action_bar,
            text="Cancel",
            font=("Arial", 10, "bold"),
            bg="#B71C1C",
            fg="white",
            bd=0,
            command=self.clear_cart,
            cursor="hand2"
        )
        btn_cancel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        btn_undo = tk.Button(
            action_bar,
            text="Undo Item\n(Stack Pop)",
            font=("Arial", 9, "bold"),
            bg="#FF9800",
            fg="white",
            bd=0,
            command=self.undo_item,
            cursor="hand2"
        )
        btn_undo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        btn_pay = tk.Button(
            action_bar,
            text="Review / Pay\nFor Order",
            font=("Arial", 10, "bold"),
            bg="#388E3C",
            fg="white",
            bd=0,
            command=self.submit_order,
            cursor="hand2"
        )
        btn_pay.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.total_box = tk.Label(
            action_bar,
            text="Order Total\n₱ 0.00",
            font=("Arial", 11, "bold"),
            bg="#8E0000",
            fg="white",
            padx=10
        )
        self.total_box.pack(side=tk.RIGHT, fill=tk.BOTH, padx=2)

    def render_menu_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        items = self.categories[self.current_category]
        self.category_header.config(text=self.current_category)

        for idx, item in enumerate(items):
            row = idx // 2
            col = idx % 2

            card = tk.Frame(self.grid_frame, bg="#E0F7FA", bd=1, relief="solid")
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            photo = self.load_item_image(item.get("image", ""), self.current_category)
            if photo is not None:
                icon_label = tk.Label(card, image=photo, bg="#E0F7FA")
                icon_label.image = photo  # extra safety ref on the widget itself
            else:
                emoji = CATEGORY_STYLE.get(self.current_category, ("#455A64", "🍽"))[1]
                icon_label = tk.Label(card, text=emoji, font=("Arial", 22), bg="#E0F7FA")
            icon_label.pack(pady=(5, 0))

            tk.Label(card, text=item['name'], font=("Arial", 8, "bold"), bg="#E0F7FA", fg="#01579B", wraplength=120).pack()
            tk.Label(card, text=f"₱ {item['price']:.2f}", font=("Arial", 9, "bold"), bg="#E0F7FA", fg="#D32F2F").pack()

            btn_add = tk.Button(
                card,
                text="+ Add",
                font=("Arial", 8, "bold"),
                bg="#0288D1",
                fg="white",
                bd=0,
                command=lambda i=item: self.add_to_cart(i),
                cursor="hand2"
            )
            btn_add.pack(pady=4, fill=tk.X, padx=5)

        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.columnconfigure(1, weight=1)

    def switch_category(self, cat_name):
        self.current_category = cat_name
        self.render_menu_grid()

    def calculate_total(self):
        return sum(item['price'] for item in self.cart_stack)

    def add_to_cart(self, item):
        self.cart_stack.append(item)
        self.update_cart_ui()

    def undo_item(self):
        if not self.cart_stack:
            messagebox.showwarning("Cart Empty", "No items to undo!")
            return
        self.cart_stack.pop()
        self.update_cart_ui()

    def clear_cart(self):
        self.cart_stack.clear()
        self.update_cart_ui()

    def update_cart_ui(self):
        total = self.calculate_total()
        self.total_box.config(text=f"Order Total\n₱ {total:.2f}")

        if not self.cart_stack:
            self.cart_preview_label.config(text="Cart is empty")
        else:
            summary = ", ".join([item['name'] for item in self.cart_stack])
            self.cart_preview_label.config(text=f"Items: {summary}")

    def submit_order(self):
        if not self.cart_stack:
            messagebox.showerror("Empty Cart", "Please select items before reviewing order!")
            return

        order_data = {
            "id": self.next_order_id,
            "items": [item['name'] for item in self.cart_stack],
            "total": self.calculate_total()
        }

        self.kitchen_queue.append(order_data)

        messagebox.showinfo("Kiosk Payment", f"Payment Successful!\nOrder #{self.next_order_id} sent to kitchen queue.")

        self.next_order_id += 1
        self.clear_cart()
        self.refresh_kitchen_window()

    def open_kitchen_display_system(self):
        self.kitchen_win = tk.Toplevel(self.root)
        self.kitchen_win.title("Kitchen Display System (FIFO Queue)")
        self.kitchen_win.geometry("450x400")

        tk.Label(
            self.kitchen_win,
            text="👨‍🍳 KITCHEN PREPARATION QUEUE (FIFO)",
            font=("Arial", 12, "bold"),
            bg="#333333",
            fg="white",
            pady=8
        ).pack(fill=tk.X)

        self.k_tree = ttk.Treeview(self.kitchen_win, columns=("ID", "Meals", "Total"), show="headings")
        self.k_tree.heading("ID", text="Order #")
        self.k_tree.heading("Meals", text="Meal Details")
        self.k_tree.heading("Total", text="Total")
        self.k_tree.column("ID", width=60, anchor="center")
        self.k_tree.column("Meals", width=260)
        self.k_tree.column("Total", width=70, anchor="center")
        self.k_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_fulfill = tk.Button(
            self.kitchen_win,
            text="🔔 Fulfill Next Order (Dequeue FIFO)",
            font=("Arial", 10, "bold"),
            bg="#388E3C",
            fg="white",
            pady=6,
            command=self.fulfill_kitchen_order,
            cursor="hand2"
        )
        btn_fulfill.pack(fill=tk.X, padx=5, pady=5)

    def refresh_kitchen_window(self):
        for row in self.k_tree.get_children():
            self.k_tree.delete(row)
        for order in self.kitchen_queue:
            meals_str = ", ".join(order['items'])
            self.k_tree.insert("", tk.END, values=(f"#{order['id']}", meals_str, f"₱{order['total']:.2f}"))

    def fulfill_kitchen_order(self):
        if not self.kitchen_queue:
            messagebox.showwarning("Kitchen Empty", "No orders left in queue!")
            return

        done = self.kitchen_queue.popleft()
        self.refresh_kitchen_window()
        messagebox.showinfo("Order Complete", f"Order #{done['id']} completed and ready for counter pickup!")


if __name__ == "__main__":
    root = tk.Tk()
    app = JollibeeKioskGUI(root)
    root.mainloop()