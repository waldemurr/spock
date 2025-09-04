from datetime import datetime
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTabWidget,
)
from api_client import APIClient
from data_manager import DataManager


class MexcPnLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MEXC PnL Tracker")
        self.setGeometry(100, 100, 1400, 800)

        self.data_manager = DataManager()
        self.api_client = APIClient()
        self.data = self.data_manager.load_data()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.update_tables()

    def setup_ui(self):
        # Создаем вкладки
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Вкладка с валютами
        self.currencies_tab = QWidget()
        self.currencies_layout = QVBoxLayout(self.currencies_tab)

        self.currencies_table = QTableWidget()
        self.currencies_table.setColumnCount(7)
        self.currencies_table.setHorizontalHeaderLabels(
            [
                "Валюта",
                "Количество",
                "Средняя цена",
                "Общая стоимость",
                "Текущая цена",
                "Текущая стоимость",
                "PnL (%)",
            ]
        )
        self.currencies_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.currencies_layout.addWidget(self.currencies_table)

        # Вкладка со сделками
        self.trades_tab = QWidget()
        self.trades_layout = QVBoxLayout(self.trades_tab)

        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels(
            ["Валюта", "Тип", "Цена", "Количество", "Стоимость", "Дата"]
        )
        self.trades_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.trades_layout.addWidget(self.trades_table)

        # Добавляем вкладки
        self.tabs.addTab(self.currencies_tab, "Валюты")
        self.tabs.addTab(self.trades_tab, "Сделки")

        # Панель кнопок
        button_layout = QHBoxLayout()
        self.add_buy_btn = QPushButton("Добавить покупку")
        self.add_sell_btn = QPushButton("Добавить продажу")
        self.refresh_btn = QPushButton("Обновить цены")
        self.total_label = QLabel("Общий PnL: 0.00 USDT (0.00%)")

        button_layout.addWidget(self.add_buy_btn)
        button_layout.addWidget(self.add_sell_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.total_label)
        button_layout.addStretch()

        self.layout.addLayout(button_layout)

        # Подключаем кнопки к слотам
        self.add_buy_btn.clicked.connect(lambda: self.add_trade("buy"))
        self.add_sell_btn.clicked.connect(lambda: self.add_trade("sell"))
        self.refresh_btn.clicked.connect(self.update_prices)

    def add_trade(self, trade_type):
        dialog = TradeDialog(self, trade_type)
        if dialog.exec():
            try:
                trade_data = dialog.get_trade_data()
                self.data["trades"].append(trade_data)
                self.update_currencies()
                self.data_manager.save_data(self.data)
                self.update_tables()
            except ValueError:
                QMessageBox.warning(
                    self, "Ошибка", "Пожалуйста, введите корректные числовые значения"
                )

    def update_currencies(self):
        # Сбрасываем currencies
        self.data["currencies"] = {}

        # Группируем сделки по валютам
        currency_groups = {}
        for trade in self.data["trades"]:
            currency = trade["currency"]
            if currency not in currency_groups:
                currency_groups[currency] = []
            currency_groups[currency].append(trade)

        # Рассчитываем агрегированные данные для каждой валюты
        for currency, trades in currency_groups.items():

            buy_quantity = sum(t["quantity"] for t in trades if t["type"] == "buy")
            sell_quantity = sum(t["quantity"] for t in trades if t["type"] == "sell")
            net_quantity = buy_quantity - sell_quantity

            buy_cost = sum(t["cost"] for t in trades if t["type"] == "buy")
            sell_cost = sum(t["cost"] for t in trades if t["type"] == "sell")
            net_cost = buy_cost - sell_cost

            # if net_quantity > 0:
            #     avg_price = net_cost / net_quantity
            # else:
            #     avg_price = 0

            # Получаем текущую цену
            current_price = self.api_client.get_price(currency)
            current_value = current_price * net_quantity
            pnl = current_value - net_cost
            pnl_percent = (pnl / net_cost * 100) if net_cost != 0 else 0

            self.data["currencies"][currency] = {
                "quantity": net_quantity,
                "cost": net_cost,
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
            }

    def update_prices(self):
        for currency in self.data["currencies"]:
            current_price = self.api_client.get_price(currency)
            self.data["currencies"][currency]["current_price"] = current_price

            # Пересчитываем PnL
            currency_data = self.data["currencies"][currency]
            current_value = current_price * currency_data["quantity"]
            currency_data["pnl"] = current_value - currency_data["cost"]
            if currency_data["cost"] != 0:
                currency_data["pnl_percent"] = (
                    currency_data["pnl"] / currency_data["cost"]
                ) * 100

        self.data_manager.save_data(self.data)
        self.update_tables()

    def update_tables(self):
        self.update_currencies_table()
        self.update_trades_table()
        self.update_total_pnl()

    def update_currencies_table(self):
        self.currencies_table.setRowCount(0)
        for row, (currency, data) in enumerate(self.data["currencies"].items()):
            self.currencies_table.insertRow(row)

            self.currencies_table.setItem(row, 0, QTableWidgetItem(currency))
            self.currencies_table.setItem(
                row, 1, QTableWidgetItem(f"{data['quantity']:.6f}")
            )
            avg_price = data["cost"] / data["quantity"] if data["quantity"] > 0 else 0
            self.currencies_table.setItem(row, 2, QTableWidgetItem(f"{avg_price:.6f}"))
            self.currencies_table.setItem(
                row, 3, QTableWidgetItem(f"{data['cost']:.2f}")
            )
            self.currencies_table.setItem(
                row, 4, QTableWidgetItem(f"{data['current_price']:.6f}")
            )
            current_value = data["current_price"] * data["quantity"]
            self.currencies_table.setItem(
                row, 5, QTableWidgetItem(f"{current_value:.2f}")
            )

            pnl_item = QTableWidgetItem(f"{data['pnl_percent']:.2f}%")
            if data["pnl_percent"] < 0:
                pnl_item.setBackground(QColor(200, 100, 100))
            else:
                pnl_item.setBackground(QColor(100, 200, 100))
            self.currencies_table.setItem(row, 6, pnl_item)

    def update_trades_table(self):
        self.trades_table.setRowCount(0)
        for row, trade in enumerate(self.data["trades"]):
            self.trades_table.insertRow(row)

            self.trades_table.setItem(row, 0, QTableWidgetItem(trade["currency"]))

            type_item = QTableWidgetItem(
                "Покупка" if trade["type"] == "buy" else "Продажа"
            )
            if trade["type"] == "buy":
                type_item.setBackground(QColor(100, 200, 100))  # Зеленый для покупок
            else:
                type_item.setBackground(QColor(200, 100, 100))  # Красный для продаж
            self.trades_table.setItem(row, 1, type_item)

            self.trades_table.setItem(row, 2, QTableWidgetItem(f"{trade['price']:.6f}"))
            self.trades_table.setItem(
                row, 3, QTableWidgetItem(f"{trade['quantity']:.6f}")
            )
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"{trade['cost']:.2f}"))

            # Форматируем дату
            try:
                date_obj = datetime.fromisoformat(
                    trade["timestamp"].replace("Z", "+00:00")
                )
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                print(f"Error occured: {e}")
                date_str = trade["timestamp"]
            self.trades_table.setItem(row, 5, QTableWidgetItem(date_str))

    def update_total_pnl(self):
        total_pnl = sum(
            currency_data["pnl"] for currency_data in self.data["currencies"].values()
        )
        total_cost = sum(
            currency_data["cost"] for currency_data in self.data["currencies"].values()
        )
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost != 0 else 0

        self.total_label.setText(
            f"Общий PnL: {total_pnl:.2f} USDT ({total_pnl_percent:.2f}%)"
        )


class TradeDialog(QDialog):
    def __init__(self, parent=None, trade_type="buy"):
        super().__init__(parent)
        self.trade_type = trade_type
        self.setWindowTitle(f"Добавить {self.get_type_name()}")
        self.setup_ui()

    def get_type_name(self):
        return "покупку" if self.trade_type == "buy" else "продажу"

    def setup_ui(self):
        layout = QFormLayout(self)

        self.currency_edit = QLineEdit()
        self.price_edit = QLineEdit()
        self.quantity_edit = QLineEdit()

        layout.addRow("Валюта (например, TON):", self.currency_edit)
        layout.addRow(f"Цена {self.get_type_name()} (USDT):", self.price_edit)
        layout.addRow("Количество:", self.quantity_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_trade_data(self):
        return {
            "currency": self.currency_edit.text().strip().upper(),
            "type": self.trade_type,
            "price": float(self.price_edit.text()),
            "quantity": float(self.quantity_edit.text()),
            "cost": float(self.price_edit.text()) * float(self.quantity_edit.text()),
            "timestamp": datetime.now().isoformat(),
        }
