import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
from datetime import datetime, timedelta

DATA_FILE = "english_trainer_data.json"

DEFAULT_WORDS = [
    {"en": "apple", "ru": "яблоко", "level": "A1", "category": "Food"},
    {"en": "house", "ru": "дом", "level": "A1", "category": "Home"},
    {"en": "water", "ru": "вода", "level": "A1", "category": "Food"},
    {"en": "friend", "ru": "друг", "level": "A1", "category": "People"},
    {"en": "school", "ru": "школа", "level": "A1", "category": "Education"},
    {"en": "work", "ru": "работа", "level": "A2", "category": "Work"},
    {"en": "beautiful", "ru": "красивый", "level": "A2", "category": "Adjectives"},
    {"en": "important", "ru": "важный", "level": "B1", "category": "Adjectives"},
    {"en": "question", "ru": "вопрос", "level": "A2", "category": "Education"},
    {"en": "improve", "ru": "улучшать", "level": "B1", "category": "Verbs"},
    {"en": "environment", "ru": "окружающая среда", "level": "B1", "category": "Nature"},
    {"en": "achievement", "ru": "достижение", "level": "B2", "category": "Abstract"},
    {"en": "opportunity", "ru": "возможность", "level": "B2", "category": "Abstract"},
    {"en": "nevertheless", "ru": "тем не менее", "level": "C1", "category": "Connectors"},
]

