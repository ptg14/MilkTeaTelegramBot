import csv
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class MenuItem:
    category: str
    item_id: str
    name: str
    description: str
    price_m: int
    price_l: int
    available: bool

    def get_price(self, size: str) -> int:
        return self.price_m if size.upper() == "M" else self.price_l

    def format_display(self) -> str:
        status = "✅" if self.available else "❌ Hết hàng"
        return f"*{self.name}* ({self.item_id})\n📝 {self.description}\n💰 M: {self.price_m:,}đ | L: {self.price_l:,}đ\n{status}"


class Menu:
    CATEGORY_EMOJI = {
        "Trà Sữa": "🧋",
        "Trà Trái Cây": "🍹",
        "Cà Phê": "☕",
        "Đá Xay": "🧊",
        "Topping": "🍡"
    }

    def __init__(self, csv_file: str):
        self.items: Dict[str, MenuItem] = {}
        self.categories: Dict[str, List[MenuItem]] = {}
        self._load(csv_file)

    def _load(self, csv_file: str):
        with open(csv_file, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                item = MenuItem(
                    category=row['category'],
                    item_id=row['item_id'],
                    name=row['name'],
                    description=row['description'],
                    price_m=int(row['price_m']),
                    price_l=int(row['price_l']),
                    available=row['available'].lower() == 'true'
                )
                self.items[item.item_id] = item
                if item.category not in self.categories:
                    self.categories[item.category] = []
                self.categories[item.category].append(item)

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return self.items.get(item_id.upper())

    def get_category_items(self, category: str) -> List[MenuItem]:
        return self.categories.get(category, [])

    def get_available_items(self, category: str) -> List[MenuItem]:
        return [i for i in self.get_category_items(category) if i.available]

    def get_toppings(self) -> List[MenuItem]:
        return self.get_available_items("Topping")

    def format_category_menu(self, category: str) -> str:
        items = self.get_available_items(category)
        emoji = self.CATEGORY_EMOJI.get(category, "📋")
        if not items:
            return f"{emoji} *{category}*\n\n_Không có món nào_"
        text = f"{emoji} *{category}*\n\n"
        for item in items:
            text += f"• `{item.item_id}` - {item.name}\n  M: {item.price_m:,}đ | L: {item.price_l:,}đ\n\n"
        return text
