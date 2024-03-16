## Numéro d'équipe : 7
## Bouh Abdillahi (Matricule : 1940646)
## Vincent Yves Nodjom (Matricule : 1944011)
## Équipe : 7
## Github link : https://github.com/konoDioDA253/ELE8702-H24-Lab3
import sys
import math
import yaml
import random
import os
import argparse
import subprocess
import matplotlib.pyplot as plt
import numpy as np
from pathloss_3gpp_eq7 import *

# Variables GLOBAL
infini = float('inf') #définition de l'infini
# Numero propres a l'équipe
numero_equipe = '7'
numero_lab = '3'
# Nom des fichiers a ecrire dont le nom est absent du fichier de cas
pathloss_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_pl.txt"
assoc_ues_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_assoc_ue.txt"
assoc_antennas_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_assoc_ant.txt"
transmission_ant_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_transmission_ant.txt"
transmission_ue_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_transmission_ue.txt"
pdf_graph_file_name = "lab"+numero_lab+"_eq"+numero_equipe+"_graphiques.pdf"
# Structure attendue du fichier de cas
yaml_structure_message = """
ETUDE_PATHLOSS :
    PATHLOSS :
        model : [3gpp, okUmura]
        scenario : [RMa, UMa, UMi, urban_small ...] 
    ANT_COORD_GEN : [g]  
    UE_COORD_GEN : [a]   
    COORD_FILES :
        read : [fichier_lire.txt]
        write : [fichier_ecrire.txt]
    DEVICES :
        Antenna4 :
            number : [nombre_d_antennes]
        UE1-App1 :
            number : [nombre_d_UEs]
        ...  # Ajoutez ici d'autres dispositifs si nécessaire
    GEOMETRY :
        Surface :
            rectangle :
                length : [longueur_en_mètres]
                height : [hauteur_en_mètres]
    VISIBILITY :
        read : [fichier_visibility.txt]  # Fichier contenant les informations NLOS
   CLOCK : 
      tstart : (temps initial)
      tfinal : (temps final) #ms 
      dt : (pas de temps)      #ms 
      read : [lab3_eq7_segments.txt]
"""

# Germe de toutes les fonctions aléatoires
random.seed(123)

# Cette classe est utilise pour repertorier les caracteristiques d'une antenne 
class Antenna:

     def __init__(self, id):
        self.id = id          #id de l'antenne (int)
        self.frequency = None # Antenna frequency in GHz
        self.height = None    # Antenna height
        self.group = None     # group défini dans la base de données (str)
        self.coords = None    # tuple contenant les coordonnées (x,y) 
        self.assoc_ues = []   # liste avec les id des UEs associés à l'antenne
        self.scenario = None  # pathloss scénario tel que lu du fichier de cas (str)
        self.gen = None       # type de géneration de coordonnées: 'g', 'a', etc. (str)
        # Attributs rajoutes par notre equipe
        self.type = None      # Type de l'antenne
        self.name = None      # Nom de l'Antenne
        self.gain = None      # Gain de l'antenne
        self.nbits = []       # Nombre de bits recus a chaque dt
        self.live_ues = []    # Regroupement des ID des ues qui auront transmis a chaque dt
    
# Cette classe est utilise pour repertorier les caracteristiques d'une UE 
class UE:

     def __init__(self, id, app_name):
        self.id= id           # id de l'UE (int)
        self.height = None    # UE height
        self.group = None     # group défini dans la base de données (str)
        self.coords=None      # tuple contenant les coordonnées (x,y) 
        self.app=app_name     # nom de l'application qui tourne dans le UE (str)
        self.assoc_ant=None   # id de l'antenne associée à l'UE (int)
        self.los = True       # LoS ou non (bool)
        self.gen = None       # type de géneration de coordonnées: 'g', 'a', etc. (str)
        # Attributs rajoutes par notre equipe
        self.type = None      # Type de l'UE
        self.name = None      # Nom de l'UE
        self.TX_rate = None   # Debit de l'application de l'UE
        self.nbits = []       # Nombre de bits envoyes a chaque dt
        self.start_TX = []    # Liste des temps de debuts de transmission de paquets
        self.end_TX = []      # Liste des temps de fins de transmission de paquets

# Cette classe est utilise pour repertorier tous les pathloss calculer avec les antenne et les ues utilisés
class Pathloss:

     def __init__(self, id_ue, id_ant):
        self.id_ue = id_ue   # ID de l'ue
        self.id_ant = id_ant # ID de l'antenne
        self.los = None # LoS ou non (bool)
        self.value = None   # Valeur du pathloss

# Fonction permettant d'afficher un message d'erreur et de stopper le programme
# Nbre de param : 2 (msg = message , code = code d'erreur)
def ERROR(msg , code = 1):
    print("\n\n\nERROR\nPROGRAM STOPPED!!!\n")
    if msg:
        print(msg)
    print(f"\n\texit code = {code}\n\n\t\n")
    sys.exit(code)

# Fonction permettant de creer une grille pour la generation des coordonnees d'antenne
# Arguments : 5 (lh = longeur horizontal, lv = longeur vertival, N = nombre total de point , nh = nbre de point en horizontal, nv = nbre de point en vertical)
# Valeur de retour : coords = couple de coordonees
def fill_up_the_lattice(N, lh, lv, nh, nv):
    """Function appelée par get_rectangle_lattice_coords()"""
    
    def get_delta1d(L, n):
        return L/(n + 1)
    
    coords = []
    deltav = get_delta1d(lv, nv)
    deltah = get_delta1d(lh, nh)
    line = 1
    y = deltav
    count = 0
    while count < N:
        if count + nh < N:
            x = deltah
            for  i in range(nh):
                # Fill up the horizontal line
                coords.append((x,y))
                x = x + deltah
                count += 1
            line += 1
        else:
            deltah = get_delta1d(lh, N - count)
            x = deltah
            for i in range(N - count):
                # Fill up the last horizontal line
                coords.append((x,y))
                x = x + deltah
                count += 1
            line += 1
        y = y +deltav
    return coords

# Fonction utilisee dans la generation de coordonnees des antennes
# Nbre de param: 6 (lh = longeur horizontal, lv = longeur vertival, N = nombre total de point ,np = nbre de point, nh = nbre de point en horizontal, nv = nbre de point en vertical)
# valeur de retour: coords = coordonnees
def get_rectangle_lattice_coords(lh, lv, N, Np, nh, nv):
    """Function appelee par gen_lattice_coords()"""
    
    if Np > N:
        coords = fill_up_the_lattice(N, lh, lv, nh, nv)
    elif Np < N:
        coords = fill_up_the_lattice(N, lh, lv, nh, nv + 1)
    else:
        coords = fill_up_the_lattice(N, lh, lv, nh, nv)
    return coords

# Fonction utilisee dans la generation de coordonnees des antennes
def gen_lattice_coords(terrain_shape: dict, N: int):
    """Génère un ensemble de N coordonnées placées en grille 
       sur un terrain rectangulaire
    
       Args: terrain_shape: dictionary {'rectangle': {'length' : lh,
                                                   'height' : lv}
           lh and lv are given in the case file"""
    #CETTE FONCION EST OBLIGATOIRE POUR L'OPTION GRILLE (g) DU FICHIER DE CAS

    shape = list(terrain_shape.keys())[0]
    lh = terrain_shape[shape]['length']
    lv = terrain_shape[shape]['height']
    R = lv / lh    
    nv = round(math.sqrt(N / R))
    nh = round(R * nv)
    Np = nh * nv
    if shape.lower() == 'rectangle':
        coords = get_rectangle_lattice_coords(lh, lv, N, Np, nh, nv)
    else:
        msg = [f"\tImproper shape ({shape}) used in the\n",
                "\tgeneration of lattice coordinates.\n"
                "\tValid values: ['rectangle']"]
        ERROR(''.join(msg), 2)
    return coords        

# Fonction verifiant la présence d'un string dans un fichier YAML
# Arguments :  string_to_check (string a verifier), yaml_data (dictionnaire du fichier yaml )
# Retourne True si le string est présent et False sinon
def check_string_presence_in_yaml(string_to_check, yaml_data):
    for device_type, devices in yaml_data.items():
        for device_name, device_info in devices.items():
            if string_to_check == device_name:
                return True
    return False


# Fonction permettant de trouver la valeur d'une cle dans un fichier YAML
# Nbre Param: 5 (key = clé recherché, data = contenu fichier yaml, res = valeur rechercher, curr_level = niveau actuel, min_level =  niveau minimal de profondeur à partir duquel la recherche est autorisée)
# Valeur de retour: res = valeur rechercher
def get_from_dict(key, data, res=None, curr_level = 1, min_level = 1):
    """Fonction qui retourne la valeur de n'importe quel clé du dictionnaire
       key: clé associé à la valeur recherchée
       data: dictionnaire dans lequel il faut chercher
       les autres sont des paramètres par défaut qu'il ne faut pas toucher"""
    if res:
        return res
    if type(data) is not dict:
        msg = f"get_from_dict() works with dicts and is receiving a {type(data)}"
        ERROR(msg, 1)
    else:
        # data IS a dictionary
        for k, v in data.items():
            if k == key and curr_level >= min_level:
                #print(f"return data[k] = {data[k]} k = {k}")
                return data[k]
            if type(v) is dict:
                level = curr_level + 1
                res = get_from_dict(key, v, res, level, min_level)
    return res 

