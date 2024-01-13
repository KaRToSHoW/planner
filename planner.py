import tkinter as tk
from tkinter import ttk
import babel
from babel import numbers
import tkcalendar
from tkcalendar import DateEntry
import tkinter.messagebox as messagebox
import sqlite3
import os
import webbrowser

class Database:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'planner.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                task TEXT,
                deadline TEXT,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (goal_id) REFERENCES goals (id)
            )
        ''')

        self.conn.commit()

    def insert_goal(self, name):
        self.cursor.execute('INSERT INTO goals (name) VALUES (?)', (name,))
        self.conn.commit()

    def insert_task(self, goal_id, task, deadline):
        self.cursor.execute('INSERT INTO tasks (goal_id, task, deadline) VALUES (?, ?, ?)', (goal_id, task, deadline.strftime('%Y-%m-%d')))
        self.conn.commit()

    def get_goals(self):
        self.cursor.execute('SELECT * FROM goals')
        return self.cursor.fetchall()

    def get_tasks(self, goal_id):
        self.cursor.execute('SELECT * FROM tasks WHERE goal_id = ?', (goal_id,))
        return self.cursor.fetchall()

class PlannerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Цели 360: Достижения в Действии")
        master.geometry("550x350")

        # Set white background for the main window
        master.configure(bg="grey")

        self.goals = []
        self.tasks = {}
        self.task_count = 0
        self.selected_goal = None

        # Создайте фрейм для выравнивания элементов по центру
        center_frame = tk.Frame(master,pady=30,padx=30,bg='grey')
        center_frame.pack(expand=True)

        self.goal_entry = tk.Entry(center_frame, width=42,border=2)
        self.goal_entry.pack(pady=5)
        
        self.goal_label = tk.Label(center_frame, text="ЦЕЛЬ:", bg="black", width=36, height=1,foreground="white")
        self.goal_label.place(y=-17)
        
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="white", background="black", padding=(10, 7), borderwidth=2, relief=tk.FLAT, anchor="center", justify="center")

        self.create_plan_button = ttk.Button(center_frame, text="ПОСТАВИТЬ ЦЕЛЬ", command=self.open_create_plan_window, style='BW.TLabel', width=35,cursor="hand2")
        self.create_plan_button.pack(pady=5)

        self.start_button = ttk.Button(center_frame, text="НАЧАТЬ", command=self.open_start_menu,style='BW.TLabel', width=30,cursor="hand2")
        self.start_button.pack(pady=5)

        self.motivational_websites_button = ttk.Button(center_frame, text="МОТИВАЦИОННЫЕ САЙТЫ",command=self.open_motivational_websites_window, style='BW.TLabel', width=25,cursor="hand2")
        self.motivational_websites_button.pack(pady=5)

        self.task_count_label = None
        # Assuming Database class is defined somewhere
        self.db = Database()
        self.load_data()

    def load_data(self):
        # Загружаем цели и задачи из базы данных при запуске приложения
        goals = self.db.get_goals()
        for goal_info in goals:
            goal_name = goal_info[1]
            self.goals.append(goal_name)
            tasks = self.db.get_tasks(goal_info[0])
            self.tasks[goal_name] = {'tasks': [{'task': task[2], 'deadline': task[3]} for task in tasks]}

    def open_create_plan_window(self):
        goal = self.goal_entry.get().strip()
        if goal:  # Проверяем, не пуста ли цель
            self.goals.append(goal)
            self.db.insert_goal(goal)
            self.set_goal(goal)

    def set_goal(self, selected_goal):
        self.selected_goal = selected_goal

        create_plan_window = tk.Toplevel(self.master)
        create_plan_window.title("Создать План")
        create_plan_window.geometry("300x500")
        create_plan_window.configure(bg="gray") 

        # Центрирование окна
        screen_width = create_plan_window.winfo_screenwidth()
        screen_height = create_plan_window.winfo_screenheight()
        x_coordinate = int((screen_width - 500) / 2)
        y_coordinate = int((screen_height - 400) / 2)
        create_plan_window.geometry(f"300x500+{x_coordinate}+{y_coordinate}")

        # Выбрать цель
        deadline_entry_label = tk.Label(create_plan_window, text="ВЫБРАТЬ ЦЕЛЬ:", bg="black", fg="white",width=17)
        deadline_entry_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        goal_id = self.db.get_goals()[self.goals.index(selected_goal)][0]
        goal_var = tk.StringVar(create_plan_window)
        goal_var.set(selected_goal if selected_goal in self.goals else "")
        goal_dropdown = tk.OptionMenu(create_plan_window, goal_var, *self.goals)
        goal_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Ввести задачу
        task_entry_label = tk.Label(create_plan_window, text="ВВЕДИТЕ ЗАДАЧУ:", bg="black", fg="white",width=17)
        task_entry_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        task_entry = tk.Entry(create_plan_window, width=40)
        task_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Календарь
        deadline_label = tk.Label(create_plan_window, text="УКАЖИТЕ ДЕДЛАЙН:", bg="black", fg="white",width=17)
        deadline_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")


        deadline_cal = tkcalendar.DateEntry(create_plan_window, date_pattern="dd.mm.yyyy")
        deadline_cal.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Кнопки
        accept_tasks_button = tk.Button(create_plan_window, text="ПРИНЯТЬ ЗАДАЧУ", command=lambda: self.accept_tasks(selected_goal, task_entry.get(), deadline_cal.get_date(), task_listbox), width=35, bg="black", fg="white",cursor="hand2")
        accept_tasks_button.grid(row=3, column=0, columnspan=2, pady=10)

        return_home_button = tk.Button(create_plan_window, text="ВЕРНУТСЯ НА ГЛАВНУЮ", command=create_plan_window.destroy, width=35, bg="black", fg="white",cursor="hand2")
        return_home_button.grid(row=4, column=0, columnspan=2, pady=10)

        accept_tasks_button = tk.Button(create_plan_window, text="ПРИНЯТЬ ЗАДАЧУ", command=lambda: self.accept_tasks(selected_goal, task_entry.get(), deadline_cal.get_date(), task_listbox), width=35, bg="black", fg="white",cursor="hand2")
        accept_tasks_button.grid(row=3, column=0, columnspan=2, pady=10)

        return_home_button = tk.Button(create_plan_window, text="ВЕРНУТСЯ НА ГЛАВНУЮ", command=create_plan_window.destroy, width=35, bg="black", fg="white",cursor="hand2")
        return_home_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Количество задач
        self.task_count_label = tk.Label(create_plan_window, text="КОЛИЧЕСТВО ЗАДАЧ: {}".format(self.task_count), bg="black", fg="white")
        self.task_count_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        # Список задач
        task_listbox = tk.Listbox(create_plan_window, selectmode=tk.MULTIPLE, width=40)
        task_listbox.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

        for task_info in self.db.get_tasks(goal_id):
            task_listbox.insert(tk.END, f"{task_info[2]} (Дедлайн: {task_info[3]})")

        # Установить одинаковую ширину для колонок
        create_plan_window.grid_columnconfigure(1, weight=1)

    def accept_tasks(self, selected_goal, task, deadline, task_listbox):
        self.task_count += 1
        self.task_count_label.config(text="Количество задач: {}".format(self.task_count))

        if selected_goal not in self.tasks:
            self.tasks[selected_goal] = {'tasks': []}

        task_info = {'task': task, 'deadline': deadline.strftime("%d.%m.%Y")}
        self.tasks[selected_goal]['tasks'].append(task_info)

        goal_id = self.db.get_goals()[self.goals.index(selected_goal)][0]
        self.db.insert_task(goal_id, task, deadline)

        # Обновим список задач в окне создания плана
        self.update_task_listbox(selected_goal, task_listbox)

    def update_task_listbox(self, selected_goal, task_listbox):
        task_listbox.delete(0, tk.END)
        tasks = self.db.get_tasks(self.db.get_goals()[self.goals.index(selected_goal)][0])
        for task_info in tasks:
            task_listbox.insert(tk.END, f"{task_info[2]} (Дедлайн: {task_info[3]})")

    def open_motivational_websites_window(self):
        motivational_websites_window = tk.Toplevel(self.master)
        motivational_websites_window.title("Мотивационные Сайты")
        motivational_websites_window.geometry("400x300")
        motivational_websites_window.configure(bg="gray")

        websites_label = tk.Label(motivational_websites_window, text="СПИСОК МОТИВАЦИОННЫХ САЙТОВ:", bg="black", fg="white")
        websites_label.pack(pady=3)

        motivational_websites_list = [
            "1. TED Talks (ted.com)",
            "2. Coursera (coursera.org)",
            "3. Medium (medium.com)",
            "4. Duolingo (duolingo.com)",
            "5. Khan Academy (khanacademy.org)"
        ]

        def open_link(website):
            url = website.split('(')[-1].split(')')[0]
            webbrowser.open(url)

        for website in motivational_websites_list:
            website_label = tk.Label(motivational_websites_window, text=website, bg="black", fg="white", cursor="hand2", pady=3)
            website_label.bind("<Button-1>", lambda event, website=website: open_link(website))
            website_label.pack(pady=4)

        return_home_button = tk.Button(motivational_websites_window, text="ВЕРНУТЬСЯ", command=motivational_websites_window.destroy, width=40,cursor="hand2", bg="black", fg="white")
        return_home_button.pack(pady=10)
        
    def open_start_menu(self):
        start_menu = tk.Toplevel(self.master)
        start_menu.title("Меню Начала")
        start_menu.geometry("400x350")
        start_menu.configure(bg="gray") 

        goal_label = tk.Label(start_menu, text="ВЫБЕРЕТЕ ЦЕЛЬ:", bg="black", fg="white")
        goal_label.pack(pady=5)

        goal_var = tk.StringVar(start_menu)
        goal_var.set(self.selected_goal if self.selected_goal in self.goals else "")
        goal_dropdown = tk.OptionMenu(start_menu, goal_var, *self.goals, command=lambda event=None: self.update_task_listbox(goal_var.get(), task_listbox))
        goal_dropdown.pack(pady=5)

        task_label = tk.Label(start_menu, text="СПИСОК ЗАДАЧ:", bg="black", fg="white")
        task_label.pack(pady=5)

        task_listbox = tk.Listbox(start_menu, selectmode=tk.MULTIPLE, width=50)
        task_listbox.pack(pady=5)

        # Загрузим задачи для текущей цели
        self.update_task_listbox(goal_var.get(), task_listbox)

        def delete_selected_tasks():
            selected_tasks = task_listbox.curselection()
            if selected_tasks:
                selected_goal = self.selected_goal
                selected_tasks_indexes = list(selected_tasks)
                selected_tasks_indexes.sort(reverse=True)

                # Удаляем задачи из базы данных
                with sqlite3.connect('planner.db') as conn:
                    c = conn.cursor()

                    for index in selected_tasks_indexes:
                        task_id = self.tasks[selected_goal]['tasks'][index].get('id')
                        if task_id is not None:
                            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))

                # Удаляем задачи из данных
                for index in selected_tasks_indexes:
                    del self.tasks[selected_goal]['tasks'][index]

                # Обновляем отображение списка задач
                update_task_listbox(self, selected_goal, task_listbox)

        delete_button = tk.Button(start_menu, text="УДАЛИТЬ ВЫДЕЛЕННЫЕ ЗАДАЧИ", command=delete_selected_tasks, bg="black", fg="white",cursor="hand2")
        delete_button.pack(pady=5)

        return_home_button = tk.Button(start_menu, text="ВЕРНУТЬСЯ", command=start_menu.destroy, bg="black", fg="white",cursor="hand2")
        return_home_button.pack(pady=5)
        
        def update_task_listbox(self, selected_goal, task_listbox):
            task_listbox.delete(0, tk.END)
            tasks = self.tasks.get(selected_goal, {}).get('tasks', [])
            for task_info in tasks:
                task_listbox.insert(tk.END, f"{task_info['task']} (Дедлайн: {task_info['deadline']})")

    def start(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PlannerGUI(root)
    root.mainloop()