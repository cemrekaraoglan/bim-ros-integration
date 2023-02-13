from stl import mesh
import numpy as np

import ifcopenshell.util.selector
import ifcopenshell.geom
import ifcopenshell
import ifcopenshell.util.schema
import ifcopenshell.util.element
from OCC.Core import Bnd
from OCC.Core import BRepBndLib
import OCC.Core.BRepAlgoAPI
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.TopoDS import *
from OCC.Display.SimpleGui import init_display
from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_Vec
from OCC.Core.StlAPI import *
from OCC.Core.BRep import *
from OCC.Core.TopExp import *
from OCC.Core.TopAbs import *
from OCC.Core.BRepBuilderAPI import *
from OCC.Core.TopLoc import TopLoc_Location
import time
from ifc_export import create_ifc
from IFC2OWL import main
import os
from typing import overload, NewType, Optional, Tuple
Standard_Real = NewType('Standard_Real', float)

display, start_display, add_menu, add_function_to_menu = init_display("wx")

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_PYTHON_OPENCASCADE, True)
current_directory = os.path.dirname(os.path.realpath(__file__))
path = r"/home/ubuntu/ros2/src/slicer/wall_cut/Project1.ifc"
model = ifcopenshell.open(path)

#the thickness of the steel framing behind the gypsumboard
cut_width = 0.1

#default gypsumboard size
gk_size = 1.2

#1- Fetch the shapes from the imported IFC model
def get_shapes(model):

    cuts = []
    walls = []
    openings = []
    p_min_wall = []
    p_max_wall = []
    p_min_opening = []
    p_max_opening = []
    bbox_opening = Bnd.Bnd_Box()
    bbox_walls = []
    bbox_openings = []
    opening_shapes = []

    #placement points for the vertical cut objects
    V_placement_pts = []

    print('Process has started...')
    wall_shapes = []
    bbox_wall = Bnd.Bnd_Box()
     
    #-------------------------------------------------
    # this part will come from IFCOWL file
    walls.append(model.by_type("IfcWall"))
    openings.append(model.by_type("IfcOpeningElement"))
    #--------------------------------------------------

    for wall in walls:
        for i in range(len(wall)):
            bbox_wall = Bnd.Bnd_Box()
            wall_shapes.append(ifcopenshell.geom.create_shape(settings, wall[i]).geometry)
            BRepBndLib.brepbndlib_AddOptimal(wall_shapes[i], bbox_wall)
            p_min_wall.append(bbox_wall.CornerMin())
            p_max_wall.append(bbox_wall.CornerMax())
            bbox_walls.append(bbox_wall)

    for opening in openings:
        for i in range(len(opening)):
            bbox_wall = Bnd.Bnd_Box()
            opening_shapes.append(ifcopenshell.geom.create_shape(settings, opening[i]).geometry)
            BRepBndLib.brepbndlib_AddOptimal(opening_shapes[i], bbox_opening)
            p_min_opening.append(bbox_opening.CornerMin())
            p_max_opening.append(bbox_opening.CornerMax())
            bbox_openings.append(bbox_opening)

    print('Walls are imported...')
    #display.DisplayShape(opening_shapes)
    #display.DisplayShape (wall_shapes)

    #2 - Form the installation cuts using the imported data

    indices = []

    # ---------------------------------------------------
    #deconstruct wall geometry
    print('Wall slicing is starting...')

    for w in range(len(wall_shapes)):
        wall_corner_minX = p_min_wall[w].X()
        wall_corner_minY = p_min_wall[w].Y()
        wall_corner_minZ = p_min_wall[w].Z()
        wall_corner_maxX = p_max_wall[w].X()
        wall_corner_maxY = p_max_wall[w].Y()
        wall_corner_maxZ = p_max_wall[w].Z()
        
    # ---------------------------------------------------

        #create cutting objects for each opening inside the wall
        for s in range(len(opening_shapes)):

            a = bbox_walls[w].IsOut(bbox_openings[s])

            if a == False:
                indices.append(w)

                # ---------------------------------------------------
                #deconstruct opening geometry
                opening_corner_minZ = p_min_opening[s].Z()
                opening_corner_maxZ = p_max_opening[s].Z()
                opening_corner_minX = p_min_opening[s].X()
                opening_corner_maxX = p_max_opening[s].X()
                opening_corner_minY = p_min_opening[s].Y()
                opening_corner_maxY = p_max_opening[s].Y()
                # ---------------------------------------------------

                # ---------------------------------------------------
                # forming the horizontal cutting objects for the boolean operation in the next step

                P1 = gp_Pnt(wall_corner_minX, wall_corner_minY, opening_corner_maxZ)
                
                H_cut_length_X = Standard_Real(round(abs(wall_corner_maxX - wall_corner_minX), 3))
                H_cut_length_Y = Standard_Real(round(abs(wall_corner_maxY-wall_corner_minY), 3))
                H_cut_length_Z = cut_width

                cut = BRepPrimAPI_MakeBox(P1, H_cut_length_X, H_cut_length_Y, H_cut_length_Z).Shape()
                cuts.append(cut)

                # end of forming horizontal cutting objects
                # ---------------------------------------------------


                # ---------------------------------------------------   
                # forming the vertical cutting objects for the boolean operation in the next step

                P2 = gp_Pnt(opening_corner_maxX, opening_corner_minY, wall_corner_minZ)
                P3 = gp_Pnt(opening_corner_minX, opening_corner_minY, wall_corner_minZ)
            
  
                V_placement_pts.append(P2)
                V_placement_pts.append(P3)

                #cutting the remaining part of the wall 
                wall_piece = Standard_Real(round(abs(opening_corner_minX - wall_corner_minX), 3))
            
                if wall_piece > gk_size:
                    V_cut_number = round(wall_piece/gk_size)
                    

                for num in range(V_cut_number):
                    factor = num + 1
                    Px = gp_Pnt(opening_corner_minX-(gk_size*factor), opening_corner_minY, wall_corner_minZ)
                    V_placement_pts.append(Px)
    
                V_cut_length_X = cut_width
                V_cut_length_Y = Standard_Real(round(abs(wall_corner_maxY-wall_corner_minY),3))
                V_cut_length_Z = Standard_Real(round(abs(wall_corner_maxZ-wall_corner_minZ),3))


                for V_placement_pt in V_placement_pts:
                    cutx = BRepPrimAPI_MakeBox(V_placement_pt, V_cut_length_X, V_cut_length_Y, V_cut_length_Z).Shape()
                    cuts.append(cutx)

                # end of forming vertical cutting objects
                # ---------------------------------------------------

    # ---------------------------------------------------
    #display.DisplayShape(cuts)
    print('Wall is cut into meshes...')
    return wall_shapes, indices, cuts


