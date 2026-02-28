from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
from menu import MenuItem

@dataclass
class CartItem:
    item: MenuItem
    size: str
    quantity: int
    toppings: List[MenuItem] = field(default_factory=list)
    note: str = ""

    @property
    def item_price(self) -> int:
        return self.item.get_price(self.size) + sum(t.price_m for t in self.toppings)

    @property
    def total_price(self) -> int:
        return self.item_price * self.quantity

    def format_display(self, idx: int) -> str:
        txt = f"{idx}. *{self.item.name}* ({self.size}) x{self.quantity}\n   💰 {self.item.get_price(self.size):,}đ"
        if self.toppings:
            names = ", ".join(t.name for t in self.toppings)
            txt += f"\n   🍡 {names} (+{sum(t.price_m for t in self.toppings):,}đ)"
        if self.note:
            txt += f"\n   📝 {self.note}"
        txt += f"\n   ➡️ {self.total_price:,}đ"
        return txt


class Cart:
    def __init__(self, user_id: int, user_name: str = ""):
        self.user_id = user_id
        self.user_name = user_name
        self.items: List[CartItem] = []
        self.customer_name = ""
        self.customer_phone = ""
        self.delivery_note = ""
        self.created_at = datetime.now()

    def add_item(self, item: MenuItem, size: str, qty: int = 1, toppings: List[MenuItem] = None, note: str = ""):
        self.items.append(CartItem(item=item, size=size.upper(), quantity=qty, toppings=toppings or [], note=note))

    def remove_item(self, idx: int) -> bool:
        if 1 <= idx <= len(self.items):
            self.items.pop(idx - 1)
            return True
        return False

    def clear(self):
        self.items.clear()
        self.customer_name = ""
        self.customer_phone = ""
        self.delivery_note = ""

    @property
    def total_price(self) -> int:
        return sum(i.total_price for i in self.items)

    @property
    def total_items(self) -> int:
        return sum(i.quantity for i in self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    def format_cart(self) -> str:
        if self.is_empty:
            return "🛒 Giỏ hàng trống!"
        txt = "🛒 *GIỎ HÀNG*\n" + "━" * 20 + "\n\n"
        for i, item in enumerate(self.items, 1):
            txt += item.format_display(i) + "\n\n"
        txt += "━" * 20 + f"\n📦 Tổng: {self.total_items} món\n💵 *{self.total_price:,}đ*"
        return txt

    def format_order_summary(self) -> str:
        txt = "📋 *XÁC NHẬN ĐƠN*\n" + "━" * 20 + "\n\n"
        txt += f"👤 {self.customer_name}\n📞 {self.customer_phone}\n"
        if self.delivery_note:
            txt += f"📝 {self.delivery_note}\n"
        txt += "\n*Chi tiết:*\n"
        for i, item in enumerate(self.items, 1):
            txt += f"{i}. {item.item.name} ({item.size}) x{item.quantity}"
            if item.toppings:
                txt += f" + {', '.join(t.name for t in item.toppings)}"
            txt += f" - {item.total_price:,}đ\n"
        txt += "\n" + "━" * 20 + f"\n💵 *TỔNG: {self.total_price:,}đ*"
        return txt

    def format_for_owner(self, order_id: str) -> str:
        txt = f"🔔 *ĐƠN MỚI!*\n📋 `{order_id}`\n" + "━" * 20 + "\n\n"
        txt += f"👤 {self.customer_name}\n📞 {self.customer_phone}\n"
        if self.user_name:
            txt += f"🆔 @{self.user_name}\n"
        if self.delivery_note:
            txt += f"📝 {self.delivery_note}\n"
        txt += f"🕐 {datetime.now().strftime('%H:%M %d/%m/%Y')}\n\n*📦 CHI TIẾT:*\n"
        for i, item in enumerate(self.items, 1):
            txt += f"\n{i}. *{item.item.name}*\n   Size {item.size} | SL: {item.quantity}\n"
            if item.toppings:
                txt += f"   Topping: {', '.join(t.name for t in item.toppings)}\n"
            txt += f"   Giá: {item.total_price:,}đ\n"
        txt += "\n" + "━" * 20 + f"\n💵 *TỔNG: {self.total_price:,}đ*"
        return txt


class CartManager:
    def __init__(self):
        self.carts: Dict[int, Cart] = {}

    def get_cart(self, user_id: int, user_name: str = "") -> Cart:
        if user_id not in self.carts:
            self.carts[user_id] = Cart(user_id, user_name)
        return self.carts[user_id]

    def clear_cart(self, user_id: int):
        if user_id in self.carts:
            self.carts[user_id].clear()
