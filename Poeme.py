# -*- coding: utf8 -*-

# Génère des phrases de poésie avec possibilité de choisir les rimes, le nombre de syllabes, de paragraphes, de vers etc...

# Documents nécéssaires dans le fichier :
# PoemeDB.sqlite

## Introduction
# Importations
import sqlite3
import os, sys
import tkinter as tk
from tkinter import filedialog
from tkinter import font
import random
import darkmode as dm

# Initialisations

path = sys.argv[0]
print(path)
path = "/".join(path.split("/")[:-1]) + "/Resources"
database = path + "/PoemeDB.sqlite"
symboles = ",;:…./\&'§@#!()-_$*¥€%£?"
count = 0
dark = "indigo"
light = "white"
databaseInfos = path + "/datas.sqlite"
darkmode = dm.Dark(databaseInfos, dark, light, dark)

conn = sqlite3.connect(database)
cur = conn.cursor()

# Création liste des mots possibles
motPossible = []
cur.execute("""SELECT DISTINCT ortho FROM MOTS""")
ortho = cur.fetchall()
for mot1 in ortho:
    motPossible.append(mot1[0])

# Création syllPossible : dictionnaire des syllabes possibles présentes plus de 10 fois avec les associtations API, courant vers la notation de la base de données
# Création aidephon : texte à afficher dans fenêtre "Aide Phonétique", syllabes présentes plus de 20 fois
syllPossible = dict()
aidephon = "Veuillez n'utiliser que ces symboles\n(Syllabes ou API),\nsinon l'application crash\n\nSyllabes\tCourant\tAPI\tOccurence"

cur.execute("""
SELECT dersyll, courant, API, count(*) as nboccurence
FROM SYLLABES, MOTS
WHERE SYLLABES.id = MOTS.iddersyll
GROUP BY iddersyll
HAVING COUNT(iddersyll) >= 10
ORDER BY LOWER(dersyll) ASC""")

syllaide = cur.fetchall()

for syll in syllaide:
    aidephon += "\n"
    syllPossible[syll[0]] = [syll[0]]
    syllPossible[syll[2]] = [syll[0]]
    aidephon += "\t".join(syll[:-1]) + "\t" + str(syll[-1])

conn.commit()
conn.close

## Fonctions

