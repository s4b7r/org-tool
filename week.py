import tkinter as tk
from tkinter import END
from functools import partial
from tkinter.colorchooser import askcolor
import pickle
from pathlib import Path
from typing import Self


# DEBUG = True

# Define days and hours
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOURS = [f"{h}:00" for h in range(8, 17+1)]
INPUT_CATEGORIES = ['Proj', 'Self', 'Plan', 'Buff', 'Beig', 'Meet']

ROWS_PER_HOUR = 4
COLS_PER_DAY = len(INPUT_CATEGORIES) + (BUTTONS_PER_SLOT := 1)
INPUT_ROWS_TOTAL = ROWS_PER_HOUR * len(HOURS)
INPUT_COLS_TOTAL = COLS_PER_DAY * len(DAYS)

N_ROW_HEADERS = 1
N_COL_HEADERS = 2
COL_DAYHEADER_ROW = 0
COL_CATHEADER_ROW = COL_DAYHEADER_ROW + 1
ROW_HOURHEADER_COL = 0

SAVE_FILE = Path('.') / '.save'


class Timeslot:
    def __init__(self):
        self._data : Timeslot_Data = Timeslot_Data()
        self._gui_childs = []
        self._gui_childs_attrs = []

    def __getattr__(self, name):
        if name == 'data': raise AttributeError
        return getattr(self.data, name)

    def __setattr__(self, name, value):
        if name in Timeslot_Data.RETURN_ATTRIBUTES:
            setattr(self.data, name, value)
            self.update_gui_childs()
        else:
            super().__setattr__(name, value)

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = Timeslot_Data(data=value)
        self.update_gui_childs()

    def add_gui_child(self, child, attr_name=None):
        self._gui_childs.append(child)
        if attr_name:
            self._gui_childs_attrs.append({'child': child, 'attr': attr_name})

    def update_gui_childs_bg(self):
        for child in self._gui_childs:
            child.config(bg=self.bg)

    def update_gui_childs(self):
        self.update_gui_childs_bg()

        for child in self._gui_childs_attrs:
            attr = child['attr']
            child = child['child']
            val = getattr(self, attr)
            child.delete(0, END)
            child.insert(0, f'{val:.2f}')
            # Do not show zeros
            if val == 0:
                child.delete(0, END)
        
        update_summary(sum_table, slot_grid)


class Timeslot_Data:
    RETURN_ATTRIBUTES = ['title', 'bg'] + INPUT_CATEGORIES
    
    def __init__(self, data: Self = None):
        self.title = ''
        self.bg = '#ffffff'
        for cat in INPUT_CATEGORIES:
            setattr(self, cat, 0.)
        if data:
            for attr in self.RETURN_ATTRIBUTES:
                setattr(self, attr, getattr(data, attr))

    def __str__(self):
        return f'Timeslot_Data<{", ".join((f"{k}: {getattr(self, k)}" for k in self.RETURN_ATTRIBUTES))}>'


def create_table_window(root):
    table_window = tk.Toplevel(root)
    table_window.title("Timeslot")
    table_window.bind("<Escape>", lambda _: root.destroy())
    table_window.protocol('WM_DELETE_WINDOW', lambda: root.destroy())

    table = tk.Text(table_window, width=40, height=20)
    table.pack(fill="both", expand=True)
    return table


TABLE_MAPPING = {
                'Title': 'title',
                'Color': 'bg'
                }


def update_timeslot_from_table(slot, table_frame):
    for widget in table_frame.winfo_children():
        if isinstance(widget, tk.Entry):
            key = widget.grid_info()['row']
            value = widget.get()
            for i, attr in enumerate(TABLE_MAPPING.values()):
                if key == i:
                    setattr(slot, attr, value)
            if key >= len(TABLE_MAPPING):
                if ',' in value:
                    value = value.replace(',', '.')
                try:
                    value = float(value)
                except ValueError:
                    value = 0.
                setattr(slot, INPUT_CATEGORIES[key - len(TABLE_MAPPING)], float(value))
    update_table(None, table_frame=table_frame, slot=slot)


