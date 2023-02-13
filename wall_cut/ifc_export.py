import time
import ifcopenshell
from typing import overload, NewType, Optional, Tuple
Standard_Real = NewType('Standard_Real', float)

O = 0., 0., 0.
X = 1., 0., 0.
Y = 0., 1., 0.
Z = 0., 0., 1.

# Creates an IfcAxis2Placement3D from Location, Axis and RefDirection specified as Python tuples
def create_ifcaxis2placement(ifcfile, point=O, dir1=Z, dir2=X):
    point = ifcfile.createIfcCartesianPoint(point)
    dir1 = ifcfile.createIfcDirection(dir1)
    dir2 = ifcfile.createIfcDirection(dir2)
    axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement

# Creates an IfcLocalPlacement from Location, Axis and RefDirection, specified as Python tuples, and relative placement
def create_ifclocalplacement(ifcfile, point=O, dir1=Z, dir2=X, relative_to=None):
    axis2placement = create_ifcaxis2placement(ifcfile,point,dir1,dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(relative_to,axis2placement)
    return ifclocalplacement2

# Creates an IfcPolyLine from a list of points, specified as Python tuples
def create_ifcpolyline(ifcfile, point_list):
    ifcpts = []
    for point in point_list:
        point = list(point)
        point2 = ifcfile.createIfcCartesianPoint([Standard_Real(point[0][0]), Standard_Real(point[0][1]), Standard_Real(point[0][2])])
        ifcpts.append(point2)
    polyline = ifcfile.createIfcPolyLine(ifcpts)
    print(polyline)
    return polyline

# Creates an IfcExtrudedAreaSolid from a list of points, specified as Python tuples
def create_ifcextrudedareasolid(ifcfile, point_list, ifcaxis2placement, extrude_dir, extrusion):
    polyline = create_ifcpolyline(ifcfile, set(point_list))
    ifcclosedprofile = ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    ifcdir = ifcfile.createIfcDirection(extrude_dir)
    ifcextrudedareasolid = ifcfile.createIfcExtrudedAreaSolid(ifcclosedprofile, ifcaxis2placement, ifcdir, extrusion)
    return ifcextrudedareasolid

# IFC template creation
def create_ifc(filenames, corner, list_of_points, ext_height, maxX, minX, fab_status):
    filename = f"{filenames}.ifc"
    timestamp = time.time()
    timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))
    creator = "Elif Akbas, Cemre Karaoglan, Beyza Kaya "
    organization = "RWTH"
    application, application_version = "IfcOpenShell", "0.5"
   

    ifcfile = ifcopenshell.file()
    owner_history = ifcfile.createIfcOwnerHistory()
    project = ifcfile.createIfcProject()
    context = ifcfile.createIfcGeometricRepresentationContext

    # IFC hierarchy creation
    site_placement = create_ifclocalplacement(ifcfile)
    site = ifcfile.createIfcSite(ifcopenshell.guid.new(), owner_history, "Site", None, None, site_placement, None, None, "ELEMENT", None, None, None, None, None)

    building_placement = create_ifclocalplacement(ifcfile, relative_to=site_placement)
    building = ifcfile.createIfcBuilding(ifcopenshell.guid.new(), owner_history, 'Building', None, None, building_placement, None, None, "ELEMENT", None, None, None)

    storey_placement = create_ifclocalplacement(ifcfile, relative_to=building_placement)
    elevation = 0.0
    building_storey = ifcfile.createIfcBuildingStorey(ifcopenshell.guid.new(), owner_history, 'Storey', None, None, storey_placement, None, None, "ELEMENT", elevation)

    container_storey = ifcfile.createIfcRelAggregates(ifcopenshell.guid.new(), owner_history, "Building Container", None, building, [building_storey])
    container_site = ifcfile.createIfcRelAggregates(ifcopenshell.guid.new(), owner_history, "Site Container", None, site, [building])
    container_project = ifcfile.createIfcRelAggregates(ifcopenshell.guid.new(), owner_history, "Project Container", None, project, [site])

    # Wall creation: Define the wall shape as a polyline axis and an extruded area solid
    wall_placement = create_ifclocalplacement(ifcfile, relative_to=storey_placement)
    point1 = ifcfile.createIfcCartesianPoint([Standard_Real(maxX), Standard_Real(0.0), Standard_Real(0.0)])
    point2 = ifcfile.createIfcCartesianPoint([Standard_Real(minX), Standard_Real(0.0), Standard_Real(0.0)])
    polyline = create_ifcpolyline(ifcfile, [point1, point2])
    axis_representation = ifcfile.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])

#-------------------------------------------------------------------------------------------IMPORTANT

    extrusion_placement = create_ifcaxis2placement(ifcfile, corner)
    point_list_extrusion_area = list_of_points
    solid = create_ifcextrudedareasolid(ifcfile, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 1.0), ext_height)
    body_representation = ifcfile.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])

    product_shape = ifcfile.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])

    wall = ifcfile.createIfcBuildingElementProxy(ifcopenshell.guid.new(), owner_history, "Panel", "Panel to be fabricated", None, wall_placement, product_shape, None)

    ifcfile.createIfcRelContainedInSpatialStructure(ifcopenshell.guid.new(), owner_history, "Building Storey Container", None, wall, building_storey)

    # Write the contents of the file to disk
    ifcfile.write(filename)