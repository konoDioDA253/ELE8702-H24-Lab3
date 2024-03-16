### Calcul du pathloss avec les formules 3GPP
# On considere seulement les scenario RMa, UMa et UMi
import math
import sys
infini = float('inf') #définition de l'infini
# Fonction donnant le group et les coords a partir du ID d'un objet dans une liste du meme objet
# Nbre Param: 2 (liste d'obets de type ue ou antenne et l'identifiant de l'objet)
def get_group_and_coords_by_id_3GPP(object_list, target_id):
    for object in object_list:
        if object.id == target_id:
            return object.group, object.coords
    return None  

# Fonction calculant la distance entre deux point sur le terrain
# Nbre Param: 2 (coodonnées du point 1 et 2 )
# Valeur de retour: valeur numerique de la distance calculer
def calculate_distance_3GPP(coord1, coord2):
    x1, y1 = coord1 # coordonnées du premier point
    x2, y2 = coord2 # coordonnées du deuxième point
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Fonction permettant d'afficher un message d'erreur et de stopper le programme
# Nbre Param: 2 (message à envoyer et code d'erreur )
def ERROR_3GPP(msg , code = 1):
    print("\n\n\nERROR\nPROGRAM STOPPED!!!\n")
    if msg:
        print(msg)
    print(f"\n\texit code = {code}\n\n\t\n")
    sys.exit(code)

# Fonction permettant de trouver la valeur d'une cle dans un fichier YAML
# Nbre Param: 5 (key = clé recherché, data = contenu fichier yaml, res = valeur rechercher, curr_level = niveau actuel, min_level =  niveau minimal de profondeur à partir duquel la recherche est autorisée)
# Valeur de retour: res = valeur rechercher
def get_from_dict_3GPP(key, data, res=None, curr_level = 1, min_level = 1):
    """Fonction qui retourne la valeur de n'importe quel clé du dictionnaire
       key: clé associé à la valeur recherchée
       data: dictionnaire dans lequel il faut chercher
       les autres sont des paramètres par défaut qu'il ne faut pas toucher"""
    if res:
        return res
    if type(data) is not dict:
        msg = f"get_from_dict_3GPP() works with dicts and is receiving a {type(data)}"
        ERROR_3GPP(msg, 1)
    else:
        # data IS a dictionary
        for k, v in data.items():
            if k == key and curr_level >= min_level:
                #print(f"return data[k] = {data[k]} k = {k}")
                return data[k]
            if type(v) is dict:
                level = curr_level + 1
                res = get_from_dict_3GPP(key, v, res, level, min_level)
    return res 

# Fonction permet de verifier que la hauteur d'un equipement antenne & ue est bien dans l'intervalle definit
# Nbre param: 4 ( value = valeur la hauteur, range1 = borne sup, range2 = borne inf, id_ue = indentifiant ue et id_ant = indentifiant antenne)
# Valeur de retour: warning_message =messager a l'usager
def check_range(value, range1, range2, id_ue, id_ant):
    warning_message = ""
    if value < range1 or value > range2:
        warning_message = f"""WARNING HAUTEUR: La hauteur {value}m  d'un equipement de la combinaison UE {id_ue} et antenne {id_ant} est en dehors de l'intervalle [{range1}m, {range2}m].
Nous ne pouvons pas appliquer les formules de calcul du pathloss 3GPP.
Le programme poursuit malgré cela en assumant les valeurs fournies pour cette combinaison d'equipements...\n"""
    return warning_message








# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     RMa LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

