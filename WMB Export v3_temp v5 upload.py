import bpy
import struct
import mathutils
import math
import random
import numpy as np
import pprint
import re
from collections import OrderedDict
import time
import io
import sys

LOG_VERTEX = True

WMB_MAGIC_NUMBER = "WMB"
WMB_VERSION      = 538312982

VERTEX_GROUP_HEADER_SIZE = 0x30

WMB_MAGIC_NUMBER_OFFSET               = 0x0000
WMB_VERSION_OFFSET                    = 0x0004
WMB_UNKOWN_A_OFFSET                   = 0x0008
WMB_UNKOWN_B_OFFSET                   = 0x000C
WMB_UNKOWN_C_OFFSET                   = 0x000E
WMB_BOUNDING_BOX_X_OFFSET             = 0x0010
WMB_BOUNDING_BOX_Y_OFFSET             = 0x0014
WMB_BOUNDING_BOX_Z_OFFSET             = 0x0018
WMB_BOUNDING_BOX_U_OFFSET             = 0x001C
WMB_BOUNDING_BOX_V_OFFSET             = 0x0020
WMB_BOUNDING_BOX_W_OFFSET             = 0x0024
WMB_BONES_OFFSET                      = 0x0028
WMB_NUMBER_OF_BONES_OFFSET            = 0x002C
WMB_BONE_INDEX_TRANSLATE_TABLE_OFFSET = 0x0030
WMB_BONE_TRANSLATE_TABLE_SIZE_OFFSET  = 0x0034
WMB_VERTEX_GROUP_OFFSET               = 0x0038
WMB_NUMBER_OF_VERTEX_GROUPS_OFFSET    = 0x003C
WMB_BATCHES_OFFSET                    = 0x0040
WMB_NUMBER_OF_BATCHES_OFFSET          = 0x0044
WMB_LOD_OFFSET                        = 0x0048
WMB_NUMBER_OF_LOD_OFFSET              = 0x004C
WMB_UNKNOWN_D_OFFSET                  = 0x0050
WMB_NUMBER_OF_UNKNOWN_D_OFFSET        = 0x0054
WMB_BONE_MAP_OFFSET                   = 0x0058
WMB_BONE_MAP_SIZE_OFFSET              = 0x005C
WMB_BONE_SETS_OFFSET                  = 0x0060
WMB_NUMBER_OF_BONE_SETS_OFFSET        = 0x0064
WMB_MATERIALS_OFFSET                  = 0x0068
WMB_NUMBER_OF_MATERIALS_OFFSET        = 0x006C
WMB_MESH_OFFSET                       = 0x0070
WMB_NUMBER_OF_MESHES_OFFSET           = 0x0074
WMB_MESH_MATERIAL_OFFSET              = 0x0078
WMB_NUMBER_OF_MESH_MATERIALS_OFFSET   = 0x007C
WMB_UNKNOWN_E_OFFSET                  = 0x0080
WMB_NUMBER_OF_UNKOWN_E_OFFSET         = 0x0084

class VertexGroup:
    id = 0
    def __init__(self):
        self.id              = 0 
        self.vtxOffset       = 0
        self.vtxExOffset     = 0
        self.unknownA        = 0
        self.unknownB        = 0 
        self.vtxSize         = 28
        self.vtxExSize       = 12
        self.unknownC        = 0
        self.unknownD        = 0
        self.numOfvertices   = 0
        self.vtxExFlags      = 0
        self.idxBuffOffset   = 0
        self.numOfindices    = 0
        self.numOfverticesEx = 0
        self.meshes          = []
        self.name = ""

    def new(self):
        VertexGroup.id = VertexGroup.id+1
        vtxGroup = VertexGroup()
        vtxGroup.id = VertexGroup.id
        return vtxGroup
    
    def addVertex(self, vertexData):
        self.vertexes.append(vertexData)

    def addVertexEx(self, vertexExData):
        self.VertexEx.append(vertexExData)


'''
KEY

LOD
|-BATCH
|---VERTEX
'''
HASH_FILE         = "HASH FILE"
VERTEX_LOG_FILE_T = "LOG FILE"
WRITE_FILE        = "WRITE FILE"

sceneObjectsList = [obj for obj in bpy.data.objects]

class loopInfo:
    def __init__(self):
        self.loopData = None
        self.loopIndex = None

