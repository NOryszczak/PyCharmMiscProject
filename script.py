import sys
import os
import csv
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        self.initUI()

    def initUI(self):
        self.setWindowTitle("CSV Converter")
        self.resize(400, 300)
        self.setAcceptDrops(True)

        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setScaledContents(True)
        if os.path.exists(self.logo_path):
            pixmap = QPixmap(self.logo_path)
            self.bg_label.setPixmap(pixmap)
        else:
            self.bg_label.setStyleSheet("background-color: #333;")

        label_height = 30
        label_y = 20
        padding = 10
        self.label = QLabel("Przeciągnij tutaj plik CSV", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "color: white; background: rgba(0,0,0,0.5);"
            " font-size: 16px;"
            " border: 2px solid white;"
            " border-radius: 5px;"
        )
        self.label.setGeometry(
            padding,
            label_y,
            self.width() - 2 * padding,
            label_height
        )

    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        padding = 10
        self.label.setGeometry(
            padding,
            20,
            self.width() - 2 * padding,
            30
        )
        super().resizeEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.csv'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath.lower().endswith('.csv'):
                try:
                    out_file = self.process_file(filepath)
                    QMessageBox.information(
                        self,
                        "Sukces",
                        f"Plik zapisany jako {os.path.basename(out_file)} w folderze {os.path.dirname(out_file)}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Błąd",
                        f"Wystąpił błąd podczas przetwarzania:\n{str(e)}"
                    )
                break

    def process_file(self, input_file):
        input_name = os.path.splitext(os.path.basename(input_file))[0]
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        base = f"{input_name}_{timestamp}.csv"
        output_file = os.path.join(os.path.dirname(input_file), base)

        with open(input_file, mode="r", encoding="utf-8", newline="") as infile, \
             open(output_file, mode="w", encoding="utf-8", newline="") as outfile:

            reader = csv.reader(infile)
            header = next(reader)
            idx_map = {name: i for i, name in enumerate(header)}

            all_headers = ["LP"] + header
            quoted_headers = ['"' + h + '"' for h in all_headers]
            outfile.write("|".join(quoted_headers) + "\n")

            quote_cols = [idx_map[col] for col in ["PUP_NIP", "PUP_NAZWA", "AKT_SYM", "AKT_DATA", "BF_NAZWA"] if col in idx_map]
            nom_idx = idx_map.get("KWOTA_NOM")
            brut_idx = idx_map.get("KWOTA_BRUT")
            date_idxs = [idx_map[col] for col in ["AKT_DATA", "PP_DATA"] if col in idx_map]

            for lp, row in enumerate(reader, start=1):
                for di in date_idxs:
                    if di < len(row):
                        row[di] = row[di].replace('-', '.')

                for num_idx in (nom_idx, brut_idx):
                    if num_idx is not None and num_idx < len(row):
                        value = row[num_idx].replace(' ', '')
                        if ',' not in value:
                            value += ',00'
                        row[num_idx] = value

                for i in quote_cols:
                    if i < len(row):
                        row[i] = '"' + row[i] + '"'

                output_fields = [str(lp)] + row
                outfile.write("|".join(output_fields) + "\n")

        return output_file

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = DragDropWidget()
    w.show()
    sys.exit(app.exec())