# Cas RMA LOS : Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# Valeur de retour: pl = pathloss calculer
def rma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # Definition des fonctions retourne le minimum des deux valeurs passées en paramétre
    # Valeur de retour: val = valeur minimal
    def valeur_minimum(val1, val2):
        if val1 < val2:
            val = val1
        if val1 >= val2:
            val = val2
        return val
    # Cette fonction retourne la valeur du pathloss pl dans le cas RMa pour les condition de min respectés
    # Nbre de param: 3 (distance_3D_m = distance entre sommet ue et sommet antenne, frequence_GHz = frequence de l'antenne en Ghz, hauteur_standard_m = hauteur standard definir pour la formule de 3gpp)
    # Valeur de retour: pl = valeur numerique du pathoss calculer
    def _rma_los_pl1(distance_3D_m, frequence_GHz, hauteur_standard_m):
        min1 = valeur_minimum(0.03*pow(hauteur_standard_m, 1.72), 10)
        min2 = valeur_minimum(0.044*pow(hauteur_standard_m, 1.72), 14.77)
        pl = 20*math.log10(40*math.pi*distance_3D_m*frequence_GHz/3) + min1*math.log10(distance_3D_m) - min2 + 0.002*math.log10(hauteur_standard_m)*distance_3D_m
        return pl
    # Cette fonction retourne la valeur du pathloss pl dans le cas RMa 
    # Nbre de param: 3 (distance_3D_m = distance entre sommet ue et sommet antenne, frequence_GHz = frequence de l'antenne en Ghz, hauteur_standard_m = hauteur standard definir pour la formule de 3gpp)
    # Valeur de retour: pl = valeur numerique du pathoss calculer
    def _rma_los_pl2(distance_3D_m, frequence_GHz, hauteur_standard_m, distance_BP_m):
        pl1 = _rma_los_pl1(distance_BP_m, frequence_GHz, hauteur_standard_m)
        pl = pl1 + 40*math.log10(distance_3D_m/distance_BP_m)
        return pl
    
    # Definition des variables
    c = 3e8 # vitesse en m/s
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords) # distance entre la base de l'UE et l'antenne associer en metre
    distance_2D_km = distance_2D_m/1000     # distance entre la base de l'UE et l'antenne associer en km
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device))) # fréquence antenne en GHz
    frequence_Hz = 1000000000*frequence_GHz # fréquence antenne en Hz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device))) # hauteur de l'antenne en m
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device)) # hauteur de l'ue en km
    hauteur_standard_m = 5 # corresponds a la hauteur de batiment moyenne, 5m par defaut



    distance_BP_m = 2* math.pi * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c # distance de Breakpoint en m
    distance_BP_km = distance_BP_m/1000 # distance de Breakpoint en km

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) # distance entre le sommet de l'ue et l'antenne en m
    distance_3D_km = distance_3D_m/1000     # distance entre le sommet de l'ue et l'antenne en km
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message += check_range(hauteur_BS_m, 10, 150, ue_id, antenna_id)
    warning_message += check_range(hauteur_UT_m, 1, 10, ue_id, antenna_id)
    warning_message += check_range(hauteur_standard_m, 5, 50, ue_id, antenna_id)

    # Calcul de pathloss (on verifie les condition sur la distance standard et on applique la formule associé pour le calcul du pathloss)
    # Valeur de retour: pathloss = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_m < distance_BP_m :
        pathloss = _rma_los_pl1(distance_3D_m, frequence_GHz, hauteur_standard_m)
    if distance_BP_km < distance_2D_km and distance_2D_km < 10 :
        pathloss = _rma_los_pl2(distance_3D_m, frequence_GHz, hauteur_standard_m, distance_BP_m)
    if distance_2D_m < 10 :
        warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
        pathloss = 0
    if 10 < distance_2D_km :
        warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 10 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
        pathloss = infini
    return pathloss, warning_message

# Cas RMA NLOS :Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont non aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# Valeur de retour: pathloss = pathloss calculer, warning_message = message d'avertissement
def rma_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions (fonction retournant le max des deux valeurs passée en paramètre et un message d'avertissement)
    # Nbre param: 4 (pl_los = Valeur du pathloss en los , pl_nlosp = valeur du pathloss en nlos, warning_message_rma_los, warning_message_rma_nlosp)
    # Valeur de retour: pl = valeur max des deux pathloss et message d'avertissement associer
    def max_comparator(pl_los, pl_nlosp, warning_message_rma_los, warning_message_rma_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_rma_nlosp # on recupére le message d'erreur correspondant à la situation de nlos
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_rma_los   # on recupére le message d'erreur correspondant à la situation de los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8 # la vitesse de la lumière en m/m
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords) # distance entre la base de l'UE et l'antenne associer en metre
    distance_2D_km = distance_2D_m/1000  # distance entre la base de l'UE et l'antenne associer en km
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))    # frequence de l'antenne en GHz
    frequence_Hz = 1000000000*frequence_GHz # Frequence de l'antenne en GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))    # Hauteur de l'antenne en m
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device)) # Hauteur de l'ue en m
    hauteur_standard_m = 5 # corresponds a la hauteur de batiment moyenne, 5m par defaut
    largeur_standard_m = 20 # correspond a la largeur moyenne des rues, 20m par defaut

    distance_BP_m = 2* math.pi * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) # distance entre le sommet de l'ue et l'antenne en m
    distance_3D_km = distance_3D_m/1000  # distance entre le sommet de l'ue et l'antenne en km
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message_rma_nlosp = ""
    warning_message_rma_nlosp += check_range(hauteur_BS_m, 10, 150, ue_id, antenna_id)
    warning_message_rma_nlosp += check_range(hauteur_UT_m, 1, 10, ue_id, antenna_id)
    warning_message_rma_nlosp += check_range(hauteur_standard_m, 5, 50, ue_id, antenna_id)
    warning_message_rma_nlosp += check_range(largeur_standard_m, 5, 50, ue_id, antenna_id)

    # Calcul de pathloss (on verifie les condition sur la distance standard et on applique la formule associé pour le calcul du pathloss)
    # Valeur de retour: pl = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_rma_los = ""
        pl_rma_los, warning_message_rma_los = rma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_rma_nlosp = 161.04 - 7.1*math.log10(largeur_standard_m) + 7.5*math.log10(hauteur_standard_m) - (24.37 - 3.7*(hauteur_standard_m/hauteur_BS_m)**2)*math.log10(hauteur_BS_m) + (43.42 - 3.1*math.log10(hauteur_BS_m))*(math.log10(distance_3D_m) - 3) + 20*math.log10(frequence_GHz) - (3.2*(math.log10(11.75*hauteur_UT_m))**2 - 4.97)
        pathloss, warning_message = max_comparator(pl_rma_los, pl_rma_nlosp, warning_message_rma_los, warning_message_rma_nlosp)
    if distance_2D_m < 10  :
        warning_message += warning_message_rma_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
        pathloss = 0
    if 5 < distance_2D_km :
        warning_message += warning_message_rma_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
        pathloss = infini
    return pathloss, warning_message























# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     UMa LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

# Cas UMA LOS : Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# valeur de retour: pathloss= pathloss calculer , warning_message = message d'avertissement
def uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # cette fonction calcul le pathloss pour la valeur de distance  et la fréquence passer en paramétre
    # Nbre de param: 2 (distance_3D_m = distance entre sommet ue et sommet antenne , frequence_GHz = fréquence de l'antenne en GHz)
     # Valeur de retour: pl = valeur numerique du pathoss calculer
    def _uma_los_pl1(distance_3D_m, frequence_GHz):
        pl = 28.0 + 22*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz)
        return pl

    def _uma_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m):
        pl = 28.0 + 40*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) - 9*math.log10(distance_prime_BP_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) 
        return pl
    
    # Definition des variables
    c = 3e8 # vitesse en m/s
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords) # distance entre la base de l'UE et l'antenne associer en metre
    distance_2D_km = distance_2D_m/1000     # distance entre la base de l'UE et l'antenne associer en km
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device))) # frenquence de l'atenne en Ghz
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device))) # hauteur de antenne en m
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device)) #hauteur de l'ue en m

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    # distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    # distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) # distance entre le sommet de l'ue et l'antenne en m
    distance_3D_km = distance_3D_m/1000 # distance entre le sommet de l'ue et l'antenne en km

    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message += check_range(hauteur_UT_m, 1.5, 22.5, ue_id, antenna_id)

    # Calcul de pathloss (on verifie les condition sur la distance standard et on applique la formule associé pour le calcul du pathloss en appelant la fontion predefinit)
    # Valeur de retour: pathloss = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_m < distance_prime_BP_m :
        pathloss = _uma_los_pl1(distance_3D_m, frequence_GHz)
    if distance_prime_BP_km < distance_2D_km and distance_2D_km < 5 :
        pathloss = _uma_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m)
    if distance_2D_m < 10 :
            warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message

# Cas UMA LOS : Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont non aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# valeur de retour: pathloss= pathloss calculer , warning_message = message d'avertissement
def uma_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    

    # Definition des fonctions (fonction retournant le max des deux valeurs passée en paramètre et un message d'avertissement)
    # Nbre param: 4 (pl_los = Valeur du pathloss en los , pl_nlosp = valeur du pathloss en nlos, warning_message_rma_los, warning_message_rma_nlosp)
    # Valeur de retour: pl = pathloss correspondant aux conditions et warning_message = message d'avertissement 
    def max_comparator(pl_los, pl_nlosp, warning_message_uma_los, warning_message_uma_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_uma_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_uma_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8 # vitesse en m/s
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device))) # frequence de l'antenne en Ghz
    frequence_Hz = 1000000000*frequence_GHz  # frequence de l'antenne en Hz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))    # hauteur de l'antenne en metre
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))     # Hauteur de l'ue en m

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    # distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    # distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)      # distance entre le sommet de l'ue et l'antenne en m
    distance_3D_km = distance_3D_m/1000     # distance entre le sommet de l'ue et l'antenne en km
    
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message_uma_nlosp = ""
    warning_message_uma_nlosp += check_range(hauteur_UT_m, 1.5, 22.5, ue_id, antenna_id)

    # Calcul de pathloss(on verifie les condition sur la distance standard dans le cas UMa et on applique la formule associé pour le calcul du pathloss)
    # Valeur de retour: pathloss = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_uma_los = ""
        pl_uma_los, warning_message_uma_los = uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_uma_nlosp = 13.54 + 39.08*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) -0.6*(hauteur_UT_m - 1.5)
        pathloss, warning_message = max_comparator(pl_uma_los, pl_uma_nlosp, warning_message_uma_los, warning_message_uma_nlosp)
    if distance_2D_m < 10  :
            warning_message += warning_message_uma_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message += warning_message_uma_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message






























# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     UMi LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
# Cas UMi LOS : Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# Valeur de retour: pl = pathloss calculer
def umi_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # cette fonction calcul le pathloss pour la valeur de distance  et la fréquence passer en paramétre dans cas UMi
    # Nbre de param: 2 (distance_3D_m = distance entre sommet ue et sommet antenne , frequence_GHz = fréquence de l'antenne en GHz)
    # Valeur de retour pl = valeur numerique du pathoss calculer
    def _umi_los_pl1(distance_3D_m, frequence_GHz):
        pl = 32.4 + 21*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz)
        return pl

    # cette fonction calcul le pathloss pour la valeur de distance, fréquence, distance de Breakpoint, hauteur de l'antenne et la hauteur de l'ue passer en paramétre dans cas UMi
    # Nbre de param: 2 (distance_3D_m = distance entre sommet ue et sommet antenne , frequence_GHz = fréquence de l'antenne en GHz)
    # Valeur de retour: pl = valeur numerique du pathoss calculer
    def _umi_los_pl2(distance_3D_m, frequence_GHz, distance_BP_m, hauteur_BS_m, hauteur_UT_m):
        pl = 32.4 + 40*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) - 9.5*math.log10(distance_BP_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) 
        return pl
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))
    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000

    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message += check_range(hauteur_UT_m, 1.5, 22.5, ue_id, antenna_id)

    
    # Calcul de pathloss (on verifie les condition sur la distance standard dan le cas UMi(LOS) et on applique la formule associé pour le calcul du pathloss)
    # Valeur de retour: pathloss = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_m < distance_prime_BP_m :
        pathloss = _umi_los_pl1(distance_3D_m, frequence_GHz)
    if distance_prime_BP_m < distance_2D_m and distance_2D_km < 5 :
        pathloss = _umi_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m)
    if distance_2D_m < 10 :
            warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message += f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message


# Cas UMi NLOS : Cette fonction permet de calculer le pathloss d'une combianaison d'ue et antenne lorsque ces derniers sont non aligées
# Nbre de param: 6 (fichier_de_cas, fichier_de_device, antenna_id = identifiant de l'antenne, ue_id = identiafiant de l'ue, antennas = liste des antenne, ues = liste des ue)
# Valeur de retour: pl = valeur numerique du pathoss calculer
def umi_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions
    def max_comparator(pl_los, pl_nlosp, warning_message_umi_los, warning_message_umi_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_umi_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_umi_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))       ## frequence de l'antenne en GHz 
    frequence_Hz = 1000000000*frequence_GHz     # frequence de l'antenne  en GHz 
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))    # hauteur de l'antenne
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device)) # hauteur de l'ue

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)      # distance entre le sommet de l'ue et l'antenne en m
    distance_3D_km = distance_3D_m/1000     # distance entre le sommet de l'ue et l'antenne en km
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    warning_message = ""
    warning_message_umi_nlosp = ""
    warning_message_umi_nlosp += check_range(hauteur_UT_m, 1.5, 22.5, ue_id, antenna_id)
    
   # Calcul de pathloss (on verifie les condition sur la distance standard dan le cas UMi (NLOS) et on applique la formule associé pour le calcul du pathloss)
    # Valeur de retour: pathloss = valeur numerique du pathoss selon la condition respecter et warning_message = message d'avertissement associé au calcul
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_umi_los = ""
        pl_umi_los, warning_message_umi_los = umi_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_umi_nlosp = 35.3*math.log10(distance_3D_m) + 22.4 + 21.3*math.log10(frequence_GHz) - 0.3*(hauteur_UT_m - 1.5)
        pathloss, warning_message = max_comparator(pl_umi_los, pl_umi_nlosp, warning_message_umi_los, warning_message_umi_nlosp)
    if distance_2D_m < 10  :
            warning_message += warning_message_umi_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if  5 < distance_2D_km :
            warning_message += warning_message_umi_nlosp + f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message