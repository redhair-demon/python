import random
import networkx as nx
import matplotlib.pyplot as plt
import gen_names as gn
import graph_gen as gg

WIDTH = 5632

prov_file_format = """base_manpower = {}
base_tax = {}
base_production = {}

culture = {}
religion = {}

native_size = 20                # The stack size of the natives that attack (make sure "is_city = no", or there will be zero natives appearing in a province)
native_ferocity = 4             # How tough the native attack will be
native_hostileness = 3          # How likely natives are to attack

{}
"""

def set_lakes(provinces: dict, loc):
    names = gn.generate_names(len(provinces))
    for i, p in enumerate(provinces):
        if ('SEA_ZONE' in provinces[p]['type'] and 
            all(['SEA_ZONE' not in provinces[x]['type'] for x in provinces[p]['adj']])):
            provinces[p]['type'] = provinces[p]['type'].replace("SEA_ZONE", "LAKE")
        provinces[p]['name'] = names[i]
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(f" PROV{provinces[p]['province']}: \"{f_name(provinces[p]['name'])}\"\n PROV_ADJ{provinces[p]['province']}: \"{f_name(provinces[p]['name'])}{random.choice(['an', 'ian', 'er'])}\"\n")
    return provinces

def split_lwsl(provinces: dict):
    lands, wastes, seas, lakes = {}, {}, {}, {}
    for p in provinces:
        name = provinces[p]['type']
        if 'SEA_ZONE' in name: seas[p] = provinces[p]
        elif 'PROVINCE' in name: lands[p] = provinces[p]
        elif 'WASTELAND' in name: wastes[p] = provinces[p]
        elif 'LAKE' in name: lakes[p] = provinces[p]
    return lands, wastes, seas, lakes

def print_areas(file, areas, provinces, loc, prefix = "Group areas"):
    file.write(f'\n# {prefix}\n\n')
    for key in areas:
        file.write(f'{areas[key]["name"]} = {{ # N={len(areas[key]["in"])}\n\t{" ".join([provinces[x]["province"] for x in areas[key]["in"]])} \n}}\n')
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(yml_name(areas[key]['name'], f_name(areas[key]['name'])))
            # file_loc.write(f" {areas[key]['name']}:0 \"{f_name(areas[key]['name'])}\"\n")

def print_regions(file, regions, loc, prefix = "Group regions"):
    file.write(f'\n# {prefix}\n\n')
    for key in regions: 
        file.write(f'{regions[key]["name"]} = {{\n\tareas = {{\n\t\t{" ".join([x for x in regions[key]["in"]])}\n\t}}\n}}\n')
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(yml_name(regions[key]['name'], f_name(regions[key]['name'])))

def print_sr(file, srs, loc, prefix = "Group superregions"):
    file.write(f'\n# {prefix}\n\n')
    for key in srs: 
        file.write(f'{srs[key]["name"]} = {{\n\t{" ".join([x for x in srs[key]["in"]])} \n}}\n')
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(yml_name(srs[key]['name'], f_name(srs[key]['name'])))

def split_list(input_list, n):
    res = [[] for _ in range(n)]
    for i, l in enumerate(input_list):
        res[i % n].append(l)
    return res