def nullBytes(num): return b"".join([b"\x00" for x in range(num)])

def floatToByte(number):
    v = number#float(number)
    v *= 127.0
    v += 127.0
    return int(v)

def floatTo2Byte(number): return np.float16(number).view("int16")


#REMBER TO DO THIS
'''    for polygon in mesh.data.polygons:
        for loopIndex in polygon.loop_indices:
            loopData        = mesh.data.loops[loopIndex]
            loopVtxIndex    = loopData.vertex_index
            indexBufferData.append(loopVtxIndex)

            if loopVtxIndex not in usedVertexList:
                realVertexList.append( mesh.data.vertices[loopVtxIndex] )
                usedVertexList.append(loopVtxIndex)
    return realVertexList'''

def GetVertexSize(mesh):
    hasBoneWeights = False
    #Calculate Vertex Size and format
    for g in mesh.vertex_groups:
        if g.name.startswith("bone"):
            hasBoneWeights = True
            break
        #NOTE: Mesh vertex are grouped together even if a vertex has no
        # bone or color data we will still treat them like they do
         # Chose between dataFlag 0xb, 0x7, 0xa

    if hasBoneWeights:
        if mesh.data.vertex_colors:
            dataFlag = random.choice([0xB, 0xA])
        else:
                              # TODO: Figure out which to use, if mesh has color use dataFlag 0xb or 0xa
            dataFlag = 0x7    # else use dataFlag 0x7
    else:                                              #Chose between dataFlag 0x5, 0x4, 0xe, 0xc
        if mesh.data.uv_layers:                        # if  mesh vertexes have uv mapping use dataFlag 0x5, 0xe, 0xc
            dataFlag = random.choice([0x5, 0xE, 0XC])  # TODO: Figure out which to use
        else:                                          #else use  0x4
            dataFlag = 0x4
    return dataFlag