def update_table(_, table_frame, slot):
    def pick_color(_, *, entry: tk.Entry):
        # print(entry)
        _, color = askcolor()
        entry.delete(0, END)
        entry.insert(0, color)
        update_timeslot_from_table(slot, table_frame)

    key_value_pairs = {
                        k: getattr(slot, attr) for k, attr in TABLE_MAPPING.items()
                    } | {
                        k: getattr(slot, k) for k in INPUT_CATEGORIES
                    }
    for widget in table_frame.winfo_children():
        widget.destroy()
    for i, (key, value) in enumerate(key_value_pairs.items()):
        label = tk.Label(table_frame, text=key, name=f'klabel_{key}')
        label.grid(row=i, column=0, padx=5, pady=5)
        entry_field = tk.Entry(table_frame, name=f'ventry_{key}')
        entry_field.grid(row=i, column=1, padx=5, pady=5)
        entry_field.insert(0, value)
        entry_field.bind('<FocusIn>', lambda e: e.widget.selection_range(0, END))
        entry_field.bind("<FocusOut>", lambda _, slot=slot: update_timeslot_from_table(slot, table_frame))
        if key == 'Color':
            entry_field.bind('<FocusIn>', partial(pick_color, entry=entry_field))


def create_sum_window(root):
    sum_window = tk.Toplevel(root)
    sum_window.title("Summary")
    sum_window.bind("<Escape>", lambda _: root.destroy())
    sum_window.protocol('WM_DELETE_WINDOW', lambda: root.destroy())

    table = tk.Text(sum_window, width=40, height=20)
    table.pack(fill="both", expand=True)
    return table


def update_summary(sum_table, slot_grid):
    VERT = ['Proj', 'Self']
    HOR = ['Plan', 'Buff', 'Beig', 'Meet']

    for i, name in enumerate(VERT):
        label = tk.Label(sum_table, text=name, name=f'vert_label_{name}')
        label.grid(row=i+(N_HEADER_ROWS := 1)+(N_SUM_ROWS := 1), column=0, padx=5, pady=5)
    label = tk.Label(sum_table, text='Sum', name=f'vert_label_Sum')
    label.grid(row=N_HEADER_ROWS, column=0, padx=5, pady=5)
    
    for i, name in enumerate(HOR):
        label = tk.Label(sum_table, text=name, name=f'hor_label_{name}')
        label.grid(row=0, column=i+(N_HEADER_COLS := 1)+(N_SUM_COLS := 1), padx=5, pady=5)
    label = tk.Label(sum_table, text='Sum', name=f'hor_label_Sum')
    label.grid(row=0, column=N_HEADER_COLS, padx=5, pady=5)

    sums = {k: 0 for k in VERT + HOR}
    for slot_row in slot_grid:
        for slot in slot_row:
            for k in sums:
                sums[k] += getattr(slot, k)

    for i, name in enumerate(VERT):
        label = tk.Label(sum_table, text=f'{sums[name]:.2f}', name=f'sum_label_{name}')
        label.grid(row=i+N_HEADER_ROWS+N_SUM_ROWS, column=N_HEADER_COLS, padx=5, pady=5)
    
    for i, name in enumerate(HOR):
        label = tk.Label(sum_table, text=f'{sums[name]:.2f}', name=f'sum_label_{name}')
        label.grid(row=N_HEADER_ROWS, column=i+N_HEADER_COLS+N_SUM_COLS, padx=5, pady=5)

    label = tk.Label(sum_table, text=f'{sum((sums[k] for k in VERT)):.2f}', name=f'vert_sum')
    label.grid(row=len(VERT)+N_HEADER_ROWS+N_SUM_ROWS, column=N_HEADER_COLS, padx=5, pady=5)
    label = tk.Label(sum_table, text=f'{sum((sums[k] for k in HOR)):.2f}', name=f'hor_sum')
    label.grid(row=N_HEADER_ROWS, column=len(HOR)+N_HEADER_COLS+N_SUM_COLS, padx=5, pady=5)

    sums_on_projects = {k: None for k in HOR}
    for plan_cat in HOR:
        sums_on_projects[plan_cat] = {k: 0 for k in VERT}
        for slot_row in slot_grid:
            for slot in slot_row:
                amount = getattr(slot, plan_cat)
                slot_sum_on_projects = sum((getattr(slot, proj) for proj in VERT))
                if slot_sum_on_projects == 0: continue
                for proj in VERT:
                    amount_on_proj = getattr(slot, proj)
                    sums_on_projects[plan_cat][proj] += amount / slot_sum_on_projects * amount_on_proj
    
    for i, proj in enumerate(VERT):
        for j, plan_cat in enumerate(HOR):
            label = tk.Label(sum_table, text=f'{sums_on_projects[plan_cat][proj]:.2f}', name=f'sum_label_{proj}{plan_cat}')
            label.grid(row=N_HEADER_ROWS+N_SUM_ROWS+i, column=N_HEADER_COLS+N_SUM_COLS+j, padx=5, pady=5)


