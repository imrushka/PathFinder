# -*- coding: utf-8 -*-
# импортирую необходимые в работе библиотеки
import random
import sqlite3
import sys

from PyQt5 import QtGui
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QLabel, QMessageBox
from PyQt5.QtWidgets import QPushButton


# сооздаю класс MainWindow как главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('design_for_project.ui', self)  # Загружаем дизайн
        # инициалилирую константы цветов и
        self.setWindowTitle('path_finder')
        self.start_color = '#ff0000'
        self.finish_color = '#017c14'
        self.path_color = '#000dff'
        self.process_color = '#741a72'
        self.wall_color = '#5b5b5b'
        self.draw = True
        self.current_tool = 'кисть'
        self.current_type = 'стена'
        self.number_of_starting = 0
        self.number_of_finishing = 0
        self.do_process = False
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.btn_play.clicked.connect(self.play)
        # для стены
        self.btn_wall.clicked.connect(self.set_color)
        self.btn_wall.setShortcut('Ctrl+W')
        # для старта
        self.btn_start.clicked.connect(self.set_color)
        self.btn_start.setShortcut('Ctrl+S')
        # для фниниша
        self.btn_finish.clicked.connect(self.set_color)
        self.btn_finish.setShortcut('Ctrl+F')
        # для пути
        self.btn_path.clicked.connect(self.set_color)
        self.btn_path.setShortcut('Ctrl+P')
        # для процесса поиска(окрашивание рассмотреных клеток)
        self.btn_process.clicked.connect(self.set_color)
        self.btn_process.setShortcut('Ctrl+Z')
        # для генерациии случайной карты
        self.generate.clicked.connect(self.radio_change)
        self.generate.setShortcut('Ctrl+G')
        self.clear_all.clicked.connect(self.radio_change)
        self.clear_all.setShortcut('Ctrl+R')
        self.download_the_map.clicked.connect(self.download_map)
        self.x_axis = QLabel(self)
        self.x_axis.move(400, 10)
        self.x_axis.resize(1120, 20)
        string_for_x_till9 = '   '.join([str(i) for i in range(1, 10)])
        string_for_x_till40 = '  '.join([str(i) for i in range(10, 41)])
        self.x_axis.setText(' ' + string_for_x_till9 + '   ' +
                            string_for_x_till40)
        x, y = 385, 31
        # создам массив из label и заполню каждое числом
        y_coors = []
        for i in range(35):
            y_coors.append(QLabel(self))
            y_coors[-1].move(x, y)
            y_coors[-1].resize(12, 10)
            y_coors[-1].setText(str(i + 1))
            y += 18
        self.cells = []
        self.cells_colors = []
        x, y = 400, 30
        w, h = 18, 18
        for i in range(35):
            row = []
            row_colors = []
            for j in range(40):
                # в двумерный массив сораняю кнопки для создания подобия клетчатой карты
                row.append(QPushButton(self))
                row[-1].move(x, y)
                row[-1].resize(w, h)
                row[-1].setStyleSheet("background-color: white")
                row_colors.append('white')
                row[-1].setText(f'{i}             {j}')
                row[-1].clicked.connect(self.cell_clicked)
                row[-1].setEnabled(True)
                x += w
            x -= w * 40
            y += h
            self.cells.append(row)
            self.cells_colors.append(row_colors)
        self.combo_tool.currentIndexChanged.connect(self.selectionchange)
        self.combo_type.currentIndexChanged.connect(self.type_change)
        self.show_pr.toggled.connect(self.show_process)
        self.update_table_button.clicked.connect(self.update_table)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        # отбражаю координаты на лейбле
        self.coords.setText(f"Coordinates: {event.x()}, {event.y()}")

    def keyPressEvent(self, event):
        if int(event.modifiers()) == (Qt.ControlModifier):
            if event.key() == Qt.Key_L:
                self.play()
            elif event.key() == Qt.Key_U:
                self.update_table()
            elif event.key() == Qt.Key_D:
                self.download_map()

    def download_map(self):
        if self.are_you_sure():
            # поключусь к таблице
            self.number_of_starting = 0
            self.number_of_finishing = 0
            self.con = sqlite3.connect('cells_of_pathfinder_map.db')
            cur = self.con.cursor()
            # для того чтобы все изменения в цветх отбражаллись правильно обновляю таблицу цветов
            que = "UPDATE COLORS SET\n"
            que += "color=?\n"
            que += "WHERE color_id = ?"
            data1 = []
            colors_self = [
                'white', self.start_color, self.finish_color, self.wall_color,
                self.process_color, self.path_color
            ]
            for i in range(6):
                data1.append((colors_self[i], i))
            with self.con:
                cur.executemany(que, data1)
            with self.con:
                # соберу инфу о клетках и цветах
                result_cells = cur.execute("""SELECT * FROM CELLS""").fetchall()
                # покажу изменения на карте
                for elem in result_cells:
                    col_id, value, x_pos, y_pos = elem
                    if col_id == 1:
                        self.number_of_starting = 1
                    elif col_id == 2:
                        self.number_of_finishing = 1
                    self.cells[y_pos][x_pos].setStyleSheet(f'background-color: {colors_self[col_id]}')
                    self.cells_colors[y_pos][x_pos] = colors_self[col_id]

    def update_table(self):
        # метод который обнавляет инофрмацию в базе данных карты
        # подключусь к базе данных
        self.con = sqlite3.connect('cells_of_pathfinder_map.db')
        value_of_cell = ''
        # data массив для хранения информаии для первой подтаблицы
        data = []
        # data1 массив для хранения информаии для второй подтаблицы
        data1 = []
        value_track = 0
        for i in range(35):
            for j in range(40):
                # запишу информацию о каждой клетке
                if self.cells_colors[i][j] == self.start_color:
                    col_id = 1
                    color = self.start_color
                    value_of_cell = 'старт'
                if self.cells_colors[i][j] == self.finish_color:
                    col_id = 2
                    color = self.finish_color
                    value_of_cell = 'фниниш'
                if self.cells_colors[i][j] == self.wall_color:
                    col_id = 3
                    color = self.wall_color
                    value_of_cell = 'стена'
                if self.cells_colors[i][j] == self.path_color:
                    col_id = 5
                    color = self.path_color
                    value_of_cell = 'путь'
                if self.cells_colors[i][j] == self.process_color:
                    col_id = 4
                    color = self.process_color
                    value_of_cell = 'процесс'
                if self.cells_colors[i][j] == 'white':
                    col_id = 0
                    color = 'white'
                    value_of_cell = 'пусто'
                # теперь можно создать кортеж для sql запроса и пометить его в сазданный раннее массив
                data.append((col_id, value_of_cell, j, i))

            # обонвлю всю информаицию для каждой клетки через  sql запрос
            cur = self.con.cursor()
            que = "UPDATE CELLS SET\n"
            que += f"color_id= ?, value=?\n"
            que += "WHERE x_pos = ? AND y_pos = ?"
            with self.con:
                cur.executemany(que, data)
            # теперь можно обновить таблицу цветов клеток
            que = "UPDATE COLORS SET\n"
            que += "color=?\n"
            que += "WHERE color_id = ?"
            data1 = []
            colors_self = [
                'white', self.start_color, self.finish_color, self.wall_color,
                self.process_color, self.path_color
            ]
            for i in range(6):
                data1.append((colors_self[i], i))

            with self.con:
                cur.executemany(que, data1)
        self.update_success()

    # это метод для поключения чек бокса  который будет менять перерменную сообщающую о выборе

    def update_success(self):
        msg2 = QMessageBox(self)
        msg2.setIcon(QMessageBox.Information)
        msg2.setInformativeText("Карта сохранена успешно")
        msg2.setWindowTitle("Ура!")
        msg2.setStandardButtons(QMessageBox.Ok)
        msg2.exec_()

    def show_process(self):
        if self.sender().isChecked() is True:
            self.do_process = True
        else:
            # убераю все клетки процесса на карте если они имеются
            for i in range(35):
                for j in range(40):
                    if self.cells_colors[i][j] == self.process_color:
                        self.cells_colors[i][j] = 'white'
                        self.cells[i][j].setStyleSheet(
                            'background-color: white')
            # меняю переменнную о отображении процесса
            self.do_process = False

    # метод меняющий текущий тип клетки на карте человека, подключается к комбо боксу
    def type_change(self):
        # меняю переменную на полученый сигнал подключенного комбо бокса
        self.current_type = self.sender().currentText()

    # метод меняющий текущий тип инструмента человека, подключается к комбо боксу
    def selectionchange(self):
        # меняю переменную на сигнал полуечнный из комбо бокса
        self.current_tool = self.sender().currentText()

    # метод меняющий цыет кнопки и ее значения вв массивах о цветах и кнопках при нажатии на них
    def cell_clicked(self):
        # получаю информацию от какой кнопки был получен сигнал, звписываю в координаты
        x, y = (
            int(self.sender().text().split()[0]),
            int(self.sender().text().split()[1]),
        )
        # проверяю переменнeю о текущем инструменте чтобы установить соответствующий цвет у кнопки
        if self.current_tool == 'кисть':
            # проверяю переменную о текущем типе изменяемой клетки
            if self.current_type == 'старт':
                # обращяюсь по полученному сигналу к клетке в матрице клеток и меняю значения а матриуе цветов клеток
                if self.cells_colors[x][y] == self.finish_color:
                    # необходимо учитывать количесво клеток старта и финиша в данный момент чтобы не возникла ошибка при подсчете пути
                    # меняю переменную о количесвое фонишной точке на карте
                    self.number_of_finishing -= 1
                    # проверяю на допуcтимость установления на карте
                if self.number_of_starting != 1:
                    self.cells[x][y].setStyleSheet(
                        f'background-color: {self.start_color}')
                    self.cells_colors[x][y] = self.start_color
                    self.number_of_starting += 1
            if self.current_type == 'стена':
                # если клетка стены перекряыла клетку финиша или старта то я меняю переменную о их количестве
                if self.cells_colors[x][y] == self.start_color:
                    self.number_of_starting -= 1
                if self.cells_colors[x][y] == self.finish_color:
                    self.number_of_finishing -= 1
                self.cells[x][y].setStyleSheet(
                    f'background-color: {self.wall_color}')
                self.cells_colors[x][y] = self.wall_color
            if self.current_type == 'финиш':
                # также при подсчетете клеток необходимо учитывать перекрытие клетками того же типа
                if self.cells_colors[x][y] == self.start_color:
                    self.number_of_starting -= 1
                if self.number_of_finishing != 1:
                    self.cells[x][y].setStyleSheet(
                        f'background-color: {self.finish_color}')
                    self.cells_colors[x][y] = self.finish_color
                    self.number_of_finishing += 1
        if self.current_tool == 'ластик':

            if self.cells_colors[x][y] == self.start_color:
                self.number_of_starting -= 1
            if self.cells_colors[x][y] == self.finish_color:
                self.number_of_finishing -= 1
            self.cells[x][y].setStyleSheet('background-color: white')
            self.cells_colors[x][y] = 'white'

    def converter(self, width, length):
        # метод конвертирующий и проверюящий на правильность матрицу цветов
        # перед началом поиска пути
        # если на карте недостает точки старта или финиша то фозвращаю ложь
        have_finish = False
        have_start = False
        for i in range(length):
            for j in range(width):
                if self.cells_colors[i][j] == self.start_color:
                    have_start = True
                if self.cells_colors[i][j] == self.finish_color:
                    have_finish = True
                if (self.cells_colors[i][j] == self.path_color
                        or self.cells_colors[i][j] == self.process_color):
                    self.cells_colors[i][j] = 'white'
                    self.cells[i][j].setStyleSheet('background-color: white')

        if not have_finish or not have_start:
            # если нужных точек недостает то уведомлю пользователю об этом через сообщение
            self.alert_point()
            return False
        return True

    def alert_point(self):
        # метод сообщающий об ошибке количесва необходимыч точек
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            "для устранения проблемы, доставьте\nнедостающие точки или сгенерируйте\nкарту случайно"
        )
        msg.setInformativeText("Похоже что нехватает коненчой точки")
        msg.setWindowTitle("Ошибка")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def alert_color(self):
        # метод сообщающий об повторении в цветах кнопок типов клеток
        msg1 = QMessageBox(self)
        msg1.setIcon(QMessageBox.Critical)
        msg1.setText("для устранения проблемы, выберите\nдругие цвета клеток")
        msg1.setInformativeText("Похоже что какие-то цвета одинаковы")
        msg1.setWindowTitle("Ошибка")
        msg1.setStandardButtons(QMessageBox.Ok)
        msg1.exec_()

    def no_path(self):
        # метод сообщающий о том что пути не нашлось
        msg2 = QMessageBox(self)
        msg2.setIcon(QMessageBox.Information)
        msg2.setText("для устранения проблемы, поменяте расположение стены")
        msg2.setInformativeText("Похоже что я не могу найти путь")
        msg2.setWindowTitle("Упс!")
        msg2.setStandardButtons(QMessageBox.Ok)
        msg2.exec_()

    def play(self):
        # метод запускающий поиск пути
        # функция подсчета дистанции до точки путем округления дистанции воспринимая длину клетки за 10 единиц

        def distance_counter(x, y, x1, y1):
            xd = abs(x - x1)
            yd = abs(y - y1)
            rem = abs(xd - yd)
            return min(xd, yd) * 14 + rem * 10

        # инициализирую класс клетки

        class Node:
            def __init__(self, x, y, value, f, h, g, parent_coords):
                # в работе нам понадобятся координаты точки на карте
                self.x = x
                self.y = y
                # значение точки на карте
                self.value = value
                # ее значение функций
                # пояснение:(F(f) = F(g) + F(h)) где F(h) это расстояние данной точки до точки старта
                # F(g) это расстояние до точки финиша
                # F(f) это сумма двух предидущий функций
                self.f = f
                self.g = g
                self.h = h
                # также нам понадобится знать откуда мы пришли к даннойточке чтобы воостановить ответ
                self.parent_coords = parent_coords

        # обозначаю длину и ширину карты для избежания ошибок связанных с неправильным числом
        width = 40
        length = 35
        if self.converter(width, length):
            # в алгоритме нам нужно знать какие точки мы рассматриваем в данный момент и какие уже рассмотрели
            # для этого содаю два массива
            Open = []
            Closed = []
            # теперь создам массив для клеток
            Matrix_of_signs = []
            # проверю подходит ли поле для начала работы обратясь к методу проверки
            if self.converter(width, length):
                try:
                    # теперь ипользую наш массив цветов клеток для его дальнейшей конвертации
                    matrix_of_colors = self.cells_colors
                    # обознаю константы отвечающие за отображение цветов
                    start_color = self.start_color
                    finish_color = self.finish_color
                    path_color = self.path_color
                    process_color = self.process_color
                    wall_color = self.wall_color
                    # константы о координатах стартовой и конечной точекна карте
                    start_x, start_y, fx, fy = 0, 0, 0, 0
                    # для того чтобы не выйти за пределы массивва, я окружу изачальный масив стенками
                    Matrix_of_signs.append([
                        Node(0, j, '0', 0, 0, 0, 0) for j in range(width + 2)])
                    for i in range(1, length + 1):
                        N = [Node(i, 0, '0', 0, 0, 0, 0)]
                        for j in range(1, width + 1):
                            # теперь проверяю тип текущей клетки и создам экзепляр клсса Node и задам соответсвующие параметры
                            # "0" это стнека, "*" это статовая позиция, " " это пустая клетка, "#" это конечная позиция
                            if matrix_of_colors[i - 1][j - 1] == 'white':
                                N.append(Node(i, j, ' ', 0, 0, 0, 0))
                            if matrix_of_colors[i - 1][j - 1] == start_color:
                                N.append(Node(i, j, '*', 0, 0, 0, (i, j)))
                                start_x = i
                                start_y = j
                            if matrix_of_colors[i - 1][j - 1] == finish_color:
                                N.append(Node(i, j, '#', 0, 0, 0, 0))
                                fx = i
                                fy = j
                            if matrix_of_colors[i - 1][j - 1] == wall_color:
                                N.append(Node(i, j, '0', 0, 0, 0, 0))
                        N.append(Node(i, width + 2, '0', 0, 0, 0, 0))
                        Matrix_of_signs.append(N)
                    Matrix_of_signs.append([Node(length + 2, j, '0', 0, 0, 0, 0)
                                            for j in range(width + 2)])
                    # теперь задам все занчения определенных в классе Node для их дальнейшего использования
                    # использую функцию посчета дистанции между точками для становления F(h) F(g) F(f)
                    Matrix_of_signs[start_x][start_y].g = distance_counter(
                        start_x, start_y, fx, fy)
                    Matrix_of_signs[start_x][start_y].h = distance_counter(
                        start_x, start_y, start_x, start_y)
                    Matrix_of_signs[start_x][start_y].f = (
                            Matrix_of_signs[start_x][start_y].h +
                            Matrix_of_signs[start_x][start_y].g)
                    # теперь можно занести стартовую точку в массив рассматреваемых точек
                    Open.append(Matrix_of_signs[start_x][start_y])
                    # теперь начнем циккл, чье количество превышает максимальное возможное число рассмотров
                    self.cells_counter = 0
                    for loop in range(100000000):
                        self.cells_counter += 1
                        # обозначим переменную о текущей клетке
                        current_node = sorted(Open,
                                              key=lambda x: [x.f, x.g, x.h])[0]
                        # теперь можно занести его число уде рассмотреных точек и удалить его из числа рассматриевых
                        Closed.append(current_node)
                        # теперь буду отображать процесс на карте
                        if (current_node.value != '*'
                                and current_node.value != '#'
                                and self.do_process):
                            self.cells_colors[current_node.x -
                                              1][current_node.y -
                                                 1] = self.process_color
                            self.cells[current_node.x - 1][
                                current_node.y - 1].setStyleSheet(
                                f'background-color: {self.process_color}')
                        Open.remove(current_node)
                        # проверю если мы дошли до финиша
                        if current_node.value == '#':
                            break
                        # получу координаты текущей клетки
                        x = current_node.x
                        y = current_node.y
                        # рассмотрю все соседнии точки
                        # буду использовать очень крутой способ обращения ко всем сосдям пришедший из олипийского программирования
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                if i == 0 and j == 0:
                                    continue
                                else:
                                    # теперь обозначу цену за проход по диагонали и проход по прямой
                                    # если мы идем по диагонали то цена составит 14 а если по прямой то 10
                                    # это складывется из того что длина нашей клетки 10 и по диагонали это int(sqrt(10 ** 2 * 10 ** 2)) = 14

                                    if abs(i) + abs(j) == 2:
                                        path_cost = 14
                                    else:
                                        path_cost = 10
                                    x, y = current_node.x + i, current_node.y + j
                                    # проверю не смотрю ли я на непроходимую точку или ту что я уже рассмотрел
                                    if (Matrix_of_signs[x][y].value != '0' and Matrix_of_signs[x][y] not in Closed):
                                        if Matrix_of_signs[x][y] not in Open:
                                            # если я еще не рассмотрел эту току то установлю F(h) F(g) F(f) и значения координат тоски откуда мы пришли в соседнюю
                                            Matrix_of_signs[x][y].h = (
                                                        Matrix_of_signs[current_node.x][current_node.y].h + path_cost)
                                            Matrix_of_signs[x][y].g = distance_counter(x, y, fx, fy)
                                            Matrix_of_signs[x][y].f = (
                                                        Matrix_of_signs[x][y].h + Matrix_of_signs[x][y].g)
                                            Matrix_of_signs[x][y].parent_coords = (current_node.x, current_node.y,)
                                            Open.append(Matrix_of_signs[x][y])
                                        else:
                                            # если я уже рассмотрел соседа то мне нужно улчшить дистанцию до точки
                                            Matrix_of_signs[x][y].f = min(Matrix_of_signs[current_node.x][
                                                                              current_node.y].h + path_cost + distance_counter(
                                                x, y, fx, fy),
                                                                          Matrix_of_signs[x][y].f, )
                                            if Matrix_of_signs[x][y].f == Matrix_of_signs[current_node.x][
                                                current_node.y].h + path_cost + distance_counter(x, y, fx, fy):
                                                Matrix_of_signs[x][y].h = (Matrix_of_signs[current_node.x][
                                                                               current_node.y].h + path_cost)
                                                Matrix_of_signs[x][y].g = distance_counter(x, y, fx, fy)
                                                Matrix_of_signs[x][y].parent_coords = (current_node.x, current_node.y,)
                    answer = []
                    # теперь восстановлю ответ
                    for i in range(length + 2):
                        layer = []
                        for j in range(width + 2):
                            layer.append('0')
                        answer.append(layer)
                    # запущу цикл меняющий в answer значения для клеток пути, буду возаращаться опраясь на иформацию о точке откуда мы пришли к соседу
                    x2, y2 = Matrix_of_signs[fx][fy].parent_coords
                    while True:
                        if x2 == start_x and y2 == start_y:
                            break
                        answer[x2][y2] = ' '
                        x2, y2 = Matrix_of_signs[x2][y2].parent_coords
                    self.path_number = 0
                    # теперь отбражу путь на карте цветов и кнопок
                    # также нужно вести учет длины пути
                    for i in range(1, length + 1):
                        for j in range(1, width + 1):
                            if answer[i][j] == ' ':
                                self.path_number += 1
                                # нужно не забыть что мы окружили карту стеной и поэтому реальное расположение находинтся на 1 единицу меньше
                                self.cells[i - 1][j - 1].setStyleSheet(
                                    f'background-color: {self.path_color}')
                                self.cells_colors[i - 1][j - 1] = self.path_color
                    # теперь необходимо сообщить пользователю о найденом пути и его длине
                    self.success()
                except Exception as e:
                    # если возникает какая-то ошибка то это начит что путь найти не возможно
                    # необходимо сообщить о том что пути нет
                    self.no_path()

    def success(self):
        # метод сообщающий о найденом пути
        msg2 = QMessageBox(self)
        msg2.setIcon(QMessageBox.Information)
        msg2.setInformativeText(
            f"Похоже что мы нашли наиктротчайший путь!\nДлина вашего пути: {self.path_number}\n"
            f"Клеток рассмотрено {self.cells_counter}"
        )
        msg2.setWindowTitle("Ура!")
        msg2.setStandardButtons(QMessageBox.Ok)
        msg2.exec_()

    def are_you_sure(self):
        # метод предупреждающий о том что если создавать катру
        # случайным образом то предыдущие изменения удалятся
        msg2 = QMessageBox(self)
        msg2.setIcon(QMessageBox.Question)
        msg2.setInformativeText(
            "Если вы продолжите то все старые\nизменения на карте будут удалены"
        )
        msg2.setWindowTitle("Предупреждение")
        msg2.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return_value = msg2.exec_()
        # даю возможность отказаться от выбора
        if return_value == QMessageBox.Ok:
            return True
        return False

    def radio_change(self):
        # метод генерирующий карту если пользователь подтверждает выбор
        if self.are_you_sure():
            if self.sender().text() == 'случайная карта':
                # также получу информацию от пользователя о плотности дальнейшей карты
                percentage, ok_pressed = QInputDialog.getInt(
                    self,
                    "Введите число",
                    "Какова плотность карты (в % от всех клеток)?",
                    30,
                    10,
                    50,
                    5,
                )
                if ok_pressed:
                    number = int(35 * 40 * percentage / 100)
                else:
                    number = int(35 * 40 * 0.4)
                    number = random.randrange(300, 35 * 10)
                self.number_of_starting = 0
                self.number_of_finishing = 0
                # очищу карту перед созданием новой
                for i in range(35):
                    for j in range(40):
                        self.cells[i][j].setStyleSheet(
                            'background-color: white')
                        self.cells_colors[i][j] = 'white'
                self.random_coordinates = []

                for i in range(number):
                    x = random.randrange(35)
                    y = random.randrange(40)
                    # исключу возможность повторения точек выбранных случайно
                    while (x, y) in self.random_coordinates:
                        x = random.randrange(35)
                        y = random.randrange(40)
                    self.random_coordinates.append((x, y))
                    # установлю различные точки случайным образом на карте
                    if i == 1:
                        self.number_of_finishing = 1
                        self.cells[x][y].setStyleSheet(
                            f'background-color: {self.finish_color}')
                        self.cells_colors[x][y] = self.finish_color
                    elif i == 0:
                        self.number_of_starting = 1
                        self.cells[x][y].setStyleSheet(
                            f'background-color: {self.start_color}')
                        self.cells_colors[x][y] = self.start_color
                    else:
                        self.cells[x][y].setStyleSheet(
                            f'background-color: {self.wall_color}')
                        self.cells_colors[x][y] = self.wall_color
            else:
                # если сигнал был послан от другой точки то это кнопка "очистить все"
                # надо не забыть установить количетсво стартовых и конечных позиций
                self.number_of_starting = 0
                self.number_of_finishing = 0
                # удаляю все клеки на карте
                for i in range(35):
                    for j in range(40):
                        self.cells[i][j].setStyleSheet(
                            'background-color: white')
                        self.cells_colors[i][j] = 'white'

    def set_color(self):
        # метод устнавливаюший цвет определенного типв клетки
        color = QColorDialog.getColor()
        # получу имя цвета через диалог с пользователем
        # проверю для какого типа клетки мне нужно поменять цвет
        if self.sender().text() == 'старт':
            ch_set = set()
            ch_set.add(self.wall_color)
            ch_set.add(color.name())
            ch_set.add(self.finish_color)
            ch_set.add(self.path_color)
            ch_set.add(self.process_color)
            # покажу изменения на карте
            if len(ch_set) == 5:
                for i in range(35):
                    for j in range(40):
                        if self.cells_colors[i][j] == self.start_color:
                            self.cells_colors[i][j] = color.name()
                            self.cells[i][j].setStyleSheet(
                                f'background-color: {color.name()}')
                self.start_color = color.name()
            else:
                self.alert_color()

        if self.sender().text() == 'финиш':
            ch_set = set()
            ch_set.add(self.wall_color)
            ch_set.add(color.name())
            ch_set.add(self.start_color)
            ch_set.add(self.path_color)
            ch_set.add(self.process_color)
            if len(ch_set) == 5:
                for i in range(35):
                    for j in range(40):
                        if self.cells_colors[i][j] == self.finish_color:
                            self.cells_colors[i][j] = color.name()
                            self.cells[i][j].setStyleSheet(
                                f'background-color: {color.name()}')
                self.finish_color = color.name()
            else:
                self.alert_color()

        if self.sender().text() == 'путь':
            ch_set = set()
            ch_set.add(self.wall_color)
            ch_set.add(color.name())
            ch_set.add(self.finish_color)
            ch_set.add(self.start_color)
            ch_set.add(self.process_color)
            if len(ch_set) == 5:
                for i in range(35):
                    for j in range(40):
                        if self.cells_colors[i][j] == self.path_color:
                            self.cells_colors[i][j] = color.name()
                            self.cells[i][j].setStyleSheet(
                                f'background-color: {color.name()}')

                self.path_color = color.name()
            else:
                self.alert_color()

        if self.sender().text() == 'процесс':
            ch_set = set()
            ch_set.add(self.wall_color)
            ch_set.add(color.name())
            ch_set.add(self.finish_color)
            ch_set.add(self.path_color)
            ch_set.add(self.start_color)
            if len(ch_set) == 5:
                for i in range(35):
                    for j in range(40):
                        if self.cells_colors[i][j] == self.process_color:
                            self.cells_colors[i][j] = color.name()
                            self.cells[i][j].setStyleSheet(
                                f'background-color: {color.name()}')
                self.process_color = color.name()
            else:
                self.alert_color()

        if self.sender().text() == 'стена':
            ch_set = set()
            ch_set.add(self.start_color)
            ch_set.add(color.name())
            ch_set.add(self.finish_color)
            ch_set.add(self.path_color)
            ch_set.add(self.process_color)
            if len(ch_set) == 5:
                for i in range(35):
                    for j in range(40):
                        if self.cells_colors[i][j] == self.wall_color:
                            self.cells_colors[i][j] = color.name()
                            self.cells[i][j].setStyleSheet(
                                f'background-color: {color.name()}')
                self.wall_color = color.name()
            else:
                self.alert_color()
        # установлю цвет кнопки если цвет не повторяется
        if color.isValid() and len(ch_set) == 5:
            self.sender().setStyleSheet(f'background-color: {color.name()}'
                                        )
            self.sender().setFont(QFont('Century Gothic', 12))


# установлю картинку заднего фона
stylesheet = """
    MainWindow {
        background-image: url("back.jpg"); 
        background-repeat: no-repeat; 
        background-position: center;
    }
"""


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":
    # запущу прграмму
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    # создам экземляр класса
    sys.excepthook = except_hook
    window = MainWindow()
    # поменяю размер окна
    window.resize(1200, 720)
    # покажу все виджеты
    window.show()
    sys.exit(app.exec_())