#NOTE: SORT VERTEX GROUP ORDER BEFORE ADDING TO ORDEREDDICT
def VertexStuff(objectList, theVertexGroupDic):
    #print("starting from", hex(contents.tell()) )
    vertexGroupNameList = []
    for mesh in objectList:
        if mesh.vertex_groups:
            vtxGroupList = [g for g in mesh.vertex_groups if not g.name.startswith("bone")]
            for group in vtxGroupList:
                if group.name not in vertexGroupNameList:
                    vertexGroupNameList.append(group.name)
                    
                    vertexGroup = VertexGroup()                          #Create Vertex Group
                    vertexGroup.name = group.name
                    
                    vertexGroup.meshes.append(mesh)
                    vertexGroup.numOfvertices = len(mesh.data.vertices)
                    vertexGroup.numOfindices  = len(mesh.data.loops)
                    vertexGroup.vtxExFlags = GetVertexSize(mesh)         #Store Vertex Size and format
                    
                    theVertexGroupDic[group.name] = vertexGroup             #Store Vertex Group
                    #theVertexGroupDic[group.name].meshes.append(mesh)
                    
                    
                else:
                    #vertxGroupList[group.name].numOfvertices += len(vData)
                    theVertexGroupDic[group.name].numOfvertices += len( mesh.data.vertices ) #Add mesh vertices data to Vertex Group
                    #print("vert"theVertexGroupDic[group.name].numOfvertices )

                    theVertexGroupDic[group.name].numOfindices  += len(mesh.data.loops)
                    theVertexGroupDic[group.name].vtxExFlags = GetVertexSize(mesh)           #Store Vertex Size and format
                    theVertexGroupDic[group.name].meshes.append(mesh)
                    
                    #DEBUG PURPOSE:
                    if group.name == "Group 1":
                        theVertexGroupDic[group.name].vtxExFlags = 0xB
                        theVertexGroupDic[group.name].vtxExSize   = 0x14
                    if group.name == "Group 2":
                        theVertexGroupDic[group.name].vtxExFlags = 0x7
                        theVertexGroupDic[group.name].vtxExSize   = 0xC
                    if group.name == "Group 3":
                        theVertexGroupDic[group.name].vtxExFlags = 0xA
                        theVertexGroupDic[group.name].vtxExSize   = 0x10

    
    #Sort the vertex Group so we can iterate correctly
    sortedVertexGroupList = sorted(theVertexGroupDic)
    
    #add up all vtx groups header
    #start = contents.tell()+len(theVertexGroupDic)*0x30
    #print("num vertex groups:", len(theVertexGroupDic))
    print()
    for index, groupName in enumerate(sortedVertexGroupList):
        if index == 0:
            vtxOffset         = start#+(theVertexGroupDic[groupName].numOfvertices*theVertexGroupDic[groupName].vtxSize)
            vtxExOffset       = vtxOffset+(   theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxSize   )
            indexBufferOffset = vtxExOffset+( theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize )
            
            print("vertex offset      ", hex(vtxOffset)         )
            print("vertex ex offset   ", hex(vtxExOffset)       )
            print("index buffer offset", hex(indexBufferOffset) )
            print()
            
            theVertexGroupDic[groupName].vtxOffset     = vtxOffset
            theVertexGroupDic[groupName].vtxExOffset   = vtxExOffset
            theVertexGroupDic[groupName].idxBuffOffset = indexBufferOffset
        else:
            prevGroupName = sortedVertexGroupList[ sortedVertexGroupList.index(groupName)-1 ]
            #prevGroupName = list(theVertexGroupDic)[ list( theVertexGroupDic ).index(groupName)-1 ]
            offset =  theVertexGroupDic[prevGroupName].idxBuffOffset+(0x4*theVertexGroupDic[prevGroupName].numOfindices)
            
            print( theVertexGroupDic.keys() )
            print("Current Group:", groupName)
            print("Previous Group", prevGroupName)
            print(group.name, "vertex offset:", hex(offset) )
            print()

            vtxOffset = offset
            vtxLength = theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxSize
            print(groupName, theVertexGroupDic[groupName].numOfvertices)
            print(groupName, theVertexGroupDic[groupName].vtxSize)
            print()
            #vtxExOffset       = vtxOffset+(   theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxSize   )
            
            vtxExOffset       = vtxOffset+vtxLength
            vtxExLength = theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize
            
            indexBufferOffset = vtxExOffset+( theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize ) #<---Test Veriable 0x10
            indexBufferLength = theVertexGroupDic[groupName].numOfindices* 0x4

            print("vertex offset      ", hex(vtxOffset), "Length:", hex(vtxLength)         )
            print("vertex ex offset   ", hex(vtxExOffset), "Length:", hex(vtxExLength)       )
            print("index buffer offset", hex(indexBufferOffset), "Length:", hex(indexBufferLength) )
            print()

            theVertexGroupDic[groupName].vtxOffset     = vtxOffset
            theVertexGroupDic[groupName].vtxExOffset   = vtxExOffset
            theVertexGroupDic[groupName].idxBuffOffset = indexBufferOffset

    #return vertxGroupList