# Fonction permettant de lire un fichier YAML 
# Argument : fname (nom du fichier YAML a lire)
# Valeur de retour : dictionnaire du contenu du fichier yaml
def read_yaml_file(fname):
    # Fonction utilisée pour lire les fichiers de type .yaml
    # fname: nom du fichier .yaml à lire
    # le retour de la fonction est un dictionnaire avec toute l'information qui se trouve
    # dans le fichier .yaml
    # Si vous préférez vous pouvez utiliser une autre fonction pour lires les fichiers
    # de type .yaml.
    # À noter que dans cette fonction il faut ajouter les vérifications qui s'imposent
    # par exemple, l'existance du fichier
    
    # Vérifier l'existence du fichier
    if not os.path.exists(fname):
        ERROR(f"Le fichier {fname} n'existe pas.")
    print(f"INFO : Reading data in file '{fname}' in the current directory.")
    # Ouvrir et lire le fichier YAML
    with open(fname, 'r') as file:
        return yaml.safe_load(file)

# Fonction attribuant des coordonnées aléatoires
# Prends en paramètre le fichier de cas pour avoir la longueur et la largeur du terrain  
# Valeur de retour: coordonnees_aleatoires = valeur nuérique des coodonnées aléatoire  
def gen_random_coords(fichier_de_cas):
    # Cette fonction doit générer les coordonées pour le cas de positionnement aléatoire
    # TODO PRESENTABLE
    longueur_geometry = get_from_dict('length', fichier_de_cas)
    hauteur_geometry = get_from_dict('height', fichier_de_cas)
    

    x_aleatoire = random.uniform(1, longueur_geometry)
    y_aleatoire = random.uniform(1, hauteur_geometry)
    coordonnees_aleatoires = [x_aleatoire, y_aleatoire]
    return coordonnees_aleatoires

# ***********APPELER SEULEEMENT DANS LE CAS D'UN WRITE**************
# Fonction initialisant une liste de ues et assignant des coordonnées aléatoirement à chaque ue dans la liste
# Nbre de parametre: 2 (fichier_de_cas = fichier de cas , fichier_de_devices = fichier de devices)
# Valeur de retour: liste_ues_avec_coordonnees = la liste de tous les ue avec leurs coordonnées
def assigner_coordonnees_ues(fichier_de_cas, fichier_de_devices):
    liste_ues_avec_coordonnees = []
    terrain_shape =  get_from_dict('Surface',fichier_de_cas)
    id_counter = 0  # Tenir à jour un compteur pour chaque type d'antenne

    devices = get_from_dict('DEVICES',fichier_de_cas)
    for ue_group,ue_info in devices.items():
        if ue_group.startswith('UE'):
            nombre_ues = get_from_dict('number', get_from_dict(ue_group, get_from_dict(next(iter(fichier_de_cas)), fichier_de_cas)))
            type_de_generation = get_from_dict('UE_COORD_GEN', fichier_de_cas)
            
            start = id_counter
            for i in range(nombre_ues):
                id = start + i
                # Verifier existence du groupe de ue issu du fichier de cas dans fichier de devices
                if check_string_presence_in_yaml(ue_group, fichier_de_devices) == False :
                    ERROR(f"Le string {ue_group} introduit dans le fichier de cas n'est pas present dans le fichier de devices_db.yaml")
                app_name = get_from_dict('app', get_from_dict(ue_group,fichier_de_devices))
                ue = UE(id=id, app_name=app_name)
                ue.coords = gen_random_coords(fichier_de_cas)
                ue.gen = type_de_generation
                ue.group = ue_group #get_from_dict('name', get_from_dict(ue_group,fichier_de_devices))
                ue.type = get_from_dict('type', get_from_dict(ue_group,fichier_de_devices))
                ue.name = get_from_dict('name', get_from_dict(ue_group,fichier_de_devices))
                ue.TX_rate = get_from_dict('R', get_from_dict(ue_group,fichier_de_devices))

                liste_ues_avec_coordonnees.append(ue)

            # Mettre a jour le compteur pour ce type d'antenne
            id_counter += nombre_ues

    return liste_ues_avec_coordonnees
# ******************************************************************


# ***********APPELER SEULEEMENT DANS LE CAS D'UN WRITE**************
# Fonction initialisant une liste de antennes et assignant des coordonnées selon la grille à chaque antenne
# Nbre de parametre: 2 (fichier_de_cas = fichier de cas , fichier_de_devices = fichier de device)
# Valeur de retour: liste_antennes_avec_coordonnees = la liste de tous les antenne avec leurs coordonnées
def assigner_coordonnees_antennes(fichier_de_cas, fichier_de_devices):
    liste_antennes_avec_coordonnees = []
    terrain_shape =  get_from_dict('Surface',fichier_de_cas)
    id_counter = 0  # Tenir à jour un compteur pour chaque type d'antenne

    devices = get_from_dict('DEVICES',fichier_de_cas)
    for antenna_group, antenna_info in devices.items():
        if antenna_group.startswith('Antenna'):
            nombre_antennes = get_from_dict('number', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_cas)), fichier_de_cas)))
            type_de_generation = get_from_dict('ANT_COORD_GEN', fichier_de_cas)
            
            coords = gen_lattice_coords(terrain_shape, nombre_antennes)
            for id, coord in enumerate(coords, start=id_counter):
                # Verifier existence du groupe de antenna issu du fichier de cas dans fichier de devices
                if check_string_presence_in_yaml(antenna_group, fichier_de_devices) == False :
                    ERROR(f"Le string {antenna_group} introduit dans le fichier de cas n'est pas present dans le fichier de devices_db.yaml")
                antenna = Antenna(id)
                antenna.coords = coord
                antenna.gen = type_de_generation
                antenna.group = antenna_group #get_from_dict('name', get_from_dict(antenna_group,fichier_de_devices))
                antenna.type = get_from_dict('type', get_from_dict(antenna_group,fichier_de_devices))
                antenna.gain = get_from_dict('gain', get_from_dict(antenna_group,fichier_de_devices))                
                antenna.name = get_from_dict('name', get_from_dict(antenna_group,fichier_de_devices))
                liste_antennes_avec_coordonnees.append(antenna)

            # Mettre a jour le compteur pour ce type d'antenne
            id_counter += nombre_antennes

    return liste_antennes_avec_coordonnees
# ******************************************************************






# ***********APPELER SEULEEMENT DANS LE CAS D'UN READ**************
# Fonction initialisant une liste de antennes et assignant des coordonnées selon la grille à chaque antenne
# Nbre de param: 1 (filename = nom du fichier a lire) 
# Valeur de retour: liste_ues_avec_coordonnees = liste des ues avec leur coordonnées
def lire_coordonnees_ues(filename, fichier_de_devices):
    liste_ues_avec_coordonnees = []
    print(f"INFO : Reading UEs data in file '{filename}' in the current directory.")
    # Ouvrir le fichier en mode lecture
    with open(filename, 'r') as f:
        # Lire chaque ligne du fichier
        for ligne in f:
            # Vérifier si la ligne commence par "ue"
            if ligne.startswith("ue"):
                # Diviser la ligne en utilisant le caractère de tabulation comme séparateur
                elements = ligne.strip().split()

                # Récupérer les éléments individuels
                nom_ue = elements[0]
                id_ue = int(elements[1])
                group_ue = elements[2]
                coord_x_ue = float(elements[3])
                coord_y_ue = float(elements[4])
                appname_ue = elements[5]

                # Assigner les elements a l'ue
                ue = UE(id=id_ue, app_name=appname_ue)
                ue.coords = [coord_x_ue, coord_y_ue]
                ue.group = group_ue
                ue.name = get_from_dict('name', get_from_dict(group_ue,fichier_de_devices))
                ue.height = get_from_dict('height', get_from_dict(group_ue,fichier_de_devices))
                ue.type = get_from_dict('type', get_from_dict(group_ue,fichier_de_devices))
                ue.TX_rate = get_from_dict('R', get_from_dict(group_ue,fichier_de_devices))
                liste_ues_avec_coordonnees.append(ue)

    return liste_ues_avec_coordonnees
# ******************************************************************

# ***********APPELER SEULEEMENT DANS LE CAS D'UN READ**************
# Fonction initialisant une liste de antennes et assignant des coordonnées selon la grille à chaque antenne
# Nbre param: 2 (filename = fichier dans lequel on veux lire les données)
# Valeur de retour: Liste des antenne 
def lire_coordonnees_antennes(filename, fichier_de_devices):
    liste_antennes_avec_coordonnees = []
    print(f"INFO : Reading antennas data in file '{filename}' in the current directory.")

    # Ouvrir le fichier en mode lecture
    with open(filename, 'r') as f:
        # Lire chaque ligne du fichier
        for ligne in f:
            # Vérifier si la ligne commence par "antenna"
            if ligne.startswith("antenna"):
                # Diviser la ligne en utilisant le caractère de tabulation comme séparateur
                elements = ligne.strip().split()

                # Récupérer les éléments individuels
                nom_antenne = elements[0]
                id_ant = int(elements[1])
                group_ant = elements[2]
                coord_x_ant = float(elements[3])
                coord_y_ant = float(elements[4])

                # Assigner les elements a l'antenne
                antenna = Antenna(id_ant)
                antenna.coords = [coord_x_ant, coord_y_ant]
                antenna.group = group_ant
                antenna.name = get_from_dict('name', get_from_dict(antenna.group,fichier_de_devices))
                antenna.frequency = get_from_dict('frequency', get_from_dict_3GPP(antenna.group, get_from_dict_3GPP(next(iter(fichier_de_devices)), fichier_de_devices)))
                antenna.height = get_from_dict('height', get_from_dict_3GPP(antenna.group, get_from_dict_3GPP(next(iter(fichier_de_devices)), fichier_de_devices)))
                antenna.type = get_from_dict('type', get_from_dict_3GPP(antenna.group, get_from_dict_3GPP(next(iter(fichier_de_devices)), fichier_de_devices)))
                antenna.gain = get_from_dict('gain', get_from_dict_3GPP(antenna.group, get_from_dict_3GPP(next(iter(fichier_de_devices)), fichier_de_devices)))
                liste_antennes_avec_coordonnees.append(antenna)

    return liste_antennes_avec_coordonnees
