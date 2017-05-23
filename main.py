#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time

import requests
from hurry.filesize import size
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QStandardItemModel
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QAction, QApplication, QProgressDialog, QFileDialog,
                             QHBoxLayout, QLabel, QMenu, QSlider,
                             QStyleFactory, QTableWidget, QTableWidgetItem,
                             QToolButton, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager
import audio


def time_convert(time):
    seconds = time / 1000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


class vkmus(QWidget):

    def __init__(self):
        super().__init__()
        self.tracknum = 0
        self.downloader = QNetworkAccessManager()
        self.initUI()
        self.dont_autoswitch = False

    def pbutton_hnd(self):
        if self.player.state() == self.player.PausedState:
            self.player.play()
        else:
            self.player.pause()

    def set_track(self):
        self.player.setMedia(QMediaContent(QUrl(self.tracks[self.tracknum]["url"])))
        self.trackname.setText("%(artist)s - %(title)s" % self.tracks[self.tracknum])
        self.table.selectRow(self.tracknum)
        self.player.play()
        self.slider.setMaximum(int(self.tracks[self.tracknum]["duration"])*1000)
        self.tracklen.setText(time_convert(self.slider.maximum()))
        if self.tracks[self.tracknum]["cover"]:
            img = QImage()
            img.loadFromData(requests.get(self.tracks[self.tracknum]["cover"]).content)
            self.albumpic.setPixmap(QPixmap(img))
        else:
            self.albumpic.setPixmap(QPixmap())

    def next_track(self):
        if self.tracknum + 1 > len(self.tracks) - 1:
            self.tracknum = 0
        else:
            self.tracknum += 1
        self.dont_autoswitch = True
        self.set_track()
        self.dont_autoswitch = False

    def previous_track(self):
        if self.tracknum - 1 < 0:
            self.tracknum = len(self.tracks) - 1
        else:
            self.tracknum -= 1
        self.dont_autoswitch = True
        self.set_track()
        self.dont_autoswitch = False

    def create_player_ui(self):
        # Виджет плеера
        self.player = QWidget()
        self.player_body = QHBoxLayout()
        self.player.setLayout(self.player_body)
        self.playerwdt = QWidget()
        self.player.setObjectName("player")
        self.albumpic = QLabel()
        self.albumpic.setMinimumWidth(135)
        self.albumpic.setMaximumHeight(135)
        self.player_body.addWidget(self.albumpic)
        self.player_body.addWidget(self.playerwdt)
        self.playerlyt = QVBoxLayout()
        self.trackname = QLabel()
        self.trackname.setAlignment(Qt.AlignCenter)
        self.player.setMaximumHeight(135)
        self.slider = QSlider(Qt.Horizontal)
        self.tracklen = QLabel()
        self.trackpos = QLabel()
        # Кнопки управления
        self.controls = QWidget()
        self.controlslyt = QHBoxLayout()
        self.playbtn = QToolButton()
        self.prevbtn = QToolButton()
        self.nextbtn = QToolButton()
        # Позиция
        self.pos = QWidget()
        self.poslyt = QHBoxLayout()
        self.pos.setLayout(self.poslyt)
        # Иконки
        self.playbtn.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))
        self.prevbtn.setIcon(self.style().standardIcon(self.style().SP_MediaSkipBackward))
        self.nextbtn.setIcon(self.style().standardIcon(self.style().SP_MediaSkipForward))
        # Сигналы
        self.playbtn.clicked.connect(self.pbutton_hnd)
        self.prevbtn.clicked.connect(self.previous_track)
        self.nextbtn.clicked.connect(self.next_track)
        # Добавляем
        self.controlslyt.addWidget(self.prevbtn)
        self.controlslyt.addWidget(self.playbtn)
        self.controlslyt.addWidget(self.nextbtn)
        self.playerwdt.setLayout(self.playerlyt)
        self.playerlyt.addWidget(self.trackname)
        self.poslyt.addWidget(self.trackpos)
        self.poslyt.addWidget(self.slider)
        self.poslyt.addWidget(self.tracklen)
        self.playerlyt.addWidget(self.pos)
        self.playerlyt.addWidget(self.controls)
        self.controls.setLayout(self.controlslyt)
        self.main_box.addWidget(self.player)

    def state_handle(self):
        if self.player.state() == self.player.StoppedState:
            if not self.dont_autoswitch:
                self.next_track()
        elif self.player.state() == self.player.PlayingState:
            self.playbtn.setIcon(self.style().standardIcon(self.style().SP_MediaPause))
        elif self.player.state() == self.player.PausedState:
            self.playbtn.setIcon(self.style().standardIcon(self.style().SP_MediaPlay))

    def timechange(self, value):
        self.trackpos.setText(time_convert(value))

    def progress_control(self, received, total):
        self.progress.setMaximum(total)
        self.progress.setValue(received)

    def download_finished(self):
        successdialog = QMessageBox()
        successdialog.setText("Загрузка %(artist)s - %(title)s завершена!")
        successdialog.setWindowTitle("Загрузка завершена")
        successdialog.setIcon(successdialog.Information)
        with open(self.path, 'wb') as f:
            f.write(self.curdown.readAll())
        successdialog.show()
    def downmenu(self, pos):
        menu = QMenu()
        downact = menu.addAction("Скачать")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == downact:
            track = self.tracks[self.table.itemAt(pos).row()]
            self.path, _ = QFileDialog.getSaveFileName(None, "Куда скачать?",
                                                  "%(artist)s - %(title)s.mp3" % track,
                                                  "MPEG-1/2/2.5 Layer 3 (*.mp3)")
            self.curdown = self.downloader.get(QNetworkRequest(QUrl(track["url"])))
            self.progress = QProgressDialog()
            self.progress.setWindowTitle("Загрузка %(artist)s - %(title)s" % track)
            self.progress.setLabel(QLabel("Загрузка %(artist)s - %(title)s" % track))
            self.progress.canceled.connect(self.curdown.close)
            self.curdown.downloadProgress.connect(self.progress_control)
            self.curdown.finished.connect(self.download_finished)
            self.progress.show()

    def new_cookie(self, cookie):
        if cookie.name() == "remixsid":
            print("Auth complete")
            self.cookie = str(cookie.value(), 'utf-8')
            self.create_player_ui()
            self.tracks = audio.audio_get(self.cookie)
            self.web.close()
            self.log_label.close()
            self.player = QMediaPlayer()
            self.player.positionChanged.connect(self.slider.setValue)
            self.player.stateChanged.connect(self.state_handle)
            self.slider.sliderReleased.connect(self.changepos)
            self.slider.valueChanged.connect(self.timechange)
            self.table = QTableWidget()
            self.table.setColumnCount(4)
            self.table.setRowCount(len(self.tracks))
            self.table.setHorizontalHeaderLabels(["№","Трек", "Исполнитель", "Длительность"])
            self.table.setShowGrid(False)
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self.downmenu)
            i = 0
            for track in self.tracks:
                self.table.setItem(i,0,QTableWidgetItem(str(i)))
                self.table.setItem(i,1,QTableWidgetItem(track["title"]))
                self.table.setItem(i,2,QTableWidgetItem(track["artist"]))
                self.table.setItem(i,3,QTableWidgetItem(time_convert(int(track["duration"])*1000)))
                i += 1
            self.table.cellDoubleClicked.connect(self.switch_track)
            self.table.horizontalHeader().setSectionResizeMode(self.table.horizontalHeader().ResizeToContents)
            self.table.verticalHeader().setVisible(False)
            self.table.setEditTriggers(self.table.NoEditTriggers)
            self.table.setSelectionBehavior(self.table.SelectRows)
            self.table.setSelectionMode(self.table.SingleSelection)
            self.table.setSortingEnabled(True)
            self.table.setStyleSheet("""
            QTableWidget::item:hover {
                background-color:!important;
            }
            """)
            trackslen = 0
            for track in self.tracks:
                trackslen += int(track["duration"])
            self.main_box.addWidget(self.table)
            trackinfo = QLabel("%s треков, %s, примерно %s" % (
                len(self.tracks),
                time_convert(trackslen * 1000),
                size(trackslen * 128 * 192)
            ))
            trackinfo.setObjectName("trackcount")
            self.main_box.addWidget(trackinfo)

    def switch_track(self,track, _):
        self.tracknum = track - 2
        self.set_track()

    def changepos(self):
        self.player.setPosition(self.slider.value())

    def initUI(self):
        self.setStyle(QStyleFactory.create("Macintosh"))
        self.main_box = QVBoxLayout()
        self.web = QWebEngineView()
        self.web.load(QUrl("http://m.vk.com"))
        self.web.show()
        self.store = self.web.page().profile().cookieStore()
        self.store.cookieAdded.connect(self.new_cookie)
        self.setLayout(self.main_box)
        self.log_label = QLabel("Авторизуйтесь в мобильной версии ВК для начала")
        self.main_box.addWidget(self.log_label)
        self.main_box.addWidget(self.web)
        self.setGeometry(600, 600, 800, 600)
        self.setWindowTitle('VKMus')
        self.main_box.setObjectName("body")
        self.setStyleSheet("""
        #body {
            margin:0;
        }
        #player {
            border-bottom:1px solid grey;
        }
        #trackcount {
            border-top:1px solid grey;
        }
        """)
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = vkmus()
    sys.exit(app.exec_())