def getVerteGroups(objectList, theVertexGroupDic, buffer):
    #print("starting from", hex(contents.tell()) )
    vertexGroupNameList = []
    for mesh in objectList:
        if mesh.vertex_groups:
            vtxGroupList = [g for g in mesh.vertex_groups if not g.name.startswith("bone")]
            for group in vtxGroupList:
                if group.name not in vertexGroupNameList:
                    vertexGroupNameList.append(group.name)
                    
                    vertexGroup = VertexGroup()                          #Create Vertex Group
                    vertexGroup.name = group.name
                    
                    vertexGroup.meshes.append(mesh)
                    vertexGroup.numOfvertices = len(mesh.data.vertices)
                    vertexGroup.numOfindices  = len(mesh.data.loops)
                    vertexGroup.vtxExFlags = GetVertexSize(mesh)         #Store Vertex Size and format
                    
                    theVertexGroupDic[group.name] = vertexGroup             #Store Vertex Group
                    #theVertexGroupDic[group.name].meshes.append(mesh)
                    
                    
                else:
                    #vertxGroupList[group.name].numOfvertices += len(vData)
                    theVertexGroupDic[group.name].numOfvertices += len( mesh.data.vertices ) #Add mesh vertices data to Vertex Group
                    #print("vert"theVertexGroupDic[group.name].numOfvertices )

                    theVertexGroupDic[group.name].numOfindices  += len(mesh.data.loops)
                    theVertexGroupDic[group.name].vtxExFlags = GetVertexSize(mesh)           #Store Vertex Size and format
                    theVertexGroupDic[group.name].meshes.append(mesh)
                    
                    #DEBUG PURPOSE:
                    if group.name == "Group 1":
                        theVertexGroupDic[group.name].vtxExFlags = 0xB
                        theVertexGroupDic[group.name].vtxExSize   = 0x14
                    if group.name == "Group 2":
                        theVertexGroupDic[group.name].vtxExFlags = 0x7
                        theVertexGroupDic[group.name].vtxExSize   = 0xC
                    if group.name == "Group 3":
                        theVertexGroupDic[group.name].vtxExFlags = 0xA
                        theVertexGroupDic[group.name].vtxExSize   = 0x10

    
    #Sort the vertex Group so we can iterate correctly
    sortedVertexGroupList = sorted(theVertexGroupDic)
    
    #add up all vtx groups header
    #start = 
    #print("num vertex groups:", len(theVertexGroupDic))
    #print()
    for index, groupName in enumerate(sortedVertexGroupList):
        if index == 0:
            vtxOffset         = buffer.tell()+len(theVertexGroupDic)*0x30
            vtxExOffset       = vtxOffset+(   theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxSize   )
            indexBufferOffset = vtxExOffset+( theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize )
            
            theVertexGroupDic[groupName].vtxOffset     = vtxOffset
            theVertexGroupDic[groupName].vtxExOffset   = vtxExOffset
            theVertexGroupDic[groupName].idxBuffOffset = indexBufferOffset
        else:
            prevGroupName = sortedVertexGroupList[ sortedVertexGroupList.index(groupName)-1 ]
            offset =  theVertexGroupDic[prevGroupName].idxBuffOffset+(0x4*theVertexGroupDic[prevGroupName].numOfindices)

            vtxOffset = offset
            vtxLength = theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxSize
            
            vtxExOffset       = vtxOffset+vtxLength
            #vtxExLength = theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize
            
            indexBufferOffset = vtxExOffset+( theVertexGroupDic[groupName].numOfvertices* theVertexGroupDic[groupName].vtxExSize ) #<---Test Veriable 0x10
            #indexBufferLength = theVertexGroupDic[groupName].numOfindices* 0x4

            theVertexGroupDic[groupName].vtxOffset     = vtxOffset
            theVertexGroupDic[groupName].vtxExOffset   = vtxExOffset
            theVertexGroupDic[groupName].idxBuffOffset = indexBufferOffset

#vtxGroupDataList    = [] #Vertex groups in blender not named after bones
vertexGroupDic      = {}
vtxType2DataList    = [] #List of Vertex
vtxExType4DataList  = [] #List of Vertex Ex
indexBufferDataList = [] #Loop of all vertices
batchDataList       = [] #Object Groups "users_group"
lodDataList         = [] #Not usre yet


print("---------------------------------------------------------------")
FILEBUFFER = io.BytesIO( )

#Fill WMB Header
WMBHEADERBUFFER = io.BytesIO(nullBytes(0x90))
WMBHEADERBUFFER.seek(0)

WMBHEADERBUFFER.write( WMB_MAGIC_NUMBER.encode()+nullBytes(1) )         #Write magic number
WMBHEADERBUFFER.write( struct.pack("<i", WMB_VERSION )        )         #Write file version
WMBHEADERBUFFER.seek(WMB_BONES_OFFSET)
WMBHEADERBUFFER.write( struct.pack("<i", 0x90) ) #Write Bone offset
#WMBHEADERBUFFER.seek(  WMBHEADERBUFFER.getbuffer().nbytes )

FILEBUFFER.write( WMBHEADERBUFFER.getbuffer() )

#-------------------------------------
#|     Copying bone data from list      |
#-------------------------------------
BONEBUFFER = io.BytesIO()

file = open(HASH_FILE, "r")
content = file.readlines()

for line in content:
    lineList = line.split(":")
    id = lineList[0]
    
    if id ==   "0": #Write Bone Data
        eList = [int(num) for num in lineList[1].split(" ")]
        for index, data in enumerate(eList):
            if index in (0, 1):
                BONEBUFFER.write( struct.pack( "<H", data) )
            else:
                BONEBUFFER.write( struct.pack( "<I", data) )

    elif id == "1": #Write Index Buffer
        data = int(lineList[1])
        BONEBUFFER.write( struct.pack( "<H", data) )
    
    elif id == "2": #STORE BONE MAP FOR LATER
        pass

    elif id == "3": #STORE BONE SET HEADER FOR LATER
        pass
    
    elif id == "4": #STORE BONE SETS FOR LATER
        pass