def analyse(nbsyll, dersyll = ''):
    """
    * Renvoie une phrase aléatoire de nbsyll-syllabes et de dernière syllabe dersyll
    * Ainsi que la dernière syllabe de cette phrase
    * Suppose que dersyll est possible et que nbsyll est un entier
    * nbsyll sera automatiquement mis entre 1 et 12
    """
    if nbsyll < 2:
        # Cas de une syllabe
        if dersyll == '':
            req = """
            AND iddersyll in (SELECT iddersyll
            FROM MOTS JOIN SYLLABES ON iddersyll = SYLLABES.id
            GROUP BY iddersyll
            HAVING COUNT(iddersyll) >= 10)"""
        else:
            req = """AND SYLLABES.dersyll = '%s'""" % dersyll

        cur.execute("""
        SELECT ortho, dersyll
        FROM MOTS JOIN SYLLABES ON iddersyll = SYLLABES.id
        WHERE nbsyll = 1
        AND length(ortho) > 3
        %s
        ORDER BY RANDOM() LIMIT 1;"""%req)
        newWords = cur.fetchone()
        nouveau = newWords[0]
        dersyll = newWords[1]

        cur.execute("""
        SELECT PONCT
        FROM PONCTUATION
        WHERE freq > (SELECT abs(random() / 10000000000000000000))
        ORDER BY random();""")

        ponct = cur.fetchone()[0]

        nouveau = nouveau[0].upper() + nouveau[1:] + ponct + "\n"
        return (nouveau, dersyll)

    if nbsyll > 12:
        # Si nbsyll trop élevé
        nbsyll = 12

    syllabe = dersyll
    cur.execute("""
    SELECT id, phrase
    FROM PHRASES
    WHERE nbsyllabe = ?
    ORDER BY RANDOM() LIMIT 1""", (nbsyll,))
    [id, phrase] = cur.fetchone()
    phraselist = phrase.split(" ")
    nouveau = ""

    for i in range(len(phraselist)):

        if i == len(phraselist) - 1 and syllabe != '':
            # Si dernier mot phrase et rime imposée :
            # Requête avec dernière syllabe
            req = """
            AND SYLLABES.dersyll = '%s'""" % syllabe
        elif i == len(phraselist) - 1:
            # Si dernier mot phrase mais pas de rime imposée :
            # Choix syllabe existant plus de 10 fois
            req = """
            AND iddersyll in (SELECT iddersyll
            FROM MOTS JOIN SYLLABES ON iddersyll = SYLLABES.id
            GROUP BY iddersyll
            HAVING COUNT(iddersyll) >= 10)"""
        else:
            # Sinon, mot au milieu de phrase :
            # Pas de contrainte sur la dernière syllabe
            req = ""

        mot = phraselist[i].lower()
        if mot in symboles:
            # Si symbole : le laisser
            nouveau += mot + " "
        else:
            if mot[-1] in symboles and mot[:-1] in motPossible:
                # Si mot suivi de symbole (ex : mot = "ciel,") :
                # Garder symbole et changer le mot
                punctInside = mot[-1] + " "
                mot = mot[:-1]

            else:
                # Si pas de symbole : ponctuation vide
                punctInside = " "

            cur.execute("""
            SELECT cgram, genre, nombre, nbsyll, verper, haspir, cvcv
            FROM MOTS
            WHERE ortho = ?
            ORDER BY freqfilms DESC LIMIT 1""", (mot,))

            info = cur.fetchone()

            if len(mot) == 1 and info[6][0] == "C":
                nouveau += phraselist[i] + "'"
                punctInside = ""

            elif info[0][:3] == "ART" or info[0][:3] == "PRO" or info[0] == "ADJ:pos":
                nouveau += phraselist[i]
                punctInside = " "

            elif (info[0][:3] == "PRE" or info[0] == "CON") and len(mot) < 4:
                # Si petite préposition : la garder
                nouveau += phraselist[i]
                punctInside = " "

            else:
                if info[0][:3] == "PRE" or info[0][:3] == "CON":
                    # Si préposition mais pas petit mot :
                    # Ne pas prendre petit préposition
                    req = """ AND length(ortho) > 3""" + req

                elif info[0][:3] == "NOM" or info[0][:3] == "ADJ" or info[0][:3] == "VER":
                    # Si nom, adj ou ver :
                    # Garder 1er lettre cons ou voy pour liaison apostrophe

                    if info[4] != '':
                        # Garder que la personne du verbe sous forme %__%
                        # Si plusieurs possibilités de conjugaison, n'en garder qu'une

                        if mot[-1] == "s" and '2s' in info[4]:
                            # Mot à la 2e personne du singulier
                            info4 = ("%2s%",)
                        elif mot[-1] != "s" and ('1s' in info[4] or '3s' in info[4]):
                            if '1s' in info[4]:
                                # Mot à la 1e personne du singulier
                                info4 = ("%1s%",)
                            else:
                                # Mot à la 3e personne du singulier
                                info4 = ("%3s%",)
                        else:
                            # Mot à une autre personne
                            info4 = ("%" + info[4].split("-")[0] + "%",)

                        info = info[:4] + info4 + info[5:]

                    req = """AND cvcv LIKE '%s'"""%(info[-1][0]+"%") + req
                cur.execute("""
                SELECT ortho, dersyll
                FROM MOTS JOIN SYLLABES ON iddersyll = SYLLABES.id
                WHERE cgram = ?
                AND genre = ?
                AND nombre = ?
                AND nbsyll = ?
                AND verper LIKE ?
                AND haspir = ?
                %s
                ORDER BY RANDOM() LIMIT 1"""%req, info[:-1])
                newWords = cur.fetchone()
                try:
                    nouveaumot = newWords[0]
                    dersyll = newWords[1]
                except TypeError:
                    # print(phraselist, mot, newWords)
                    if count < 10:
                        erreur.append(id)
                        return analyse(nbsyll, syllabe)
                    else:
                        raise RecursionError("Nombre de répétition dépassés, relance le poème")
                else:
                    # Si majuscule au milieu (ou au début) de la phrase : la garder
                    if phraselist[i][0].isupper():
                        nouveaumot = nouveaumot[0].upper() + nouveaumot[1:]

                    nouveau += nouveaumot

            nouveau += punctInside

    cur.execute("""
    SELECT PONCT
    FROM PONCTUATION
    WHERE freq > (SELECT abs(random() / 10000000000000000000))
    ORDER BY random();""")

    ponct = cur.fetchone()[0]

    nouveau = nouveau.strip(" ") + ponct + "\n"
    conn.commit()
    conn.close
    # print(id)
    return nouveau, dersyll

