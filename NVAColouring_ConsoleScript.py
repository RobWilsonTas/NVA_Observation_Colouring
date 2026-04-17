from qgis.core import (QgsCategorizedSymbolRenderer, QgsRendererCategory,QgsMarkerSymbol, QgsSvgMarkerSymbolLayer, QgsFillSymbol)
from PyQt5.QtGui import QColor
import hashlib

#This script is designed to be run in console on NVA layers, where you select the layer you want to colour then click run

"""
##################################################################
Manual colour choices for certain species
Please feel free to expand this list with more overrides
"""

manualColourOverrides = {
    'Rubus fruticosus agg.': (150,0,255),
    'Rubus sp.': (150,0,255), 
    'Chrysanthemoides monilifera subsp. monilifera': (255,255,0),
    'Erica lusitanica': (150,255,0),
    'Cortaderia jubata': (255,200,255),
    'Ilex aquifolium': (255,0,0),
    'Rosa rubiginosa': (255,130,220),
    'Crataegus monogyna': (150,80,0),
    'Lycium ferocissimum': (255,100,0)
    }

"""
##################################################################
Main script
"""

#Grab the layer the user currently has selected in QGIS
layerForColouring = iface.activeLayer()
fieldNames = [field.name() for field in layerForColouring.fields()]
if 'SPECIES_NAME' not in fieldNames or 'PREFERRED_COMMON_NAMES' not in fieldNames:
    raise Exception("This script is designed to run on NVA layers with the columns SPECIES_NAME and PREFERRED_COMMON_NAMES") 

#Make a category for each species
#This shows up on the map legend so we know which colour belongs to which species
categoryExpression =  '"SPECIES_NAME" || \' - \' ||  if("PREFERRED_COMMON_NAMES" IS NULL, \'\', "PREFERRED_COMMON_NAMES")'

#Colours found using "Iterative repulsion optimisation with penalty-weighted nearest-neighbour scoring and resets in oklab colour space"
totalColourPalette = [(255, 38, 181), (80, 72, 252), (201, 189, 255), (0, 253, 0), (0, 253, 255), (0, 121, 255), (14, 28, 163), (102, 225, 162), (255, 26, 0), (199, 0, 245), (177, 184, 6), (255, 110, 167), (37, 175, 73), (31, 0, 255), (136, 108, 255), (28, 255, 157), (254, 35, 249), (200, 0, 157), (253, 0, 117), (196, 253, 2), (196, 100, 244), (249, 164, 0), (157, 10, 195), (185, 126, 10), (138, 0, 254), (254, 111, 250), (181, 0, 0), (41, 212, 35), (0, 180, 254), (255, 219, 5)]

#Keep track of categorys we’ve seen and the colour we assigned to each one
uniqueCategories = set()
colourForCategory = {}

#Go through each feature in the layer
for feature in layerForColouring.getFeatures():
    
    #Build a readable category
    category = (feature['SPECIES_NAME'] or '') + ' - ' +  (feature['PREFERRED_COMMON_NAMES'] or '')
    uniqueCategories.add(category)
    scientificName = feature["SPECIES_NAME"]

    #If we’ve set a manual colour for this species, use it
    if scientificName in manualColourOverrides:
        colourForCategory[category] = QColor(*manualColourOverrides[scientificName])
        
    else:
        #Pick a colour from the palette in a way that always gives the same colour for the same species
        #This hash thing is designed to get a unique, fixed number for each string, which is used to pick a colour
        hashIndex = int(hashlib.sha256(scientificName.encode()).hexdigest(), 16) % len(totalColourPalette)
        colourForCategory[category] = QColor(*totalColourPalette[hashIndex])


categoriesForRenderer = []
#Build the visual symbols for each category
for category in sorted(uniqueCategories):
    currentColour = colourForCategory[category]
    
    #Point layer
    if layerForColouring.geometryType() == 0:  
        
        #Use a triangle marker to match the QML
        symbol = QgsMarkerSymbol.createSimple({
            "name": "equilateral_triangle",
            "color": str(currentColour.red()) + ',' + str(currentColour.green()) + ',' + str(currentColour.blue()),
            "outline_color": "0,0,0",
            "outline_width": "0.2",
            "size": "3.2"})

    #Line layer
    elif layerForColouring.geometryType() == 1:
        
        #Style the line with the colour
        symbol = QgsLineSymbol.createSimple({
            'line_color': str(currentColour.red()) + ',' + str(currentColour.green()) + ',' + str(currentColour.blue()),
            'line_width': '0.7'})

    #Polygon layer
    elif layerForColouring.geometryType() == 2:  
        
        #Style the polygon so that it's transparent inside, and the outline is the species colour
        symbol = QgsFillSymbol.createSimple({'color': str(currentColour.red()) + ',' + str(currentColour.green()) + ',' + str(currentColour.blue()) + ',50',  
            'outline_color': str(currentColour.red()) + ',' + str(currentColour.green()) + ',' + str(currentColour.blue()),
            'outline_width': '0.5'})

    #Add this category and symbol to the renderer
    categoriesForRenderer.append(QgsRendererCategory(category, symbol, category))
    
"""
##################################################################
Deal with 'all other values'
"""

#Add "All other values" category for anything not explicitly listed
if layerForColouring.geometryType() == 0:
    symbol = QgsMarkerSymbol()
    fontLayer = QgsFontMarkerSymbolLayer()
    fontLayer.setCharacter("X")
    fontLayer.setFontFamily("Arial Black")
    fontLayer.setSize(4)
    fontLayer.setColor(QColor(255, 5, 0))
    fontLayer.setStrokeColor(QColor(35, 35, 35))
    fontLayer.setStrokeWidth(0.4)
    symbol.changeSymbolLayer(0, fontLayer)
    
elif layerForColouring.geometryType() == 1:
    symbol = QgsLineSymbol.createSimple({'color': '255,0,0', 'width': '2'})
    
elif layerForColouring.geometryType() == 2:
    symbol = QgsFillSymbol.createSimple({'color': '255,0,0,255', 'outline_color': '255,0,0', 'outline_width': '2'})

categoriesForRenderer.append(QgsRendererCategory(None, symbol, "missing data..."))

"""
##################################################################
Actually apply the symbology
"""

#Apply these categories to the layer so it shows up on the map
layerForColouring.setRenderer(QgsCategorizedSymbolRenderer(categoryExpression, categoriesForRenderer))
layerForColouring.triggerRepaint()
iface.layerTreeView().refreshLayerSymbology(layerForColouring.id())