file.close()

FILEBUFFER.write( BONEBUFFER.getbuffer() )


for lodIndex, LoD in enumerate([obj for obj in sceneObjectsList if obj.type == "EMPTY"]):
    lodData = [
        0, #0 Name Offset
        0, #1 LoD Level
        0, #2 Batch Start
        0, #3 BatchInfo Offset
        0  #4 Num of BatchInfo
    ]

    #LoD Level
    lodData[1] = lodIndex

    #Calculate Name Offset

    lodData[2] = len( batchDataList )
    print("batchList", len( batchDataList ) )
    lodDataList.append(lodData)

    #Vertex groups
    #[FORGET THIS]  Gonna save the vertex groups first and store the vertex/ex data
    #  Gonna store vertex groups header and store the vertex/ex data 
    
meshes =  [obj for obj in LoD.children if obj.type == "MESH"]
allMeshes = meshes
for mesh in meshes:
    for child in mesh.children:
        allMeshes.append( child )
#allMeshes += meshes

#Fill Vertex Group
#VertexStuff(allMeshes, vertexGroupDic)
getVerteGroups(allMeshes, vertexGroupDic, FILEBUFFER)
vertexGroupSize = len(vertexGroupDic)*0x30

#Fill Vertex Group bytes so we can work
VERTEXGROUPBUFFER = io.BytesIO( nullBytes(vertexGroupSize) )
VERTEXGROUPBUFFER.seek(0)

sortedaVertexGroupDic = OrderedDict()

for data in sorted(vertexGroupDic): sortedaVertexGroupDic[data] = vertexGroupDic[data]

if LOG_VERTEX: VERTEX_LOG_FILE = open(VERTEX_LOG_FILE_T, "w+")

#NOTE: LOOP IS WRITING OVER OTHER VERTEX GROUPS!!!!!!!
#  Vertex Group Loop starts here
print("dict format:", sortedaVertexGroupDic.keys())