# ******************************************************************



# Fonction ecrivant un log_message dans un nouveau fichier 
# Nbre de param: 2 (filename = nom du fichier dans lequel un veut ecrire, log_message = message à ecrire)
def write_to_file(filename, log_message):
    with open(filename, 'w') as file:
        file.write(log_message)
    print(f"INFO : Wrote file '{filename}' in the current directory.")


# Fonction qui ecrit les information par rapport aux coordonnees des antennes et au UEs dans le fichier de sortie specifiee
# Nbre de param : 3 (antennas = liste des antennes, ues = liste des ues, fichier_de_cas)
def write_coordinates_to_file(antennas, ues, fichier_de_cas):
    coord_file_name, mode = check_coord_files_mode(fichier_de_cas)
    if mode == 0 :

        with open(coord_file_name, 'w') as file:
            for antenna in antennas:
                line = f"antenna\t{antenna.id}\t{antenna.group}\t{antenna.coords[0]}\t{antenna.coords[1]}\n"
                file.write(line)

            for ue in ues:
                line = f"ue\t{ue.id}\t{ue.group}\t{ue.coords[0]}\t{ue.coords[1]}\t{ue.app}\n"
                file.write(line)
        print(f"INFO : Wrote file '{coord_file_name}' in the current directory.")
    else :
        return

# Fonction qui écrire dans un fichier la valeurs des pathlosses calculer, l'id de l'ue et des antennes associés et le senario utilisé et le model
# Paramatre: 2 (pathlosses = liste des pathlosses calculer , fichier_de_cas = nom du fichier dans lequel on veut ecrire)
def write_pathloss_to_file(pathlosses, fichier_de_cas):
    filename = pathloss_file_name
    with open(filename, 'w') as file:
        for pathloss in pathlosses:
            model = get_from_dict('model', fichier_de_cas)
            model_formatted = model.lower()
            scenario = get_from_dict('scenario', fichier_de_cas)
            scenario_formatted = scenario.lower()  # Tout en minuscules
            if pathloss.los == True: ### Ajouter
                alignement = "los" ### ajouter
            else:
                alignement = "nlos" ## ajouter 
            line = f"{pathloss.id_ue}\t{pathloss.id_ant}\t{pathloss.value}\t{model_formatted}\t{scenario_formatted}\t{alignement}\n"
            file.write(line)
    print(f"INFO : Wrote file '{filename}' in the current directory.")

# Fonction qui ecrit dans un fichier l'id de l'antenne et tous les id des ues associees
# Parametre : 1 (liste des antennes)
def write_assoc_ues_to_file(antennas):
    filename = assoc_antennas_file_name # nom du fichier dans lequel on veut ecrire 
    with open(filename, 'w') as file:
        for antenna in antennas:
            line = f"{antenna.id}"
            for ue in antenna.assoc_ues :
                line += f"\t{ue}"
            line += "\n"
            file.write(line)
    print(f"INFO : Wrote file '{filename}' in the current directory.")

# Fonction qui ecrit dans un fichier l'id de l'ue avec l'antenne associee
# Parametre : 1 (liste des UEs)
def write_assoc_ant_to_file(ues):
    filename = assoc_ues_file_name # nom du fichier dans lequel on veut ecrire 
    with open(filename, 'w') as file:
        for ue in ues:
            line = f"{ue.id}\t{ue.assoc_ant}\n"
            file.write(line)
    print(f"INFO : Wrote file '{filename}' in the current directory.")

# Fonction qui ecrit dans un fichier les id des antennes suivi du nomnbre de bits recus avec les ues concernees a chaque dt de la transmission
# Parametre : 2 (liste des antennes et fichier de cas)
def write_transmission_ant_to_file(antennas, fichier_de_cas):
    filename = transmission_ant_file_name # nom du fichier dans lequel on veut ecrire 
    temps_initial = get_from_dict('tstart',fichier_de_cas) # temps de debut de simulation
    temps_final = get_from_dict('tfinal',fichier_de_cas) # temps de fin de simulation
    pas_temps = get_from_dict('dt',fichier_de_cas) # pas de temps dt
    segment_filename = get_from_dict('read', get_from_dict('CLOCK', fichier_de_cas)) # Nom du fichier de segment
    with open(filename, 'w') as file:
        for antenna in antennas:
            line = f"{antenna.id}"
            line += "\n"
            file.write(line)
            for slot in  range(int((temps_final-temps_initial)/pas_temps)): 
                line = f"{float(slot)}\t"
                line += ":\t"
                if antenna.nbits != [] :
                    if antenna.nbits[slot] != 0 :
                        line += f"{antenna.nbits[slot]}"
                        for ue in antenna.live_ues[slot]:
                            line += f"\t{ue}"
                line += "\n"
                file.write(line)
    print(f"INFO : Wrote file '{filename}' in the current directory.")

# Fonction qui ecrit dans un fichier les id des ues suivi du nombre de bits recus a chaque dt de la transmission
# Parametre : 2 (liste des ues et fichier de cas)
def write_transmission_ue_to_file(ues, fichier_de_cas):
    filename = transmission_ue_file_name # nom du fichier dans lequel on veut ecrire 
    temps_initial = get_from_dict('tstart',fichier_de_cas) # temps de debut de simulation
    temps_final = get_from_dict('tfinal',fichier_de_cas) # temps de fin de simulation
    pas_temps = get_from_dict('dt',fichier_de_cas) # pas de temps dt
    segment_filename = get_from_dict('read', get_from_dict('CLOCK', fichier_de_cas)) # Nom du fichier de segment
    with open(filename, 'w') as file:
        for ue in ues:
            line = f"{ue.id}"
            line += "\n"
            file.write(line)
            for slot in  range(int((temps_final-temps_initial)/pas_temps)): 
                line = f"{float(slot)}"
                if ue.nbits != [] :
                    if ue.nbits[slot] != 0 :
                        line += f"\t{ue.nbits[slot]}"
                line += "\n"
                file.write(line)
    print(f"INFO : Wrote file '{filename}' in the current directory.")



