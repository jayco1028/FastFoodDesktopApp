import collections
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def resource_path(relative_path):
    """Resolve relative paths for local execution and PyInstaller builds."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


IMAGE_DIR = resource_path("image")

CATEGORY_STYLE = {
    "Chickenjoy": ("#F57C00", "🍗"),
    "Yumburger": ("#8D6E63", "🍔"),
    "Jolly Spaghetti": ("#C62828", "🍝"),
    "Burger Steak": ("#5D4037", "🥩"),
    "Desserts & Drinks": ("#EC407A", "🍨"),
}


class JollibeeKioskGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Jollibee Self-Order Kiosk")
        self.root.geometry("560x960")
        self.root.minsize(480, 800)
        self.root.configure(bg="#1A1A1A")

        self.categories = {
            "Chickenjoy": [
                {
                    "name": "1pc Chickenjoy w/ Rice",
                    "price": 95.00,
                    "code": 101,
                    "image": "chicken_rice.png",
                },
                {
                    "name": "1pc Spicy Chickenjoy",
                    "price": 100.00,
                    "code": 102,
                    "image": "chicken_spicy.png",
                },
                {
                    "name": "2pc Chickenjoy Combo",
                    "price": 180.00,
                    "code": 103,
                    "image": "chicken_rice.png",
                },
                {
                    "name": "6pc Chickenjoy Bucket",
                    "price": 430.00,
                    "code": 104,
                    "image": "chicken_bucket.png",
                },
                {
                    "name": "8pc Chickenjoy Bucket",
                    "price": 549.00,
                    "code": 105,
                    "image": "chicken_bucket.png",
                },
            ],
            "Yumburger": [
                {
                    "name": "Yumburger Solo",
                    "price": 40.00,
                    "code": 201,
                    "image": "yumburger.png",
                },
                {
                    "name": "Cheesy Yumburger",
                    "price": 65.00,
                    "code": 202,
                    "image": "yumburger.png",
                },
                {
                    "name": "Bacon Cheese Yumburger",
                    "price": 99.00,
                    "code": 203,
                    "image": "yumburger.png",
                },
                {
                    "name": "Champ Burger",
                    "price": 175.00,
                    "code": 204,
                    "image": "yumburger.png",
                },
            ],
            "Jolly Spaghetti": [
                {
                    "name": "Jolly Spaghetti Solo",
                    "price": 60.00,
                    "code": 301,
                    "image": "spaghetti.png",
                },
                {
                    "name": "Jolly Spaghetti w/ Yumburger",
                    "price": 115.00,
                    "code": 302,
                    "image": "spaghetti.png",
                },
                {
                    "name": "Jolly Spaghetti Family Pan",
                    "price": 240.00,
                    "code": 303,
                    "image": "spaghetti.png",
                },
            ],
            "Burger Steak": [
                {
                    "name": "1pc Burger Steak Solo",
                    "price": 60.00,
                    "code": 401,
                    "image": "burger_steak.png",
                },
                {
                    "name": "2pc Burger Steak Solo",
                    "price": 115.00,
                    "code": 402,
                    "image": "burger_steak.png",
                },
            ],
            "Desserts & Drinks": [
                {
                    "name": "Peach Mango Pie",
                    "price": 45.00,
                    "code": 501,
                    "image": "peach_mango.png",
                },
                {
                    "name": "Halo-Halo Sundae",
                    "price": 49.00,
                    "code": 502,
                    "image": "peach_mango.png",
                },
                {
                    "name": "Pineapple Juice",
                    "price": 45.00,
                    "code": 503,
                    "image": "peach_mango.png",
                },
            ],
        }

        self.photo_references = {}
        self.pil_cache = {}
        self.cart = []
        self.kitchen_queue = collections.deque()
        self.ready_orders = []
        self.next_order_id = 1001
        self.order_type = "Dine-In"
        self.current_category = "Chickenjoy"

        self.setup_ui_shell()
        self.open_kitchen_display_system()
        self.open_order_status_monitor()

        # Center initial pop-up on launch after layout evaluates
        self.root.after(100, self.show_dinein_takeout_popup)

    # --- REUSABLE POP-UP CENTERING ENGINE ---
    def center_window(self, win, width, height):
        """Calculates exact center coordinates relative to the main app window."""
        self.root.update_idletasks()

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        pos_x = root_x + (root_w // 2) - (width // 2)
        pos_y = root_y + (root_h // 2) - (height // 2)

        # Fallback safeguard if coordinates resolve off-screen
        pos_x = max(10, pos_x)
        pos_y = max(10, pos_y)

        win.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def setup_ui_shell(self):
        """Construct main layout container."""
        for w in self.root.winfo_children():
            w.destroy()

        self.header = tk.Frame(self.root, bg="#D32F2F", height=60)
        self.header.pack(fill=tk.X)

        self.header_title = tk.Label(
            self.header,
            text=f"🐝 Jollibee ({self.order_type.upper()})",
            font=("Arial", 14, "bold"),
            bg="#D32F2F",
            fg="#FFC107",
        )
        self.header_title.pack(side=tk.LEFT, padx=15, pady=10)

        btn_switch_type = tk.Button(
            self.header,
            text="Change Mode",
            font=("Arial", 8, "bold"),
            bg="#B71C1C",
            fg="white",
            bd=0,
            command=self.show_dinein_takeout_popup,
        )
        btn_switch_type.pack(side=tk.RIGHT, padx=10)

        self.category_header = tk.Label(
            self.root,
            text=self.current_category,
            font=("Arial", 12, "bold"),
            bg="#0D47A1",
            fg="white",
            pady=4,
        )
        self.category_header.pack(fill=tk.X)

        main_body = tk.Frame(self.root, bg="#F5F5F5")
        main_body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main_body, bg="#E0E0E0", width=120)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        for cat_name in self.categories.keys():
            btn = tk.Button(
                sidebar,
                text=cat_name,
                font=("Arial", 9, "bold"),
                bg="#FFFFFF",
                fg="#333333",
                activebackground="#D32F2F",
                activeforeground="white",
                bd=0,
                pady=12,
                cursor="hand2",
                command=lambda c=cat_name: self.switch_category(c),
            )
            btn.pack(fill=tk.X, pady=1)

        self.grid_canvas = tk.Canvas(main_body, bg="#F5F5F5", highlightthickness=0)
        self.grid_frame = tk.Frame(self.grid_canvas, bg="#F5F5F5")

        scrollbar = ttk.Scrollbar(
            main_body, orient="vertical", command=self.grid_canvas.yview
        )
        self.grid_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.grid_canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.grid_canvas.configure(
                scrollregion=self.grid_canvas.bbox("all")
            ),
        )
        self.root.bind("<Configure>", self.on_window_resize)

        self.render_menu_grid()

        cart_bar = tk.Frame(self.root, bg="#FFFFFF", pady=5, bd=1, relief="raised")
        cart_bar.pack(fill=tk.X)

        self.cart_summary_label = tk.Label(
            cart_bar,
            text="Cart: 0 items",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF",
            fg="#333333",
        )
        self.cart_summary_label.pack(side=tk.LEFT, padx=15)

        btn_view_cart = tk.Button(
            cart_bar,
            text="🛒 View / Edit Basket",
            font=("Arial", 9, "bold"),
            bg="#FF9800",
            fg="white",
            bd=0,
            padx=10,
            pady=5,
            command=self.open_cart_modal,
        )
        btn_view_cart.pack(side=tk.RIGHT, padx=15)

        action_bar = tk.Frame(self.root, bg="#D32F2F", height=60, padx=10, pady=8)
        action_bar.pack(fill=tk.X)

        btn_cancel = tk.Button(
            action_bar,
            text="Cancel Order",
            font=("Arial", 10, "bold"),
            bg="#B71C1C",
            fg="white",
            bd=0,
            command=self.clear_cart,
            cursor="hand2",
        )
        btn_cancel.pack(side=tk.LEFT, fill=tk.Y, padx=2)

        self.total_box = tk.Label(
            action_bar,
            text="Total: ₱ 0.00",
            font=("Arial", 12, "bold"),
            bg="#D32F2F",
            fg="#FFC107",
            padx=10,
        )
        self.total_box.pack(side=tk.LEFT, expand=True)

        btn_pay = tk.Button(
            action_bar,
            text="CHECKOUT ➔",
            font=("Arial", 11, "bold"),
            bg="#388E3C",
            fg="white",
            bd=0,
            padx=15,
            command=self.checkout_flow,
            cursor="hand2",
        )
        btn_pay.pack(side=tk.RIGHT, fill=tk.Y, padx=2)

    # --- DINE-IN / TAKE-OUT POPUP ---
    def show_dinein_takeout_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Select Order Type")
        popup.configure(bg="#D32F2F")
        popup.transient(self.root)
        popup.grab_set()

        # Set centered position
        self.center_window(popup, 360, 260)
        self.build_popup_content(popup)

    def build_popup_content(self, popup):
        container = tk.Frame(popup, bg="#D32F2F", bd=3, relief="solid")
        container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        tk.Label(
            container,
            text="🐝 Welcome to Jollibee",
            font=("Arial", 14, "bold"),
            bg="#D32F2F",
            fg="#FFC107",
            pady=10,
        ).pack()
        tk.Label(
            container,
            text="Please select dining option:",
            font=("Arial", 10, "bold"),
            bg="#D32F2F",
            fg="white",
        ).pack(pady=(0, 15))

        btn_box = tk.Frame(container, bg="#D32F2F")
        btn_box.pack()

        def select_option(mode):
            self.order_type = mode
            self.header_title.config(text=f"🐝 Jollibee ({self.order_type.upper()})")
            popup.destroy()

        btn_dine = tk.Button(
            btn_box,
            text="🍽️\nDINE-IN",
            font=("Arial", 12, "bold"),
            bg="#FFC107",
            fg="#D32F2F",
            width=8,
            height=3,
            bd=0,
            command=lambda: select_option("Dine-In"),
        )
        btn_dine.pack(side=tk.LEFT, padx=10)

        btn_take = tk.Button(
            btn_box,
            text="🛍️\nTAKE-OUT",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#D32F2F",
            width=8,
            height=3,
            bd=0,
            command=lambda: select_option("Take-Out"),
        )
        btn_take.pack(side=tk.RIGHT, padx=10)

    # --- RESPONSIVE IMAGE HANDLERS ---
    def get_base_pil_image(self, filename, category):
        key = f"{category}_{filename}"
        if key in self.pil_cache:
            return self.pil_cache[key]

        path = os.path.join(IMAGE_DIR, filename)
        if PIL_AVAILABLE and os.path.isfile(path):
            try:
                img = Image.open(path).convert("RGBA")
            except Exception:
                img = self.create_fallback_image(category)
        else:
            img = self.create_fallback_image(category)

        self.pil_cache[key] = img
        return img

    def create_fallback_image(self, category):
        color, emoji = CATEGORY_STYLE.get(category, ("#455A64", "🍽"))
        img = Image.new("RGBA", (120, 120), color)
        draw = ImageDraw.Draw(img)

        font = None
        for font_name in (
            "seguiemj.ttf",
            "AppleColorEmoji.ttf",
            "NotoColorEmoji.ttf",
            "arial.ttf",
        ):
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
            draw.text(((120 - w) / 2, (120 - h) / 2), emoji, font=font, fill="white")
        except Exception:
            pass

        return img

    def on_window_resize(self, event):
        """Handler bound to root window resize."""
        if event.widget == self.root:
            if hasattr(self, "_resize_timer"):
                self.root.after_cancel(self._resize_timer)
            self._resize_timer = self.root.after(150, self.render_menu_grid)

    def render_menu_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        items = self.categories[self.current_category]
        self.category_header.config(text=self.current_category)

        win_w = self.root.winfo_width()
        target_img_dim = max(70, min(130, int(win_w / 5)))

        for idx, item in enumerate(items):
            row = idx // 2
            col = idx % 2

            card = tk.Frame(
                self.grid_frame, bg="white", bd=1, relief="solid", padx=5, pady=5
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            pil_img = self.get_base_pil_image(
                item.get("image", ""), self.current_category
            )
            resized = pil_img.resize((target_img_dim, target_img_dim), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)

            ref_key = f"{item['code']}_{target_img_dim}"
            self.photo_references[ref_key] = photo

            icon_label = tk.Label(card, image=photo, bg="white")
            icon_label.image = photo
            icon_label.pack(pady=(2, 0))

            tk.Label(
                card,
                text=item["name"],
                font=("Arial", 9, "bold"),
                bg="white",
                fg="#212121",
                wraplength=120,
                height=2,
            ).pack()
            tk.Label(
                card,
                text=f"₱ {item['price']:.2f}",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#D32F2F",
            ).pack()

            btn_add = tk.Button(
                card,
                text="+ Order",
                font=("Arial", 9, "bold"),
                bg="#D32F2F",
                fg="white",
                bd=0,
                command=lambda i=item: self.open_customize_modal(i),
                cursor="hand2",
            )
            btn_add.pack(pady=4, fill=tk.X)

        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.columnconfigure(1, weight=1)

    def switch_category(self, cat_name):
        self.current_category = cat_name
        self.render_menu_grid()

    # --- ITEM CUSTOMIZATION MODAL ---
    def open_customize_modal(self, item):
        modal = tk.Toplevel(self.root)
        modal.title("Customize Item")
        modal.transient(self.root)
        modal.grab_set()

        # Center Modal
        self.center_window(modal, 320, 420)

        tk.Label(
            modal,
            text=item["name"],
            font=("Arial", 12, "bold"),
            fg="#D32F2F",
            wraplength=280,
            pady=10,
        ).pack()

        opt_frame = tk.Frame(modal, pady=10)
        opt_frame.pack(fill=tk.X, padx=20)

        drink_var = tk.StringVar(value="Regular Coke")
        tk.Label(opt_frame, text="Select Drink:", font=("Arial", 9, "bold")).pack(
            anchor="w"
        )
        drinks = ["Regular Coke", "Pineapple Juice", "Sarsi", "Iced Tea (+₱10)"]
        ttk.OptionMenu(opt_frame, drink_var, drinks[0], *drinks).pack(
            fill=tk.X, pady=(2, 10)
        )

        extra_rice_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            opt_frame, text="Extra Rice (+₱25)", variable=extra_rice_var
        ).pack(anchor="w")

        extra_gravy_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            opt_frame, text="Extra Gravy (+₱10)", variable=extra_gravy_var
        ).pack(anchor="w")

        qty_frame = tk.Frame(modal, pady=10)
        qty_frame.pack()
        qty_var = tk.IntVar(value=1)

        tk.Button(
            qty_frame,
            text="-",
            width=3,
            command=lambda: qty_var.set(max(1, qty_var.get() - 1)),
            font=("Arial", 12, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            qty_frame,
            textvariable=qty_var,
            width=4,
            font=("Arial", 12, "bold"),
        ).pack(side=tk.LEFT)
        tk.Button(
            qty_frame,
            text="+",
            width=3,
            command=lambda: qty_var.set(qty_var.get() + 1),
            font=("Arial", 12, "bold"),
        ).pack(side=tk.LEFT)

        def save_to_cart():
            notes = [drink_var.get()]
            extra = 0.0
            if drink_var.get() == "Iced Tea (+₱10)":
                extra += 10.0
            if extra_rice_var.get():
                notes.append("Extra Rice")
                extra += 25.0
            if extra_gravy_var.get():
                notes.append("Extra Gravy")
                extra += 10.0

            self.cart.append(
                {
                    "name": item["name"],
                    "unit_price": item["price"] + extra,
                    "qty": qty_var.get(),
                    "notes": ", ".join(notes),
                }
            )
            self.update_cart_ui()
            modal.destroy()

        tk.Button(
            modal,
            text="Add to Basket",
            font=("Arial", 11, "bold"),
            bg="#388E3C",
            fg="white",
            bd=0,
            pady=8,
            command=save_to_cart,
        ).pack(fill=tk.X, padx=20, pady=15)

    def calculate_total(self):
        return sum(i["unit_price"] * i["qty"] for i in self.cart)

    def update_cart_ui(self):
        total = self.calculate_total()
        item_count = sum(i["qty"] for i in self.cart)
        self.total_box.config(text=f"Total: ₱ {total:.2f}")
        self.cart_summary_label.config(text=f"Cart: {item_count} items")

    def clear_cart(self):
        self.cart.clear()
        self.update_cart_ui()

    # --- CART BASKET MODAL ---
    def open_cart_modal(self):
        if not self.cart:
            messagebox.showinfo("Cart Empty", "Your basket is empty.")
            return

        modal = tk.Toplevel(self.root)
        modal.title("Your Order Basket")
        modal.transient(self.root)
        modal.grab_set()

        # Center Modal
        self.center_window(modal, 380, 420)

        tk.Label(modal, text="Basket Items", font=("Arial", 12, "bold"), pady=10).pack()
        list_frame = tk.Frame(modal)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        def refresh():
            for w in list_frame.winfo_children():
                w.destroy()
            for idx, entry in enumerate(self.cart):
                row = tk.Frame(list_frame, bg="#EEEEEE", pady=4, padx=5)
                row.pack(fill=tk.X, pady=2)
                tk.Label(
                    row,
                    text=f"{entry['qty']}x {entry['name']}\n └ {entry['notes']}",
                    font=("Arial", 8),
                    bg="#EEEEEE",
                    anchor="w",
                    justify="left",
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Button(
                    row,
                    text="❌",
                    bd=0,
                    bg="#FFCDD2",
                    command=lambda i=idx: remove(i),
                ).pack(side=tk.RIGHT)

        def remove(i):
            self.cart.pop(i)
            self.update_cart_ui()
            if not self.cart:
                modal.destroy()
            else:
                refresh()

        refresh()

    # --- PAYMENT & RECEIPT MODALS ---
    def checkout_flow(self):
        if not self.cart:
            messagebox.showerror("Empty Basket", "Please select items first!")
            return

        pay_modal = tk.Toplevel(self.root)
        pay_modal.title("Select Payment")
        pay_modal.transient(self.root)
        pay_modal.grab_set()

        # Center Modal
        self.center_window(pay_modal, 320, 280)

        tk.Label(
            pay_modal,
            text=f"Total: ₱ {self.calculate_total():.2f}",
            font=("Arial", 12, "bold"),
            fg="#D32F2F",
            pady=15,
        ).pack()

        def process(method):
            pay_modal.destroy()
            order_data = {
                "id": self.next_order_id,
                "type": self.order_type,
                "items": [f"{i['qty']}x {i['name']} ({i['notes']})" for i in self.cart],
                "total": self.calculate_total(),
                "payment": method,
            }
            self.kitchen_queue.append(order_data)
            self.show_order_complete_screen(order_data)
            self.next_order_id += 1
            self.refresh_kitchen_window()
            self.refresh_status_monitor()

        tk.Button(
            pay_modal,
            text="💳 Card",
            font=("Arial", 10, "bold"),
            width=20,
            pady=6,
            bg="#1976D2",
            fg="white",
            bd=0,
            command=lambda: process("Card"),
        ).pack(pady=4)
        tk.Button(
            pay_modal,
            text="📱 E-Wallet (GCash/Maya)",
            font=("Arial", 10, "bold"),
            width=20,
            pady=6,
            bg="#00838F",
            fg="white",
            bd=0,
            command=lambda: process("E-Wallet"),
        ).pack(pady=4)
        tk.Button(
            pay_modal,
            text="💵 Cash at Counter",
            font=("Arial", 10, "bold"),
            width=20,
            pady=6,
            bg="#388E3C",
            fg="white",
            bd=0,
            command=lambda: process("Cash"),
        ).pack(pady=4)

    def show_order_complete_screen(self, order_data):
        """Show full order completion receipt modal centered."""
        complete_modal = tk.Toplevel(self.root)
        complete_modal.title("Order Complete")
        complete_modal.transient(self.root)
        complete_modal.grab_set()
        complete_modal.configure(bg="#F5F5F5")

        # Center Modal
        self.center_window(complete_modal, 380, 520)

        tk.Label(
            complete_modal,
            text="🎉 ORDER COMPLETE!",
            font=("Arial", 16, "bold"),
            bg="#F5F5F5",
            fg="#388E3C",
            pady=15,
        ).pack()

        tk.Label(
            complete_modal,
            text=f"Order Number: #{order_data['id']}",
            font=("Arial", 18, "bold"),
            bg="#F5F5F5",
            fg="#D32F2F",
        ).pack()
        tk.Label(
            complete_modal,
            text=f"Mode: {order_data['type']} | Paid via: {order_data['payment']}",
            font=("Arial", 9, "italic"),
            bg="#F5F5F5",
        ).pack(pady=(0, 10))

        rcpt = tk.Frame(
            complete_modal, bg="white", bd=1, relief="solid", padx=10, pady=10
        )
        rcpt.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        tk.Label(
            rcpt,
            text="--- RECEIPT SUMMARY ---",
            font=("Arial", 9, "bold"),
            bg="white",
        ).pack()

        for item_str in order_data["items"]:
            tk.Label(
                rcpt,
                text=item_str,
                font=("Arial", 8),
                bg="white",
                anchor="w",
                justify="left",
                wraplength=280,
            ).pack(fill=tk.X, pady=1)

        tk.Label(
            rcpt,
            text=f"\nGrand Total: ₱ {order_data['total']:.2f}",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#D32F2F",
        ).pack(anchor="e")

        def start_new_order():
            complete_modal.destroy()
            self.clear_cart()
            self.show_dinein_takeout_popup()

        tk.Button(
            complete_modal,
            text="➕ MAKE A NEW ORDER",
            font=("Arial", 12, "bold"),
            bg="#D32F2F",
            fg="#FFC107",
            bd=0,
            pady=10,
            command=start_new_order,
            cursor="hand2",
        ).pack(fill=tk.X, padx=20, pady=15)

    # --- KITCHEN DISPLAY SYSTEM ---
    def open_kitchen_display_system(self):
        self.kitchen_win = tk.Toplevel(self.root)
        self.kitchen_win.title("Kitchen Display System (KDS)")
        self.kitchen_win.geometry("500x380")

        tk.Label(
            self.kitchen_win,
            text="👨‍🍳 KITCHEN PREPARATION QUEUE",
            font=("Arial", 11, "bold"),
            bg="#212121",
            fg="#FFC107",
            pady=8,
        ).pack(fill=tk.X)

        self.k_tree = ttk.Treeview(
            self.kitchen_win,
            columns=("ID", "Type", "Details"),
            show="headings",
        )
        self.k_tree.heading("ID", text="Order #")
        self.k_tree.heading("Type", text="Type")
        self.k_tree.heading("Details", text="Meals & Customizations")

        self.k_tree.column("ID", width=60, anchor="center")
        self.k_tree.column("Type", width=70, anchor="center")
        self.k_tree.column("Details", width=330)
        self.k_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Button(
            self.kitchen_win,
            text="🔔 Fulfill Order ➔ Mark Ready",
            font=("Arial", 10, "bold"),
            bg="#388E3C",
            fg="white",
            pady=6,
            command=self.fulfill_kitchen_order,
            cursor="hand2",
        ).pack(fill=tk.X, padx=5, pady=5)

    def refresh_kitchen_window(self):
        for row in self.k_tree.get_children():
            self.k_tree.delete(row)
        for order in self.kitchen_queue:
            self.k_tree.insert(
                "",
                tk.END,
                values=(
                    f"#{order['id']}",
                    order["type"],
                    " | ".join(order["items"]),
                ),
            )

    def fulfill_kitchen_order(self):
        if not self.kitchen_queue:
            messagebox.showwarning("Empty Queue", "No pending kitchen orders.")
            return

        done = self.kitchen_queue.popleft()
        self.ready_orders.append(done)
        self.refresh_kitchen_window()
        self.refresh_status_monitor()

    # --- ORDER MONITORING SCREEN ---
    def open_order_status_monitor(self):
        self.status_win = tk.Toplevel(self.root)
        self.status_win.title("Customer Order Status Monitor")
        self.status_win.geometry("450x450")
        self.status_win.configure(bg="#111111")

        tk.Label(
            self.status_win,
            text="📺 ORDER STATUS MONITOR",
            font=("Arial", 14, "bold"),
            bg="#D32F2F",
            fg="white",
            pady=8,
        ).pack(fill=tk.X)

        cols = tk.Frame(self.status_win, bg="#111111")
        cols.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        prep_frame = tk.Frame(cols, bg="#222222", bd=1, relief="solid")
        prep_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(
            prep_frame,
            text="PREPARING",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="black",
            pady=4,
        ).pack(fill=tk.X)
        self.prep_list = tk.Listbox(
            prep_frame,
            bg="#222222",
            fg="#FFC107",
            font=("Arial", 14, "bold"),
            bd=0,
            justify="center",
        )
        self.prep_list.pack(fill=tk.BOTH, expand=True, pady=5)

        ready_frame = tk.Frame(cols, bg="#222222", bd=1, relief="solid")
        ready_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(
            ready_frame,
            text="NOW SERVING",
            font=("Arial", 12, "bold"),
            bg="#388E3C",
            fg="white",
            pady=4,
        ).pack(fill=tk.X)
        self.ready_list = tk.Listbox(
            ready_frame,
            bg="#222222",
            fg="#81C784",
            font=("Arial", 14, "bold"),
            bd=0,
            justify="center",
        )
        self.ready_list.pack(fill=tk.BOTH, expand=True, pady=5)

    def refresh_status_monitor(self):
        self.prep_list.delete(0, tk.END)
        self.ready_list.delete(0, tk.END)

        for o in self.kitchen_queue:
            self.prep_list.insert(tk.END, f"#{o['id']}")

        for o in self.ready_orders:
            self.ready_list.insert(tk.END, f"#{o['id']}")


if __name__ == "__main__":
    root = tk.Tk()
    app = JollibeeKioskGUI(root)
    root.mainloop()