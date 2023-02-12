from stl import mesh
import numpy as np
from typing import overload, NewType, Optional, Tuple
import ifcopenshell.util.selector
import ifcopenshell.geom
import ifcopenshell
import ifcopenshell.util.schema
import ifcopenshell.util.element
from typing import overload, NewType, Optional, Tuple
from OCC.Core import Bnd
from OCC.Core import BRepBndLib
import OCC.Core.BRepAlgoAPI
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.TopoDS import *
from OCC.Display.SimpleGui import init_display
from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_Vec, gp_GTrsf
from OCC.Core.StlAPI import *
from OCC.Core.BRep import *
from OCC.Core.TopExp import *
from OCC.Core.TopAbs import *
from OCC.Core.BRepBuilderAPI import *
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Display.OCCViewer import rgb_color
from OCC.Core.Quantity import Quantity_Color
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
import os
import time
from scipy.spatial import ConvexHull
from ifc_export import create_ifc

Standard_Real = NewType('Standard_Real', float)

display, start_display, add_menu, add_function_to_menu = init_display("wx")

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_PYTHON_OPENCASCADE, True)

path = r"/home/ubuntu/ros2/src/slicer/wall_cut/Project1.ifc"
export_path = "/home/ubuntu/ros2/src/slicer/wall_cut/Project1_export.ifc"
model = ifcopenshell.open(path)

#the thickness of the steel framing behind the gypsumboard
cut_width = 0.1

#default gypsumboard size
gk_size = 1.2

cuts = []
walls = []
openings = []
p_min_wall = []
p_max_wall = []
p_min_opening = []
p_max_opening = []

#cut objects in the hoorizontal and vertical direction
H_cuts = []
V_cuts = []

bbox_opening = Bnd.Bnd_Box()
bbox_cut = Bnd.Bnd_Box()
bbox_walls = []
bbox_openings = []
bbox_final_object = []
opening_shapes = []

#placement points for the vertical cut objects
V_placement_pts = []

#1- Fetch the shapes from the imported IFC model
def get_shapes(model):
    global wall_shapes, bbox_wall
    wall_shapes = []
    bbox_wall = Bnd.Bnd_Box()
    
    index = 0
    
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

    #display.DisplayShape(opening_shapes)
    #display.DisplayShape (wall_shapes)
    return

#2 - Form the installation cuts using the imported data
def form_cuts():

    indices = []

    # ---------------------------------------------------
    #deconstruct wall geometry

    for w in range(len(wall_shapes)):
        wall_corner_minX = p_min_wall[w].X()
        wall_corner_minY = p_min_wall[w].Y()
        wall_corner_minZ = p_min_wall[w].Z()
        wall_corner_maxX = p_max_wall[w].X()
        wall_corner_maxY = p_max_wall[w].Y()
        wall_corner_maxZ = p_max_wall[w].Z()
        
        wall_width = Standard_Real(round(abs(wall_corner_maxY - wall_corner_minY), 3))
        wall_height = Standard_Real(round(abs(wall_corner_maxZ - wall_corner_minZ), 3))
        
    # ---------------------------------------------------

        #create cutting objects for each opening inside the wall
        for s in range(len(opening_shapes)):

            a = bbox_walls[w].IsOut(bbox_openings[s])

            if a == False:
                indices.append(w)
                print(w)

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

            else :
                print("no cuts formed")
    # ---------------------------------------------------
    #display.DisplayShape(cuts)

    return wall_shapes, wall_width, indices, wall_corner_minY



#3 - Panelize the walls by subtracting the cuts

def form_wall_panels(wall_shapes, wall_width, indices, min_Y):

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

    return panels


def explode_mesh(panels):

    meshes =[]
    pts_grouped = []
    pts = []
    mesh_grouped_new = []
    pline = []
    other = []
    extrusion_height = []

    for ind, panel in enumerate(panels):
        stl_writer = StlAPI_Writer()
        stl_writer.SetASCIIMode(True)
        stl_writer.Write(panel, f"object{ind}.stl")
        time.sleep(1)
        meshes.append(mesh.Mesh.from_file(f"object{ind}.stl"))

    print(meshes)

    for m in meshes:

        vertices = m.points

        for point in vertices:
            print(point)
            for p in point:
                pts.append(p)
                
        pts_grouped = [tuple(pts[i:i+3]) for i in range(0, len(pts), 3)]
        mesh_grouped = [pts_grouped[i:i+36] for i in range(0, len(pts_grouped), 36)]

        for msh in mesh_grouped:
            for i, item1 in enumerate(msh):
                for item2 in msh:
                    if item1 == item2:
                        msh.remove(item1)
            mesh_grouped_new.append(msh)


        for msh in mesh_grouped_new:
            polyline_pts = []
            other_pts = []

            msh = sorted(msh, key=lambda x: (x[2], x[0], x[1]), reverse=(True, False, False))

            extrusion_height.append(msh[len(msh)-1][2])

            for px in msh:

                if px[2] == msh[0][2]:
                    
                    polyline_pts.append(px)
                    
                else: 
                    other_pts.append(px)

                polyline_pts.append(px[0])

            pline.append(polyline_pts)
            other.append(other_pts)

    return extrusion_height, pline



def create_ifcobject(ifcfile, extrusion_heights, plines):
    # IFC template creation
    for i, pline in enumerate(plines):
        create_ifc(f'panel{i}', )
    return 


#-------------------------------------------------------------------------------------------------------------------

#Call the functions created above:

get_shapes(model)
formed_cuts = form_cuts()
panels = form_wall_panels(formed_cuts[0], formed_cuts[1], formed_cuts[2], formed_cuts[3])
create_ifcobject(explode_mesh(model, panels)[0], explode_mesh(panels)[1])
display.DisplayShape(panels)



#create_ifc_object_from_compound(final_object, model)

#model.write(export_path)

display.FitAll()
start_display()