def poeme_texte(rimes, nbsyll):
    """
    * Génère des paragraphes de rime
    * rimes : "A_B_B_A_" = rimes embrassées, "A_B_A_B_" = rimes croisées
    * Forcer phonétique des rimes : rimes = "t@t_se_se_t@t" rime avec la phonétique donnée
    * nbsyll = [12,10,8] : 1er vers = 12 syllabes, 2e vers = 10 syllabes, 3e vers = 8 syllabes
    * Suppose rimes et nbsyll de la bonne forme (syllabes existent, nbsyll des entiers, nb lettre _ rime = len(nbsyll) )"""
    # Liste erreur : voir quelles phrases posent problème
    global erreur
    global chargeVar
    texteChargement = "Chargement ...\nVers déjà fait :\n\n"
    chargeVar.set(texteChargement)
    charge.update()
    erreur = []
    # Initialisations variables
    dictsyll = dict()
    rimes = rimes.split(" ")
    poeme = ""
    i = 0
    # Création poème
    for paragraphe in rimes:
        for verssyll in paragraphe.split("_")[:-1]:
            if "." in verssyll:
                phrase = analyse(nbsyll[i], verssyll.strip("."))
            elif verssyll in dictsyll:
                phrase = analyse(nbsyll[i], dictsyll[verssyll])
            else:
                phrase = analyse(nbsyll[i])
                dictsyll[verssyll] = phrase[1]
            count = 0
            texteChargement += forme[i] + "\n"
            chargeVar.set(texteChargement)
            charge.update()
            poeme += phrase[0]
            # print(forme[i])
            i += 1
        # print()
        texteChargement += "\n"
        poeme += "\n"
    # Fin poème : un point
    chargeVar.set("")
    poeme = poeme.strip("\n")[:-1].strip(" ") + "."
    return poeme

## Fonctions pour application

