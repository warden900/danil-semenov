import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class CurrencyConverter:
    def __init__(self, root):
        """Инициализация главного окна и начальных данных"""
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("600x450")

        # База данных курсов (фиксированные значения относительно 1 USD)
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "RUB": 75.0,
            "GBP": 0.73,
            "JPY": 110.0
        }

        # Специальные переменные Tkinter для связи с полями ввода и текстом
        self.amount_var = tk.StringVar()  # Сумма ввода
        self.from_currency = tk.StringVar(value="USD")  # Выбранная исходная валюта
        self.to_currency = tk.StringVar(value="EUR")  # Выбранная целевая валюта
        self.result_var = tk.StringVar()  # Текст результата конвертации

        self.history = []  # Список для хранения объектов истории (загружается из JSON)

        # Создаем визуальные элементы и загружаем данные из файла
        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        """Создание графического интерфейса (кнопки, поля, таблицы)"""

        # Верхняя панель (фрейм) для ввода данных
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)

        # Поле ввода суммы
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.amount_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Выбор "Из какой валюты"
        ttk.Label(input_frame, text="Из:").grid(row=1, column=0, sticky=tk.W, pady=5)
        from_combo = ttk.Combobox(input_frame, textvariable=self.from_currency,
                                  values=list(self.exchange_rates.keys()), state="readonly")
        from_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Выбор "В какую валюту"
        ttk.Label(input_frame, text="В:").grid(row=2, column=0, sticky=tk.W, pady=5)
        to_combo = ttk.Combobox(input_frame, textvariable=self.to_currency,
                                values=list(self.exchange_rates.keys()), state="readonly")
        to_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Кнопка запуска расчета
        ttk.Button(input_frame, text="Конвертировать", command=self.convert).grid(row=3, column=0, columnspan=2,
                                                                                  pady=10)

        # Метка для вывода результата
        ttk.Label(input_frame, text="Результат:").grid(row=4, column=0, sticky=tk.W)
        ttk.Label(input_frame, textvariable=self.result_var, font=("Arial", 10, "bold")).grid(row=4, column=1,
                                                                                              sticky=tk.W)

        # Нижняя панель (фрейм) для таблицы истории
        history_frame = ttk.Frame(self.root, padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(history_frame, text="История конвертаций:").pack(anchor=tk.W)

        # Создание таблицы Treeview
        self.tree = ttk.Treeview(history_frame, columns=("Amount", "From", "To", "Result"), show="headings")
        self.tree.heading("Amount", text="Сумма")
        self.tree.heading("From", text="Из")
        self.tree.heading("To", text="В")
        self.tree.heading("Result", text="Результат")

        # Настройка ширины колонок таблицы
        for col in ("Amount", "From", "To", "Result"):
            self.tree.column(col, width=100)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Полоса прокрутки для таблицы
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

    def get_exchange_rate(self, from_curr, to_curr):
        """Математический расчет кросс-курса через базовую валюту (USD)"""
        try:
            if from_curr == to_curr:
                return 1.0
            # Получаем курсы относительно доллара
            from_rate = self.exchange_rates[from_curr]
            to_rate = self.exchange_rates[to_curr]
            # Формула: Целевой_курс / Исходный_курс
            return to_rate / from_rate
        except KeyError:
            messagebox.showerror("Ошибка", "Валюта не найдена")
            return None

    def convert(self):
        """Основная логика при нажатии на кнопку"""
        try:
            # Получаем текст из поля ввода и заменяем запятую на точку для float
            raw_value = self.amount_var.get().replace(',', '.')
            amount = float(raw_value)

            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть больше нуля")
                return

            from_curr = self.from_currency.get()
            to_curr = self.to_currency.get()

            # Вычисляем результат
            rate = self.get_exchange_rate(from_curr, to_curr)
            if rate is not None:
                result = amount * rate
                result_str = f"{result:.2f}"

                # Обновляем текст в интерфейсе
                self.result_var.set(f"{result_str} {to_curr}")

                # Сохраняем операцию в историю
                self.add_to_history(amount, from_curr, to_curr, result_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число (например, 100.50)")

    def add_to_history(self, amount, from_curr, to_curr, result):
        """Добавление новой записи в список, файл и таблицу"""
        item = {
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "result": result
        }
        self.history.append(item)
        self.save_history()  # Запись в файл
        self.update_history_table()  # Обновление таблицы на экране

    def save_history(self):
        """Сохранение текущего списка истории в JSON файл"""
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def load_history(self):
        """Загрузка данных из файла при старте программы"""
        if os.path.exists("history.json"):
            try:
                with open("history.json", "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                # Если файл поврежден, создаем пустой список
                self.history = []
        else:
            # Если файла нет (первый запуск), создаем пустой список
            self.history = []
        self.update_history_table()

    def update_history_table(self):
        """Очистка и полная перерисовка таблицы в интерфейсе"""
        # Удаляем все текущие строки из Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Вставляем данные из self.history в обратном порядке (новые сверху)
        for item in reversed(self.history):
            self.tree.insert("", tk.END, values=(
                item["amount"],
                item["from"],
                item["to"],
                item["result"]
            ))


# Точка входа в программу
if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()  # Запуск бесконечного цикла обработки событий окна
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
