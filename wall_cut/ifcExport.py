import ifcopenshell
from typing import overload, NewType, Optional, Tuple


def export_ifc_as_proxy( import_dir, bottom_points, extrusion_height, corner, export_dir):
        
    Standard_Real = NewType('Standard_Real', float)

    file = ifcopenshell.open(import_dir)
    
    bt_pts = []

    for p in bottom_points:
            pt = file.createIfcCartesianPoint(p)
            bt_pts.append(pt)
        
    pline = file.createIfcPolyline(bt_pts)
        
    closed_pline = file.createIfcArbitraryClosedProfileDef(
            ProfileType='AREA', OuterCurve=pline)

    corner2 = file.createIfcCartesianPoint(corner)
            
    axis_placement = file.createIfcAxis2Placement3D(Location=corner2)

    local_placement = file.createIfcLocalPlacement(None, axis_placement)

    direction = file.createIfcDirection(DirectionRatios=[0., 0., 1.])

    extruded_area_solid = file.createIfcExtrudedAreaSolid(SweptArea=closed_pline, Position=axis_placement, ExtrudedDirection=direction, Depth=Standard_Real(round(extrusion_height,2)))

    building_element_proxy = file.createIfcBuildingElementProxy(GlobalId=ifcopenshell.guid.new(), Name='Panel', ObjectPlacement=local_placement)

    reps = file.createIfcShapeRepresentation(RepresentationIdentifier='Body', RepresentationType='SweptSolid', Items=[extruded_area_solid])

    product = file.createIfcProductDefinitionShape(Representations=[reps])
    
    building_element_proxy.Representation = product

    file.add(building_element_proxy)
            
    # Save the file
    file.write(export_dir)
            