def Generer(event = None):
    """
    * Génère une nouvelle fenêtre avec le poème quand bouton générer cliqué
    * Si bouton Sauvegarder cliqué :
        * Créer le fichier nom_de_fichier trouvé dans l'entry
        * Si vide, alors créer poeme.txt dans répertoire courant
        * Supprime son contenu si fichier existe déjà
        * Écrit le contenu de la fenêtre texte ouverte
        * Ouvre le fichier"""
    def sauver():
        """
        * Créer le fichier nom_de_fichier trouvé dans l'entry
        * Si vide, alors créer poeme.txt dans répertoire courant
        * Supprime son contenu si fichier existe déjà
        * Écrit le contenu de la fenêtre texte ouverte
        * Ouvre le fichier quand bouton Sauvegarder cliqué"""
        nom_de_fichier = filedialog.asksaveasfilename(title = "Choisissez un dossier",defaultextension=".txt", filetypes = (("Texte", "*.txt"),))
        try:
            phrase = poemetext.get('1.0', 'end-1c')
            with open(nom_de_fichier, 'w') as f:
                f.write(phrase)
            nom_de_fichier = "\"" + nom_de_fichier + "\""
            os.popen("open " + nom_de_fichier)
        except FileNotFoundError:
            None

    # Création fenêtre de chargement (qui se supprime lorsque texte chargé)
    global charge
    global chargeVar
    try:
        # Monter fenêtre chargement
        charge.deiconify()
        roots.append(charge)
        darkmode.lancer(roots)
    except tk.TclError:
        # Si elle a été fermé : la créer
        charge = tk.Toplevel(root)
        chargeVar = tk.StringVar()
        charge.title("Chargement")
        chargetext = tk.Label(charge, textvariable = chargeVar , font = police)
        chargetext.grid(column = 0, row = 0)
        charge.withdraw()
        roots.append(charge)
        darkmode.lancer(roots)

    # Récupération Entry
    total = labvar.get().split("\n")

    nbsyll = []
    forme = ""
    for formeVers in total:
        if formeVers != "":
            nbsyll.append(formeVers.count("_") + 1)
            forme += formeVers.split(" ")[-1] + "_"
        else:
            forme += " "
    try:
        texte = poeme_texte(forme, nbsyll)

    except RecursionError:
        global previ
        global erreur1
        try:
            # Montrer fenêtre
            previ.deiconify()
        except tk.TclError:
            # Créer fenêtre si n'existe pas (elle a été fermée)
            previ = tk.Toplevel(root)
            previ.title('Prévisualisation')
            titre = tk.Label(previ, textvariable = titreVar , font = police)
            err1.set("Erreur, Veuillez recommencer")
            erreur1 = tk.Label(previ, textvariable = err1, font = police)
            erreur2 = tk.Label(previ, textvariable = err2,font = policelittle)
            exemple = tk.Label(previ, textvariable = labvar , font = police, justify='left')
            generer = tk.Button(previ, text = "Générer", command = Generer, font = police)

            erreur1.config(fg='red')
            titre.grid(column = 0, row = 0)
            exemple.grid(column = 0, row = 10)
            erreur1.grid(column = 0, row = 20)
            erreur2.grid(column = 0, row = 30)
            generer.grid(column = 0, row = 40)

            roots.append(previ)
            darkmode.lancer(roots)

        else:
            err1.set("Erreur, Veuillez recommencer")
            erreur1.grid(column = 0, row = 20)

    else:
        # Création nouvelle fenêtre avec poème
        poeme = tk.Toplevel(root)

        nblignes = len(nbsyll) + forme.count(" ")
        if nblignes > 30:
            # texte trop grand : fenêtre max 30 lignes
            nblignes = 30
        poemetext = tk.Text(poeme, height = nblignes, width = 48, font = police)
        poemetext.grid(column = 0, row = 0)

        # Création Bouton sauvegarde
        sauvegarder = tk.Button(poeme, command = sauver, text = "Sauvegarder", font = police)
        sauvegarder.grid(column = 0, row = 1)

        # Insertion de poème et détruit fenêtre chargement
        poemetext.insert(1.0, texte)

        roots.append(poeme)
        darkmode.lancer(roots)

    finally:
        try:
            # Cacher fenêtre chargement
            charge.withdraw()
        except tk.TclError:
            # Elle a été fermé : on ne la cache pas
            None

def Prev1(event = None):
    """Touche previsualisation cliqué"""
    titreVar.set("Prévisualisation")
    Prev()