LEVELS = ["A1", "A2", "B1", "B2", "C1"]
XP_PER_LEVEL = 100

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "words" in data and "stats" in data:
                    return data
        except Exception:
            pass

    words = []
    for i, w in enumerate(DEFAULT_WORDS, 1):
        words.append({
            **w,
            "id": i,
            "correct": 0,
            "wrong": 0,
            "streak": 0,
            "interval": 0,
            "next_review": ""
        })

    return {
        "words": words,
        "stats": {
            "xp": 0,
            "total_correct": 0,
            "total_wrong": 0,
            "sessions": 0
        }
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

class EnglishTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("English Trainer")
        self.root.geometry("1000x700")
        self.root.minsize(900, 620)

        self.current_word = None
        self.current_mode = None
        self.session_answered = 0
        self.session_correct = 0
        self.options = []

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.build_ui()
        self.refresh_dictionary()
        self.refresh_stats()

    # ---------- UI ----------

    def build_ui(self):
        header = tk.Frame(self.root, bg="#172033", height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🇬🇧 English Trainer",
            bg="#172033",
            fg="white",
            font=("Arial", 25, "bold")
        ).pack(side="left", padx=25, pady=17)

        self.header_stats = tk.Label(
            header,
            text="",
            bg="#172033",
            fg="#d9e2f2",
            font=("Arial", 12)
        )
        self.header_stats.pack(side="right", padx=25)

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)

        self.learn_tab = tk.Frame(self.tabs)
        self.dictionary_tab = tk.Frame(self.tabs)
        self.stats_tab = tk.Frame(self.tabs)

        self.tabs.add(self.learn_tab, text="  🧠 Обучение  ")
        self.tabs.add(self.dictionary_tab, text="  📚 Словарь  ")
        self.tabs.add(self.stats_tab, text="  📊 Статистика  ")

        self.build_learn_tab()
        self.build_dictionary_tab()
        self.build_stats_tab()

    def build_learn_tab(self):
        top = tk.Frame(self.learn_tab)
        top.pack(fill="x", padx=20, pady=15)

        tk.Label(top, text="Уровень:", font=("Arial", 12, "bold")).pack(side="left")
        self.level_var = tk.StringVar(value="Все")
        self.level_combo = ttk.Combobox(
            top, textvariable=self.level_var,
            values=["Все"] + LEVELS, state="readonly", width=8
        )
        self.level_combo.pack(side="left", padx=8)
        self.level_combo.bind("<<ComboboxSelected>>", lambda e: self.reset_question())

        tk.Label(top, text="Тип:", font=("Arial", 12, "bold")).pack(side="left", padx=(25, 0))
        self.mode_var = tk.StringVar(value="Смешанный")
        self.mode_combo = ttk.Combobox(
            top, textvariable=self.mode_var,
            values=["Смешанный", "Перевод", "Выбор ответа", "Написать слово"],
            state="readonly", width=18
        )
        self.mode_combo.pack(side="left", padx=8)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda e: self.reset_question())

        self.progress_label = tk.Label(
            top, text="", font=("Arial", 12), fg="#555"
        )
        self.progress_label.pack(side="right")

        card = tk.Frame(self.learn_tab, bd=1, relief="solid", bg="#f8fafc")
        card.pack(fill="both", expand=True, padx=70, pady=10)

        self.task_label = tk.Label(
            card, text="Нажми «Начать обучение»",
            font=("Arial", 15), bg="#f8fafc", fg="#667085"
        )
        self.task_label.pack(pady=(45, 15))

        self.word_label = tk.Label(
            card, text="—",
            font=("Arial", 38, "bold"),
            bg="#f8fafc"
        )
        self.word_label.pack(pady=10)

        self.answer_entry = tk.Entry(
            card, font=("Arial", 20), justify="center", width=30
        )
        self.answer_entry.pack(pady=15)
        self.answer_entry.bind("<Return>", lambda e: self.check_answer())

        self.options_frame = tk.Frame(card, bg="#f8fafc")
        self.options_frame.pack(pady=5)

        self.feedback_label = tk.Label(
            card, text="", font=("Arial", 15, "bold"),
            bg="#f8fafc"
        )
        self.feedback_label.pack(pady=15)

        buttons = tk.Frame(card, bg="#f8fafc")
        buttons.pack(pady=10)

        self.start_btn = tk.Button(
            buttons, text="▶ Начать обучение",
            command=self.next_question,
            font=("Arial", 13, "bold"), width=20
        )
        self.start_btn.pack(side="left", padx=6)

        self.check_btn = tk.Button(
            buttons, text="✓ Проверить",
            command=self.check_answer,
            font=("Arial", 13, "bold"), width=15
        )
        self.check_btn.pack(side="left", padx=6)

        self.next_btn = tk.Button(
            buttons, text="→ Следующее",
            command=self.next_question,
            font=("Arial", 13), width=15
        )
        self.next_btn.pack(side="left", padx=6)

        self.session_label = tk.Label(
            card, text="За эту сессию: 0 / 0",
            font=("Arial", 12), bg="#f8fafc", fg="#555"
        )
        self.session_label.pack(pady=20)

    def build_dictionary_tab(self):
        form = tk.LabelFrame(
            self.dictionary_tab, text="Добавить новое слово",
            font=("Arial", 12, "bold"), padx=12, pady=12
        )
        form.pack(fill="x", padx=15, pady=12)

        tk.Label(form, text="English").grid(row=0, column=0, padx=5, pady=5)
        self.en_entry = tk.Entry(form, width=22, font=("Arial", 12))
        self.en_entry.grid(row=0, column=1, padx=5)

        tk.Label(form, text="Русский").grid(row=0, column=2, padx=5)
        self.ru_entry = tk.Entry(form, width=22, font=("Arial", 12))
        self.ru_entry.grid(row=0, column=3, padx=5)

        tk.Label(form, text="Уровень").grid(row=0, column=4, padx=5)
        self.new_level = ttk.Combobox(form, values=LEVELS, state="readonly", width=7)
        self.new_level.set("A1")
        self.new_level.grid(row=0, column=5, padx=5)

        tk.Label(form, text="Категория").grid(row=0, column=6, padx=5)
        self.category_entry = tk.Entry(form, width=16, font=("Arial", 12))
        self.category_entry.grid(row=0, column=7, padx=5)

        tk.Button(
            form, text="➕ Добавить",
            command=self.add_word,
            font=("Arial", 11, "bold")
        ).grid(row=0, column=8, padx=10)

        controls = tk.Frame(self.dictionary_tab)
        controls.pack(fill="x", padx=15, pady=5)

        tk.Label(controls, text="Поиск:").pack(side="left")
        self.search_var = tk.StringVar()
        search = tk.Entry(controls, textvariable=self.search_var, width=30)
        search.pack(side="left", padx=7)
        search.bind("<KeyRelease>", lambda e: self.refresh_dictionary())

        tk.Label(controls, text="Уровень:").pack(side="left", padx=(20, 5))
        self.dict_level = tk.StringVar(value="Все")
        combo = ttk.Combobox(
            controls, textvariable=self.dict_level,
            values=["Все"] + LEVELS, state="readonly", width=8
        )
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_dictionary())

        tk.Button(
            controls, text="🗑 Удалить выбранное",
            command=self.delete_word
        ).pack(side="right")

        columns = ("en", "ru", "level", "category", "correct", "wrong", "next")
        self.tree = ttk.Treeview(
            self.dictionary_tab, columns=columns,
            show="headings", height=18
        )

        headings = {
            "en": "English",
            "ru": "Русский",
            "level": "Уровень",
            "category": "Категория",
            "correct": "✓",
            "wrong": "✗",
            "next": "Повторить"
        }

        widths = {
            "en": 170, "ru": 190, "level": 70,
            "category": 130, "correct": 55, "wrong": 55, "next": 150
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        self.tree.pack(fill="both", expand=True, padx=15, pady=10)

    def build_stats_tab(self):
        self.stats_text = tk.Text(
            self.stats_tab, font=("Arial", 14),
            padx=30, pady=30, state="disabled"
        )
        self.stats_text.pack(fill="both", expand=True, padx=30, pady=30)

        tk.Button(
            self.stats_tab, text="🔄 Обновить",
            command=self.refresh_stats,
            font=("Arial", 12)
        ).pack(pady=(0, 20))

    # ---------- Dictionary ----------

    def add_word(self):
        en = self.en_entry.get().strip()
        ru = self.ru_entry.get().strip()
        level = self.new_level.get().strip()
        category = self.category_entry.get().strip() or "Other"

        if not en or not ru:
            messagebox.showwarning("Ошибка", "Заполни английское слово и перевод.")
            return

        if any(w["en"].lower() == en.lower() for w in data["words"]):
            messagebox.showwarning("Ошибка", "Это слово уже есть в словаре.")
            return

        new_id = max([w["id"] for w in data["words"]], default=0) + 1

        data["words"].append({
            "id": new_id,
            "en": en,
            "ru": ru,
            "level": level,
            "category": category,
            "correct": 0,
            "wrong": 0,
            "streak": 0,
            "interval": 0,
            "next_review": ""
        })

        save_data()
        self.en_entry.delete(0, tk.END)
        self.ru_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.refresh_dictionary()
        self.refresh_stats()

    def delete_word(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Ошибка", "Выбери слово в таблице.")
            return

        item = self.tree.item(selected[0])
        word_id = int(item["tags"][0])

        word = next((w for w in data["words"] if w["id"] == word_id), None)
        if not word:
            return

        if not messagebox.askyesno(
            "Удаление",
            f"Удалить «{word['en']} — {word['ru']}»?"
        ):
            return

        data["words"] = [w for w in data["words"] if w["id"] != word_id]
        save_data()
        self.refresh_dictionary()
        self.refresh_stats()

    def refresh_dictionary(self):
        if not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        query = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        level = self.dict_level.get() if hasattr(self, "dict_level") else "Все"

        for w in data["words"]:
            text = f"{w['en']} {w['ru']} {w['category']}".lower()

            if query and query not in text:
                continue
            if level != "Все" and w["level"] != level:
                continue

            next_review = w.get("next_review", "") or "Сейчас"

            self.tree.insert(
                "", tk.END,
                values=(
                    w["en"], w["ru"], w["level"],
                    w["category"], w["correct"],
                    w["wrong"], next_review
                ),
                tags=(str(w["id"]),)
            )

    # ---------- Learning ----------

    def eligible_words(self):
        level = self.level_var.get()

        pool = [
            w for w in data["words"]
            if level == "Все" or w["level"] == level
        ]

        now = datetime.now()

        due = []
        for w in pool:
            nr = w.get("next_review", "")
            if not nr:
                due.append(w)
            else:
                try:
                    if datetime.fromisoformat(nr) <= now:
                        due.append(w)
                except ValueError:
                    due.append(w)

        return due or pool

    def choose_word(self):
        pool = self.eligible_words()

        if not pool:
            return None

        # Ошибочные слова получают больший вес.
        weights = []
        for w in pool:
            weight = 1 + w["wrong"] * 3
            if w["streak"] == 0:
                weight += 3
            weights.append(weight)

        return random.choices(pool, weights=weights, k=1)[0]

    def reset_question(self):
        self.current_word = None
        self.word_label.config(text="—")
        self.task_label.config(text="Нажми «Начать обучение»")
        self.feedback_label.config(text="")
        self.answer_entry.delete(0, tk.END)

        for widget in self.options_frame.winfo_children():
            widget.destroy()

    def next_question(self):
        self.current_word = self.choose_word()

        if not self.current_word:
            messagebox.showwarning(
                "Нет слов",
                "В словаре нет слов для выбранного уровня."
            )
            return

        mode = self.mode_var.get()

        if mode == "Смешанный":
            mode = random.choice(["Перевод", "Выбор ответа", "Написать слово"])

        self.current_mode = mode
        self.feedback_label.config(text="")
        self.answer_entry.delete(0, tk.END)

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        if mode == "Перевод":
            self.task_label.config(text="Переведи слово на русский:")
            self.word_label.config(text=self.current_word["en"])
            self.answer_entry.pack(pady=15)
            self.answer_entry.config(state="normal")
            self.answer_entry.focus()

        elif mode == "Написать слово":
            self.task_label.config(text="Напиши английское слово:")
            self.word_label.config(text=self.current_word["ru"])
            self.answer_entry.pack(pady=15)
            self.answer_entry.config(state="normal")
            self.answer_entry.focus()

        else:
            self.task_label.config(text="Выбери правильный перевод:")
            self.word_label.config(text=self.current_word["en"])
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.pack_forget()
            self.create_options()

        self.progress_label.config(
            text=f"Слов в словаре: {len(data['words'])}"
        )

    def create_options(self):
        correct = self.current_word["ru"]
        others = [
            w["ru"] for w in data["words"]
            if w["ru"] != correct
        ]

        random.shuffle(others)
        self.options = [correct] + others[:3]
        random.shuffle(self.options)

        for answer in self.options:
            btn = tk.Button(
                self.options_frame,
                text=answer,
                font=("Arial", 13),
                width=35,
                command=lambda a=answer: self.check_choice(a)
            )
            btn.pack(pady=4)

    def check_choice(self, answer):
        if not self.current_word:
            return
        self.process_answer(answer, self.current_word["ru"])

    def check_answer(self):
        if not self.current_word or self.current_mode == "Выбор ответа":
            return

        answer = self.answer_entry.get().strip()

        if self.current_mode == "Перевод":
            correct = self.current_word["ru"]
        else:
            correct = self.current_word["en"]

        self.process_answer(answer, correct)

    def process_answer(self, answer, correct):
        if not answer:
            return

        is_correct = answer.strip().lower() == correct.strip().lower()
        w = self.current_word

        if is_correct:
            data["stats"]["total_correct"] += 1
            data["stats"]["xp"] += 10
            w["correct"] += 1
            w["streak"] += 1

            # Интервальное повторение:
            # 1 -> 1 день, 2 -> 2 дня, 3 -> 4 дня, затем удваиваем.
            if w["interval"] <= 0:
                w["interval"] = 1
            else:
                w["interval"] = min(w["interval"] * 2, 60)

            next_date = datetime.now() + timedelta(days=w["interval"])
            w["next_review"] = next_date.isoformat(timespec="seconds")

            self.session_correct += 1

            self.feedback_label.config(
                text=f"✓ Правильно! +10 XP",
                fg="#16803c"
            )

        else:
            data["stats"]["total_wrong"] += 1
            data["stats"]["xp"] = max(0, data["stats"]["xp"] - 2)
            w["wrong"] += 1
            w["streak"] = 0
            w["interval"] = 0
            w["next_review"] = ""

            self.feedback_label.config(
                text=f"✗ Правильный ответ: {correct}",
                fg="#c62828"
            )

        self.session_answered += 1
        data["stats"]["sessions"] += 1

        save_data()
        self.refresh_stats()
        self.refresh_dictionary()

        self.session_label.config(
            text=f"За эту сессию: {self.session_correct} / {self.session_answered}"
        )

    # ---------- Statistics ----------

    def current_level(self):
        xp = data["stats"]["xp"]
        index = min(xp // XP_PER_LEVEL, 9)
        return index + 1

    def refresh_stats(self):
        if not hasattr(self, "stats_text"):
            return

        xp = data["stats"]["xp"]
        correct = data["stats"]["total_correct"]
        wrong = data["stats"]["total_wrong"]
        total = correct + wrong

        accuracy = (correct / total * 100) if total else 0
        app_level = self.current_level()
        xp_in_level = xp % XP_PER_LEVEL

        mastered = sum(
            1 for w in data["words"]
            if w["streak"] >= 3
        )

        need_review = len(self.eligible_words())

        self.header_stats.config(
            text=f"⭐ Уровень {app_level}   XP: {xp}"
        )

        text = f"""
ENGLISH TRAINER — СТАТИСТИКА

⭐ Уровень приложения: {app_level}
⭐ XP: {xp_in_level}/{XP_PER_LEVEL} до следующего уровня

📚 Слов в словаре: {len(data['words'])}
🧠 Хорошо выучено: {mastered}
🔄 Доступно для повторения: {need_review}

✅ Правильных ответов: {correct}
❌ Ошибок: {wrong}
🎯 Точность: {accuracy:.1f}%

📈 Всего учебных сессий: {data['stats']['sessions']}

Система повторения:
• Ошибка → слово появляется снова
• Правильный ответ → интервал увеличивается
• Серия правильных ответов → слово повторяется реже
• Сложные слова получают больший приоритет
"""

        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", text.strip())
        self.stats_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishTrainer(root)
    root.mainloop()