root = tk.Tk()
root.title("Week Schedule")
root.bind("<Escape>", lambda _: root.destroy())

table = create_table_window(root)
sum_table = create_sum_window(root)

# Create the header row for days
for col, day in enumerate(DAYS):
    label = tk.Label(root, text=day, borderwidth=1, relief="solid")
    label.grid(row=COL_DAYHEADER_ROW, column=col+N_ROW_HEADERS, sticky="nsew")

    label_frame = tk.Frame(root, borderwidth=1, relief="solid", name=f'colheadframe_c{col}')
    label_frame.grid(row=COL_CATHEADER_ROW, column=col+N_ROW_HEADERS, sticky="nsew")

    for i, cat in enumerate(['Edit'] + INPUT_CATEGORIES):
        label = tk.Label(label_frame, text=cat, borderwidth=1, relief="solid", name=f'colheadlabel_c{col}_i{i}')
        label.pack(side='left', fill="both", expand=True)

# Create the header column for hours
for row, hour in enumerate(HOURS):
    label = tk.Label(root, text=hour, borderwidth=1, relief="solid")
    label.grid(row=row*ROWS_PER_HOUR+N_COL_HEADERS, column=ROW_HOURHEADER_COL, rowspan=ROWS_PER_HOUR, sticky="nsew")

focus_grid = [[None for _ in range(INPUT_COLS_TOTAL)] for _ in range(INPUT_ROWS_TOTAL)]
slot_grid : list[list[Timeslot]] = [[Timeslot() for _ in range(len(DAYS))] for _ in range(INPUT_ROWS_TOTAL)]
if SAVE_FILE.exists():
    slotdata_grid : list[list[Timeslot_Data]] = [[None for _ in range(len(DAYS))] for _ in range(INPUT_ROWS_TOTAL)]
    with open(SAVE_FILE, 'rb') as f:
        slotdata_grid = pickle.load(f)
    for slot_row, data_row in zip(slot_grid, slotdata_grid):
        for slot, data in zip(slot_row, data_row):
            # print(f'{row=} {col=} {str(data)=}')
            slot.data = data

update_summary(sum_table, slot_grid)

# if DEBUG :
#     for irow, row in enumerate(slot_grid):
#         for icol, slot in enumerate(row):
#             slot.irow = irow
#             slot.icol = icol

def button_pick_color(*, slot: Timeslot):
    _, color = askcolor()
    slot.bg = color

def entry_change(_, *, slot: Timeslot, cat: str, entry: tk.Entry):
    # print(f'{slot.irow=} {slot.icol=} {cat=} {entry=} {entry.get()=}')
    val = entry.get()
    if ',' in val:
        val = val.replace(',', '.')
    try:
        val = float(val)
    except ValueError:
        val = 0.
    setattr(slot, cat, val)