def Prev():
    """Affiche la fenêtre de prévisualisation"""
    global previ
    global erreur1
    global erreur2
    global exemple
    global generer
    try:
        # Montrer fenêtre
        previ.deiconify()
    except tk.TclError:
        # Créer fenêtre si n'existe pas (elle a été fermée)
        previ = tk.Toplevel(root)
        previ.title('Prévisualisation')
        titre = tk.Label(previ, textvariable = titreVar , font = police)

        erreur1 = tk.Label(previ, textvariable = err1, font = police)
        erreur2 = tk.Label(previ, textvariable = err2,font = policelittle)
        exemple = tk.Label(previ, textvariable = labvar , font = police, justify='left')
        generer = tk.Button(previ, text = "Générer", command = Generer, font = police)

        erreur1.config(fg='red')
        titre.grid(column = 0, row = 0)
        exemple.grid(column = 0, row = 10)
        erreur1.grid(column = 0, row = 20)
        erreur2.grid(column = 0, row = 30)
        generer.grid(column = 0, row = 40)

    # Enlever textes possiblement affiché
    erreur1.grid_remove()
    erreur2.grid_remove()
    exemple.grid_remove()
    generer.grid_remove()

    # Dictionnaire des noms de syllabes correspondant aux syllabes données
    syllname = dict()

    # Récupération Entry
    global forme
    forme = formeEntry.get()
    rime = phonEntry.get()
    sylltaille = syllEntry.get()

    if len(forme) != 0:
        if len(sylltaille) != 0:
            # Création liste nbsyll
            sylltaille = sylltaille.split(",")
            nbsyll  = [""]* len(forme.replace(" ", ""))
            for syllUnit1 in sylltaille:
                syllUnit2 = syllUnit1.replace(" ", "").split("=")
                try:
                    int(syllUnit2[0])
                    int(syllUnit2[1])
                except ValueError:
                    # Si problème dans la façon dont est la taille des syllabes
                    err1.set(syllUnit1 + " est mal écrit")
                    err2.set("Veuillez respecter la mise en forme :\n 1 = 12, 2 = 6 ...")
                    erreur1.grid()
                    erreur2.grid()
                    labvar.set("")
                    previ.update()
                    return None
                try:
                    if int(syllUnit2[1]) > 12:
                        # Si nb syllabe dépasse 12
                        err1.set("Attention, nombre de syllabes max dépassés\n(max = 12)")
                        erreur1.grid()
                        nbsyll[int(syllUnit2[0]) - 1] = "_ " * 11
                    elif int(syllUnit2[1]) < 1:
                        # Si nb syllabe inférieur à 1
                        err1.set("Attention, nombre de syllabes min = 1")
                        erreur1.grid()
                        nbsyll[int(syllUnit2[0]) - 1] = " "
                    elif int(syllUnit2[1]) == 1:
                        # Si nb syllabe = 1
                        nbsyll[int(syllUnit2[0]) - 1] = " "
                    else:
                        # Sinon
                        nbsyll[int(syllUnit2[0]) - 1] = "_ " * (int(syllUnit2[1]) - 1)
                except IndexError:
                    # Si nb syllabe dépasse nombre vers
                    err1.set("Vous avez dépassé le nombre de\nvers donnés dans  la forme")
                    erreur1.grid()
                    previ.update()
                    return None
            # Pas de probleme : créer les str avec les _ suivant le nb de syllabes
            if nbsyll[0] == "":
                nbsyll[0] = "_ " * 11
            elif nbsyll[0] == " ":
                nbsyll[0] = ""
            for a in range(1, len(nbsyll)):
                if nbsyll[a] == "":
                    nbsyll[a] = str("_ " * (nbsyll[a-1].count("_")))
        else:
            # Si aucune info sur le nombre de syllabe donnée
            nbsyll = ["_ " * 11] * len(forme.replace(" ", ""))
        texte = ""
        if len(rime) == 0:
            # Sans rimes forcées, juste avec forme
            j = 0
            for i in range(len(forme)):
                if forme[i] == " ":
                    texte += '\n'
                else:
                    texte += str(nbsyll[j]) + forme[i] + "\n"
                    j+=1
        else:
            # Avec rimes forcées
            for rimeUnit in rime.split(","):
                a = rimeUnit.replace(" ", "").split("=")
                if a[0] in forme:
                    if a[1] in syllPossible:
                        syllname[a[0]] = syllPossible[a[1]][0]
                    else:
                        # Si syllabe pas possible
                        err1.set("Les rimes sont mal écrites")
                        err2.set(str(a[1]) + " n'existe pas\n")
                        erreur1.grid()
                        erreur2.grid()
                        previ.update()
                        return None
                else:
                    # Si erreur sur la façon dont sont données les rimes
                    err1.set("Les rimes sont mals écrites")
                    err2.set("Veuillez respecter la mise en forme :\nA=t@t, B=se …\n(avec les bons symboles correspondants\nà ceux donnés dans forme)")
                    erreur1.grid()
                    erreur2.grid()
                    previ.update()
                    return None

            j = 0
            for i in range(len(forme)):
                if forme[i] == " ":
                    texte += '\n'
                else:
                    if forme[i] in syllname:
                        texte += str(nbsyll[j]) + syllname.get(forme[i]) + ".\n"
                    else:
                        texte += str(nbsyll[j]) + forme[i] + "\n"
                    j += 1

    else:
        # Si aucune forme n'est donnée
        err1.set("Vous n'avez donné aucune forme")
        erreur1.grid()
        previ.update()
        return None

    forme = forme.replace(" ", "") # Variable globale de la forme pour être afficheé dans chargement

    # Si aucun problème, insertion bouton et texte de prévisualisation
    generer.grid()
    exemple.grid()

    labvar.set(texte)
    previ.update()

    # Touche Entrer -> bouton generer
    previ.bind("<Return>", Generer)

    roots.append(previ)
    darkmode.lancer(roots)