vertexBufferList = []
vertexExBufferList = []
IndexBufferList = []
#Write all vertex Groups then write individual vertex/ex for each one
start_time = time.time()
for vindex, x in enumerate(sortedaVertexGroupDic):
    
    #print("Writing vertex data at: {}".format(hex( contents.tell() )  ) )
    print("    Vertices:        ", vertexGroupDic[x].numOfvertices )
    print("    Vertex offset:   ", hex(vertexGroupDic[x].vtxOffset ) )
    print("    Vertex Ex offset:", hex(vertexGroupDic[x].vtxExOffset ) )

    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].vtxOffset     ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].vtxExOffset   ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].unknownA      ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].unknownB      ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].vtxSize       ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].vtxExSize     ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].unknownC      ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].unknownD      ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].numOfvertices ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].vtxExFlags    ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].idxBuffOffset ) )
    VERTEXGROUPBUFFER.write( struct.pack("<I", vertexGroupDic[x].numOfindices  ) )
    
    dataFlag = vertexGroupDic[x].vtxExFlags

    #Fill Vertex Data Buffer
    VERTEXBUFFER = io.BytesIO()
    VERTEXBUFFER.write( nullBytes( vertexGroupDic[x].numOfvertices*vertexGroupDic[x].vtxSize ) )
    VERTEXBUFFER.seek(0)

    #Fill Vertex Ex Buffer
    VERTEXEXBUFFER = io.BytesIO()
    VERTEXEXBUFFER.write( nullBytes( vertexGroupDic[x].numOfvertices*vertexGroupDic[x].vtxExSize ) )
    VERTEXEXBUFFER.seek(0)

    #Fill Index Buffer
    INDEXBUFFER = io.BytesIO()
    INDEXBUFFER.write( nullBytes( vertexGroupDic[x].numOfindices*0x4 ) )
    INDEXBUFFER.seek(0)

    #Write Vertex Data
    for mesh in vertexGroupDic[x].meshes:
        indexBufferData = []
        usedVertexList =  []
        usedVertexListAppend = usedVertexList.append
        stringList = ""
        loopDict = {}
        #vertexList = []
        mesh.data.calc_tangents()

        if LOG_VERTEX: VERTEX_LOG_FILE.write(mesh.name+"\n")
        
        loop_iter = iter(mesh.data.loops)
        for  loop in loop_iter:
            
            INDEXBUFFER.write( struct.pack("<I", loop.vertex_index) )
            
            vertex_index_string = str(loop.vertex_index)
            if vertex_index_string not in stringList:
                stringList = stringList+" "+vertex_index_string
                loopDict[loop.vertex_index] = loop
        
        sortedLoopDict = OrderedDict()

        for data in sorted(loopDict): sortedLoopDict[data] = loopDict[data]

        for index in sortedLoopDict:
            #NOTE: RENAME THESE FUNCTION
            loopData = sortedLoopDict[index]

            vertexCoords  = mesh.data.vertices[loopData.vertex_index].co
            vertexNormal  = mesh.data.vertices[loopData.vertex_index].normal
            vertexTangent = loopData.tangent
            try:
                vertexUV  = mesh.data.uv_layers.active.data[loopData.index].uv
            except:
                print("Mesh {} doesnt have a uv".format(mesh.name))
            
            if mesh.data.vertex_colors: vertexColors = (0,0,0)
            else: vertexColors = (0,0,0)

            if LOG_VERTEX:
                VERTEX_LOG_FILE.write( "   LOOP_INDEX:{} X:{} Y:{} Z:{} U:{} V:{}\n"
                .format(
                    loopData.vertex_index,
                    vertexCoords.x,
                    vertexCoords.y,
                    vertexCoords.z,
                    vertexUV[0],
                    vertexUV[1]) )
            
            if dataFlag in (0xb, 0x7, 0xa):
                #Write Vertex data here
                #0x4 vector      position;
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.x ) )
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.y ) )
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.z ) )

                #0x1 tangents_t  tangents;
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.x) ) )
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.y) ) )
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.z) ) )
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(1.0) ) ) #Dummy
                
                #0x2 mapping_t   mapping;
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                
                #0x1 ubyteList   boneIndex;
                #  Can be nopped for now
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                
                #0x1 ubyteList   boneWeight;
                #  Can be nopped for now
                VERTEXBUFFER.write( struct.pack("<B", 255 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                VERTEXBUFFER.write( struct.pack("<B", 0 ) )
                
                if dataFlag == 0xB:
                    #Vertex Ex Data
                    #0x2 mapping_t   mapping2
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                
                    #0x1 ubyteList   color
                    VERTEXEXBUFFER.write( struct.pack("<b", vertexColors[0] ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", vertexColors[1] ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", vertexColors[2] ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    
                    #0x2 4 normal_t    normal
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy

                    #mapping_t   mapping3
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                
                elif dataFlag == 0x7:
                    #Vertex Ex Data
                    #vector      position;
                    VERTEXEXBUFFER.write( struct.pack("<f", vertexCoords.x ) )
                    VERTEXEXBUFFER.write( struct.pack("<f", vertexCoords.y ) )
                    VERTEXEXBUFFER.write( struct.pack("<f", vertexCoords.z ) )
                    
                    #tangents_t  tangents;
                    VERTEXEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.y) ) )
                    VERTEXEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.z) ) )
                    VERTEXEXBUFFER.write( struct.pack("<B", 0) ) #Dummy
                    
                    #mapping_t   mapping
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(vertexUV.x)) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexUV.y) ) )
                    
                    #ubyteList   boneIndex;
                    #  Can be nopped for now
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    
                    #ubyteList   boneWeight;
                    #  Can be nopped for now
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                    VERTEXEXBUFFER.write( struct.pack("<b", 0 ) )
                
                elif dataFlag == 0xA:
                    #mapping_t   mapping2;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                    
                    #0x2 4 normal_t    normal
                    VERTEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy
            
            elif dataFlag in ( 0x5, 0x4, 0xe, 0xc):
                #Write Vertex Data here
                #vector      position;
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.x ) )
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.y ) )
                VERTEXBUFFER.write( struct.pack("<f", vertexCoords.z ) )
                
                #tangents_t  tangents;
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.x) ) )
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.y) ) )
                VERTEXBUFFER.write( struct.pack("<B", floatToByte(vertexTangent.z) ) )
                VERTEXBUFFER.write( struct.pack("<B", 0) ) #Dummy
                
                #mapping_t   mapping;
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                
                #mapping_t   mapping2;
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                VERTEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
                
                #ubyteList   color;
                VERTEXBUFFER.write( struct.pack("<b", vertexColors[0] ) )
                VERTEXBUFFER.write( struct.pack("<b", vertexColors[1] ) )
                VERTEXBUFFER.write( struct.pack("<b", vertexColors[2] ) )
                VERTEXBUFFER.write( struct.pack("<b", 0 ) )
                
                if dataFlag == 0x5:
                    #Vertex Ex Data
                    #normal_t    normal
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy
                    
                    #mapping_t   mapping3
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )

                elif dataFlag == 0x4:
                    #Vertex Ex Data
                    #normal_t    normal
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy

                elif dataFlag == 0xE:
                    #normal_t    normal
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy

                    #mapping_t   mapping3;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )

                    #mapping_t   mapping4;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )

                elif dataFlag == 0xC:
                    #normal_t    normal;
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.x) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.y) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", floatTo2Byte(1-vertexNormal.z) ) )
                    VERTEXEXBUFFER.write( struct.pack( "<H", 0 ) ) #Dummy

                    #mapping_t   mapping3;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )

                    #mapping_t   mapping4;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )

                    #mapping_t   mapping5;
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(vertexUV.x) ) )
                    VERTEXEXBUFFER.write( struct.pack("<H", floatTo2Byte(1-vertexUV.y) ) )
            
    vertexBufferList.append(   VERTEXBUFFER   )
    vertexExBufferList.append( VERTEXEXBUFFER )
    IndexBufferList.append(    INDEXBUFFER    )