# Create the grid cells for time slots
for col in range(len(DAYS)):
    for row in range(INPUT_ROWS_TOTAL):
        slot = slot_grid[row][col]

        cell_frame = tk.Frame(root, borderwidth=1, relief="solid", name=f'frame_r{row}_c{col}')
        cell_frame.grid(row=row+N_COL_HEADERS, column=col+N_ROW_HEADERS, sticky="nsew")
        
        # # Variables to store descriptions and times for each category
        # descriptions = [tk.StringVar() for _ in categories]
        # times = [tk.StringVar() for _ in categories]
        
        # Add a button to edit details
        edit_button = tk.Button(cell_frame, text="Edit", command=partial(button_pick_color, slot=slot), name=f'btn_r{row}_c{col}')
        edit_button.pack(side='left', fill="both", expand=True)
        focus_grid[row][col * COLS_PER_DAY] = edit_button
        slot.add_gui_child(edit_button)

        # Add six small text fields
        text_fields = []
        for i, cat in enumerate(INPUT_CATEGORIES):
            entry = tk.Entry(cell_frame, width=5, name=f'entry_r{row}_c{col}_i{i}')
            # print(f'{row=} {col=} {i=} {entry=}')
            entry.pack(side="left", fill="both", expand=True)
            text_fields.append(entry)
            focus_grid[row][col * COLS_PER_DAY + BUTTONS_PER_SLOT + i] = entry
            slot.add_gui_child(entry, attr_name=cat)

            entry.bind("<FocusOut>", partial(entry_change, slot=slot, cat=cat, entry=entry))
            entry.bind('<FocusOut>', lambda e, slot=slot: e.widget.config(bg=slot.bg), add='+')
            entry.bind("<FocusIn>", lambda _, entry=entry, slot=slot: update_table(entry, table, slot))
            entry.bind('<FocusIn>', lambda e: e.widget.selection_range(0, END), add='+')
            entry.bind('<FocusIn>', lambda e: e.widget.config(bg='grey'), add='+')

        # Set tab order
        edit_button.bind("<Tab>", lambda _, entries=text_fields: entries[0].focus_set())
        for i in range(len(INPUT_CATEGORIES)-1):
            text_fields[i].bind("<Tab>", lambda _, next_entry=text_fields[i+1]: next_entry.focus_set())

# Configure grid weights to make cells expandable
for i in range(1, len(DAYS) + 1):
    root.columnconfigure(i, weight=1)
for i in range(1, INPUT_ROWS_TOTAL + 1):
    root.rowconfigure(i, weight=1)

for row in range(INPUT_ROWS_TOTAL):
    for col in range(len(DAYS)):
        for i in range(COLS_PER_DAY):
            c = col * COLS_PER_DAY + i
            # print(f'{row=} {col=} {i=} {focus_grid[row][c]=}')
            if row > 0:
                focus_grid[row][c].bind('<Up>', lambda _, row=row, col=c: focus_grid[row-1][col].focus_set()) 
            if row < INPUT_ROWS_TOTAL - 1:
                focus_grid[row][c].bind('<Down>', lambda _, row=row, col=c: focus_grid[row+1][col].focus_set()) 
            if c > 0:
                focus_grid[row][c].bind('<Left>', lambda _, row=row, col=c: focus_grid[row][col-1].focus_set()) 
            if c < INPUT_COLS_TOTAL - 1:
                focus_grid[row][c].bind('<Right>', lambda _, row=row, col=c: focus_grid[row][col+1].focus_set())

for row in range(INPUT_ROWS_TOTAL):
    for col in range(len(DAYS)):
        slot_grid[row][col].update_gui_childs()

root.mainloop()

slotdata_grid : list[list[Timeslot_Data]] = [[None for _ in range(len(DAYS))] for _ in range(INPUT_ROWS_TOTAL)]
for slot_row, (row, data_row) in zip(slot_grid, enumerate(slotdata_grid)):
    for slot, (i, _) in zip(slot_row, enumerate(data_row)):
        data_row[i] = slot.data
        # print(f'{row=} {i=} {str(data_row[i])=}')
with open(SAVE_FILE, 'wb') as f:
    pickle.dump(slotdata_grid, f)