def aide():
    """
    * Création fenêtre d'aide phonétique
    * Lorsque bouton Aide Phonétique cliqué"""
    aide = tk.Toplevel(root)
    aide.title('Phonétique')
    aideText = tk.Text(aide, height = 20, width = 34, font = police)
    aideText.insert(1.0, aidephon)
    aideText.grid(column = 0, row = 0)
    roots.append(aide)
    darkmode.lancer(roots)

def sonnet():
    """Sonnet automatique"""
    titreVar.set("Sonnet")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "ABBA CDDC EEF GGF")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=12")
    Prev()

def haiku():
    """Haiku automatique"""
    titreVar.set("Haïku")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "ABC")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=5, 2=6, 3=5")
    Prev()

def blason():
    """Blason automatique"""
    titreVar.set("Blason")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "AABAABBB ABBA")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=4, 9=8")
    Prev()

def ballade():
    """Ballade automatique"""
    titreVar.set("Ballade")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "ABAB BC CDCD")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=10")
    Prev()

def rondeau():
    """Rondeau automatique"""
    titreVar.set("Rondeau")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "ABBA ABAB ABBAA")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=8")
    Prev()

def triangle():
    """Triangle automatique"""
    titreVar.set("Triangle")
    formeEntry.delete(0,tk.END)
    formeEntry.insert(0, "ABCD EFGH IJKL")
    syllEntry.delete(0,tk.END)
    syllEntry.insert(0, "1=1, 2=2, 3=3, 4=4, 5=5, 6=6, 7=7, 8=8, 9=9, 10=10, 11=11, 12=12")
    Prev()

## Création fenêtre application

root = tk.Tk()
root.title('Poème')

# Taille de la fenetre
fenetre = tk.Canvas(root, width = 500, height = 350)
fenetre.config(highlightthickness = 0)
fenetre.pack()

# Police utilisée dans application
police = font.Font(root, size = 20, family = 'Arial')
policelittle = font.Font(root, size = 14, family = 'Arial')

# Création widgets sur fenêtre principale
sonnetButton = tk.Button(root, text = "Sonnet", command = sonnet, font = police)
haikuButton = tk.Button(root, text = "Haïku", command = haiku, font = police)
blasonButton = tk.Button(root, text = "Blason", command = blason, font = police)
balladeButton = tk.Button(root, text = "Ballade", command = ballade, font = police)
rondeauButton = tk.Button(root, text = "Rondeau", command = rondeau, font = police)
triangleButton = tk.Button(root, text = "Triangle", command = triangle, font = police)