FILEBUFFER.write( VERTEXGROUPBUFFER.getbuffer() )
for vertBuffer, vertExBuffer, indexBuffer in zip(vertexBufferList, vertexExBufferList, IndexBufferList):
    FILEBUFFER.write( vertBuffer.getbuffer() )
    #time.slee(5)
    FILEBUFFER.write( vertExBuffer.getbuffer() )
    FILEBUFFER.write( indexBuffer.getbuffer()  )
    #FILEBUFFER.write( VERTEXBUFFER.getbuffer() )
    #FILEBUFFER.write( VERTEXEXBUFFER.getbuffer() )

with open(WRITE_FILE, "wb+") as test_file:
    test_file.write( FILEBUFFER.getbuffer() )
    test_file.close()
                
        #print("String Memory Size:%s bytes"%sys.getsizeof(stringList))
                #usedVertexListAppend( loop.vertex_index )
        # loop_iter_start = 0
        # #NOTE: RENAME THESE FUNCTION
        # for vertex in mesh.data.vertices:
        #     vertex.co
        #     vertex.normal
            
        #     #loop_iter = iter(mesh.data.loops[loop_iter_start:])
        #     #for index, loop in enumerate(loop_iter):
        #         Split list into pairs of 3
        #          thirdPair = index % 3
        #          if loop.vertex_index == vertex.index:
        #              #save position
        #              loop_iter_start = index
        #              c = c+1
        #              if thirdPair != 0:
        #                  #Skip 1 iteration
        #                  next( loop_iter )
        #              break
        #print("MATCHED Vertices:", c)

        # for polygon in mesh.data.polygons:
        #     map(polygon.loop_indices, loopFunction)
        #     for loopIndex in polygon.loop_indices:
        #         vertexList.append(_loopData.vertex_index)
        #         _loopData        = mesh.data.loops[loopIndex]
                
        #         _loopInfo = loopInfo()
        #         _loopInfo.loopIndex = loopIndex
        #         _loopInfo.loopData = _loopData

        #         indexBufferData.append(_loopData.vertex_index)

        #         if _loopData.vertex_index not in usedVertexList:
        #            loopDict[_loopData.vertex_index] = _loopInfo
        #            usedVertexList.append(_loopData.vertex_index)

        #sortedLoopDict = OrderedDict()

        #for data in sorted(loopDict): sortedLoopDict[data] = loopDict[data]

        
        #[testFunc(index) for index in sortedLoopDict]
print("Time:", time.time()-start_time)
        #for index in sortedLoopDict:
            #NOTE: RENAME THESE FUNCTION

if LOG_VERTEX:
    VERTEX_LOG_FILE.close()