import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QHeaderView, QLabel, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QCursor
from concurrent.futures import ThreadPoolExecutor

REMOTE_INDEX_URL = "https://turbo.scoredata.me/manako/index.json"
LOCAL_INDEX_FILE = "index.json"
DEFAULT_DETECT_ID = "Detect-crime"

COL_NO = 0
COL_HOTKEY = 1
COL_BLOCK_START = 2
COL_BLOCK_END = 31
COL_AVG_SCORE = 32
TOTAL_COLS = 33

COPY_ICON_PATH = "/mnt/data/fd6014fe-376f-40de-a4c1-2688240459ca.png"

def get_nested(d, keys, default=0.0):
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    try:
        return float(d)
    except:
        return default

class FetchWorker(QThread):
    update_cell = pyqtSignal(int, int, object)
    progress_update = pyqtSignal(int)

    def __init__(self, block_cells_to_fetch):
        super().__init__()
        self.block_cells_to_fetch = block_cells_to_fetch
        self.running = True

    def run(self):
        total = len(self.block_cells_to_fetch)
        for idx, (row, col, eval_url) in enumerate(self.block_cells_to_fetch, start=1):
            if not self.running:
                break
            composite_score = 0.0
            responses_url = eval_url.replace("/evaluation/", "/responses/")
            img_url = ""
            try:
                resp = requests.get(eval_url, timeout=5).json()
                if isinstance(resp, list) and len(resp) > 0:
                    payload = resp[0].get("payload", {})
                    composite_score = round(get_nested(payload, ["metrics", "composite_score"], 0.0), 3)
                try:
                    resp2 = requests.get(responses_url, timeout=5).json()
                    img_url = resp2.get("frames", [{}])[0].get("url", "")
                except:
                    pass
            except:
                pass
            self.update_cell.emit(row, col, [composite_score, eval_url, responses_url, img_url])
            self.progress_update.emit(int(idx / total * 100))

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class MinerScoreApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Score Board")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        # --- Top bar ---
        self.top_bar = QWidget()
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(0,0,0,0)
        self.detect_input = QLineEdit()
        self.detect_input.setPlaceholderText("Enter Detect ID")
        self.fetch_btn = QPushButton("Fetch Data")
        top_layout.addStretch()
        top_layout.addWidget(self.detect_input)
        top_layout.addWidget(self.fetch_btn)
        top_layout.addStretch()
        self.layout.addWidget(self.top_bar)

        # --- Progress bar ---
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0,0,0,0)
        progress_layout.addStretch()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        progress_layout.addWidget(self.progress_bar, stretch=8)
        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label, stretch=1)
        progress_layout.addStretch()
        self.progress_container.setLayout(progress_layout)
        self.layout.addWidget(self.progress_container)

        # --- Table ---
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.layout.addWidget(self.table)

        # --- Info panel ---
        self.info_container = QWidget()
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_container.setFixedHeight(200)
        self.layout.addWidget(self.info_container)
        self.info_labels = {}
        self.copy_buttons = {}
        fields = ["Composite Score", "Evaluation URL", "Responses URL", "Image URL"]
        self.copy_icon = QIcon(COPY_ICON_PATH)
        copy_size = 12
        for field in fields:
            hbox = QHBoxLayout()
            label_title = QLabel(f"{field}: ")
            label_title.setFixedWidth(120)
            label = QLabel("")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            btn_copy = QPushButton()
            btn_copy.setIcon(self.copy_icon)
            btn_copy.setFixedSize(copy_size, copy_size)
            btn_copy.setStyleSheet("border: 1px solid black;")
            btn_copy.clicked.connect(lambda checked, l=label: self.copy_with_notify(l.text()))
            hbox.addWidget(label_title)
            hbox.addWidget(label)
            hbox.addWidget(btn_copy)
            hbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            hbox.addStretch()
            self.info_layout.addLayout(hbox)
            self.info_labels[field] = label
            self.copy_buttons[field] = btn_copy

        # --- Executor ---
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.fetch_btn.clicked.connect(self.on_fetch_clicked)
        self.detect_input.returnPressed.connect(self.on_fetch_clicked)

        # --- Load index and fetch default ---
        self.load_index_json()
        self.current_detect_id = DEFAULT_DETECT_ID
        self.detect_input.setText(DEFAULT_DETECT_ID)
        self.fetch_detect_id(DEFAULT_DETECT_ID)

        # --- Show maximized at end ---
        self.showMaximized()
        QApplication.restoreOverrideCursor()

    # --- Copy helper ---
    def copy_with_notify(self, text):
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), "Copied", msecShowTime=800)

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
        self.executor.shutdown(wait=False)
        event.accept()

    def load_index_json(self):
        try:
            local_data = []
            if os.path.exists(LOCAL_INDEX_FILE):
                with open(LOCAL_INDEX_FILE, "r") as f:
                    local_data = json.load(f)
            remote_data = requests.get(REMOTE_INDEX_URL).json()
            merged = list(local_data)
            for uri in remote_data:
                if uri not in merged:
                    merged.append(uri)
            with open(LOCAL_INDEX_FILE, "w") as f:
                json.dump(merged, f)
            self.index_data = merged
        except:
            self.index_data = []

    def on_fetch_clicked(self):
        detect_id = self.detect_input.text().strip()
        if not detect_id:
            return
        if detect_id == self.current_detect_id:
            if hasattr(self, 'worker') and self.worker.isRunning():
                return
        else:
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.stop()
            self.current_detect_id = detect_id
        self.fetch_detect_id(detect_id)

    def fetch_detect_id(self, detect_id):
        filtered_uris = [uri for uri in self.index_data if detect_id in uri]
        if not filtered_uris:
            self.info_labels["Composite Score"].setText(f"No URIs found for Detect ID: {detect_id}")
            return

        hotkeys = {}
        for uri in filtered_uris:
            parts = uri.split("/")
            if len(parts) < 6:
                continue
            hotkey = parts[2]
            filename = parts[5].split("-")[0]
            try:
                block_num = int(filename)
            except:
                continue
            hotkeys.setdefault(hotkey, []).append((block_num, uri))

        hotkey_list = list(hotkeys.keys())
        biggest_block = max(max(b[0] for b in blocks) for blocks in hotkeys.values())
        block_numbers = [biggest_block - (29 - i) * 300 for i in range(30)]
        block_ids = list(range(1, 31))

        self.table.clear()
        self.table.setRowCount(len(hotkey_list) + 2)
        self.table.setColumnCount(TOTAL_COLS)

        # --- Table headers ---
        self.table.setSpan(0,0,2,1)
        item_no = QTableWidgetItem("No")
        item_no.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(0,0,item_no)

        self.table.setSpan(0,1,2,1)
        item_hotkey = QTableWidgetItem("Hotkey \\ Block")
        item_hotkey.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(0,1,item_hotkey)

        self.table.setSpan(0,32,2,1)
        item_score = QTableWidgetItem("Score")
        item_score.setForeground(QColor("red"))
        item_score.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(0,32,item_score)

        # Row0 block numbers
        for col_index, blk_num in enumerate(block_numbers, start=COL_BLOCK_START):
            label = QLabel(str(blk_num))
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setCellWidget(0, col_index, label)

        # Row1 block IDs + copy buttons
        for col_index, blk_id in enumerate(block_ids, start=COL_BLOCK_START):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2,2,2,2)
            label = QLabel(str(blk_id))
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            btn_copy = QPushButton()
            btn_copy.setIcon(self.copy_icon)
            btn_copy.setFixedSize(12,12)
            btn_copy.setStyleSheet("border:1px solid black;")
            btn_copy.clicked.connect(lambda checked, text=str(block_numbers[col_index-COL_BLOCK_START]): self.copy_with_notify(text))
            layout.addWidget(label)
            layout.addWidget(btn_copy)
            layout.setAlignment(btn_copy, Qt.AlignmentFlag.AlignHCenter)
            self.table.setCellWidget(1, col_index, container)

        # --- Hotkey rows ---
        self.block_cells = {}
        block_cells_to_fetch = []
        for row_index, hotkey in enumerate(hotkey_list, start=2):
            item_no = QTableWidgetItem(str(row_index-1))
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            item_no.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_index, COL_NO, item_no)

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(1,1,1,1)
            label = QLabel(hotkey)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            btn_copy = QPushButton()
            btn_copy.setIcon(self.copy_icon)
            btn_copy.setFixedSize(12,12)
            btn_copy.setStyleSheet("border:1px solid black;")
            btn_copy.clicked.connect(lambda checked, text=hotkey: self.copy_with_notify(text))
            layout.addWidget(label)
            layout.addWidget(btn_copy)
            layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.table.setCellWidget(row_index, COL_HOTKEY, container)

            for col_index, blk_num in enumerate(block_numbers, start=COL_BLOCK_START):
                uri_list = [u for b,u in hotkeys[hotkey] if b == blk_num]
                eval_url = f"https://turbo.scoredata.me/{uri_list[0]}" if uri_list else ""
                self.block_cells[(row_index, col_index)] = [0.0, eval_url, eval_url.replace("/evaluation/", "/responses/") if eval_url else "", ""]
                btn = QPushButton("0.000")
                btn.clicked.connect(lambda checked, r=row_index, c=col_index: self.cell_clicked(r,c))
                self.table.setCellWidget(row_index, col_index, btn)
                if eval_url:
                    block_cells_to_fetch.append((row_index, col_index, eval_url))

            self.table.setItem(row_index, COL_AVG_SCORE, QTableWidgetItem("0.000"))

        # Column widths
        self.table.setColumnWidth(COL_NO, 50)
        self.table.setColumnWidth(COL_HOTKEY, 200)
        for c in range(COL_BLOCK_START, TOTAL_COLS):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

        # Start worker
        self.worker = FetchWorker(block_cells_to_fetch)
        self.worker.update_cell.connect(self.update_cell_data)
        self.worker.progress_update.connect(lambda val: self.progress_bar.setValue(val) or self.progress_label.setText(f"{val}%"))
        self.worker.start()

    def update_cell_data(self, row, col, data):
        self.block_cells[(row, col)] = data
        btn = self.table.cellWidget(row, col)
        if btn:
            btn.setText(f"{data[0]:.3f}")

        # update average
        scores = [self.block_cells[(row, c)][0] for c in range(COL_BLOCK_START, COL_BLOCK_END+1)]
        avg_score = round(sum(scores)/len(scores),3) if scores else 0.0
        avg_item = QTableWidgetItem(f"{avg_score:.3f}")
        avg_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, COL_AVG_SCORE, avg_item)

        # update ranking colors
        all_scores = []
        for r in range(2, self.table.rowCount()):
            item = self.table.item(r, COL_AVG_SCORE)
            if item:
                try:
                    val = float(item.text()); all_scores.append((r,val))
                except: pass
        sorted_scores = sorted(all_scores, key=lambda x:x[1], reverse=True)
        rank_colors = {1:"red",2:"blue",3:"darkGreen"}
        for idx,(r,val) in enumerate(sorted_scores,start=1):
            item = self.table.item(r,COL_AVG_SCORE)
            if item:
                color = rank_colors.get(idx,"black")
                item.setForeground(QColor(color))
                item.setText(f"{val:.3f}  ")

    def cell_clicked(self,row,col):
        data = self.block_cells.get((row,col),[])
        if not data: return
        self.info_labels["Composite Score"].setText(f"{data[0]:.3f}")
        self.info_labels["Evaluation URL"].setText(data[1])
        self.info_labels["Responses URL"].setText(data[2])
        self.info_labels["Image URL"].setText(data[3] if data[3] else "No Image")

        # reset colors
        for r in range(2,self.table.rowCount()):
            hotkey_widget = self.table.cellWidget(r,COL_HOTKEY)
            if hotkey_widget: hotkey_widget.setStyleSheet("")
            for c2 in range(COL_BLOCK_START,COL_BLOCK_END+1):
                btn = self.table.cellWidget(r,c2)
                if btn: btn.setStyleSheet("background-color:white;")
        for col_index in range(COL_BLOCK_START,COL_BLOCK_END+1):
            widget = self.table.cellWidget(0,col_index)
            if widget: widget.setStyleSheet("")

        # highlight selected
        highlight_color="cyan"
        btn = self.table.cellWidget(row,col)
        if btn: btn.setStyleSheet(f"background-color:{highlight_color};")
        hotkey_widget = self.table.cellWidget(row,COL_HOTKEY)
        if hotkey_widget: hotkey_widget.setStyleSheet(f"background-color:{highlight_color};")
        block_widget = self.table.cellWidget(0,col)
        if block_widget: block_widget.setStyleSheet(f"background-color:{highlight_color};")

if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MinerScoreApp()
    sys.exit(app.exec())