colonneTypeLabel = tk.Label(root, text = "Type existant\nde poème :", font = police)
formeTitleLabel = tk.Label(root, text = "Forme (ABBA ...)", font = police)
formeEntry = tk.Entry(root, font = police)
syllEntry = tk.Entry(root, font = police)
syllTitleLabel = tk.Label(root, text = "Syllabes : 1=12, 2 = 6" , font = police)
syllAideLabel = tk.Label(root, text = "Veuillez respecter exactement la mise en forme", font = policelittle)
phonTitleLabel = tk.Label(root, text = "Phonétique : A=t@t, B=se …", font = police)
phonAideLabel = tk.Label(root, text = "Veuillez respecter exactement la mise en forme", font = policelittle)
phonEntry = tk.Entry(root, font = police)
prevButton = tk.Button(root, text = 'Prévisualiser', command = Prev1, font = police)
phonAideButton = tk.Button(root, text = 'Aide Phonétique', command = aide, font = police)

darkVar = tk.IntVar()
darkCheck = tk.Checkbutton(root, text = 'Mode sombre', variable = darkVar, onvalue=True, offvalue=False, font = police, command = darkmode.switch)

# Touche entrer cliqué
root.bind("<Return>", Prev1)

# Apparition widget
colonne = (80, 300)

# Colonne 1

ligne = 40
fenetre.create_window(colonne[0], ligne, window = colonneTypeLabel)
ligne += 50
fenetre.create_window(colonne[0], ligne, window = sonnetButton)
ligne += 30
fenetre.create_window(colonne[0], ligne, window = haikuButton)
ligne += 30
fenetre.create_window(colonne[0], ligne, window = balladeButton)
ligne += 30
fenetre.create_window(colonne[0], ligne, window = rondeauButton)
ligne += 30
fenetre.create_window(colonne[0], ligne, window = blasonButton)
ligne += 30
fenetre.create_window(colonne[0], ligne, window = triangleButton)
ligne += 50
fenetre.create_window(colonne[0], ligne, window = darkCheck)
# Colonne 2

ligne = 30
fenetre.create_window(colonne[1], ligne, window = formeTitleLabel)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = formeEntry)
ligne += 40
fenetre.create_window(colonne[1], ligne, window = syllTitleLabel)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = syllAideLabel)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = syllEntry)
ligne += 40
fenetre.create_window(colonne[1], ligne, window = phonTitleLabel)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = phonAideLabel)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = phonEntry)
ligne += 40
fenetre.create_window(colonne[1], ligne, window = prevButton)
ligne += 30
fenetre.create_window(colonne[1], ligne, window = phonAideButton)

# Fenêtre de chargement
charge = tk.Toplevel(root)
chargeVar = tk.StringVar()
charge.title("Chargement")
chargetext = tk.Label(charge, textvariable = chargeVar , font = police)
chargetext.grid(column = 0, row = 0)
charge.withdraw()

# Fenêtre de prévisualisation
labvar = tk.StringVar()
err1 = tk.StringVar()
err2 = tk.StringVar()
ex = tk.StringVar()

previ = tk.Toplevel(root)
previ.title('Prévisualisation')
titreVar = tk.StringVar()
titre = tk.Label(previ, textvariable = titreVar , font = police)
titreVar.set("Prévisualisation")

erreur1 = tk.Label(previ, textvariable = err1, font = police)
erreur2 = tk.Label(previ, textvariable = err2,font = policelittle)
exemple = tk.Label(previ, textvariable = labvar , font = police, justify='left')
generer = tk.Button(previ, text = "Générer", command = Generer, font = police)

erreur1.config(fg='red')
titre.grid(column = 0, row = 0)
exemple.grid(column = 0, row = 10)
erreur1.grid(column = 0, row = 20)
erreur2.grid(column = 0, row = 30)
generer.grid(column = 0, row = 40)

roots = [root]
darkmode.lancer(roots, darkCheck)

previ.withdraw()

# Création fenêtre
root.mainloop()