def print_continents(file, cont, srs, rs, ars, all_provs, path, prefix, cultures, religions, techs, loc):
    file.write(f'\n# {prefix}\n\n')
    rel = split_list(random.sample(list(religions.keys()), len(religions)), len(cont))
    cul = split_list(random.sample(list(cultures.keys()), len(cultures)), len(cont))
    natives = [False for _ in cont]
    natives[:len(cont)//3] = [True for _ in range(len(cont)//3)]
    random.shuffle(natives)
    for p in all_provs:
        all_provs[p]['tech'] = 'yet'
    for index, key in enumerate(cont): 
        provs = set()
        cont[key]['natives'] = natives[index]
        for sr in cont[key]['in']:
            srs[sr]['tech'] = random.choices(techs)[0]
            srs[sr]['rel'] = random.choices(rel[index], [len(religions[x]) for x in rel[index]])[0]
            for r in srs[sr]['in']:
                rs[r]['rel'] = random.choice(list(religions[srs[sr]['rel']]))
                rs[r]['cult'] = random.choices(cul[index], [len(cultures[x]) for x in cul[index]])[0]
                for a in rs[r]['in']:
                    ars[a]['cult'] = random.choice(list(cultures[rs[r]['cult']]))
                    for p in ars[a]['in']:
                        provs.add(p)
                        all_provs[p]['cult'] = ars[a]['cult']
                        all_provs[p]['rel'] = rs[r]['rel']
                        empty = random.choice(["WASTE" in all_provs[x]["type"] or all_provs[x]['tech'] == "" for x in all_provs[p]['adj']])
                        if empty or random.choices([cont[key]['natives'], False], [9, 1])[0]: all_provs[p]['tech'] = ""
                        else: all_provs[p]['tech'] = f"\nowner = R{techs.index(srs[sr]['tech']):02d}\n"
        for x in provs:
            with open(f"{path}/history/provinces/{all_provs[x]['province']} - {all_provs[x]['name']}.txt", 'w') as prov_file:
                if "WASTE" not in all_provs[x]["type"]:
                    prov_file.write(prov_file_format.format(2, 2, 2, all_provs[x]['cult'], all_provs[x]['rel'], all_provs[x]['tech']))
        file.write(f'{cont[key]["name"]} = {{\n\t{" ".join([all_provs[x]["province"] for x in provs])} \n}}\n')
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(yml_name(cont[key]['name'], f_name(cont[key]['name'])))

def print_trade_node(node, g: nx.DiGraph, trades, all_provs, file_tn, file_tc, loc, apg: nx.Graph):
    if not trades[node]['printed']:
        for pr in g.pred[node]:
            if trades[pr]['printed']: continue
            print_trade_node(pr, g, trades, all_provs, file_tn, file_tc, loc, apg)
        if not nx.is_connected(apg): print("error here")
        color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
        outgoing = "\n\t".join([f"outgoing={{\n\t\tname=\"{x}\"\n\t\tpath={{{' '.join([all_provs[p]['province'] for p in nx.shortest_path(apg, trades[node]['mem'][0], trades[x]['mem'][0], weight='weight')])}}}\n\t}}" for x in g.succ[node]])
        file_tn.write(f'{trades[node]["name"]} = {{\n\tcolor = {{ {color[0]} {color[1]} {color[2]} }} \n\tlocation={trades[node]["loc"]} \n\t{outgoing} \n\tmembers={{\n\t\t{" ".join([all_provs[x]["province"] for x in trades[node]["mem"]])}\n\t}} \n}}\n')
        file_tc.write(f'{trades[node]["name"]}_tc = {{\n\tcolor = {{ {color[0]} {color[1]} {color[2]} }} \n\tprovinces={{\n\t\t{" ".join([all_provs[x]["province"] for x in trades[node]["mem"]])}\n\t}} \n\tnames = {{ name = \"{trades[node]["name"].upper()}_TC_Root_Culture_GetName\" }} \n\tnames = {{ name = \"{trades[node]["name"].upper()}_TC_Trade_Company\" }} \n}}\n')
        
        
        trades[node]['printed'] = True
        with open(loc, 'a', encoding='utf-8-sig') as file_loc:
            file_loc.write(yml_name(trades[node]['name'], f_name(trades[node]['name']), "trade"))
            file_loc.write(yml_name(f"{trades[node]['name']}_tc", f"{f_name(trades[node]['name'])} Charter", "trade"))
            file_loc.write(yml_name(f"{trades[node]['name'].upper()}_TC_Root_Culture_GetName", f"[Root.GetAdjective] {f_name(trades[node]['name'])} Trade Company", "trade"))
            file_loc.write(yml_name(f"{trades[node]['name'].upper()}_TC_Trade_Company", f"{f_name(trades[node]['name'])} Trade Company", "trade"))

def connect(input_cc, g: nx.DiGraph, provs):
    sorted_cc = sorted(input_cc, key=len)
    done = []
    cc = sorted_cc[0]
    closest = {'dist': None, 'from': None, 'to': None}
    for cc2 in filter(lambda b: sorted_cc.index(b)>sorted_cc.index(cc), sorted_cc):
        if cc2 in done: continue
        for cc_i in cc:
            cl = sort_closest(provs[cc_i], provs, cc2, cyl=True)
            if closest['dist'] == None or (distance(provs[cc_i]['xy'], provs[cl[0]]['xy']) < closest['dist']):
                closest['dist'] = distance(provs[cc_i]['xy'], provs[cl[0]]['xy'])
                closest['from'] = cc_i
                closest['to'] = cl[0]
                if (closest['dist'] == 0): print("zerooo")
    g.add_edge(closest['from'], closest['to'])

    return g

def connets(g: nx.DiGraph, provs: dict, limit_dist: int, limit_size: int):
    for n in g.nodes:
        cl = sort_closest(provs[n], provs, cyl=True)
        for c in cl:
            if c == n or nx.has_path(g, n, c) or len(g[n]) + len(g.pred[n]) >= limit_size or distance(provs[c]['xy'], provs[n]['xy'], cyl=True) > limit_dist**2 or len(list(nx.all_simple_paths(g, c, n))) >= 1:
                continue
            g.add_edge(c, n)
        if len(g[n]) + len(g.pred[n]) == 0:
            g.add_edge(cl[1], n)
    
    while not nx.is_weakly_connected(g):
        g = connect(nx.weakly_connected_components(g), g, provs)

    return g

def print_trades(file_tc, file_tn, trades, ars, all_provs, path, limit_dist, limit_size, loc, real_all):
    keys = list(trades.keys())
    G = nx.DiGraph()
    for key in keys: 
        trades[key]['out'] = set()
        G.add_nodes_from([(key, {"xy": (trades[key]['xy'][1], -trades[key]['xy'][0])})])
    G = connets(G, trades, limit_dist, limit_size)
   
    
    for key in keys: 
        provs = set()
        for a in trades[key]['in']:
            for p in ars[a]['in']:
                provs.add(p)
        trades[key]['mem'] = list(provs)
        trades[key]['loc'] = all_provs[trades[key]['mem'][0]]["province"]
        trades[key]['posts'] = set(random.choices(list(trades[key]['mem']), k=hash(key) % 6 + 2))
        trades[key]['posts'].add(trades[key]['mem'][0])
        trades[key]['printed'] = False
        for post in trades[key]['posts']:
            with open(f"{path}/history/provinces/{all_provs[post]['province']} - {all_provs[post]['name']}.txt", 'a') as prov_file:
                prov_file.write(f"\ncenter_of_trade = 1\n")
    apl = real_all.copy()
    # print(apl)
    apg = nx.Graph()
    apg.add_nodes_from((a, {'xy': apl[a]['xy']}) for a in apl)
    for p in apl:
        for adj in apl[p]['adj']:
            if adj in apl: 
                pt = apl[p]['type']
                at = apl[adj]['type']
                apg.add_edge(p, adj, weight=2 if 'SEA' in pt and 'SEA' in at else 0.5 if 'PROV' in pt and 'PROV' in at else 3 if ('SEA' in pt and 'PROV' in at) or ('SEA' in at and 'PROV' in pt) else 10000 if 'WASTE' in at or 'WASTE' in pt else 1000)
    
    for node in G:
        print_trade_node(node, G, trades, apl, file_tn, file_tc, loc, apg)
    
def center(prov_keys, all_provs):
    x = sum([all_provs[i]['xy'][0] for i in prov_keys])//len(prov_keys)
    y = sum([all_provs[i]['xy'][1] for i in prov_keys])//len(prov_keys)
    return [x, y]

def distance(a, b, cyl=False):
    if cyl: return (min(abs(a[1] - b[1]), WIDTH - abs(a[1] - b[1])))**2 + (a[0] - b[0])**2
    return (a[0] - b[0])**2 + (a[1] - b[1])**2

def sort_closest(prov: dict, all_provs: dict, sorting = None, cyl=False):
    if sorting == None: sorting = all_provs.keys()
    return sorted(sorting, key=lambda p: distance(prov['xy'], all_provs[p]['xy'], cyl=cyl) )# (prov['xy'][0] - all_provs[p]['xy'][0])**2 + (prov['xy'][1] - all_provs[p]['xy'][1])**2)

def group_by_xy(provs: dict, limit_size: list = [3, 10], limit_dist: int = 150, typ: str = "area", cyl = False):
    groups = {}
    print(f"Generating {typ}s from {len(provs)} items...")
    names = gn.generate_names(len(provs))
    for i, l in enumerate(provs):
        name = f"{names[i]}_{typ}"
        if provs[l]['par'] == None:
            cl = sort_closest(provs[l], provs, cyl=cyl)
            for p in filter(lambda a: a!=l, cl):
                if provs[p]['par'] == None:
                    if distance(provs[p]['xy'], provs[l]['xy']) <= (limit_dist)**2:
                        groups[name] = {'in': set([l, p]), 'par': None, 'xy': center([l, p], provs), 'name': name}# random.choice([provs[l]['name'], name])}
                        provs[p]['par'] = name
                        provs[l]['par'] = name
                        break
                else:
                    if len(groups[provs[p]['par']]['in']) > limit_size[1] or distance(groups[provs[p]['par']]['xy'], provs[l]['xy']) > (limit_dist)**2:
                        continue
                    else:
                        groups[provs[p]['par']]['in'].add(l)
                        groups[provs[p]['par']]['xy'] = center(groups[provs[p]['par']]['in'], provs)
                        provs[l]['par'] = provs[p]['par']
                        break
            if provs[l]['par'] == None:
                groups[name] = {'in': set([l]), 'par': None, 'xy': center([l], provs), 'name': name}# random.choice([provs[l]['name'], name])}
                provs[l]['par'] = name
    
    temp = groups.copy()
    for key in temp:
        if key in groups and len(groups[key]['in']) < limit_size[0]:
            cl = sort_closest(groups[key], groups)
            for ar in filter(lambda d: d!=key, cl):
                if len(groups[key]['in']) > limit_size[0]: break
                if distance(groups[key]['xy'], groups[ar]['xy']) <= (limit_dist)**2:
                    deleted = groups.pop(ar)
                    groups[key]['in'].update(deleted['in'])
                    for l in deleted['in']: provs[l]['par'] = key

    return groups

def f_name(name: str):
    if "sea_superregion" in name:
        name = f"{name.split('_')[0].capitalize()} ocean"
    elif "sea_region" in name:
        name = f"Sea of {name.split('_')[0].capitalize()}"
    else:
        name = name.split('_')[0].capitalize()
    return name
    
def yml_name(tag:str, name: str, typ: str = "area"):
    if typ == "trade":
        return f" {tag}: \"{name}\"\n"
    else:
        return f" {tag}: \"{name}\"\n {tag}_name: \"{name}\"\n {tag}_adj: \"{name}\"\n"

def gen_areas(provinces: dict, path: str, cultures: dict, religions: dict, techs: list, seed: int = 1):
    # random.seed(seed)
    
    areas_loc = f"{path}/localisation/random_map_mod_loc_l_english.yml"
    with open(areas_loc, 'w', encoding='utf-8-sig') as file:
        file.write("l_english:\n")

    provinces = set_lakes(provinces, areas_loc)
    temp = provinces.copy()
    for i in temp:
        temp[i]['par'] = None
    lands, wastes, seas, lakes = split_lwsl(temp)
    # land_areas = group_by_xy(lands, [3, 8])
    land_areas = gg.group_kmean(lands, 6, "area")
    # sea_areas = group_by_xy(seas, [6, 10], 800)
    sea_areas = gg.group_kmean(seas, 8, "sea_area")

    with open(f'{path}/map/area.txt', 'w') as file:
        print_areas(file, land_areas, provinces, areas_loc, "Land areas")
        print_areas(file, sea_areas, provinces, areas_loc, "Sea areas")

    # land_regions = group_by_xy(land_areas, [4, 6], 400, "region")
    land_regions = gg.group_kmean(land_areas, 5, "region")
    # sea_regions = group_by_xy(sea_areas, [4, 6], 1000, "sea_region")
    sea_regions = gg.group_kmean(sea_areas, 5, "sea_region")

    with open(f'{path}/map/region.txt', 'w') as file:
        print_regions(file, land_regions, areas_loc, "Land regions")
        print_regions(file, sea_regions, areas_loc, "Sea regions")

    # land_sr = group_by_xy(land_regions, [4, 8], 1000, "superregion")
    land_sr = gg.group_kmean(land_regions, 5, "superregion")
    # sea_sr = group_by_xy(sea_regions, [3, 6], 1500, "sea_superregion", cyl=True)
    sea_sr = gg.group_kmean(sea_regions, 5, "sea_superregion")

    with open(f'{path}/map/superregion.txt', 'w') as file:
        print_sr(file, land_sr, areas_loc, "Land superregions")
        print_sr(file, sea_sr, areas_loc, "Sea superregions")

    
    # continents = group_by_xy(land_sr, [3, 6], 2000, "continent")
    continents = gg.group_kmean(land_sr, 4, "continent")

    # adding wastelands to continents begin
    waste_areas = {x: {'in': set([x]), 'par': x, 'xy': provinces[x]['xy'], 'name': f"waste_{x}"} for x in wastes}
    lw_sr, lw_reg, lw_ar = land_sr.copy(), land_regions.copy(), land_areas.copy()
    lw_sr.update(waste_areas)
    lw_reg.update(waste_areas)
    lw_ar.update(waste_areas)

    for w in waste_areas:
        cl = sort_closest(waste_areas[w], lands)
        continents[land_sr[land_regions[land_areas[lands[cl[0]]['par']]['par']]['par']]['par']]['in'].add(w)
    # end

    with open(f'{path}/map/continent.txt', 'w') as file:
        print_continents(file, continents, lw_sr, lw_reg, lw_ar, provinces, path, "custom continents", cultures, religions, techs, areas_loc)

    temp = {}
    for l in reversed(list(land_areas.keys())):
        temp[l] = land_areas[l]
        temp[l]['par'] = None
    # trades = group_by_xy(temp, [6, 12], 700, "trade")
    trades = gg.group_kmean(temp, 9, "trade")
    # print(len(trades))
    with open(f"{path}/common/tradenodes/00_tradenodes.txt", 'w') as file_tn:
        with open(f"{path}/common/trade_companies/00_trade_companies.txt", 'w') as file_tc:
            print_trades(file_tc, file_tn, trades, land_areas, lands, path, 500, 3, areas_loc, provinces)

    return land_areas
    

        