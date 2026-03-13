import folium
import pandas as pd


def visualize_solution_folium(nodes_df, P, x, F_p, A_p, inst=None, filename='solution_map.html'):
    """
    Visualize the matheuristic solution using Folium - clean style for papers.
    
    Path segments:
    - Pickup leg (hub → facilities → origin hospital): GREEN dashed
    - Delivery leg (origin hospital → facilities → destination hospital): BLUE solid
    """
    
    # Node coordinate lookup
    node_coords = {}
    node_types = {}
    for _, row in nodes_df.iterrows():
        node_id = row['id']
        node_coords[node_id] = (row['lat'], row['lon'])
        node_types[node_id] = row['type']
    
    def get_base_node(node_str):
        """Extract base node ID from path node string."""
        if '_origin_' in node_str:
            return node_str.split('_origin_')[0]
        elif '_dest_' in node_str:
            return node_str.split('_dest_')[0]
        return node_str
    
    # Get active paths
    active_paths = [p for p in P if hasattr(x[p], 'X') and x[p].X > 0.5]
    
    # Collect edges by type
    pickup_edges = []    # hub → origin (green)
    delivery_edges = []  # origin → destination (blue)
    active_nodes = set()
    used_facilities = set()
    used_hubs = set()
    
    for path_id in active_paths:
        path = P[path_id]
        is_hub_path = 'P_j_ik_jk_' in path_id
        
        if path_id in F_p:
            used_facilities.update(F_p[path_id])
        
        if isinstance(path, list) and len(path) > 1:
            # Find origin hospital index (first hospital in path)
            origin_idx = None
            for i, node in enumerate(path):
                base = get_base_node(str(node))
                if node_types.get(base) == 'hospital':
                    origin_idx = i
                    break
            
            for i in range(len(path) - 1):
                node1 = get_base_node(str(path[i]))
                node2 = get_base_node(str(path[i + 1]))
                
                if node1 not in node_coords or node2 not in node_coords:
                    continue
                
                active_nodes.add(node1)
                active_nodes.add(node2)
                
                edge = (node1, node2)
                
                # Classify edge
                if is_hub_path and origin_idx is not None and i < origin_idx:
                    # Pickup leg: hub → origin
                    pickup_edges.append(edge)
                    if node_types.get(node1) == 'hub':
                        used_hubs.add(node1)
                else:
                    # Delivery leg: origin → destination
                    delivery_edges.append(edge)
    
    # Map center
    if active_nodes:
        lats = [node_coords[n][0] for n in active_nodes if n in node_coords]
        lons = [node_coords[n][1] for n in active_nodes if n in node_coords]
        center = [sum(lats)/len(lats), sum(lons)/len(lons)]
    else:
        center = [nodes_df['lat'].mean(), nodes_df['lon'].mean()]
    
    # Create map - clean white style
    m = folium.Map(
        location=center,
        zoom_start=9,
        tiles='CartoDB positron'
    )
    
    # === DRAW INACTIVE NODES FIRST (background) ===
    for _, row in nodes_df.iterrows():
        node_id = row['id']
        if node_id in active_nodes:
            continue
        
        ntype = row['type']
        
        if ntype == 'hospital':
            folium.RegularPolygonMarker(
                location=[row['lat'], row['lon']],
                number_of_sides=4,
                radius=6,
                rotation=45,
                color='#9d0208',
                fill=True,
                fillColor='#d62828',
                fillOpacity=0.3,
                weight=1.5,
                popup=f"{node_id}"
            ).add_to(m)
        elif ntype == 'facility':
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                color='#023e8a',
                fill=True,
                fillColor='#0077b6',
                fillOpacity=0.3,
                weight=1.5,
                popup=f"{node_id}"
            ).add_to(m)
        elif ntype == 'hub':
            folium.RegularPolygonMarker(
                location=[row['lat'], row['lon']],
                number_of_sides=3,
                radius=9,
                color='#1b4332',
                fill=True,
                fillColor='#2d6a4f',
                fillOpacity=0.3,
                weight=1.5,
                popup=f"{node_id}"
            ).add_to(m)
    
    # === DRAW EDGES ===
    # Pickup edges (green, dashed)
    for n1, n2 in pickup_edges:
        if n1 in node_coords and n2 in node_coords:
            folium.PolyLine(
                [[node_coords[n1][0], node_coords[n1][1]],
                 [node_coords[n2][0], node_coords[n2][1]]],
                color='#2d6a4f',
                weight=3.5,
                opacity=0.9,
                dash_array='10,5'
            ).add_to(m)
    
    # Delivery edges (blue, solid)
    for n1, n2 in delivery_edges:
        if n1 in node_coords and n2 in node_coords:
            folium.PolyLine(
                [[node_coords[n1][0], node_coords[n1][1]],
                 [node_coords[n2][0], node_coords[n2][1]]],
                color='#1d3557',
                weight=3.5,
                opacity=0.9
            ).add_to(m)
    
    # === DRAW ACTIVE NODES (foreground) ===
    active_hospitals = set()
    active_stations = set()
    active_hubs = set()
    
    for node_id in active_nodes:
        if node_id not in node_coords:
            continue
        
        lat, lon = node_coords[node_id]
        ntype = node_types.get(node_id, 'unknown')
        
        if ntype == 'hospital':
            active_hospitals.add(node_id)
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=4,
                radius=10,
                rotation=45,
                color='#9d0208',
                fill=True,
                fillColor='#d62828',
                fillOpacity=1.0,
                weight=2,
                popup=f"<b>{node_id}</b>"
            ).add_to(m)
            
        elif ntype == 'facility':
            active_stations.add(node_id)
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color='#023e8a',
                fill=True,
                fillColor='#0077b6',
                fillOpacity=1.0,
                weight=2,
                popup=f"<b>{node_id}</b>"
            ).add_to(m)
            
        elif ntype == 'hub':
            active_hubs.add(node_id)
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=3,
                radius=14,
                color='#1b4332',
                fill=True,
                fillColor='#2d6a4f',
                fillOpacity=1.0,
                weight=2.5,
                popup=f"<b>{node_id}</b>"
            ).add_to(m)
    
    # Stats
    n_direct = len([p for p in active_paths if 'P_ik_jk_' in p and 'P_j_ik_jk_' not in p])
    n_hub = len([p for p in active_paths if 'P_j_ik_jk_' in p])
    
    # Legend - clean academic style
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 30px; left: 30px; 
                background: white;
                padding: 14px 16px;
                border: 1px solid #888;
                border-radius: 3px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 11px;
                line-height: 1.9;
                box-shadow: 0 1px 4px rgba(0,0,0,0.12);
                z-index: 9999;">
        
        <div style="font-weight: 600; font-size: 11px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 6px;">
            Legend
        </div>
        
        <table style="border-collapse: collapse;">
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="16" height="16" style="vertical-align: middle;">
                        <rect x="3" y="3" width="10" height="10" transform="rotate(45 8 8)" fill="#d62828" stroke="#9d0208" stroke-width="1.5"/>
                    </svg>
                </td>
                <td>Hospital</td>
            </tr>
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="16" height="16" style="vertical-align: middle;">
                        <circle cx="8" cy="8" r="5" fill="#0077b6" stroke="#023e8a" stroke-width="1.5"/>
                    </svg>
                </td>
                <td>Recharging station</td>
            </tr>
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="16" height="16" style="vertical-align: middle;">
                        <polygon points="8,2 14,14 2,14" fill="#2d6a4f" stroke="#1b4332" stroke-width="1.5"/>
                    </svg>
                </td>
                <td>Distribution hub</td>
            </tr>
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="16" height="16" style="vertical-align: middle;">
                        <rect x="3" y="3" width="10" height="10" transform="rotate(45 8 8)" fill="#ccc" stroke="#aaa" stroke-width="1"/>
                    </svg>
                </td>
                <td style="color: #666;">Inactive node</td>
            </tr>
            <tr><td colspan="2" style="height: 8px;"></td></tr>
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="24" height="12" style="vertical-align: middle;">
                        <line x1="0" y1="6" x2="24" y2="6" stroke="#2d6a4f" stroke-width="3" stroke-dasharray="6,3"/>
                    </svg>
                </td>
                <td>Pickup leg</td>
            </tr>
            <tr>
                <td style="padding: 2px 8px 2px 0;">
                    <svg width="24" height="12" style="vertical-align: middle;">
                        <line x1="0" y1="6" x2="24" y2="6" stroke="#1d3557" stroke-width="3"/>
                    </svg>
                </td>
                <td>Delivery leg</td>
            </tr>
        </table>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save(filename)
    
    print(f"Map saved: {filename}")
    print(f"  Paths: {len(active_paths)} ({n_direct} direct, {n_hub} via hub)")
    print(f"  Nodes: {len(active_hospitals)} hospitals, {len(active_stations)} stations, {len(active_hubs)} hubs")
    
    return m