#3 - Panelize the walls by subtracting the cuts
def form_wall_panels(wall_shapes, indices, cuts):

    panels = []

    for ind in indices:

        p = wall_shapes[ind]

        for i in range(len(cuts)):

            p = OCC.Core.BRepAlgoAPI.BRepAlgoAPI_Cut(p, cuts[i]).Shape()

        if p.IsNull() == False:

            #place the objects on the surface to form panels
            translation = gp_Vec()
            translation2 = gp_Vec()

            translation = gp_Vec(0.0, 0.05, 0.0)
            translation2 = gp_Vec(0.0, -0.05, 0.0)

            trsf = gp_Trsf()
            trsf2 = gp_Trsf()

            trsf.SetTranslation(translation)
            trsf2.SetTranslation(translation2)
            loc = TopLoc_Location(trsf)
            loc2 = TopLoc_Location(trsf2)

            p_moved = p.Moved(loc)
            p_moved2 = p.Moved(loc2)

        else: 
            continue
        
        panels.append(p_moved)
        panels.append(p_moved2)

    print('Meshes are created...')
    return panels


def explode_mesh(panels):

    meshes =[]
    pts_grouped = []
    pts = []
    mesh_grouped_new = []
    pline = []
    other = []
    extrusion_height = []

    #export meshes and reimport them to create IFC
    for ind, panel in enumerate(panels):
        display.DisplayShape(panel)
        stl_writer = StlAPI_Writer()
        stl_writer.SetASCIIMode(False)
        stl_writer.Write(TopoDS_Shape(panel), f"{current_directory}/stl_models/object{ind}.stl")
        time.sleep(2.0)
        msh = mesh.Mesh.from_file(f"{current_directory}/stl_models/object{ind}.stl")
        meshes.append(msh)
    
    #group the points to form the mesh
    for m in meshes:
        vertices = m.points
        for point in vertices:
            for p in point:
                pts.append(float(p))
                
        pts_grouped = [tuple(pts[i:i+3]) for i in range(0, len(pts), 3)]
        mesh_grouped = [pts_grouped[i:i+36] for i in range(0, len(pts_grouped), 36)]

        for msh in mesh_grouped:
            for i, item1 in enumerate(msh):
                for item2 in msh:
                    if item1 == item2:
                        msh.remove(item1)
            mesh_grouped_new.append(msh)

    #use the groups of points to create data needed for the IFC objects
    for msh in mesh_grouped_new:

        polyline_pts = []
        other_pts = []
        corners = []
        x_coord = []

        msh = sorted(msh, key=lambda x: (-x[2], x[0], x[1]))
        extrusion_height.append(msh[len(msh)-1][2])
        corners.append(msh[0])

        for msh_points in msh:

            if msh_points[2] == msh[0][2]:
                    
                polyline_pts.append(msh_points)
                    
            else: 
                other_pts.append(msh_points)

            x_coord.append(msh_points[0])

        minX = min(x_coord)
        maxX = max(x_coord)
  
        polyline_pts.append(polyline_pts[0])
        pline.append(polyline_pts)
        other.append(other_pts)

    return extrusion_height, pline, corners, maxX, minX


def create_ifcobject(extrusion_heights, plines, corners, maxX, minX):

    for i, pline in enumerate(plines):
        
        create_ifc(f'{current_directory}/ifc_models/panel{i}', corners, pline, extrusion_heights[i], maxX, minX,'None')
    
    print('IFC files are exported...')

    return 

#-------------------------------------------------------------------------------------------------------------------


#Call the functions created above:

formed_cuts = get_shapes(model)

panels = form_wall_panels(formed_cuts[0], formed_cuts[1], formed_cuts[2])

print('Display has started...')

print('Meshes are written to stl files...')

explode_mesh(panels)

print('Each panel is created from the meshes in the stl files...')

create_ifcobject(explode_mesh(panels)[0], explode_mesh(panels)[1], explode_mesh(panels)[2], explode_mesh(panels)[3], explode_mesh(panels)[4])

display.DisplayShape(panels)

display.FitAll()

start_display()

print('Process is completed, objects are ready to be cut.')





