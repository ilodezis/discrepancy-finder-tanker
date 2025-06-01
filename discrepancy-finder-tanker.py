import sys
import os
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFileDialog,
    QAction, QToolBar, QStatusBar, QTableView, QTabWidget, QMessageBox,
    QHeaderView, QTextEdit, QLabel, QProgressDialog, QStyleFactory,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QIcon, QPalette, QColor, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QSize, QAbstractTableModel, QModelIndex
import logging
import csv

# Logger
LOG_PATH = Path.home() / "fuel_discrepancy_finder.log"
logging.basicConfig(
    filename=str(LOG_PATH), level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='a'
)

# Base directory
BASE_DIR = Path(__file__).parent.resolve()

# Translations (only Russian)
T = {
    'window_title': 'Поиск расхождений: Заправки',
    'open_registry': 'Открыть реестр',
    'open_act': 'Открыть акт (.csv)',
    'compare': 'Сравнить',
    'save': 'Сохранить',
    'clear': 'Очистить',
    'exit': 'Выход',
    'menu_file': 'Файл',
    'tab_results': 'Результаты',
    'tab_logs': 'Логи',
    'registry_label': 'Реестр: --',
    'act_label': 'Акт: --',
    'sum_registry': 'Сумма реестра: 0.00',
    'sum_act': 'Сумма акта: 0.00',
    'warn_load': 'Загрузите оба файла перед сравнением.',
    'err_id_reg': 'Столбец "Идентификатор заказа" не найден в реестре. Доступные: {}',
    'err_amount_reg': 'Столбец "Стоимость" не найден в реестре. Доступные: {}',
    'err_id_act': 'Столбец "Заказ" не найден в акте. Доступные: {}',
    'err Missing_act': 'Столбец "Приход (Клиент)" не найден в акте. Доступные: {}',
    'err_load': 'Не удалось загрузить {}: {}',
    'no_diff': 'Расхождений не найдено.',
    'diff_found': 'Найдено {} расхождений.',
    'dlg_compare': 'Сравнение...',
    'save_dialog': 'Сохранить результаты',
    'msg_saved': 'Результаты сохранены:\n{}',
    'reminder': '<b>Напоминание:</b> Убедитесь, что файлы загружены в правильном формате и содержат необходимые столбцы.'
}

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df
    def rowCount(self, parent=QModelIndex()): return len(self._df)
    def columnCount(self, parent=QModelIndex()): return len(self._df.columns)
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            return str(self._df.iat[index.row(), index.column()])
        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return None

class LogHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.append(msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tr = T
        self.setWindowTitle(self.tr['window_title'])
        self.setWindowIcon(QIcon(resource_path('assets/icons/ya_zapravki.ico')))
        self.resize(900, 600)
        self.registry_path = None
        self.act_path = None
        self.diffs = pd.DataFrame()
        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        # Reminder banner
        self.reminder = QLabel(self.tr['reminder'], self)
        self.reminder.setTextFormat(Qt.RichText)
        self.reminder.setStyleSheet(
            'padding:8px; background:#fff3cd; border:1px solid #ffeeba; border-radius:6px;'
        )
        # Tab widget
        self.table = QTableView()
        self.log = QTextEdit(); self.log.setReadOnly(True)
        tabs = QTabWidget()
        tabs.addTab(self.table, self.tr['tab_results'])
        tabs.addTab(self.log, self.tr['tab_logs'])
        # Layout
        c = QWidget(); vbox = QVBoxLayout(c)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)
        vbox.addWidget(self.reminder)
        vbox.addWidget(tabs)
        self.setCentralWidget(c)
        # Toolbar, menu, status
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        # Shadow for central widget
        shadow = QGraphicsDropShadowEffect(self.centralWidget())
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.centralWidget().setGraphicsEffect(shadow)

    def _create_actions(self):
        ic = QIcon.fromTheme
        self.a_open_reg = QAction(ic('document-open'), self.tr['open_registry'], self)
        self.a_open_reg.triggered.connect(lambda: self._load('reg'))
        self.a_open_act = QAction(ic('document-open'), self.tr['open_act'], self)
        self.a_open_act.triggered.connect(lambda: self._load('act'))
        self.a_compare = QAction(ic('view-refresh'), self.tr['compare'], self)
        self.a_compare.setEnabled(False); self.a_compare.triggered.connect(self._compare)
        self.a_save = QAction(ic('document-save'), self.tr['save'], self)
        self.a_save.setEnabled(False); self.a_save.triggered.connect(self._save)
        self.a_clear = QAction(ic('edit-clear'), self.tr['clear'], self)
        self.a_clear.triggered.connect(self._clear)
        self.a_exit = QAction(self.tr['exit'], self)
        self.a_exit.triggered.connect(self.close)

    def _create_menu(self):
        m = self.menuBar().addMenu(self.tr['menu_file'])
        for a in [self.a_open_reg, self.a_open_act, None, self.a_compare, self.a_save, None, self.a_clear, None, self.a_exit]:
            m.addAction(a) if a else m.addSeparator()

    def _create_toolbar(self):
        tb = QToolBar(); tb.setIconSize(QSize(24, 24)); self.addToolBar(tb)
        for a in [self.a_open_reg, self.a_open_act, None, self.a_compare, self.a_save, None, self.a_clear, self.a_exit]:
            tb.addAction(a) if a else tb.addSeparator()
        tb.setStyleSheet(
            'QToolBar{background:#ececec; spacing:6px; border-radius:6px;}'
        )

    def _create_statusbar(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        self.l_reg = QLabel(self.tr['registry_label']); sb.addPermanentWidget(self.l_reg)
        self.l_act = QLabel(self.tr['act_label']); sb.addPermanentWidget(self.l_act)
        self.l_sum_reg = QLabel(self.tr['sum_registry']); sb.addPermanentWidget(self.l_sum_reg)
        self.l_sum_act = QLabel(self.tr['sum_act']); sb.addPermanentWidget(self.l_sum_act)
        for lbl in (self.l_reg, self.l_act, self.l_sum_reg, self.l_sum_act):
            lbl.setStyleSheet(
                'padding:4px; border:1px solid #888; background:#eef; border-radius:4px;'
            )

    def _normalize(self, x):
        """Normalize numeric values from different formats"""
        if pd.isna(x):
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        # Convert string to number
        s = str(x).strip().replace(' ', '')
        if not s:
            return 0.0
        # Handle different decimal separators
        if ',' in s and '.' in s:
            s = s.replace('.', '') if s.rfind('.') < s.rfind(',') else s.replace(',', '')
        s = s.replace(',', '.')
        try:
            return round(float(s), 2)
        except (ValueError, TypeError):
            logging.warning(f"Failed to convert value: {x}")
            return 0.0

    def _load(self, mode):
        """Load and preprocess data files"""
        if mode == 'reg':
            path, _ = QFileDialog.getOpenFileName(self, 'Открыть реестр', '', 'Excel files (*.xlsx *.xls)')
            if not path: return
            try:
                # Try both header rows for Excel
                df = None
                for header in [0, 6]:
                    try:
                        df = pd.read_excel(path, header=header)
                        # Ищем столбцы по возможным названиям
                        id_variants = ['Идентификатор заказа', 'ИД заказа', 'ID заказа', 'Номер заказа']
                        amount_variants = ['Стоимость', 'Сумма', 'Стоимость заказа', 'Сумма заказа']
                        
                        id_col = next((col for col in id_variants if col in df.columns), None)
                        amount_col = next((col for col in amount_variants if col in df.columns), None)
                        
                        if id_col and amount_col:
                            logging.info(f"Найдены столбцы: {id_col}, {amount_col}")
                            break
                    except Exception as e:
                        logging.warning(f"Не удалось прочитать заголовки в строке {header}: {e}")
                
                if df is None or not (id_col and amount_col):
                    available_cols = ', '.join(df.columns) if df is not None else 'нет данных'
                    raise ValueError(f"Не найдены нужные столбцы. Доступные столбцы: {available_cols}")
                
                # Process registry data
                df = df[[id_col, amount_col]].copy()
                df = df.loc[df[id_col].notna()]
                df[id_col] = df[id_col].astype(str).str.strip().str.lower()
                df[amount_col] = df[amount_col].apply(self._normalize)
                total = df[amount_col].sum()
                
                # Переименовываем столбцы к стандартным названиям
                df.columns = ['Идентификатор заказа', 'Стоимость']
                
                self.registry_data = df
                self.registry_path = path
                self.l_reg.setText(f"Реестр: {Path(path).name}")
                self.l_sum_reg.setText(f"Сумма реестра: {total:,.2f}")
                logging.info(f"Реестр загружен: {len(df)} строк, сумма={total:,.2f}")
                
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f"Ошибка загрузки реестра: {str(e)}")
                logging.error(f"Ошибка загрузки реестра: {e}")
                return

        else:  # mode == 'act'
            path, _ = QFileDialog.getOpenFileName(self, 'Открыть акт', '', 'CSV files (*.csv)')
            if not path: return
            try:
                # Read CSV with auto-detected delimiter
                with open(path, 'r', encoding='utf-8') as f:
                    dialect = csv.Sniffer().sniff(f.readline())
                    df = pd.read_csv(path, delimiter=dialect.delimiter)
                
                if 'Заказ' not in df.columns:
                    raise ValueError("Не найден столбец 'Заказ'")
                if 'Приход (Клиент)' not in df.columns:
                    raise ValueError("Не найден столбец 'Приход (Клиент)'")
                if 'Расход (Клиент)' not in df.columns:
                    raise ValueError("Не найден столбец 'Расход (Клиент)'")
                
                # Process act data
                df = df[['Заказ', 'Приход (Клиент)', 'Расход (Клиент)']].copy()
                df = df.loc[df['Заказ'].notna()]
                df['Заказ'] = df['Заказ'].astype(str).str.strip().str.lower()
                df['Приход (Клиент)'] = df['Приход (Клиент)'].apply(self._normalize)
                df['Расход (Клиент)'] = df['Расход (Клиент)'].apply(self._normalize)
                
                # Calculate net amount for each row
                df['Сумма'] = df['Приход (Клиент)'] - df['Расход (Клиент)']
                # Calculate total net amount
                total_income = df['Приход (Клиент)'].sum()
                total_expense = df['Расход (Клиент)'].sum()
                total = total_income - total_expense
                
                self.act_data = df
                self.act_path = path
                self.l_act.setText(f"Акт: {Path(path).name}")
                # Update status bar with net amount
                self.l_sum_act.setText(f"Сумма акта (приход - расход): {total:,.2f}")
                logging.info(f"Act loaded: {len(df)} rows, net total={total:,.2f} (income={total_income:,.2f}, expense={total_expense:,.2f})")
                
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f"Ошибка загрузки акта: {str(e)}")
                logging.error(f"Act load error: {e}")
                return
                
        self.a_compare.setEnabled(bool(self.registry_path and self.act_path))

    def _update_buttons(self):
        self.a_compare.setEnabled(bool(self.registry_path and self.act_path))

    def _compare(self):
        """Compare registry and act data"""
        if self.registry_data is None or self.act_data is None:
            QMessageBox.warning(self, 'Предупреждение', self.tr['warn_load'])
            return

        try:
            # Use already loaded and preprocessed data
            reg_df = pd.DataFrame({
                'ID': self.registry_data['Идентификатор заказа'],
                'Registry': self.registry_data['Стоимость']
            })
            
            # Group act data by order ID and sum the amounts
            act_grouped = self.act_data.groupby('Заказ')['Сумма'].sum().reset_index()
            act_grouped.columns = ['ID', 'Act']
            
            # Debug log
            logging.info(f"Registry rows: {len(reg_df)}, Unique orders in act: {len(act_grouped)}")
            
            # Merge and compare
            merged = pd.merge(reg_df, act_grouped, on='ID', how='outer').fillna(0)
            merged['Registry'] = merged['Registry'].round(2)
            merged['Act'] = merged['Act'].round(2)
            merged['Diff'] = (merged['Registry'] - merged['Act']).round(2)
            
            # Find differences
            diffs = merged.loc[merged['Diff'].abs() > 0.01]
            
            if diffs.empty:
                self.table.setModel(PandasModel())
                self.a_save.setEnabled(False)
                QMessageBox.information(self, 'Информация', self.tr['no_diff'])
                return
                
            # Format numbers
            for col in ['Registry', 'Act', 'Diff']:
                diffs[col] = diffs[col].map(lambda x: f"{x:,.2f}")
                
            self.diffs = diffs
            self.table.setModel(PandasModel(self.diffs))
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.a_save.setEnabled(True)
            
            QMessageBox.information(self, 'Информация', self.tr['diff_found'].format(len(diffs)))
            logging.info(f"Found {len(diffs)} discrepancies")
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f"Ошибка при сравнении: {str(e)}")
            logging.error(f"Compare error: {e}")
            return

    def _clear(self):
        self.registry_path = None
        self.act_path = None
        self.diffs = pd.DataFrame()
        self.table.setModel(PandasModel(self.diffs))
        self.log.clear()
        self.l_reg.setText(self.tr['registry_label'])
        self.l_act.setText(self.tr['act_label'])
        self.l_sum_reg.setText(self.tr['sum_registry'])
        self.l_sum_act.setText(self.tr['sum_act'])
        self.a_compare.setEnabled(False)
        self.a_save.setEnabled(False)
        logging.info("Данные очищены")

    def _save(self):
        if self.diffs.empty:
            return
        default = Path.home() / 'Downloads' / 'расхождения.txt'
        fn, _ = QFileDialog.getSaveFileName(self, self.tr['save_dialog'], str(default), 'Text Files (*.txt)')
        if not fn:
            return
        with open(fn, 'w', encoding='utf-8') as f:
            f.write('ID\tРеестр\tАкт\tРазница\n')
            for _, row in self.diffs.iterrows():
                f.write(f"{row['ID']}\t{row['Registry']}\t{row['Act']}\t{row['Diff']}\n")
        QMessageBox.information(self, self.tr['save_dialog'], self.tr['msg_saved'].format(fn))
        logging.info(f"Сохранено в {fn}")

    def _setup_logging(self):
        log_handler = LogHandler(self.log)
        log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', BASE_DIR)
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Загрузка иконки
    icon_path = resource_path('assets/icons/ya_zapravki.ico')
    app.setWindowIcon(QIcon(icon_path))
    
    # Загрузка шрифта Inter
    font_path = resource_path('assets/fonts/Inter-VariableFont_opsz,wght.ttf')
    QFontDatabase.addApplicationFont(font_path)
    app.setFont(QFont('Inter', 10))
    
    # Глобальная таблица стилей
    app.setStyleSheet("""
        QWidget { font-family: 'Inter'; }
        QPushButton, QLineEdit, QComboBox {
            border: 1px solid #CCCCCC; border-radius: 6px; padding: 4px 8px; background-color: #FFFFFF;
        }
        QPushButton:hover { background-color: #F5F5F5; }
        QPushButton:pressed { background-color: #E6E6E6; }
        QTableWidget, QTableView {
            border: 1px solid #CCCCCC; border-radius: 6px; gridline-color: #E0E0E0;
        }
        QToolBar { background: #ECECEC; spacing: 6px; border-radius: 6px; }
        QMainWindow { background-color: #F0F0F0; }
        QGroupBox { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 8px; padding: 8px; margin-top: 20px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; margin-left: 10px; background-color: transparent; }
    """)
    # Палитра акцентов
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(240, 240, 240))
    pal.setColor(QPalette.Highlight, QColor(255, 0, 0))
    app.setPalette(pal)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())