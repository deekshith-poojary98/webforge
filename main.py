import sys
import os
import re
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPlainTextEdit, QPushButton, QFileDialog,
                            QMessageBox, QSplitter, QAction,
                            QToolBar, QDialog, QTextEdit, QLabel, QLineEdit, QMenu, QToolButton)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, QObject, pyqtSlot, QRect
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon, QPainter
from yaml_converter import yaml_to_html

class LineNumberWidget(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setStyleSheet("""
            QWidget {
                background-color: #21262d;
                color: #7d8590;
                border-right: 1px solid #30363d;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
            }
        """)
        
    def sizeHint(self):
        return QSize(self.line_number_width(), 0)
    
    def line_number_width(self):
        digits = 1
        max_num = max(1, self.editor.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor("#21262d"))
        
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#7d8590"))
                rect = QRect(0, int(top), self.width(), self.editor.fontMetrics().height())
                painter.drawText(rect, Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1

class YAMLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        structure_format = QTextCharFormat()
        structure_format.setForeground(QColor("#9d4edd"))
        structure_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'^(title|body):', structure_format))

        secondary_format = QTextCharFormat()
        secondary_format.setForeground(QColor("#ff9e00"))
        secondary_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((r'^\s*(text|style|children):', secondary_format))

        type_value_format = QTextCharFormat()
        type_value_format.setForeground(QColor("#2ecc71"))
        self.highlighting_rules.append((r'^\s*-\s*type:\s*([a-z]+)', type_value_format))

        css_property_format = QTextCharFormat()
        css_property_format.setForeground(QColor("#ff6b6b"))
        self.highlighting_rules.append((r'^\s*-\s*type:', css_property_format))
        self.highlighting_rules.append((r'^\s*(?!title|body|text|style|children)[a-z-]+(?=:)', css_property_format))

        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#a0a0a0"))
        self.highlighting_rules.append((r'"[^"]*"', value_format))
        self.highlighting_rules.append((r"'[^']*'", value_format))
        self.highlighting_rules.append((r'\b\d+\b', value_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6c7a89"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#.*$', comment_format))

        list_item_format = QTextCharFormat()
        list_item_format.setForeground(QColor("#bdc3c7"))
        self.highlighting_rules.append((r'^\s*-\s*', list_item_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

class YAMLEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabStopWidth(40)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = self.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.setFont(font)
        self.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QPlainTextEdit:focus {
                border: 1px solid #4dabf7;
            }
        """)
        
        self.highlighter = YAMLHighlighter(self.document())
        
        self.line_number_widget = LineNumberWidget(self)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_width(0)
        
        self.textChanged.connect(self.on_text_changed)
        
    def on_text_changed(self):
        if hasattr(self.parent(), 'on_editor_text_changed'):
            self.parent().on_editor_text_changed()
    
    def line_number_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_width(self, new_block_count):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_widget.scroll(0, dy)
        else:
            self.line_number_widget.update(0, rect.y(), self.line_number_widget.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_width(0)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_widget.setGeometry(cr.left(), cr.top(), self.line_number_width(), cr.height())
    
    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#21262d")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.wrap_selection_with_component("div")
            return
            
        elif event.key() == Qt.Key_S and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.wrap_selection_with_component("section")
            return
            
        elif event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.indent_selection()
                return
            else:
                cursor = self.textCursor()
            current_line = cursor.block().text()
            current_indent = len(current_line) - len(current_line.lstrip())
            
            cursor.insertText("  ")
            return
            
        elif event.key() == Qt.Key_Backtab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.unindent_selection()
                return
            else:
                self.unindent_current_line()
                return
            
        elif event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            current_line = cursor.block().text()
            current_indent = len(current_line) - len(current_line.lstrip())
            
            if current_line.rstrip().endswith(':'):
                super().keyPressEvent(event)
                cursor.insertText("  " * (current_indent // 2 + 1))
            else:
                super().keyPressEvent(event)
                cursor.insertText("  " * (current_indent // 2))
            return
            
        super().keyPressEvent(event)
    
    def wrap_selection_with_component(self, component_type):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            QMessageBox.information(self, "No Selection", 
                                  "Please select the YAML content you want to wrap first.")
            return
        
        selected_text = cursor.selectedText()
        lines = selected_text.split('\n')
        
        first_line_indent = len(lines[0]) - len(lines[0].lstrip())
        indent_str = " " * first_line_indent
        
        wrapper = f"{indent_str}- type: {component_type}\n"
        wrapper += f"{indent_str}  children:\n"
        
        for line in lines:
            if line.strip():
                wrapper += f"{indent_str}    {line.strip()}\n"
        
        cursor.insertText(wrapper)
    
    def indent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        
        start_block = self.document().findBlock(cursor.selectionStart())
        end_block = self.document().findBlock(cursor.selectionEnd())
        
        cursor.beginEditBlock()
        
        cursor.setPosition(start_block.position())
        
        current_block = start_block
        while current_block.isValid() and current_block.position() <= end_block.position():
            cursor.movePosition(cursor.StartOfLine)
            cursor.insertText("  ")
            current_block = current_block.next()
            cursor.movePosition(cursor.NextBlock)
        
        cursor.endEditBlock()
    
    def unindent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        
        start_block = self.document().findBlock(cursor.selectionStart())
        end_block = self.document().findBlock(cursor.selectionEnd())
        
        cursor.beginEditBlock()
        
        cursor.setPosition(start_block.position())
        
        current_block = start_block
        while current_block.isValid() and current_block.position() <= end_block.position():
            cursor.movePosition(cursor.StartOfLine)
            line_text = current_block.text()
            if line_text.startswith("  "):
                cursor.movePosition(cursor.Right, cursor.KeepAnchor, 2)
                cursor.removeSelectedText()
            current_block = current_block.next()
            cursor.movePosition(cursor.NextBlock)
        
        cursor.endEditBlock()
    
    def unindent_current_line(self):
        cursor = self.textCursor()
        cursor.movePosition(cursor.StartOfLine)
        line_text = cursor.block().text()
        if line_text.startswith("  "):
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, 2)
            cursor.removeSelectedText()

class HTMLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#4dabf7"))
        self.highlighting_rules.append((r'</?[!?]?[a-zA-Z][^>]*>', tag_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6c7a89"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'<!--.*-->', comment_format))

        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#ff9e00"))
        self.highlighting_rules.append((r'\b[a-zA-Z-]+(?==)', attr_format))

        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#2ecc71"))
        self.highlighting_rules.append((r'"[^"]*"', value_format))
        self.highlighting_rules.append((r"'[^']*'", value_format))

        css_format = QTextCharFormat()
        css_format.setForeground(QColor("#9d4edd"))
        self.highlighting_rules.append((r'[a-zA-Z-]+(?=:)', css_format))

        css_value_format = QTextCharFormat()
        css_value_format.setForeground(QColor("#4dabf7"))
        self.highlighting_rules.append((r':\s*[^;]+', css_value_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

class YAMLPreviewApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebForge")
        self.setMinimumSize(1200, 800)
        self.current_file = None
        self.modified = False
        self.initial_content = ""
        
        self.setup_icons()
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
                color: #f0f6fc;
            }
            QWidget {
                background-color: #0d1117;
                color: #f0f6fc;
            }
            QPlainTextEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
            }
            QPlainTextEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #1c2128;
            }
            QWebEngineView {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QMenuBar {
                background-color: #161b22;
                color: #f0f6fc;
            }
            QMenuBar::item:selected {
                background-color: #21262d;
            }
            QMenu {
                background-color: #161b22;
                color: #f0f6fc;
            }
            QMenu::item:selected {
                background-color: #21262d;
            }
            QToolBar {
                background-color: #161b22;
                border: none;
                spacing: 5px;
            }
            QToolButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
                color: #f0f6fc;
                font-weight: 600;
            }
            QToolButton:hover {
                background-color: #30363d;
                border-color: #4dabf7;
            }
            QToolButton:pressed {
                background-color: #21262d;
            }
            QStatusBar {
                background-color: #161b22;
                color: #f0f6fc;
                border-top: 1px solid #30363d;
            }
            QSplitter::handle {
                background-color: #30363d;
            }
            QScrollBar:vertical {
                background-color: #161b22;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #30363d;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #161b22;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #30363d;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QDialog {
                background-color: #0d1117;
                color: #f0f6fc;
            }
            QTextEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
            }
            QLineEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #1c2128;
            }
            QPushButton {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #4dabf7;
            }
            QLabel {
                color: #f0f6fc;
            }
        """)

        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                color: #f0f6fc;
            }
        """)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.create_toolbar()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #30363d;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #4dabf7;
            }
        """)
        layout.addWidget(splitter)

        self.yaml_editor = YAMLEditor()
        self.yaml_editor.textChanged.connect(self.on_editor_text_changed)
        self.yaml_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.4;
            }
            QPlainTextEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #1c2128;
            }
        """)
        splitter.addWidget(self.yaml_editor)

        self.preview_area = QWebEngineView()
        self.preview_area.setMinimumWidth(400)
        self.preview_area.setStyleSheet("""
            QWebEngineView {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
        """)
        self.setup_javascript_bridge()
        splitter.addWidget(self.preview_area)

        splitter.setSizes([600, 600])

        self.statusBar().showMessage("Ready")

        self.yaml_editor.setPlainText("")
        self.initial_content = ""

    def setup_icons(self):
        try:
            possible_ico_paths = [
                os.path.join(os.getcwd(), 'logo.ico'),
                os.path.join(os.path.dirname(__file__), 'logo.ico'),
                os.path.join(os.getcwd(), 'icons', 'logo.ico'),
                os.path.join(os.path.dirname(__file__), 'icons', 'logo.ico')
            ]
            
            ico_loaded = False
            for ico_path in possible_ico_paths:
                if os.path.exists(ico_path):
                    icon = QIcon(ico_path)
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        print(f"✅ Loaded window icon from: {ico_path}")
                        ico_loaded = True
                        break
                    else:
                        print(f"❌ Invalid ICO file at: {ico_path}")
            
            if not ico_loaded:
                print("⚠️ No valid ICO file found. Trying to create a simple icon...")
                self.create_fallback_icon()
            
            possible_png_paths = [
                os.path.join(os.getcwd(), 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'logo.png'),
                os.path.join(os.getcwd(), 'icons', 'logo.png'),
                os.path.join(os.path.dirname(__file__), 'icons', 'logo.png')
            ]
            
            self.logo_png_path = None
            for png_path in possible_png_paths:
                if os.path.exists(png_path):
                    self.logo_png_path = png_path
                    print(f"✅ PNG logo available at: {png_path}")
                    break
            
            if not self.logo_png_path:
                print("⚠️ No PNG logo file found")
                
        except Exception as e:
            print(f"❌ Error setting up icons: {e}")
            self.create_fallback_icon()

    def create_fallback_icon(self):
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
            
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#0d1117"))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            painter.setBrush(QColor("#4dabf7"))
            painter.setPen(QColor("#4dabf7"))
            painter.drawEllipse(2, 2, 28, 28)
            
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "WF")
            painter.end()
            
            icon = QIcon(pixmap)
            self.setWindowIcon(icon)
            print("✅ Created fallback icon")
            
        except Exception as e:
            print(f"❌ Error creating fallback icon: {e}")

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 8px;
                padding: 4px;
                background: transparent;
                border: none;
            }
            QToolButton {
                padding: 6px 12px;
                margin: 0px;
                border: none;
                background: transparent;
                color: #f0f6fc;
                font-size: 13px;
                font-weight: 600;
            }
            QToolButton:hover {
                color: #4dabf7;
                background: rgba(77, 171, 247, 0.15);
                border-radius: 6px;
            }
            QToolButton:pressed {
                color: #339af0;
                background: rgba(77, 171, 247, 0.25);
            }
            QToolButton::menu-indicator {
                image: none;
                width: 8px;
            }
            QToolBar::separator {
                width: 1px;
                background: #30363d;
                margin: 0px 8px;
            }
        """)
        self.addToolBar(toolbar)

        file_menu = QMenu()
        file_menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                color: #f0f6fc;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4dabf7;
                color: #ffffff;
            }
        """)
        
        new_action = QAction("New", self)
        new_action.setStatusTip("Create a new file")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setStatusTip("Open an existing file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setStatusTip("Save the current file")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export HTML", self)
        export_action.setStatusTip("Export to HTML file")
        export_action.triggered.connect(self.export_html)
        file_menu.addAction(export_action)
        
        file_btn = QToolButton()
        file_btn.setText("File")
        file_btn.setMenu(file_menu)
        file_btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(file_btn)

        preview_menu = QMenu()
        preview_menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                color: #f0f6fc;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4dabf7;
                color: #ffffff;
            }
        """)
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh the preview")
        refresh_action.triggered.connect(self.update_preview)
        preview_menu.addAction(refresh_action)
        
        browser_action = QAction("Open in Browser", self)
        browser_action.setStatusTip("Open preview in default browser")
        browser_action.triggered.connect(self.open_in_browser)
        preview_menu.addAction(browser_action)
        
        view_html_action = QAction("View HTML", self)
        view_html_action.setStatusTip("View the generated HTML code")
        view_html_action.triggered.connect(self.view_html)
        preview_menu.addAction(view_html_action)
        
        preview_btn = QToolButton()
        preview_btn.setText("Preview")
        preview_btn.setMenu(preview_menu)
        preview_btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(preview_btn)

        edit_menu = QMenu()
        edit_menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                color: #f0f6fc;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4dabf7;
                color: #ffffff;
            }
        """)
        
        search_action = QAction("Search", self)
        search_action.setStatusTip("Search in YAML (Ctrl+F)")
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.show_search_dialog)
        edit_menu.addAction(search_action)
        
        replace_action = QAction("Replace", self)
        replace_action.setStatusTip("Find and replace (Ctrl+H)")
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.show_replace_dialog)
        edit_menu.addAction(replace_action)
        
        edit_menu.addSeparator()
        
        goto_line_action = QAction("Go to Line", self)
        goto_line_action.setStatusTip("Go to specific line number (Ctrl+G)")
        goto_line_action.setShortcut("Ctrl+G")
        goto_line_action.triggered.connect(self.show_goto_line_dialog)
        edit_menu.addAction(goto_line_action)
        
        edit_btn = QToolButton()
        edit_btn.setText("Edit")
        edit_btn.setMenu(edit_menu)
        edit_btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(edit_btn)

        help_menu = QMenu()
        help_menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                color: #f0f6fc;
                padding: 10px 18px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #4dabf7;
                color: #ffffff;
            }
        """)
        
        docs_action = QAction("Documentation", self)
        docs_action.setStatusTip("View documentation")
        docs_action.triggered.connect(self.show_docs)
        help_menu.addAction(docs_action)
        
        help_btn = QToolButton()
        help_btn.setText("Help")
        help_btn.setMenu(help_menu)
        help_btn.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(help_btn)


    def on_editor_text_changed(self):
        current_content = self.yaml_editor.toPlainText()
        self.modified = (current_content != self.initial_content)
        self.preview_timer.start(500)

    def update_preview(self):
        try:
            yaml_text = self.yaml_editor.toPlainText()
            html_content, success = yaml_to_html(yaml_text)
            
            temp_html = os.path.join(os.getcwd(), 'temp_preview.html')
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.preview_area.load(QUrl.fromLocalFile(temp_html))
            
            if success:
                self.statusBar().showMessage("Preview updated successfully", 3000)
            else:
                self.statusBar().showMessage("Preview updated with errors", 3000)
                
        except Exception as e:
            error_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        .error-container {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            margin: 0;
            padding: 1.2em;
            background-color: #2d2d2d;
            border-top: 2px solid #404040;
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        }}
        .error-title {{
            color: #ff6b6b;
            font-weight: 600;
            margin-bottom: 0.8em;
            font-size: 1.1em;
        }}
        .error-message {{
            font-family: 'Consolas', monospace;
            white-space: pre-wrap;
            color: #ff8787;
            background-color: #363636;
            padding: 1em;
            border-radius: 8px;
            margin-top: 0.5em;
            font-size: 0.95em;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-title">Preview Error</div>
        <div class="error-message">{str(e)}</div>
    </div>
</body>
</html>"""
            
            temp_html = os.path.join(os.getcwd(), 'temp_preview.html')
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(error_html)
            
            self.preview_area.load(QUrl.fromLocalFile(temp_html))
            
            self.statusBar().showMessage(f"Error updating preview: {str(e)}", 5000)

    def export_html(self):
        try:
            yaml_text = self.yaml_editor.toPlainText().strip()
            
            if not yaml_text:
                QMessageBox.information(self, "Empty Editor", 
                                      "The editor is empty. Please add some YAML content or load an example first.")
                self.statusBar().showMessage("Editor is empty - nothing to export", 3000)
                return
            
            html_content, success = yaml_to_html(yaml_text)
            
            if not success:
                QMessageBox.warning(self, "Export Error", 
                                  "Cannot export invalid YAML. Please fix the errors first.")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save HTML File", "", "HTML Files (*.html);;All Files (*)"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    QMessageBox.information(self, "Success", 
                                          f"HTML file saved successfully to:\n{file_path}")
                    self.statusBar().showMessage(f"HTML exported to: {file_path}", 3000)
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", 
                                       f"Failed to save file: {str(e)}")
                    self.statusBar().showMessage(f"Export failed: {str(e)}", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                               f"An unexpected error occurred: {str(e)}")
            self.statusBar().showMessage(f"Export failed: {str(e)}", 5000)

    def view_html(self):
        yaml_text = self.yaml_editor.toPlainText().strip()
        
        if not yaml_text:
            QMessageBox.information(self, "Empty Editor", 
                                  "The editor is empty. Please add some YAML content or load an example first.")
            self.statusBar().showMessage("Editor is empty - nothing to view", 3000)
            return
        
        html, success = yaml_to_html(yaml_text)
        
        if not success:
            QMessageBox.warning(self, "View HTML Error", 
                              "Cannot view invalid YAML. Please fix the errors first.")
            return
        try:
            from html.parser import HTMLParser
            from html.entities import entitydefs
            import re

            class HTMLFormatter(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.formatted = []
                    self.indent_level = 0
                    self.indent_size = 2
                    self.in_tag = False
                    self.last_tag = None
                    self.current_data = []

                def handle_starttag(self, tag, attrs):
                    # Process any pending data
                    if self.current_data:
                        data = ''.join(self.current_data).strip()
                        if data:
                            indent = ' ' * (self.indent_level * self.indent_size)
                            self.formatted.append(f'{indent}{data}')
                        self.current_data = []

                    indent = ' ' * (self.indent_level * self.indent_size)
                    attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs)
                    if attrs_str:
                        self.formatted.append(f'{indent}<{tag} {attrs_str}>')
                    else:
                        self.formatted.append(f'{indent}<{tag}>')
                    self.indent_level += 1
                    self.in_tag = True
                    self.last_tag = tag

                def handle_endtag(self, tag):
                    # Process any pending data
                    if self.current_data:
                        data = ''.join(self.current_data).strip()
                        if data:
                            indent = ' ' * (self.indent_level * self.indent_size)
                            self.formatted.append(f'{indent}{data}')
                        self.current_data = []

                    self.indent_level -= 1
                    indent = ' ' * (self.indent_level * self.indent_size)
                    if self.in_tag and self.last_tag == tag:
                        # If the tag was empty, modify the previous line
                        self.formatted[-1] = self.formatted[-1].replace('>', f'</{tag}>')
                    else:
                        self.formatted.append(f'{indent}</{tag}>')
                    self.in_tag = False

                def handle_data(self, data):
                    if data.strip():
                        self.current_data.append(data)

                def handle_entityref(self, name):
                    if name in entitydefs:
                        self.current_data.append(entitydefs[name])
                    else:
                        self.current_data.append(f'&{name};')

                def handle_charref(self, name):
                    if name.startswith('x'):
                        self.current_data.append(chr(int(name[1:], 16)))
                    else:
                        self.current_data.append(chr(int(name)))

                def get_formatted_html(self):
                    # Process any remaining data
                    if self.current_data:
                        data = ''.join(self.current_data).strip()
                        if data:
                            indent = ' ' * (self.indent_level * self.indent_size)
                            self.formatted.append(f'{indent}{data}')
                    
                    # Clean up the formatted HTML
                    formatted = '\n'.join(self.formatted)
                    # Remove any double newlines
                    formatted = re.sub(r'\n\s*\n', '\n', formatted)
                    # Remove any trailing whitespace
                    formatted = re.sub(r'[ \t]+$', '', formatted, flags=re.MULTILINE)
                    
                    if '<head>' in formatted:
                        css_reset = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow-x: hidden;
                background-color: #f5f5f0;
            }
            body > *:first-child {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
            section {
                display: block;
                width: 100%;
            }
        </style>"""
                        formatted = formatted.replace('<head>', '<head>' + css_reset)
                    
                    if '<body' in formatted:
                        formatted = re.sub(r'<body[^>]*style="[^"]*"', 
                                         lambda m: re.sub(r'margin:\s*[^;]+;|padding:\s*[^;]+;', '', m.group(0)), 
                                         formatted)
                        if 'style=' not in formatted:
                            formatted = formatted.replace('<body', '<body style="margin: 0; padding: 0;"')
                        elif 'margin:' not in formatted and 'padding:' not in formatted:
                            formatted = formatted.replace('style="', 'style="margin: 0; padding: 0; ')
                    
                    return formatted

            formatter = HTMLFormatter()
            formatter.feed(html)
            formatted_html = formatter.get_formatted_html()
        except Exception:
            formatted_html = html
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated HTML")
        dialog.setMinimumSize(800, 600)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(formatted_html)
        text_edit.setReadOnly(True)
        font = text_edit.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        text_edit.setFont(font)
        
        HTMLHighlighter(text_edit.document())
        
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(100)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(formatted_html))
        button_layout.addStretch()
        button_layout.addWidget(copy_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def open_file(self):
        if self.modified:
            reply = QMessageBox.question(self, 'Open File',
                'Do you want to save the current file before opening a new one?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                if not self.save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open YAML File",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.yaml_editor.setPlainText(content)
                    self.initial_content = content
                    self.current_file = file_path
                    self.modified = False
                    self.setWindowTitle(f"WebForge - {os.path.basename(file_path)}")
                    self.statusBar().showMessage(f"File opened: {file_path}", 3000)
                    self.update_preview()
            except Exception as e:
                QMessageBox.critical(self, "Error",
                    f"Failed to open file: {str(e)}")
                self.statusBar().showMessage(f"Error opening file: {str(e)}", 5000)

    def new_file(self):
        if self.modified:
            reply = QMessageBox.question(self, 'New File',
                'Do you want to save the current file before creating a new one?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                if not self.save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        self.yaml_editor.clear()
        self.current_file = None
        self.initial_content = ""
        self.modified = False
        self.setWindowTitle("WebForge - Untitled")
        self.statusBar().showMessage("New file created", 3000)

    def save_file(self):
        if not self.current_file:
            return self.save_file_as()
        
        try:
            content = self.yaml_editor.toPlainText()
            with open(self.current_file, 'w', encoding='utf-8') as file:
                file.write(content)
            self.initial_content = content
            self.modified = False
            self.statusBar().showMessage(f"File saved: {self.current_file}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to save file: {str(e)}")
            self.statusBar().showMessage(f"Error saving file: {str(e)}", 5000)
            return False

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save YAML File",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.yaml_editor.toPlainText())
                self.current_file = file_path
                self.modified = False
                self.setWindowTitle(f"WebForge - {os.path.basename(file_path)}")
                self.statusBar().showMessage(f"File saved: {file_path}", 3000)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error",
                    f"Failed to save file: {str(e)}")
                self.statusBar().showMessage(f"Error saving file: {str(e)}", 5000)
                return False
        return False

    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, 'Save Changes',
                'Do you want to save your changes before closing?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                if not self.save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        event.accept()

    def setup_javascript_bridge(self):
        class WebForgeBridge(QObject):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent
            
            @pyqtSlot()
            def loadExample(self):
                self.parent.load_example_yaml()
        
        self.bridge = WebForgeBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("webforge", self.bridge)
        self.preview_area.page().setWebChannel(self.channel)

    def load_example_yaml(self):
        try:
            if self.modified:
                reply = QMessageBox.question(self, 'Load Example',
                    'Do you want to save the current file before loading the example?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                
                if reply == QMessageBox.Save:
                    if not self.save_file():
                        return
                elif reply == QMessageBox.Cancel:
                    return
            example_content = """title: Earth & Soul

body:
  style:
    background-color: "#f5f5f0"
    color: "#2c3e2d"
    font-family: "Cormorant Garamond, serif"
    font-size: "16px"
    line-height: "1.6"
    margin: "0"
    padding: "0"
  children:
    - type: section
      style:
        background-image: "url('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80')"
        background-size: "cover"
        background-position: "center"
        height: "100vh"
        display: "flex"
        flex-direction: "column"
        justify-content: "center"
        align-items: "center"
        text-align: "center"
        position: "relative"
        border-radius: "0px"
      children:
        - type: div
          style:
            background-color: "rgba(44, 62, 45, 0.7)"
            padding: "40px"
            border-radius: "8px"
            max-width: "800px"
            margin: "0 20px"
            display: "flex"
            flex-direction: "column"
            align-items: "center"
          children:
            - type: header
              text: "Reconnect with Nature"
              style:
                color: "#f5f5f0"
                font-size: "64px"
                font-weight: "300"
                margin-bottom: "20px"
                font-family: "Cormorant Garamond, serif"
                text-align: "center"
            - type: paragraph
              text: "Discover sustainable living, eco-friendly products, and mindful practices for a harmonious life with nature."
              style:
                color: "#f5f5f0"
                font-size: "24px"
                font-weight: "300"
                margin-bottom: "40px"
                font-family: "Cormorant Garamond, serif"
                text-align: "center"
            - type: button
              text: "Begin Your Journey"
              link: "#explore"
              style:
                background-color: "#8ba888"
                color: "#f5f5f0"
                padding: "16px 40px"
                border-radius: "30px"
                font-weight: "500"
                font-size: "18px"
                border: "none"
                cursor: "pointer"
                transition: "all 0.3s"
                font-family: "Montserrat, sans-serif"
                letter-spacing: "1px"
                text-align: "center"

    - type: section
      style:
        padding: "40px 20px"
        background-color: "#f5f5f0"
        border-radius: "0px"
      children:
        - type: header
          text: "Latest from Our Blog"
          style:
            color: "#2c3e2d"
            font-size: "42px"
            font-weight: "300"
            margin-bottom: "60px"
            text-align: "center"
            font-family: "Cormorant Garamond, serif"
        - type: div
          style:
            display: "grid"
            grid-template-columns: "repeat(auto-fit, minmax(300px, 1fr))"
            gap: "40px"
            max-width: "1200px"
            margin: "0 auto"
          children:
            - type: div
              style:
                background-color: "#ffffff"
                border-radius: "12px"
                overflow: "hidden"
                box-shadow: "0 4px 20px rgba(44, 62, 45, 0.1)"
              children:
                - type: image
                  src: "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                  alt: "Sustainable Living"
                  style:
                    width: "100%"
                    height: "250px"
                    object-fit: "cover"
                - type: div
                  style:
                    padding: "30px"
                  children:
                    - type: header
                      text: "Mindful Living in the Digital Age"
                      style:
                        color: "#2c3e2d"
                        font-size: "24px"
                        font-weight: "500"
                        margin-bottom: "15px"
                        font-family: "Montserrat, sans-serif"
                    - type: paragraph
                      text: "Finding balance between technology and nature in our modern world."
                      style:
                        color: "#5c6c5c"
                        font-size: "16px"
                        line-height: "1.6"
                        font-family: "Montserrat, sans-serif"
            - type: div
              style:
                background-color: "#ffffff"
                border-radius: "12px"
                overflow: "hidden"
                box-shadow: "0 4px 20px rgba(44, 62, 45, 0.1)"
              children:
                - type: image
                  src: "https://images.unsplash.com/photo-1518495973542-4542c06a5843?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                  alt: "Eco Products"
                  style:
                    width: "100%"
                    height: "250px"
                    object-fit: "cover"
                - type: div
                  style:
                    padding: "30px"
                  children:
                    - type: header
                      text: "Eco-Friendly Home Essentials"
                      style:
                        color: "#2c3e2d"
                        font-size: "24px"
                        font-weight: "500"
                        margin-bottom: "15px"
                        font-family: "Montserrat, sans-serif"
                    - type: paragraph
                      text: "Transform your living space with sustainable and natural products."
                      style:
                        color: "#5c6c5c"
                        font-size: "16px"
                        line-height: "1.6"
                        font-family: "Montserrat, sans-serif"
            - type: div
              style:
                background-color: "#ffffff"
                border-radius: "12px"
                overflow: "hidden"
                box-shadow: "0 4px 20px rgba(44, 62, 45, 0.1)"
              children:
                - type: image
                  src: "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                  alt: "Nature Connection"
                  style:
                    width: "100%"
                    height: "250px"
                    object-fit: "cover"
                - type: div
                  style:
                    padding: "30px"
                  children:
                    - type: header
                      text: "The Healing Power of Nature"
                      style:
                        color: "#2c3e2d"
                        font-size: "24px"
                        font-weight: "500"
                        margin-bottom: "15px"
                        font-family: "Montserrat, sans-serif"
                    - type: paragraph
                      text: "Exploring the profound impact of nature on our mental and physical wellbeing."
                      style:
                        color: "#5c6c5c"
                        font-size: "16px"
                        line-height: "1.6"
                        font-family: "Montserrat, sans-serif"

    - type: section
      style:
        background-color: "#8ba888"
        padding: "80px 20px"
        text-align: "center"
        border-radius: "0px"
      children:
        - type: header
          text: "Join Our Community"
          style:
            color: "#f5f5f0"
            font-size: "42px"
            font-weight: "300"
            margin-bottom: "20px"
            font-family: "Cormorant Garamond, serif"
        - type: paragraph
          text: "Subscribe to our newsletter for mindful living tips, sustainable product updates, and exclusive content."
          style:
            color: "#f5f5f0"
            font-size: "18px"
            margin-bottom: "40px"
            max-width: "600px"
            margin-left: "auto"
            margin-right: "auto"
            font-family: "Montserrat, sans-serif"
        - type: div
          style:
            max-width: "500px"
            margin: "0 auto"
            display: "flex"
            gap: "10px"
            justify-content: "center"
          children:
            - type: input
              type: "email"
              placeholder: "Enter your email"
              style:
                width: "60%"
                padding: "15px 20px"
                border: "none"
                border-radius: "30px"
                font-size: "16px"
                font-family: "Montserrat, sans-serif"
            - type: button
              text: "Subscribe"
              style:
                background-color: "#2c3e2d"
                color: "#f5f5f0"
                padding: "15px 30px"
                border-radius: "30px"
                font-weight: "500"
                font-size: "16px"
                border: "none"
                cursor: "pointer"
                transition: "all 0.3s"
                font-family: "Montserrat, sans-serif"
                white-space: "nowrap"
"""
            
            self.yaml_editor.setPlainText(example_content)
            self.initial_content = example_content
            self.current_file = None
            self.modified = False
            self.setWindowTitle("WebForge - Earth & Soul Example")
            self.statusBar().showMessage("Nature example loaded successfully", 3000)
            
            self.update_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to load example: {str(e)}")
            self.statusBar().showMessage(f"Error loading example: {str(e)}", 5000)

    def show_docs(self):
        try:
            readme_file = os.path.join(os.getcwd(), 'README.md')
            if os.path.exists(readme_file):
                with open(readme_file, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                html_content = self.markdown_to_html(readme_content)
                
                docs_html = os.path.join(os.getcwd(), 'temp_docs.html')
                with open(docs_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                import webbrowser
                webbrowser.open('file://' + os.path.abspath(docs_html))
                
                self.statusBar().showMessage("Documentation opened in browser", 3000)
            else:
                QMessageBox.warning(self, "File Not Found", 
                                  "README.md file not found.")
                self.statusBar().showMessage("README.md file not found", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to open documentation: {str(e)}")
            self.statusBar().showMessage(f"Error opening documentation: {str(e)}", 5000)
    
    def markdown_to_html(self, markdown_content):
        md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'nl2br',
                'attr_list',
                'def_list',
                'footnotes',
                'md_in_html',
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False,
                }
            }
        )
        
        html_content = md.convert(markdown_content)
        
        logo_html = ""
        if hasattr(self, 'logo_png_path') and self.logo_png_path and os.path.exists(self.logo_png_path):
            logo_html = f"""
            <div class="header">
                <div class="logo-container">
                    <img src="file://{os.path.abspath(self.logo_png_path)}" alt="WebForge Logo" class="logo">
                    <div class="header-text">
                        <h1 class="app-title">WebForge</h1>
                        <p class="app-subtitle">Forge • Preview • Deploy</p>
                    </div>
                </div>
            </div>
            """
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebForge Documentation</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #f0f6fc;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
            padding: 40px 0;
            border-bottom: 1px solid #30363d;
            margin-bottom: 40px;
        }}
        
        .logo-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            gap: 30px;
        }}
        
        .logo {{
            width: 80px;
            height: 80px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }}
        
        .logo:hover {{
            transform: scale(1.05);
        }}
        
        .header-text {{
            flex: 1;
        }}
        
        .app-title {{
            font-size: 3rem;
            font-weight: 700;
            color: #4dabf7;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        .app-subtitle {{
            font-size: 1.2rem;
            color: #7d8590;
            font-weight: 300;
        }}
        
        .content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px 40px;
        }}
        h1 {{
            color: #4dabf7;
            font-size: 2.5em;
            font-weight: 600;
            margin: 0 0 20px 0;
            border-bottom: 2px solid #4dabf7;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #4dabf7;
            font-size: 2em;
            font-weight: 600;
            margin: 30px 0 15px 0;
        }}
        h3 {{
            color: #4dabf7;
            font-size: 1.5em;
            font-weight: 600;
            margin: 25px 0 10px 0;
        }}
        h4 {{
            color: #4dabf7;
            font-size: 1.2em;
            font-weight: 600;
            margin: 20px 0 8px 0;
        }}
        p {{
            margin: 0 0 15px 0;
            font-size: 1rem;
        }}
        code {{
            background-color: #2d2d2d;
            color: #4dabf7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: #e0e0e0;
            font-size: 0.9em;
        }}
        .highlight {{
            background-color: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            overflow-x: auto;
        }}
        .highlight code {{
            background: none;
            padding: 0;
            color: #e0e0e0;
            font-size: 0.9em;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        strong {{
            color: #ffffff;
            font-weight: 600;
        }}
        em {{
            color: #a0a0a0;
            font-style: italic;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #404040;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #2d2d2d;
            color: #4dabf7;
            font-weight: 600;
        }}
        td {{
            background-color: #1a1a1a;
        }}
        blockquote {{
            border-left: 4px solid #4dabf7;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #2d2d2d;
            color: #b0b0b0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #404040;
            margin: 30px 0;
        }}
        a {{
            color: #4dabf7;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
{logo_html}
<div class="content">
{html_content}
</div>
</body>
</html>"""
        
        return full_html

    def show_search_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Search")
        dialog.setFixedSize(450, 200)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        search_label = QLabel("Search for:")
        search_label.setStyleSheet("color: #f0f6fc; font-weight: 600;")
        layout.addWidget(search_label)
        
        search_input = QLineEdit()
        search_input.setMinimumHeight(35)
        search_input.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #1c2128;
            }
        """)
        layout.addWidget(search_input)
        
        match_label = QLabel("")
        match_label.setStyleSheet("color: #4dabf7; font-size: 12px; font-style: italic;")
        match_label.setWordWrap(True)
        layout.addWidget(match_label)
        
        button_layout = QHBoxLayout()
        
        find_next_btn = QPushButton("Find Next")
        find_next_btn.setMinimumHeight(35)
        find_next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
        find_next_btn.clicked.connect(lambda: self.find_text_with_counter(search_input.text(), dialog, match_label))
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #21262d;
                border-color: #4dabf7;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(find_next_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        search_input.setFocus()
        
        dialog.exec()

    def show_replace_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Find and Replace")
        dialog.setFixedSize(500, 320)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        find_label = QLabel("Find:")
        find_label.setStyleSheet("color: #e0e0e0; font-weight: 600;")
        layout.addWidget(find_label)
        
        find_input = QLineEdit()
        find_input.setMinimumHeight(35)
        find_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
            }
        """)
        layout.addWidget(find_input)
        
        replace_label = QLabel("Replace with:")
        replace_label.setStyleSheet("color: #e0e0e0; font-weight: 600;")
        layout.addWidget(replace_label)
        
        replace_input = QLineEdit()
        replace_input.setMinimumHeight(35)
        replace_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
            }
        """)
        layout.addWidget(replace_input)
        
        match_label = QLabel("")
        match_label.setStyleSheet("color: #4dabf7; font-size: 12px; font-style: italic;")
        match_label.setWordWrap(True)
        layout.addWidget(match_label)
        
        button_layout = QHBoxLayout()
        
        find_btn = QPushButton("Find")
        find_btn.setMinimumHeight(35)
        find_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
        find_btn.clicked.connect(lambda: self.find_text_with_counter(find_input.text(), dialog, match_label))
        
        replace_btn = QPushButton("Replace")
        replace_btn.setMinimumHeight(35)
        replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        replace_btn.clicked.connect(lambda: self.replace_text_with_counter(find_input.text(), replace_input.text(), dialog, match_label))
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.setMinimumHeight(35)
        replace_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        replace_all_btn.clicked.connect(lambda: self.replace_all_text_with_counter(find_input.text(), replace_input.text(), dialog, match_label))
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(find_btn)
        button_layout.addWidget(replace_btn)
        button_layout.addWidget(replace_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        find_input.setFocus()
        
        dialog.exec()

    def find_text(self, search_text, dialog=None):
        if not search_text.strip():
            return
        
        cursor = self.yaml_editor.textCursor()
        document = self.yaml_editor.document()
        
        cursor.setPosition(cursor.position())
        
        found = document.find(search_text, cursor)
        
        if found.isNull():
            cursor.setPosition(0)
            found = document.find(search_text, cursor)
        
        if not found.isNull():
            self.yaml_editor.setTextCursor(found)
            self.yaml_editor.setFocus()
        else:
            if dialog:
                QMessageBox.information(dialog, "Not Found", f'Text "{search_text}" not found.')
            else:
                self.statusBar().showMessage(f'Text "{search_text}" not found.', 3000)

    def replace_text(self, search_text, replace_text, dialog=None):
        if not search_text.strip():
            return
        
        cursor = self.yaml_editor.textCursor()
        
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(replace_text)
            self.statusBar().showMessage("Text replaced", 2000)
        else:
            self.find_text(search_text, dialog)
            cursor = self.yaml_editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == search_text:
                cursor.insertText(replace_text)
                self.statusBar().showMessage("Text replaced", 2000)

    def replace_all_text(self, search_text, replace_text, dialog=None):
        if not search_text.strip():
            return
        
        full_text = self.yaml_editor.toPlainText()
        
        count = full_text.count(search_text)
        
        if count == 0:
            if dialog:
                QMessageBox.information(dialog, "Not Found", f'Text "{search_text}" not found.')
            else:
                self.statusBar().showMessage(f'Text "{search_text}" not found.', 3000)
            return
        
        new_text = full_text.replace(search_text, replace_text)
        self.yaml_editor.setPlainText(new_text)
        
        if dialog:
            QMessageBox.information(dialog, "Replace All", f'Replaced {count} occurrence(s) of "{search_text}".')
        else:
            self.statusBar().showMessage(f'Replaced {count} occurrence(s)', 3000)

    def find_text_with_counter(self, search_text, dialog=None, match_label=None):
        if not search_text.strip():
            if match_label:
                match_label.setText("")
            return
        
        full_text = self.yaml_editor.toPlainText()
        total_matches = full_text.count(search_text)
        
        if total_matches == 0:
            if match_label:
                match_label.setText("No matches found")
            if dialog:
                QMessageBox.information(dialog, "Not Found", f'Text "{search_text}" not found.')
            else:
                self.statusBar().showMessage(f'Text "{search_text}" not found.', 3000)
            return
        
        cursor = self.yaml_editor.textCursor()
        document = self.yaml_editor.document()
        
        cursor.setPosition(cursor.position())
        
        found = document.find(search_text, cursor)
        
        if found.isNull():
            cursor.setPosition(0)
            found = document.find(search_text, cursor)
        
        if not found.isNull():
            self.yaml_editor.setTextCursor(found)
            self.yaml_editor.setFocus()
            
            current_pos = found.selectionStart()
            text_before = full_text[:current_pos]
            current_match = text_before.count(search_text) + 1
            
            if match_label:
                match_label.setText(f"Match {current_match} of {total_matches}")
        else:
            if match_label:
                match_label.setText("No matches found")

    def replace_text_with_counter(self, search_text, replace_text, dialog=None, match_label=None):
        if not search_text.strip():
            return
        
        cursor = self.yaml_editor.textCursor()
        
        if cursor.hasSelection() and cursor.selectedText() == search_text:
            cursor.insertText(replace_text)
            self.statusBar().showMessage("Text replaced", 2000)
            self.find_text_with_counter(search_text, dialog, match_label)
        else:
            self.find_text_with_counter(search_text, dialog, match_label)
            cursor = self.yaml_editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == search_text:
                cursor.insertText(replace_text)
                self.statusBar().showMessage("Text replaced", 2000)
                self.find_text_with_counter(search_text, dialog, match_label)

    def replace_all_text_with_counter(self, search_text, replace_text, dialog=None, match_label=None):
        if not search_text.strip():
            return
        
        full_text = self.yaml_editor.toPlainText()
        
        count = full_text.count(search_text)
        
        if count == 0:
            if match_label:
                match_label.setText("No matches found")
            if dialog:
                QMessageBox.information(dialog, "Not Found", f'Text "{search_text}" not found.')
            else:
                self.statusBar().showMessage(f'Text "{search_text}" not found.', 3000)
            return
        
        new_text = full_text.replace(search_text, replace_text)
        self.yaml_editor.setPlainText(new_text)
        
        if match_label:
            match_label.setText(f"Replaced {count} occurrence(s)")
        
        if dialog:
            QMessageBox.information(dialog, "Replace All", f'Replaced {count} occurrence(s) of "{search_text}".')
        else:
            self.statusBar().showMessage(f'Replaced {count} occurrence(s)', 3000)

    def show_goto_line_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Line")
        dialog.setFixedSize(400, 200)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        line_label = QLabel("Line number:")
        line_label.setStyleSheet("color: #f0f6fc; font-weight: 600;")
        layout.addWidget(line_label)
        
        line_input = QLineEdit()
        line_input.setMinimumHeight(35)
        line_input.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #4dabf7;
                background-color: #1c2128;
            }
        """)
        layout.addWidget(line_input)
        
        total_lines = self.yaml_editor.blockCount()
        info_label = QLabel(f"Total lines: {total_lines}")
        info_label.setStyleSheet("color: #7d8590; font-size: 12px; font-style: italic;")
        layout.addWidget(info_label)
        
        button_layout = QHBoxLayout()
        
        goto_btn = QPushButton("Go to Line")
        goto_btn.setMinimumHeight(35)
        goto_btn.setStyleSheet("""
            QPushButton {
                background-color: #4dabf7;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
        """)
        goto_btn.clicked.connect(lambda: self.goto_line(line_input.text(), dialog))
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #21262d;
                border-color: #4dabf7;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addWidget(goto_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        line_input.setFocus()
        line_input.selectAll()
        
        line_input.returnPressed.connect(lambda: self.goto_line(line_input.text(), dialog))
        
        dialog.exec()

    def goto_line(self, line_text, dialog=None):
        try:
            line_number = int(line_text.strip())
            total_lines = self.yaml_editor.blockCount()
            
            if line_number < 1:
                if dialog:
                    QMessageBox.warning(dialog, "Invalid Line", "Line number must be greater than 0.")
                else:
                    self.statusBar().showMessage("Line number must be greater than 0.", 3000)
                return
            
            if line_number > total_lines:
                if dialog:
                    QMessageBox.warning(dialog, "Invalid Line", f"Line number {line_number} exceeds total lines ({total_lines}).")
                else:
                    self.statusBar().showMessage(f"Line number {line_number} exceeds total lines ({total_lines}).", 3000)
                return
            
            cursor = self.yaml_editor.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.MoveAnchor, line_number - 1)
            cursor.movePosition(cursor.StartOfLine)
            self.yaml_editor.setTextCursor(cursor)
            self.yaml_editor.setFocus()
            
            if dialog:
                dialog.accept()
            
            self.statusBar().showMessage(f"Jumped to line {line_number}", 2000)
            
        except ValueError:
            if dialog:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid line number.")
            else:
                self.statusBar().showMessage("Please enter a valid line number.", 3000)

    def open_in_browser(self):
        try:
            yaml_text = self.yaml_editor.toPlainText().strip()
            
            if not yaml_text:
                QMessageBox.information(self, "Empty Editor", 
                                      "The editor is empty. Please add some YAML content or load an example first.")
                self.statusBar().showMessage("Editor is empty - nothing to preview", 3000)
                return
            
            html_content, success = yaml_to_html(yaml_text)
            
            if not success:
                QMessageBox.warning(self, "Preview Error", 
                                  "Cannot open invalid YAML in browser. Please fix the errors first.")
                return
            
            temp_html = os.path.join(os.getcwd(), 'temp_preview.html')
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(temp_html))
            
            self.statusBar().showMessage("Opened preview in browser", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Failed to open in browser: {str(e)}")
            self.statusBar().showMessage(f"Error opening in browser: {str(e)}", 5000)

def main():
    app = QApplication(sys.argv)
    window = YAMLPreviewApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 