# Fonction calculant la distance entre deux point sur le terrain
# Nbre Param: 2 (coodonnées du point 1 et 2 )
# Valeur de retour = valeur numérique de la distance calculer
def calculate_distance(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Fonction donnant le group et les coords a partir du ID d'un objet dans une liste du meme objet
# Nbre param : 2 (object_list = liste d'objet , target_id = identifiant de l'objet a recupérer)
def get_group_and_coords_by_id(object_list, target_id):
    for object in object_list:
        if object.id == target_id:
            return object.group, object.coords
    return None  

# Fonction permettant de verifier que les conditions d'application du model okumura sont respectes (sauf pour la distance UE-Antenne)
# Nbre param: 5 (fc = frequence de l'antenne,ht = hauteur de l'antenne,hr = hauteur de l'ue, antenna_group = le grouppe de l'antenne, ue_group =le groppe de l'ue)
# Valeur de retour: bolleen
def verify_okumura_conditions(fc,ht,hr, antenna_group, ue_group): 
    if fc > 1500 :
        ERROR(f"""La fréquence {fc} MHz du groupe d'antenne '{antenna_group}' introduite dans le fichier de cas YAML est plus grande que 1.5 GHz. 
Le model okumura ne s'applique pas. 
Veuillez changer le groupe de l'antenne consideree dans le fichier YAML de cas ou modifier l'attribut 'frequency' du groupe {antenna_group} dans le fichier devices_db.yaml""")
    if fc < 150 :
        ERROR(f"""La fréquence {fc} MHz du groupe d'antenne '{antenna_group}' introduite dans le fichier de cas YAML est plus petite que 0.15 GHz.
Le model okumura ne s'applique pas. 
Veuillez changer le groupe de l'antenne consideree dans le fichier YAML de cas ou modifier l'attribut 'frequency' du groupe {antenna_group} dans le fichier devices_db.yaml""")
    if ht > 300 :
        ERROR(f"""La hauteur {ht} metres du groupe d'antenne '{antenna_group}' introduite dans le fichier de cas YAML est plus grande que 300 metres. 
Le model okumura ne s'applique pas. 
Veuillez changer le groupe de l'antenne consideree dans le fichier YAML de cas ou modifier l'attribut 'height' du groupe {antenna_group} dans le fichier devices_db.yaml""")
    if ht < 30 : 
        ERROR(f"""La hauteur {ht} metres du groupe d'antenne '{antenna_group}' introduite dans le fichier de cas YAML est plus petite que 30 metres. 
Le model okumura ne s'applique pas.
Veuillez changer le groupe de l'antenne consideree dans le fichier YAML de cas ou modifier l'attribut 'height' du groupe {antenna_group} dans le fichier devices_db.yaml""")
    if hr > 10 :
        ERROR(f"""La hauteur {ht} metres du groupe d'UE '{ue_group}' introduite dans le fichier de cas YAML est plus grande que 10 metres. 
Le model okumura ne s'applique pas. 
Veuillez changer le groupe de l'ue consideree dans le fichier YAML de cas ou modifier l'attribut 'height' du groupe {ue_group} dans le fichier devices_db.yaml""")
    if hr < 1 : 
        ERROR(f"""La hauteur {ht} metres du groupe d'UE '{ue_group}' introduite dans le fichier de cas YAML est plus petite que 1 metres. 
Le model okumura ne s'applique pas. 
Veuillez changer le groupe de l'ue consideree dans le fichier YAML de cas ou modifier l'attribut 'height' du groupe {ue_group} dans le fichier devices_db.yaml""")
    return True

# Fonction permettant de calculer le pathloss entre une antenne et une UE tout en verifiant les condition d'application
# Nbre de parametre: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identifiant de l'ue, antennas = liste des antennes, ues = liste des ues)
# valeur de retour: pathloss = valeur numerique du pathloss calculer, warning_message = le message d'erreur
def okumura(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    model = get_from_dict('model', fichier_de_cas)
    scenario = get_from_dict('scenario', fichier_de_cas)
    # Convertir en minuscules pour supporter les combinaisons de majuscules et minuscules
    model = model.lower()
    scenario = scenario.lower()
    warning_message = ""
    if model == "okumura" and scenario == "urban_small":
        antenna_group, antenna_coords = get_group_and_coords_by_id(antennas, antenna_id)
        ue_group, ue_coords = get_group_and_coords_by_id(ues, ue_id)
        fc = 1000*get_from_dict('frequency', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        ht = get_from_dict('height', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        hr = get_from_dict('height', get_from_dict(ue_group,fichier_de_device))
        verify_okumura_conditions(fc,ht,hr, antenna_group, ue_group)        
        distance = calculate_distance(antenna_coords, ue_coords)/1000 # distance in km!
        
        A = (1.1 * math.log10(fc) - 0.7) * hr - 1.56 * math.log10(fc) + 0.8
            
        if distance < 1 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 1 km.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
        elif distance > 20 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 20 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
        else:
            pathloss = 69.55 + 26.16 * math.log10(fc) - 13.82 * math.log10(ht) - A + (44.9 - 6.55 * math.log10(ht)) * math.log10(distance)
        
        return pathloss, warning_message
    
    if model == "okumura" and scenario == "urban_large":
        antenna_group, antenna_coords = get_group_and_coords_by_id(antennas, antenna_id)
        ue_group, ue_coords = get_group_and_coords_by_id(ues, ue_id)
        fc = 1000*get_from_dict('frequency', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        ht = get_from_dict('height', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        hr = get_from_dict('height', get_from_dict(ue_group,fichier_de_device))
        verify_okumura_conditions(fc,ht,hr, antenna_group, ue_group)
        distance = calculate_distance(antenna_coords, ue_coords)/1000 # distance in km!
        
        if fc < 300:
            A = 8.29 * (math.log10(1.54 * hr))**2 - 1.1
        elif fc >= 300:
            A = 3.2 * (math.log10(11.75 * hr))**2 - 4.97
        
        if distance < 1 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 1 km.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
        elif distance > 20 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 20 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
        else:       
            pathloss = 69.55 + 26.16 * math.log10(fc) - 13.82 * math.log10(ht) - A + (44.9 - 6.55 * math.log10(ht)) * math.log10(distance)
        
        return pathloss, warning_message
    
    if model == "okumura" and scenario == "suburban":
        antenna_group, antenna_coords = get_group_and_coords_by_id(antennas, antenna_id)
        ue_group, ue_coords = get_group_and_coords_by_id(ues, ue_id)
        fc = 1000*get_from_dict('frequency', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        ht = get_from_dict('height',get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        hr = get_from_dict('height', get_from_dict(ue_group,fichier_de_device))
        verify_okumura_conditions(fc,ht,hr, antenna_group, ue_group)
        distance = calculate_distance(antenna_coords, ue_coords)/1000 # distance in km!
        
        A = (1.1 * math.log10(fc) - 0.7) * hr - 1.56 * math.log10(fc) + 0.8

        if distance < 1 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 1 km.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
        elif distance > 20 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 20 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
        else:
            pathloss_urban_small = 69.55 + 26.16 * math.log10(fc) - 13.82 * math.log10(ht) - A + (44.9 - 6.55 * math.log10(ht)) * math.log10(distance)
            pathloss = pathloss_urban_small - 2 * (math.log10(fc / 28))**2 - 5.4
        
        return pathloss, warning_message
    
    if model == "okumura" and scenario == "open":
        antenna_group, antenna_coords = get_group_and_coords_by_id(antennas, antenna_id)
        ue_group, ue_coords = get_group_and_coords_by_id(ues, ue_id)
        fc = 1000*get_from_dict('frequency', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        ht = get_from_dict('height', get_from_dict(antenna_group, get_from_dict(next(iter(fichier_de_device)), fichier_de_device)))
        hr = get_from_dict('height', get_from_dict(ue_group,fichier_de_device))
        verify_okumura_conditions(fc,ht,hr, antenna_group, ue_group)
        distance = calculate_distance(antenna_coords, ue_coords)/1000 # distance in km!
        
        A = (1.1 * math.log10(fc) - 0.7) * hr - 1.56 * math.log10(fc) + 0.8
        
        if distance < 1 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 1 km.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
        elif distance > 20 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 20 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
        else:
            pathloss_urban_small = 69.55 + 26.16 * math.log10(fc) - 13.82 * math.log10(ht) - A + (44.9 - 6.55 * math.log10(ht)) * math.log10(distance)
            pathloss = pathloss_urban_small - 4.78 * (math.log10(fc))**2 + 18.33 * math.log10(fc) - 40.94

        return pathloss, warning_message

    # Si aucun cas n'est sélectionnee :
    # FAIRE UN MESSAGE D'ERREUR CORRESPONDANT
    ERROR("""SVP, entrer un model et un scenario dans le fichier de cas YAML parmi les propositions suivantes (model,scenario) :
           (model : okumura, scenario : urban_small)
           (model : okumura, scenario : urban_large)
           (model : okumura, scenario : suburban)
           (model : okumura, scenario : open)
          """)
    return 0

# Fonction permettant de verifier l'integrite du fichier de visibilite fourni par l'utilisateur a travers le fichier de cas
# Arguments: 4
# filename : nom du fichier de visibilité à verifier
# nombre_ue : nombre de ue
# ues : liste d'objets de type UE
# antennas : liste d'objets de type Antenna
# Return value: None
def sanity_check_visibility_file(filename, nombre_ue, ues, antennas):
    # Vérifier si le fichier existe 
    if not os.path.exists(filename):
        ERROR(f"Le fichier '{filename}' n'existe pas dans le repertoire courant.")
    
    with open(filename, 'r') as file:
        lines = file.readlines()

        # Vérifier s'il y a des lignes vides
        if any(line.strip() == '' for line in lines):
            ERROR(f"Le fichier '{filename}' contient des lignes vides.")

        # Vérifier le bon nombre de colonnes et l'absence de répétitions de chiffres
        first_digits_set = set()
        for line in lines:
            ue_numbers = line.strip().split()
            ant_line = ue_numbers[1:]
            if len(ant_line) != len(set(ant_line)):
                ERROR(f"Il y a des répétitions de id d'antenne dans la ligne {ue_numbers} du fichier '{filename}'.")

            if len(ue_numbers) < 2:
                ERROR(f"Chaque ligne du fichier '{filename}' doit contenir au moins deux chiffres (UE et antenne).")

            # Vérifier si le premier chiffre est différent des précédents
            first_digit = ue_numbers[0]
            if first_digit in first_digits_set:
                ERROR(f"""Le premier chiffre de la ligne du fichier '{filename}' est en double : {first_digit}.
                Le premier chiffre d'une ligne represente une UE et ne peut donc pas se retrouver sur une autre ligne.""")
            first_digits_set.add(first_digit)



            # Vérifier la présence des UE et des antennes dans les listes respectives
            ue_id = int(ue_numbers[0])
            ant_ids = [int(id) for id in ue_numbers[1:]]
            if not any(ue.id == ue_id for ue in ues):
                ERROR(f"L'UE avec l'ID {ue_id} du fichier '{filename}' n'est pas présente dans la liste des UEs. SVP choisir dans '{filename}' un autre ID en concordance avec le nombnre d'UE total")
            for ant_id in ant_ids:
                if not any(antenna.id == ant_id for antenna in antennas):
                    ERROR(f"L'antenne avec l'ID {ant_id} du fichier '{filename}' n'est pas présente dans la liste des antennes. SVP choisir dans '{filename}' un autre ID en concordance avec le nombnre d'antennes total")

        # Vérifier le nombre de lignes
        ue_count = len(lines)
        min_ue_count = 0.05 * nombre_ue
        max_ue_count = 0.30 * nombre_ue
        if ue_count < min_ue_count or ue_count > max_ue_count:
            ERROR(f"""Le nombre de lignes ({ue_count}) dans le fichier '{filename}' n'est pas compris entre 5% et 30% du nombre d'UE spécifié ({nombre_ue}).
            SVP, mettre un nombre de ligne entre {min_ue_count} et {max_ue_count} dans le fichier '{filename}'.""")




# Fonction permettant de vérifier si la combinaison ue antenne fournie en argument est en situation LoS ou non
# Arguments : ue (objet UE), antenne (objet Antenna), fichier_de_cas, ues (liste d'objets UE), antennas (liste d'objets Antenna)
# Retourne True si la combinaison ue antenne est LoS
# Retourne False sinon
def verifie_presence_visibility_los(ue, antenne, fichier_de_cas, ues, antennas):
    visibility_filename = get_from_dict('read', get_from_dict('VISIBILITY', fichier_de_cas))
    sanity_check_visibility_file(visibility_filename, len(ues), ues, antennas)
    with open(visibility_filename, 'r') as f:
        for line in f:
            ids = list(map(int, line.split()))
            if ids[0] == ue and antenne in ids[1:]:
                return False
    return True

# ****************************CHANGER POUR 3GPP**********************************
# Fonction permettant d'assigner un pathloss à chaque combinaison (antenne,UE) du terrain
# Nbre param: 4 (fichier_de_cas, fichier_de_device, antennas = liste des antenne, ues =liste des ues)
# Valeur de retour: pathloss_list = liste des pathloss calculer, warning_log = message d'avertissement 
def pathloss_attribution(fichier_de_cas, fichier_de_device, antennas, ues):
    pathloss_list =[]
    warning_log = ""
    model = get_from_dict('model', fichier_de_cas)
    scenario = get_from_dict('scenario', fichier_de_cas)
    # Si le nom de scenario est mal ecrit, afficher un warning
    if not (scenario[0].isupper() and scenario[1].isupper() and scenario[-1].islower()):
        print("INFO : Scenario name in case file is misspelled. It should have 2 uppercases and 1 lowercase. ")
    # Convertir en minuscules pour supporter les combinaisons de majuscules et minuscules
    model = model.lower()
    scenario = scenario.lower()

    if model == "3gpp" :
        if scenario == "rma" :
            for ue in ues:
                for antenna in antennas:
                    pathloss = Pathloss(ue.id, antenna.id)
                    pathloss.los = verifie_presence_visibility_los(ue.id, antenna.id, fichier_de_cas, ues, antennas)
                    if pathloss.los == True :
                        pathloss_value, warning_message = rma_los(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    if pathloss.los == False :
                        pathloss_value, warning_message = rma_nlos(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    pathloss.value = pathloss_value
                    warning_log += warning_message
                    pathloss_list.append(pathloss)
            return pathloss_list, warning_log
        if scenario == "uma" :
            for ue in ues:
                for antenna in antennas:
                    pathloss = Pathloss(ue.id, antenna.id)
                    pathloss.los = verifie_presence_visibility_los(ue.id, antenna.id, fichier_de_cas, ues, antennas)
                    if pathloss.los == True :
                        pathloss_value, warning_message = uma_los(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    if pathloss.los == False :
                        pathloss_value, warning_message = uma_nlos(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    pathloss.value = pathloss_value
                    warning_log += warning_message
                    pathloss_list.append(pathloss)
            return pathloss_list, warning_log
        if scenario == "umi" :
            for ue in ues:
                for antenna in antennas:
                    pathloss = Pathloss(ue.id, antenna.id)
                    pathloss.los = verifie_presence_visibility_los(ue.id, antenna.id, fichier_de_cas, ues, antennas)
                    if pathloss.los == True :
                        pathloss_value, warning_message = umi_los(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    if pathloss.los == False :
                        pathloss_value, warning_message = umi_nlos(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                    pathloss.value = pathloss_value
                    warning_log += warning_message
                    pathloss_list.append(pathloss)
            return pathloss_list, warning_log
        # Si aucun nom de scenario 3GPP n'est reconnu :
        ERROR("""Non de scenario invalide dans le fichier de cas.
                SVP, entrer un scenario conforme dans le fichier de cas YAML parmi les propositions suivantes (model, scenario) :
           (model : 3gpp, scenario : RMa)
           (model : 3gpp, scenario : UMa)
           (model : 3gpp, scenario : UMi)
            """)
    if model == "okumura" :
        for ue in ues:
            for antenna in antennas:
                pathloss = Pathloss(ue.id, antenna.id)
                pathloss.los = verifie_presence_visibility_los(ue.id, antenna.id, fichier_de_cas, ues, antennas)
                pathloss_value, warning_message = okumura(fichier_de_cas, fichier_de_device, antenna.id, ue.id, antennas, ues)
                pathloss.value = pathloss_value
                warning_log += warning_message
                pathloss_list.append(pathloss)
        return pathloss_list, warning_log

    # Si aucun nom de modele n'est reconnu :
    ERROR("""Non de modele invalide dans le fichier de cas.
            SVP, entrer un model conforme dans le fichier de cas YAML parmi les propositions suivantes (model) :
           (model : 3gpp)
           (model : okumura)
          """)
# ********************************************************************************

# Fonction permettant d'associer les UEs du terrain a leur antenne ayant le pathloss minimal
# Nbre de param: 3 (pathlosses = liste des pathloss, antennas = liste des antenne, ues = liste des ues)
# Valeur de retour: antennas = liste des antennes associer, ues = liste des ues associer
def association_ue_antenne(pathlosses, antennas, ues):
    # Initialiser un dictionnaire pour stocker l'antenne avec le pathloss le plus petit pour chaque UE
    ue_to_antenna = {}

    for pathloss_object in pathlosses:
        ue_id = pathloss_object.id_ue
        ant_id = pathloss_object.id_ant
        pathloss_value = pathloss_object.value
        pathloss_los = pathloss_object.los

        # Si l'UE n'est pas dans le dictionnaire ou que la valeur du pathloss est plus petite que le minimum courant,
        # Mettre a jour l'entree du dictionnaire
        if ue_id not in ue_to_antenna or pathloss_value < ue_to_antenna[ue_id][1]:
            ue_to_antenna[ue_id] = (ant_id, pathloss_value, pathloss_los)

    # Mettre a jour l'attribut assoc_ant de l'UE correspondante
    for ue_id, (ant_id, _, pathloss_los) in ue_to_antenna.items():
        ue = next((ue for ue in ues if ue.id == ue_id), None)
        if ue:
            ue.assoc_ant = ant_id
            ue.los = pathloss_los
        

    # Mettre a jour l'attribut assoc_ue de l'antenne correspondante
    for ant in antennas:
        associated_ues = [ue.id for ue in ues if ue.assoc_ant == ant.id]
        ant.assoc_ues = associated_ues

    return antennas, ues

# Fonction retournant si nous sommes en mode de lecture ou d'ecriture
# Nbre de param : 1 (fichier_de_cas)
# Valeur de retour: nom_du_fichier, mode (lecture  ou ecriture)
def check_coord_files_mode(fichier_de_cas):
    nom_du_fichier = ""
    
    coord_files_mode = get_from_dict("COORD_FILES", fichier_de_cas)
    if coord_files_mode == None or len(coord_files_mode.keys()) > 1 :
        ERROR("""La clé COORD_FILES n'est pas définie correctement dans le fichier de cas.
SVP commenter SOIT la clé read SOIT la clé write dans le fichier de cas.""")            
    else:
        if 'read' in coord_files_mode.keys() and 'write' not in coord_files_mode.keys():
            mode = True
            nom_du_fichier = get_from_dict("read", fichier_de_cas)
            return nom_du_fichier, mode
            
        elif 'write' in coord_files_mode.keys() and 'read' not in coord_files_mode.keys():
            mode = False
            nom_du_fichier = get_from_dict("write", fichier_de_cas)
            return nom_du_fichier, mode

# Fonction permettant de verifier l'integritee du fichier de coordonnee fourni en entree au moment de sa lecture
# Argument : filename (nom du fichier)
def sanity_check_coordinates_file(filename):
    if not os.path.exists(filename):
        ERROR(f"Le fichier {filename} n'existe pas dans le repertoire courant.")
    
    
    with open(filename, 'r') as file:
        lines = file.readlines()

        id_antenna = -1
        id_ue = -1

        for line in lines:
            # Vérifier s'il y a des lignes vides
            if line.strip() == '':
                ERROR(f"Le fichier '{filename}' contient des lignes vides.")

            # Vérifier le nombre de colonnes
            parts = line.strip().split()
            if parts[0] == 'antenna':
                # Vérifier le format des lignes antenna
                if len(parts) != 5:
                    ERROR(f"Le format de la ligne antenna dans le fichier '{filename}' est incorrect. Il doit y avoir 5 colonnes : string chiffre string chiffre chiffre")
                # Vérifier si l'identifiant est incrémenté correctement
                current_id = int(parts[1])
                if current_id != id_antenna + 1:
                    ERROR(f"""L'identifiant de l'antenne dans le fichier '{filename}' n'est pas incrémenté correctement: {line.strip()}.
                    Se rappeler que l'id doit commencer a 0 et doit s'incrementer un a un par la suite.""")
                id_antenna = current_id
            elif parts[0] == 'ue':
                # Vérifier le format des lignes ue
                if len(parts) != 6:
                    ERROR(f"Le format de la ligne ue dans le fichier '{filename}' est incorrect. Il doit y avoir 6 colonnes : string chiffre string chiffre chiffre string")
                # Vérifier si l'identifiant est incrémenté correctement
                current_id = int(parts[1])
                if current_id != id_ue + 1:
                    ERROR(f"""L'identifiant de l'UE dans le fichier '{filename}' n'est pas incrémenté correctement: {line.strip()}. 
                    Se rappeler que l'id doit commencer a 0 et doit s'incrementer un a un par la suite.""")
                id_ue = current_id
            else:
                ERROR(f"La première colonne de la ligne n'est ni 'antenna' ni 'ue': {line.strip()} dans le fichier '{filename}'.")

# Fonction lisant le fichier de segment et y associe le debut et fin de transmission de paquets pour chaque UE
# Nbre de param: 2 (filename = nom du fichier a lire, ues = liste d'objets UE) 
# Valeur de retour: liste_ues_avec_coordonnees = liste des ues avec leur coordonnées
def lire_fichier_segments(filename, ues):
    print(f"INFO : Reading UEs data in file '{filename}' in the current directory.")
    # Ouvrir le fichier en mode lecture
    with open(filename, 'r') as f:
        # Lire chaque ligne du fichier
        for ligne in f:
            # Diviser la ligne en utilisant le caractère de tabulation comme séparateur
            elements = ligne.strip().split()

            # Récupérer les éléments individuels
            id_ue = int(elements[0])
            start_TX = float(elements[1])
            end_TX = float(elements[2])

            # Recherche de l'UE correspondante dans la liste des UEs
            for ue in ues:
                if ue.id == id_ue:
                    # Ajouter les valeurs start_TX et end_TX à leurs listes respectives dans l'objet UE
                    ue.start_TX.append(start_TX)
                    ue.end_TX.append(end_TX)
                    break  # Sortir de la boucle une fois que l'UE correspondante est trouvée
    return ues

# Fonction permettant de verifier l'integritee du fichie de segment decrivant le profil de tranmission des UEs
# Arguments : fichier_de_cas
# Valeur de retour : None
def sanity_check_transmission_profile(fichier_de_cas):
    file_path = get_from_dict('read', get_from_dict('CLOCK', fichier_de_cas))
    if not isinstance(file_path, str):
        ERROR("Le chemin du fichier n'est pas une chaîne de caractères.")
    if not os.path.exists(file_path):
        ERROR("Le fichier spécifié n'existe pas.")
    if not os.access(file_path, os.R_OK):
        ERROR("Le programme n'a pas les autorisations nécessaires pour lire le fichier.")
    if os.path.getsize(file_path) == 0:
        ERROR("Le fichier est vide.")
    ue_transmissions = {}  # Initialisation de la variable ue_transmissions
    with open(file_path, 'r') as file:
        for line_num, line in enumerate(file, start=1):
            # Vérifier le format de chaque ligne
            line_data = line.strip().split('\t')
            if len(line_data) != 3:
                ERROR(f"Erreur à la ligne {line_num}: Format de ligne incorrect.")
            try:
                ue_id, start_time, end_time = map(float, line_data)
            except ValueError:
                ERROR(f"Erreur à la ligne {line_num}: Les valeurs ne sont pas numériques.")            
            # Vérifier que le temps de début vient après le temps de fin
            if start_time >= end_time:
                ERROR(f"Erreur à la ligne {line_num}: Le temps de début de transmission doit venir après le temps de fin.")            
            # Vérifier la validité des valeurs
            if not (ue_id.is_integer() and ue_id >= 0):
                ERROR(f"Erreur à la ligne {line_num}: L'ID de l'UE doit être un entier positif ou nul.")
            if start_time < 0 or end_time < 0:
                ERROR(f"Erreur à la ligne {line_num}: Les temps de début et de fin de transmission doivent être positifs.")
            # Vérifier l'intégrité des données (UE ne transmet pas plus d'un paquet en même temps)
            if ue_id in ue_transmissions:
                if ue_transmissions[ue_id] >= start_time:
                    ERROR(f"Erreur à la ligne {line_num}: L'UE {ue_id} transmet plus d'un paquet en même temps.")
            ue_transmissions[ue_id] = end_time  # Mettre à jour le temps de fin de transmission de l'UE
    return

# Fonction permettant de verifier l'integritee des valeurs de temps de debut, fin et pas de la simulation
# Arguments : temps_initial, temps_final, pas_temps
# Valeur de retour : None
def sanity_check_timing_values(temps_initial, temps_final, pas_temps):
    # Vérification des bornes temporelles
    if temps_initial < 0 or temps_final < 0:
        ERROR("tstart and tfinal MUST be positive values.")
    if temps_initial >= temps_final:
        ERROR("tstart MUST be smaller than tfinal.")

    # Vérification de la granularité temporelle
    if pas_temps <= 0:
        ERROR("dt MUST be a positive value.")




# Fonction permettant de faire la simulation de la transmission a chaque dt et retournant une liste d'objets Antenna et une liste d'objets UE avec les attributs nbits et live_ues mis a jour
# Arguments : fichier_de_cas, fichier_de_device, antennas (liste d'objets Antenna), ues (liste d'objets UE)
# Valeur de retour : antennas = liste d'objets Antenna, ues = liste d'objets UE
def simulate_packet_transmission(fichier_de_cas, fichier_de_device, antennas, ues) :

    temps_initial = get_from_dict('tstart',fichier_de_cas) # temps de debut de simulation
    temps_final = get_from_dict('tfinal',fichier_de_cas) # temps de fin de simulation
    pas_temps = get_from_dict('dt',fichier_de_cas) # pas de temps dt
    segment_filename = get_from_dict('read', get_from_dict('CLOCK', fichier_de_cas)) # Nom du fichier de segment
    sanity_check_timing_values(temps_initial, temps_final, pas_temps)

    # Lire le fichier de segments et en extraire les informations de transmission des UEs
    sanity_check_transmission_profile(fichier_de_cas)
    ues = lire_fichier_segments(segment_filename, ues)

    # Lire l

    # Boucle de simulation
    temps_courant = temps_initial
    while temps_courant < 0.99*(temps_final-(temps_final-pas_temps*int((temps_final - temps_initial) / pas_temps))) + temps_initial : # tant que le temps courant est inferieur au temps de fin de simulation
        # Logique de simulation de transmission de paquets entre antennes et UEs
        # Pour chaque UE
        for ue in ues:
            # Verifier si l'UE a des transmissions prevues pendant ce pas de temps
            # if ue.id == 2 :
            #     print("EH!")
            for i in range(len(ue.start_TX)):
                if temps_courant <= ue.start_TX[i] <= temps_courant + pas_temps or ue.start_TX[i]<= temps_courant <= ue.end_TX[i]:
                    M = min(temps_courant + pas_temps, ue.end_TX[i]) - max(temps_courant, ue.start_TX[i])  # Durée de la transmission
                    R = ue.TX_rate*1000  # Débit de la transmission en bits per second
                    nbits_transmis = int(R * M)  # Nombre de bits transmis
                    # Mettre a jour l'attribut nbits de l'UE 
                    # if len(ue.nbits) >= (temps_courant + pas_temps) :
                    #     ue.nbits[int(temps_courant / pas_temps)] += nbits_transmis 
                    # else:
                    #     ue.nbits.append(nbits_transmis)

                    if ue.nbits == [] :
                        # Mettre à jour l'attribut nbits de l'antenne si celui-ci est vide
                        while len(ue.nbits) < int((temps_final - temps_initial) / pas_temps) :
                            ue.nbits.append(0)
                    ue.nbits[int(round(temps_courant / pas_temps)) - int(round(temps_initial / pas_temps))] += nbits_transmis 
                    
                    # Mettre à jour les donnees de l'antenne associee
                    antenne_associee_id = ue.assoc_ant
                    for antenne in antennas:
                        if antenne.id == antenne_associee_id:
                            # if len(antenne.nbits) >= (temps_courant + pas_temps):
                            #     # while len(antenne.nbits) < int((temps_final - temps_initial) / pas_temps) :
                            #     #     # Mettre à jour l'attribut nbits de l'antenne si celui-ci est vide
                            #     #     antenne.nbits.append(0)
                            #     # Mettre à jour l'attribut nbits de l'antenne
                            #     antenne.nbits[int(temps_courant / pas_temps)]  += nbits_transmis
                            # else :
                            #     antenne.nbits.append(nbits_transmis)
                            
                            if antenne.nbits == [] :
                                # Mettre à jour l'attribut nbits de l'antenne si celui-ci est vide
                                while len(antenne.nbits) < int((temps_final - temps_initial) / pas_temps) :
                                    antenne.nbits.append(0)
                            antenne.nbits[int(round(temps_courant / pas_temps)) - int(round(temps_initial / pas_temps))] += nbits_transmis 
                            
                            # Ajouter l'UE à la liste des UEs actives de l'antenne si pas deja ajoute 
                            if antenne.live_ues == [] :
                                while len(antenne.live_ues) < int((temps_final - temps_initial) / pas_temps) :
                                    antenne.live_ues.append([])
                            if ue.id not in antenne.live_ues[int(temps_courant / pas_temps) - int(round(temps_initial / pas_temps))]:
                                antenne.live_ues[int(round(temps_courant / pas_temps)) - int(round(temps_initial / pas_temps))].append(ue.id)                            
                            break

        
        # Mise à jour du temps
        temps_courant += pas_temps

    
    return antennas, ues


# Fonction lab3 requise, retourne une liste d'antenne et une liste d'UE
# Prends en parametre data_case qui est le dictionnaire du fichier de cas
def lab3 (data_case):
    #TODO ....
    # antennas est une liste qui contient les objets de type Antenna
    # ues est une liste qui contient les objets de type UE
    #
    # antennas = [ant0,ant1,...] 
    #            ant1, ant2 etc sont des instances (objets) de la classe Antenna
    # ues = [ue0, ue1,...] 
    #             ue0, ue1, etc sont des instances (objets) de la classe UE
    # avant de faire le retour, les objets appartenant aux listes antennas et ues 
    # doivent avoir leur coordonées initialisées
    # CETTE FONCTION EST OBLIGATOIRE
    fichier_de_cas = data_case
    fichier_de_devices = read_yaml_file("devices_db.yaml")
    coord_file_name, mode = check_coord_files_mode(fichier_de_cas)
    if mode == False :
        ERROR("SVP mettre le mode lecture sur le fichier de coordonnees dans le fichier de cas! Le programme doit lire les coordonnees!")
        # ues = assigner_coordonnees_ues(fichier_de_cas, fichier_de_devices)
        # antennas = assigner_coordonnees_antennes(fichier_de_cas, fichier_de_devices)
    if mode == True :
        sanity_check_coordinates_file(coord_file_name)        
        ues = lire_coordonnees_ues(coord_file_name, fichier_de_devices)
        antennas = lire_coordonnees_antennes(coord_file_name, fichier_de_devices)
    return (antennas,ues)

# Fonction vérifiant si le fichier YAML fournit en input a la bonne structure 
# Nbre param: 1 (file_path = nom du fichier ayant la stucture )
# Valeur de retour : booleen
def validate_yaml_structure(file_path):
    try:
        with open(file_path, 'r') as file:
            yaml_content = yaml.load(file, Loader=yaml.FullLoader)
    except yaml.YAMLError as e:
        print(f"Error loading YAML file '{file_path}': {e}")
        return False

    # Define the expected structure
    expected_structure = {
        'ETUDE_DE_TRANSMISSION': {
            'PATHLOSS': {
                'model': None,
                'scenario': None,
            },
            'ANT_COORD_GEN': None,
            'UE_COORD_GEN': None,
            'COORD_FILES': None,
            'DEVICES': None,
            'GEOMETRY': {
                'Surface': {
                    'rectangle': {
                        'length': None,
                        'height': None
                    }
                }
            },
            'VISIBILITY': None,
            'CLOCK': None            
        }
    }

    # Validate the structure
    if not validate_structure(yaml_content, expected_structure):
        # Invalid structure in YAML file
        return False

    # Valid structure in YAML file
    return True

# Fonction comparant deux structures YAML et retournant False si différence existe
# Nbre de param: 2 (content = contenue , expected_structure = la structure au quelle on s'attend)
# variable de retour: booleen
def validate_structure(content, expected_structure):
    if not isinstance(content, dict) or not isinstance(expected_structure, dict):
        return False

    for key, value in expected_structure.items():
        if key not in content:
            return False

        if value is not None and not validate_structure(content[key], value):
            return False

    return True

# Fonction permettant d'afficher la disposition des equipements Antennes et UEs sur un plot
# Nbre param: 2 ( antennas = liste des antennes , ues = liste des ues, plot_filename = nom du fichier a plot)
# Valeur de retour : None
def plot_equipment_positions(antennas, ues, plot_filename):
    # Créer une nouvelle figure
    plt.figure(figsize=(8, 6))
    
    # Tracer les positions des antennes
    for antenna in antennas:
        plt.plot(antenna.coords[0], antenna.coords[1], 'ro', label='_nolegend_')  # Ajouter '_nolegend_' pour ne pas afficher cette entrée dans la légende
    plt.plot([], [], 'ro', label='Antennes')  # Entrée personnalisée pour les antennes dans la légende
        
    # Tracer les positions des UE
    for ue in ues:
        plt.plot(ue.coords[0], ue.coords[1], 'bo', label='_nolegend_')  # Ajouter '_nolegend_' pour ne pas afficher cette entrée dans la légende
    plt.plot([], [], 'bo', label='UEs')  # Entrée personnalisée pour les UE dans la légende
    
    # Définir les labels et le titre du plot
    plt.xlabel('Longueur (m)')
    plt.ylabel('Largeur (m)')
    plt.title('Disposition des équipements')
    
    # Afficher la légende
    plt.legend()
    
    filename = plot_filename

    # Sauvegarder le graphique dans un fichier PDF
    pdf_filename = f"{filename}.pdf"
    plt.savefig(pdf_filename)
    # plt.close()

    # Sauvegarder le graphique dans un fichier PNG
    png_filename = f"{filename}.png"
    plt.savefig(png_filename)
    plt.close()




    


# Fonction pour plot la traffic moyen pour chaque UE
# Arguments : filename, ues= list of objects UE
# Valeur de retour : None
def plot_average_traffic_ues(filename, ues):
    # Calculer la moyenne du trafic pour chaque UE
    average_traffic_ues = [sum(ue.nbits) / len(ue.nbits) if ue.nbits else 0  for ue in ues]

    # Extraire les ID des UEs
    ue_ids = [ue.id for ue in ues]

    # Tracer le graphique
    plt.bar(ue_ids, average_traffic_ues)
    plt.title("Trafic moyen de chaque UE")
    plt.xlabel("ID de l'UE")
    plt.ylabel("Nombre moyen de bits transmis")
    plt.grid(True)

    # Sauvegarder le graphique dans un fichier PDF
    pdf_filename = f"{filename}.pdf"
    plt.savefig(pdf_filename)
    # plt.close()

    # Sauvegarder le graphique dans un fichier PNG
    png_filename = f"{filename}.png"
    plt.savefig(png_filename)
    plt.close()


# Fonction pour plot la traffic moyen pour chaque antenne
# Arguments : filename, antennas= list of objects Antenna
# Valeur de retour : None
def plot_average_traffic_antennas(filename, antennas):
    # Calculer la moyenne du trafic pour chaque antenne
    average_traffic_antennas = [sum(antenne.nbits) / len(antenne.nbits) if antenne.nbits else 0 for antenne in antennas]

    # Extraire les ID des antennes
    antenna_ids = [antenne.id for antenne in antennas]

    # Tracer le graphique
    plt.bar(antenna_ids, average_traffic_antennas)
    plt.title("Trafic moyen de chaque antenne")
    plt.xlabel("ID de l'antenne")
    plt.ylabel("Nombre moyen de bits reçus")
    plt.grid(True)

    # Sauvegarder le graphique dans un fichier PDF
    pdf_filename = f"{filename}.pdf"
    plt.savefig(pdf_filename)
    # plt.close()

    # Sauvegarder le graphique dans un fichier PNG
    png_filename = f"{filename}.png"
    plt.savefig(png_filename)
    plt.close()



# Fonction to plot the traffic per time slot
# Arguments : antennas= list of objects Antenna, ues= liste of objects UE, fichier_de_cas, filename_prefix
# Valeur de retour : None
def plot_bits_received_per_slot(antennas, ues, fichier_de_cas, filename_prefix):
    num_slots = len(ues[0].nbits)  # Nombre de créneaux basé sur la longueur de la liste de bits reçus d'un UE
    slot_interval = get_from_dict('dt',fichier_de_cas) # pas de temps dt
    temps_initial = get_from_dict('tstart',fichier_de_cas)

    # Création des créneaux en millisecondes
    slots = np.arange(temps_initial, round(num_slots * slot_interval, 4)  + temps_initial, slot_interval)
    slot_sum_bits_received = np.zeros(num_slots)  # Tableau pour stocker la somme des bits reçus pour chaque créneau

    # Parcours de chaque antenne
    for antenna in antennas:
        live_ues = antenna.live_ues
        # Initialisation d'un tableau temporaire pour stocker les bits reçus pour chaque créneau
        temp_slot_sum_bits_received = np.zeros(num_slots)
        # Sommation des bits reçus pour chaque créneau pour toutes les UE associées à l'antenne
        for ue_ids_in_slot in live_ues:
            for ue_id in ue_ids_in_slot:
                # Recherche de l'UE dans la liste d'UE
                ue = next((ue for ue in ues if ue.id == ue_id), None)
                if ue:
                    # Sommation des bits reçus pour chaque créneau
                    temp_slot_sum_bits_received += np.array(ue.nbits)
        # Ajout des bits reçus pour chaque créneau à la somme totale
        slot_sum_bits_received += temp_slot_sum_bits_received

    # Création du graphique
    plt.bar(slots, slot_sum_bits_received, width=slot_interval, align='edge')
    plt.xlabel('Temps (ms)')
    plt.ylabel('Nombre de bits')
    plt.title('Traffic par slot de temps')
    plt.grid(True)

    # Ajouter la durée d'un slot et le numéro de chaque slot au-dessus du graphique
    for slot, slot_value in enumerate(slots):
        plt.text(slot_value + slot_interval/2, slot_sum_bits_received[slot], f'{slot + 1}\n',
                 horizontalalignment='center', verticalalignment='bottom')

    # Ajouter la durée d'un slot comme légende
    plt.legend([f'{num_slots} Slots\nDurée d\'un slot: {slot_interval} ms'])

    # Sauvegarde en PNG
    png_filename = f"{filename_prefix}.png"
    plt.savefig(png_filename, format='png')

    # Sauvegarde en PDF
    pdf_filename = f"{filename_prefix}.pdf"
    plt.savefig(pdf_filename, format='pdf')



def check_pdftk_installed():
    try:
        # Attempt to run pdftk command
        subprocess.run(["pdftk", "--version"], check=True)
        print("INFO: pdftk is installed.")
    except FileNotFoundError:
        print("INFO: pdftk is not installed.")


# Fonction pour combiner les png en un pdf
# Arguments : les noms de fichier pdf en input et le nom du fichier pdf en output
# Valeur de retour : None 
def create_pdf_from_plot(pdf_files, output_pdf):

    # Is pdftk installed?
    try:
        if os.name == 'posix':  # Check if running on Linux or macOS
            # with open(os.devnull, 'w') as devnull:
            devnull = open(os.devnull, 'w')
            stdout, stderr = devnull, devnull
        else:  # Assume Windows
            stdout, stderr = subprocess.DEVNULL, subprocess.DEVNULL

        # Run pdftk command and redirect output
        subprocess.run(["pdftk", "--version"], check=True, stdout=stdout, stderr=stderr)
    except FileNotFoundError:
        ERROR("Package 'pdftk' is not installed. Please install it using your distribution's package manager ('sudo apt install pdftk' for Ubuntu/Debian, 'sudo pacman -S pdftk' for Arch Linux)")

    # Commande pdftk pour fusionner les fichiers PDF
    pdftk_cmd = ["pdftk"] + pdf_files + ["cat", "output", output_pdf]

    # Exécution de la commande pdftk
    subprocess.run(pdftk_cmd, check=True)
    for pdf_file in pdf_files:
        os.remove(pdf_file)

   # Remove corresponding PNG files
    for pdf_file in pdf_files:
        png_file = os.path.splitext(pdf_file)[0] + ".png"
        if os.path.exists(png_file):
            os.remove(png_file)

    print(f"INFO : Wrote file '{output_pdf}' in the current directory.")



# Fonction permettant de traiter les arguments en entree de la commande CLI python pour lancer le code source
# Nombre d'argument: 1 (arg = argument )
# Valeur de retour : YAML_file_exists, YAML_file_correct_extension, correct_yaml_structure, case_file_name
def treat_cli_args(arg):
    # arg est une liste qui contient les arguments utilisés lors de l'appel du programme par CLI. 
    # Cette fonction doit retourner le nom du fichier de cas à partir de l'interface de commande (CLI)
    #... 
    # TODO
    #....
    # CETTE FONCTION EST OBLIGATOIRE
    # À noter que dans cette fonction il faut ajouter les vérifications qui s'imposent
    # par exemple, nombre d'arguments appropriés, existance du fichier de cas, etc.
    
    # Vérifier le nombre d'arguments
    # case_file_name = "lab2_eq7_cas.yaml" # UNCOMMENT TO ALLOW DEBUGGING IN VSCODE
    if len(arg) != 1:
        ERROR("Nombre d'arguments incorrect. Veuillez spécifier 1 nom de fichier de cas dans le format YAML, par exemple 'lab3_eq7_cas.yaml' .")
    case_file_name = arg[0] # UNCOMMENT FOR CLI FINAL RELEASE, COMMENT OTHERWISE
    # Check if the file exists
    YAML_file_exists = True
    YAML_file_correct_extension = True
    correct_yaml_structure = True
    if os.path.isfile(case_file_name):
        # Check if the file has a YAML extension
        _, file_extension = os.path.splitext(case_file_name)
        if file_extension.lower() not in ['.yaml', '.yml']:
            YAML_file_correct_extension = False
        else:
            # YAML has the correct extension
            # Check if the YAML structure is good
            file_path = case_file_name
            if validate_yaml_structure(file_path):
                correct_yaml_structure = True
            else:
                correct_yaml_structure = False
    else:
        YAML_file_exists = False
    return YAML_file_exists, YAML_file_correct_extension, correct_yaml_structure, case_file_name

# Fonction faisant un sanity check (verification) sur les dimensions du terrain et affiche un warning le cas échéant
# Nbre de param: 1 (ficchier_de_cas)
def sanity_check_dimensions(fichier_de_cas):
    length = get_from_dict('length', fichier_de_cas)
    height = get_from_dict('height', fichier_de_cas)
    if length <= 1000 or height <= 1000 :
        print(f"WARNING : The rectangle's dimensions ({length} meters by {height} meters) are too small!!")
        print("WARNING : Are you sure that the dimensions specified in the case file are in meters?")
        print("Continuing anyway...")
    if length >= 100000 or height >= 100000 :
        print(f"WARNING : The rectangle's dimensions ({length} meters by {height} meters) are too big!!")
        print("WARNING : Are you sure that the dimensions specified in the case file are in meters?")
        print("Continuing anyway...")

# Fonction vérifiant si le programme doit fournir un fichier log des warnings du calcul des pathloss
# Si des warning concernant le calcul des pathloss sont apparus, ils se retrouvent dans ce fichier
# Nbre de param: 3 (warning_log = warning message , filename = nom du fichier des warning, fichier_de_cas)
def write_pathloss_warning_log_file(warning_log, filename, fichier_de_cas):
    if warning_log == "":
        print("No problem detected during the pathloss calculation!")
    else:
        write_to_file(filename, warning_log)
        count = warning_log.count("WARNING")
        model = get_from_dict('model', fichier_de_cas)
        scenario = get_from_dict('scenario', fichier_de_cas)
        print(f"WARNING : During the pathloss calculation, a total of {count} pathloss values had parameters that did not meet the conditions of the {model} model (considering scenario {scenario}). Please find more details in the file '{filename}'.")


# Fonction main du programme (requise), elle appelle les autres fonctions du programme
# Argument : arg (argument de la CLI)
def main(arg):
    # Verification de la validitee du fichier yaml fourni par la commande CLI
    yaml_exist, yaml_correct_extenstion, correct_yaml_structure, case_file_name = treat_cli_args(arg)
    print("YAML case file name = ", case_file_name)
    if (yaml_exist == False):
        ERROR("YAML case file doesn't exist!")   
    else:
        print("YAML case file exists")
    if yaml_correct_extenstion == False :
        ERROR(f"The YAML case file does not have the correct extension (needs to be a .yaml file).")
    else:
        print(f"The YAML case file has the correct extension.")
    if correct_yaml_structure == True:
        print(f"The YAML case file has the correct structure.")
    else:
        ERROR(f"""The YAML case file does not have the correct structure. \n \nHere is an idea of the awaited structure : \n {yaml_structure_message} """)

    # Debut du programme :
    device_file_name = "devices_db.yaml"
    data_case = read_yaml_file(case_file_name)
    data_device = read_yaml_file(device_file_name)
    
    fichier_de_cas = data_case
    sanity_check_dimensions(fichier_de_cas)
    fichier_de_device = data_device
    antennas, ues = lab3(fichier_de_cas)

    # Calcul pathloss et Association
    pathlosses, warning_log = pathloss_attribution(fichier_de_cas,fichier_de_device,antennas,ues)
    antennas, ues = association_ue_antenne(pathlosses, antennas, ues)

    # Transmission des paquets
    antennas, ues = simulate_packet_transmission(fichier_de_cas, fichier_de_device, antennas, ues)

    # Ecriture des fichiers de sortie et du plot des equipements
    write_pathloss_warning_log_file(warning_log, "pathloss_warning_log.txt", fichier_de_cas)
    write_coordinates_to_file(antennas,ues, fichier_de_cas)
    write_pathloss_to_file(pathlosses, fichier_de_cas)
    write_assoc_ues_to_file(antennas)
    write_assoc_ant_to_file(ues)
    write_transmission_ant_to_file(antennas, fichier_de_cas)
    write_transmission_ue_to_file(ues, fichier_de_cas)
    plot_equipment_positions(antennas, ues, "plot_disposition_equipement")
    plot_average_traffic_ues("average_traffic_ues", ues)
    plot_average_traffic_antennas("average_traffic_antennas", antennas)
    plot_bits_received_per_slot(antennas, ues, fichier_de_cas, "average_traffic_per_slot")
    create_pdf_from_plot(["plot_disposition_equipement.pdf", "average_traffic_per_slot.pdf", "average_traffic_antennas.pdf", "average_traffic_ues.pdf"], pdf_graph_file_name)

if __name__ == '__main__':
    # sys.argv est une liste qui contient les arguments utilisés lors de l'appel 
    # du programme à partir du CLI. Cette liste est créée automatiquement par Python. Vous devez 
    # juste inscrire l'argument tel que montré ci-dessous.
    main(sys.argv[1:])

