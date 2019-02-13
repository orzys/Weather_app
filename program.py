#!/usr/bin/python
# -*- coding: utf-8 -*-

#biblioteki pythonowe
from __future__ import unicode_literals #polskie znaki
import numpy as np
import sys, random
from urllib.request import urlopen
from enum import Enum
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt
import json


#biblioteka PyQT

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class WzglednaData(Enum):
    Dzis=0
    Jutro=1
    Pojutrze=2

class MainWindow(QMainWindow):
    
    def __init__(self, app:QApplication):
        super().__init__()

        # rodzic okna
        self.app=app

        # ustawienia
        self.data=datetime.today()
        self.miasto='Elblag,pl'
        self.prognoza_na=WzglednaData.Jutro

        # interpolacja
        self.godziny=[]
        self.temp_przed=[]
        self.temp_po=[]

        # klucz do api OpenWeatherMap
        self.klucz_do_api='1784fcecb8d4c6cb640c19be37f4f265'


        self.zaladuj_ui()

        print('\nProgram gotowy')


    def zaladuj_ui(self):

        from PyQt5 import uic
        # wczytywanie ui z pliku
        uic.loadUi('okienko.ui', self)
        # ustawianie stylu
        self.app.setStyle(QStyleFactory.create('Fusion'))

        self.de_data.setDate(QDate(self.data.year, self.data.month, self.data.day))


    def rb_zmianaPrognozyNa(self):

        if self.rb_dzis.isChecked(): self.prognoza_na = WzglednaData.Dzis
        elif self.rb_jutro.isChecked(): self.prognoza_na = WzglednaData.Jutro
        elif self.rb_pojutrze.isChecked(): self.prognoza_na = WzglednaData.Pojutrze

        print('prognoza na:',str(self.prognoza_na))


    def le_zmianaMiasta(self, nowe_miasto):
        print('miasto:',nowe_miasto)

        
    def de_zmianaDaty(self, nowa_data):
        print('data:',nowa_data)

        
    def btn_sprawdzKlik(self):
        self.pobierz_dane(self.prognoza_na)
        self.interpolacja()
        self.pokaz_wykresy()


\

    def pobierz_dane(self, prognoza_na:WzglednaData):

        # kasujemy poprzednie dane:
        self.godziny_przed=[]
        self.temp_przed=[]

        # generujemy zapytanie do open weather map
        api_zapytanie = "http://api.openweathermap.org/data/2.5/forecast?APPID=%s&q=%s&mode=json&units=metric" % (self.klucz_do_api,self.miasto)

        # pobieramy dane:
        prognozy_z_OWM = urlopen(api_zapytanie).read().decode('utf-8')
        prognozy_z_OWM = json.loads(prognozy_z_OWM)['list']


        # ustalamy jaka data nas interesuje:

        interesujaca_nas_data = self.data

        if self.prognoza_na is WzglednaData.Dzis:
            pass
        elif self.prognoza_na is WzglednaData.Jutro:
            interesujaca_nas_data = self.data + timedelta(days=1)
        elif self.prognoza_na is WzglednaData.Pojutrze:
            interesujaca_nas_data = self.data + timedelta(days=2)
        else:
            interesujaca_nas_data = datetime.data.today()


        # Filtrujemy dane na te z interesująca nas prognozą...

        for prognoza in prognozy_z_OWM:

            # Pobrane daty są w formacie YYYY-MM-DD HH:MM:SS
            data_prognozy = strdate_to_datetime(prognoza['dt_txt'])

            if data_prognozy.year == interesujaca_nas_data.year and \
               data_prognozy.month == interesujaca_nas_data.month and \
               data_prognozy.day == interesujaca_nas_data.day:

                # ...wyciągamy godziny do listy self.godziny_przed
                self.godziny_przed.append(data_prognozy.hour)

                # ...oraz odpowiadające im temperatury do listy self.temp_przed
                self.temp_przed.append(prognoza['main']['temp'])

        print('\n'+'#'*10,'Pobrane dane:','#'*10+'\n')
        pprint({'godziny': self.godziny_przed, 'temperatury': self.temp_przed})


    def interpolacja(self):

        # kasujemy poprzednie dane:
        self.godziny_po=[]
        self.temp_po=[]

        # zagęszczamy godziny
        self.godziny_po=np.arange(1,24,1)

        # interpolacja
        self.temp_po = interp_lagrange(self.godziny_przed, 
                                       self.temp_przed,
                                       self.godziny_po)

        print('\n'+'#'*10,'Dane po interpolacji:','#'*10+'\n')
        pprint({'godziny': self.godziny_po, 'temperatury': self.temp_po})


    def pokaz_wykresy(self):

        plt.title('Temperatura na '+str(self.prognoza_na))
        plt.ylabel('temperatura [st. C]')
        plt.xlabel('godzina')

        # zaznaczamy punkty danych przed interpolacją
        plt.plot(self.godziny_przed, self.temp_przed, 'ro', label='przed')

        # rysujemy prostą
        plt.plot(self.godziny_po, self.temp_po, label='po')

        plt.legend()
        plt.show()



def strdate_to_datetime(strdate:str):
    return datetime.strptime(strdate, "%Y-%m-%d %H:%M:%S")

def interplin2p(x, xi, yi, xil, yil):
    """Funkcja implementuje wzór na interpolacje liniowa w punkcie x.
    Parametry:
    xi - współrzędna x pierwszego punktu
    yi - współrzędna y pierwszego punktu
    xil - współrzędna x drugiego punktu
    yil - współrzędna y drugiego punktu
    """
    return yi+(yil-yi)*(x-xi)/(xil-xi)

def interplinvect(X_do_interp, X_raw, Y_raw):
    """Funkcja implementuje algorytm interpolacji liniowej dla danych z wektora x.
    Wartosci referencyjne xi, yi i xil, yil znajduja sie w tablicy xyvect.
    """
    xinterp, yinterp = [], []
    for xk in X_do_interp:
        N = len(X_raw)
        for i in range(0, N-1):
            if(xk>=X_raw[i]):# and xk<X_raw[i+1]):
                xinterp.append(xk)
                yinterp.append(interplin2p(xk, X_raw[i], Y_raw[i], X_raw[i+1], Y_raw[i+1]))
            i += 1
    return (xinterp, yinterp)

def interp_lagrange(X_raw, Y_raw, X_do_interp):
    """Interpolacja wielomianowa Lagrange'a
    x - argument funkcji
    y - wartosc funkcji
    xval - zadana wartosc argumentu

    ret - wartosc interpolowana funkcji
    """
    products = 0
    yval = 0
    for i in range(len(X_raw)):
        products = Y_raw[i]
        for j in range(len(X_raw)):
            if i != j:
                products *= (X_do_interp-X_raw[j])/(X_raw[i]-X_raw[j])
        yval += products
    return yval

        
if __name__ == '__main__':

    app = QApplication(sys.argv)
    okno = MainWindow(app)
    okno.show()

    sys.exit(app.exec_())