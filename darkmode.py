"""
Mode sombre dans projet python

Module pour ajouter facilement un mode sombre dans un projet tkinter python
"""

import tkinter as tk
import sqlite3

class Dark:
    """Classe qui crée un mode sombre qu'il applique sur les racines données
    Utilise une base de donnée pour se souvenir de la case cochée
    Sinon : ne se souvient pas
    """


    def __init__(self, database = None, text = None, back = None, dark = None, roots = []):
        """Initialisation :

            * database : base de donnée pour stocker les infos de mode selectionné
                si rien : ne sauvegarde pas

            * text, back, dark : couleur pour le text, l'arrière plan et couleur définie comme sombre

            * roots : racines où l'on souhaite appliquer le mode

        S'utilise de la manière suivante:

        Créez votre objet darkmode:

            darkmode = Dark(database, dark, light, dark)

        Associez le checkButton à la fonction :

            checkButton = tk.Checkbutton(root, ... , command = darkmode.DarkMode)

        Lancez le mode :
            darkmode.lancer(roots, checkButton)

        """


        # Valeurs par défaut
        if back is None:
            back = "white"
        if text is None:
            text = "black"
        if dark is None:
            dark = "black"

        self._database = database

        if database is not None:
            # Si base de données

            conn = sqlite3.connect(database)
            cur = conn.cursor()
            try:
                # Si base de données existe

                cur.execute("""SELECT text, back, dark FROM INFOS;""")
                textDB, backDB, darkDB = cur.fetchone()
                # Si valeurs différentes:
                # Changer valeurs dans base de données
                if textDB not in (back, text):
                    cur.execute("""UPDATE INFOS SET text = ?;""", (text,))
                if backDB not in (back, text):
                    cur.execute("""UPDATE INFOS SET back = ?;""", (back,))
                if backDB not in (back, text):
                    cur.execute("""UPDATE INFOS SET dark = ?;""", (dark,))

            except sqlite3.OperationalError:

                # Création base de données

                cur.execute("""
                    CREATE TABLE INFOS(
                    id INTEGER NOT NULL UNIQUE,
                    text VARCHAR(79),
                    back VARCHAR(79),
                    dark VARCHAR(79),
                    PRIMARY KEY(id AUTOINCREMENT));""")

                cur.execute("""
                    INSERT INTO
                    INFOS
                    (text, back, dark)
                    VALUES(?, ?, ?);""",(text, back, dark))


            # Récuperer valeurs base de données
            cur.execute("""SELECT text, back, dark FROM INFOS;""")

            conn.commit()

            text, back, dark = cur.fetchone()

            conn.close

        # Attiribution attibuts objet

        self._text = text
        self._back = back
        self._dark = dark

        # Liste des widgets 'enfants' des racines
        toChange = []
        for root in roots:
            toChange.append(root)
            toChange += list(root.children.values())

        self._roots = toChange


    def _get_text(self):
        """Retourne la valeur de la couleur du texte"""
        return self._text


    def _get_dark(self):
        """Retourne la valeur de la couleur sombre"""
        return self._dark


    def _get_back(self):
        """Retourne la valeur de la couleur d'arrière plan"""
        return self._back


    def _get_roots(self):
        """Retourne la valeur de la liste des widgets à changer"""

        return self._roots


    def _get_data(self):
        """Retourne la valeur de la base de données"""

        return self._database


    def _set_text(self, value):
        """Modifie la valeur de la couleur de texte"""

        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        cur.execute("""UPDATE INFOS SET text = ?;""", (value,))
        conn.commit()
        conn.close

        self._text = value


    def _set_back(self, value):
        """Modifie la valeur de la couleur d'arrière plan"""

        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        cur.execute("""UPDATE INFOS SET back = ?;""", (value,))
        conn.commit()
        conn.close

        self._back = value


    def _set_roots(self, value):
        """Modifie la valeur de la liste des widgets à changer"""

        toChange = []
        for root in value:
            toChange.append(root)
            toChange += list(root.children.values())

        self._roots = toChange


    def _set_data(self, value):
        """Modifie la valeur de la base de données"""

        self._data = value


    def _set_dark(self, value):
        """Modifie la valeur de la couleur sombre"""

        self._dark = value


    def _del_text(self, value):
        """Supprime la valeur de la couleur de texte"""

        print("Impossible de supprimer la couleur de texte")
        return None


    def _del_back(self, value):
        """Supprime la valeur de la couleur d'arrière plan"""

        print("Impossible de supprimer la couleur d'arrière plan")
        return None


    def _del_roots(self, value):
        """Supprime la valeur de la liste des widgets à changer"""

        print("Impossible de supprimer la liste des widgets à changer")
        return None


    def _del_data(self, value):
        """Supprime la valeur de la liste des widgets à changer"""

        print("Impossible de supprimer la base de données")
        return None


    def _del_dark(self, value):
        """Supprime la valeur de la liste des widgets à changer"""

        print("Impossible de supprimer la couleur sombre")
        return None


    back = property(_get_back, _set_text, _del_text)
    text = property(_get_text, _set_back, _del_back)
    roots = property(_get_roots, _set_roots, _del_roots)
    database = property(_get_data, _set_data, _del_data)
    dark = property(_get_dark, _set_dark, _del_dark)


    def check(self, darkCheckButton):
        """Cocher ou non le checkbutton:
            Si arrière plan vaut la couleur sombre : alors on est en mode sombre"""

        if self.back == self.dark:
            darkCheckButton.select()
        else:
            darkCheckButton.deselect()


    def DarkMode(self):
        """Applique le mode sombre ou lumineux"""

        back = self.back
        text = self.text

        for widgets in self.roots:

            try:
                try:
                    widgets.configure(selectbackground = (lambda : "light" if back == "white" else "")()+ "grey")
                except tk.TclError : None
                try:
                    widgets.configure(fg = text)
                except tk.TclError : None
                try:
                    widgets.configure(bg = back)
                except tk.TclError : None
                try:
                    widgets.configure(highlightbackground = back)
                except tk.TclError : None
                try:
                    widgets.configure(insertbackground = text)
                except tk.TclError : None

            except tk.TclError:
                pass
    def switch(self):
        """Inverse les couleurs"""

        self.text, self.back = self.text, self.back
        self.DarkMode()


    def lancer(self, roots, darkCheck = None):
        """Lance le mode sombre sans switcher les couleurs"""

        self.roots = roots

        self.DarkMode()
        if darkCheck is not None:
            self.check(darkCheck)

