import bpy
import struct
import mathutils
import math
import random
import numpy as np

def nullBytes(num): return b"".join([b"\x00" for x in range(num)])
nullText = "NULL".encode()
def roundup(num, round):
    if round == 0: return num

    remainder = num % round;
    if remainder == 0: return num;

    return num + round - remainder;

#BONEDATA_SIZE            = 88 (#0x58)
#BONEINDEXTRANSTABLE_SIZE = 96 #(0x60)
#MESHDATA_SIZE            = 0
boneList         = []
vertexHeaderList = []
lodList          = []
batchList        = []
matList          = []
weapon = True

class ColorTemp():
    def __init__(self):
        self.x = 255
        self.y = 255
        self.z = 255

#Coldict = {x: b"\ff\xff\xff\xff", y:b"\xff\xff\xff\xff", z:b"\xff\xff\xff\xff"}

class wmbHeader():
    
    def __init__(self):
        self.magic        = nullText
        self.version      = nullText     
        self.unknownA     = nullText
        self.unknownCount = nullText
        self.unknownTerminator = nullText
        self.boundingBoxX = nullText
        self.boundingBoxY = nullText
        self.boundingBoxZ = nullText
        self.boundingBoxU = nullText
        self.boundingBoxV = nullText
        self.boundingBoxW = nullText
        self.bonesOffset  = b"\x90\x00\x00\x00"       #numBones
        self.numBones     = nullText
        self.offsetBoneIndexTranslateTable = nullText
        self.boneTranslateTableSize = nullText
        self.offsetVertexGroups = nullText #numVertexGroups
        self.numVertexGroups    = nullText 
        self.offsetBatches      = nullText #numBatches
        self.numBatches         = nullText 
        self.offsetLods         = nullText #numLods
        self.numLods            = nullText
        self.offsetUnknownB     = nullText #numUnknownB
        self.numUnknownB        = nullText
        self.offsetBoneMap      = nullText
        self.boneMapSize        = nullText
        self.offsetBoneSets     = nullText #numBoneSets
        self.numBoneSets        = nullText
        self.offsetMaterials    = nullText #numMaterials
        self.numMaterials       = nullText
        self.offsetMeshes       = nullText #numMeshes
        self.numMeshes          = nullText 
        self.offsetMeshMaterial = nullText #numMeshMaterial
        self.numMeshMaterial    = nullText
        self.offsetUnknownC     = nullText #numUnknownC
        self.numUnknownC        = nullText 

class wmbBoneData():
    def __init__(self):
        self.boneID        = nullText
        self.parentIndex   = nullText
        self.localPosition = nullText#()  #tuple (x, y, z)
        self.localRotation = nullText#()  #tuple (x, y, z)
        self.localScale    = nullText#()  #tuple (x, y, z)
        self.position      = nullText#()  #tuple (x, y, z)
        self.rotation      = nullText#()  #tuple (x, y, z)
        self.scale         = nullText#()  #tuple (x, y, z)
        self.tPosition     = nullBytes(4)+nullBytes(4)+nullBytes(4) #()  #tuple (x, y, z)

class wmbVertexExDataType4():

    def __init__(self):
        self.nX    = nullText
        self.nY    = nullText
        self.nZ    = nullText
        self.nD    = nullText
        self.map3U = nullText
        self.map3V = nullText

class wmbVertexData():
    
    def __init__(self):
        self.posX = nullText
        self.posY = nullText
        self.posZ = nullText
        self.tanX = nullText
        self.tanY = nullText
        self.tanZ = nullText
        self.mapU = nullText
        self.mapV = nullText
        self.map2U = nullText
        self.map2V = nullText
        self.colX = nullText
        self.colY = nullText
        self.colZ = nullText
        self.colD = nullText

class wmbVertexGroupHeader():
    def __init__(self):
        self.vertexOffset  = nullText
        self.vertexExOffset= nullText
        self.unknownOffset = nullText
        self.unknownOffset = nullText
        self.vertexSize    = nullText
        self.vertexExSize  = nullText
        self.unknownSize   = nullText
        self.numVertexes   = nullText
        self.vertexExFlags = nullText
        self.indexBuffer   = nullText
        self.numIndexes    = nullText

class wmbVertexGroup():
    
    def __init__(self):
        self.vertexOffset  = nullText
        self.vertexExOffset= nullText
        self.unknownOffset = nullText
        self.vertexSize    = nullText
        self.vertexExSize  = nullText
        self.unknownSize   = nullText
        self.numVertexes   = nullText
        self.vertexExFlags = nullText
        self.indexBuffer   = nullText
        self.numIndexes    = nullText
        
class wmbBatch():
    
    def __init__(self):
        self.vertexGroupIndex = nullText
        self.boneSetIndex = nullText
        self.vertexStart = nullText
        Self.indexStart = nullText
        self.numVertex = nullText
        self.numIndex = nullText
        self.numPoly = nullText
        
class wmbLoDHeader():
    
    def __init__(self):
        self.nameOffset      = nullText
        self.lodLevel        = nullText
        self.batchStart      = nullText
        self.batchInfoOffset = nullText
        self.numBatchInfo    = nullText
    
    
class wmbBatchInfo():
    
    def __init__(self):
        self.vertexGroupIndex = nullText
        self.meshIndex        = nullText
        self.materialIndex    = nullText
        self.unknownA         = nullText
        self.meshMatPairIndex = nullText
        self.unknownB         = nullText
        
class wmbMaterials():
    def __init__(self):
        self.unknownA         = nullText
        self.unknownB         = nullText
        self.unknownC         = nullText
        self.nameOffset       = nullText
        self.shaderNameTech   = nullText
        self.techNameOffset   = nullText
        self.unknownD         = nullText
        self.textureOffset    = nullText
        self.numTextures      = nullText
        self.paramGroupOffset = nullText
        self.varOffset        = nullText
        self.numVar           = nullText

class wmbMeshHeader():

    def __init__(self):
        self.nameOffset      = nullText
        self.floatX          = nullText
        self.floatY          = nullText
        self.floatZ          = nullText
        self.floatU          = nullText
        self.floatV          = nullText
        self.floatW          = nullText
        self.materialsOffset = nullText
        self.numfMaterial    = nullText
        self.bonesOffset     = nullText
        self.numBones        = nullText

    
class wmbMaterialHeader():
    def __init__(self):
        self.unknownA         = nullText
        self.unknownB         = nullText
        self.unknownC         = nullText
        self.unknownD         = nullText
        self.nameOffset       = nullText
        self.shaderNameOffset = nullText
        self.techNameOffset   = nullText
        self.unknownE         = struct.pack("<I", 1)
        self.textureOffset    = nullText
        self.numTextures      = nullText
        self.paramGroupOffset = nullText
        self.numParamGroup    = nullText
        self.varOffset        = nullText
        self.numVariables     = nullText

class wmbTexture():
    def __init__(self):
        self.nameOffset = nullText
        self.texture    = nullText
        
class wmbParamGroupsHeader():
    def __init__(self):
        self.index = nullText
        self.paramOffset = nullText
        self.numParam = nullText
        
class wmbParameter():
    def __init__(self):
        self.parameter = nullText
        
class wmbVariable():
    def __init__(self):
        self.nameOffset = nullText
        self.value      = nullText

#Preset data till i can figure out how to get it#
WMBData = wmbHeader()
WMBData.magic        = "WMB3".encode()
WMBData.version      = struct.pack("<I", 538312982)
WMBData.unknownA     = struct.pack("<I", 0)
WMBData.unknownCount = struct.pack("<H", 8)
WMBData.unknownTerminator = struct.pack("<H", 0)
WMBData.boundingBoxX = struct.pack("<I", 0)
WMBData.boundingBoxY = struct.pack("<I", 0)
WMBData.boundingBoxZ = struct.pack("<I", 0)
WMBData.boundingBoxU = struct.pack("<I", 0)
WMBData.boundingBoxV = struct.pack("<I", 0)
WMBData.boundingBoxW = struct.pack("<I", 0)
WMBData.temp         = b"".join([b"\x00" for x in range(0x64)])

contents = open("[wmb filepath]", "wb+")

contents.write(WMBData.magic)
contents.write(WMBData.version)
contents.write(WMBData.unknownA )
contents.write(WMBData.unknownCount)
contents.write(WMBData.unknownTerminator)
contents.write(WMBData.boundingBoxX)
contents.write(WMBData.boundingBoxY)
contents.write(WMBData.boundingBoxZ)
contents.write(WMBData.boundingBoxU)
contents.write(WMBData.boundingBoxV)
contents.write(WMBData.boundingBoxW)
contents.write(WMBData.bonesOffset)
contents.write(WMBData.temp)

#print("version", WMBData.version)
for mesh in [obj for obj in bpy.data.objects if obj.type == "MESH"]:
    mesh.data.calc_tangents ()
    #Gonna put bounding box stuff here
    #mesh.dimensions
    for armature in [obj for obj in mesh.children if obj.type == "ARMATURE"]:
        c = 0
        boneDic = {} 
        count = 0
        
        for bone in armature.pose.bones:
            boneDic[bone.name] = c
            c = c+1
        
        #Bone Data
        BoneDataPos = contents.tell()
        contents.seek(0x28)
        contents.write( struct.pack( "<I",  BoneDataPos ) )
        contents.seek(0x2c)
        contents.write( struct.pack( "<I", len(armature.pose.bones) ) )
        contents.seek(BoneDataPos)
        
        for bone in armature.pose.bones:
            boneData  = wmbBoneData()
            if bone.parent:
                parentMatrix         = bone.parent.matrix
                boneData.boneID      = struct.pack( "<H", boneDic[bone.name] )
                boneData.parentIndex = struct.pack( "<H", boneDic[bone.parent.name] )

            else:
                parentMatrix         = bone.matrix
                boneData.boneID      = struct.pack( "<H", boneDic[bone.name] )
                boneData.parentIndex = struct.pack( "<H", 65535 )
            
            boneMatrix  = bone.matrix
            localMatrix = boneMatrix-parentMatrix
            print("---------------------------------------")
            print("Position", mesh.scale     )
            print("Rotation", mesh.location  )
            print("Scale   ", boneMatrix.to_scale()       )
            boneData.localPosition = b"".join( [struct.pack("<f", localMatrix[0][3]),              struct.pack("<f", localMatrix[1][3]),              struct.pack("<f", localMatrix[2][3])] )
            boneData.localRotation = b"".join( [struct.pack("<f", localMatrix.to_euler("XYZ")[0]), struct.pack("<f", localMatrix.to_euler("XYZ")[1]), struct.pack("<f", localMatrix.to_euler("XYZ")[2])] )
            boneData.localScale    = b"".join( [struct.pack("<f", localMatrix.to_scale()[0]),      struct.pack("<f", localMatrix.to_scale()[1]),      struct.pack("<f", localMatrix.to_scale()[2])] )
            
            boneData.position      = b"".join( [struct.pack("<f", boneMatrix[0][3]),              struct.pack("<f", boneMatrix[1][3]),              struct.pack("<f", boneMatrix[2][3])] )
            boneData.rotation      = b"".join( [struct.pack("<f", boneMatrix.to_euler("XYZ")[0]), struct.pack("<f", boneMatrix.to_euler("XYZ")[1]), struct.pack("<f", boneMatrix.to_euler("XYZ")[2])] )
            boneData.scale         = b"".join( [struct.pack("<f", boneMatrix.to_scale()[0]),      struct.pack("<f", boneMatrix.to_scale()[1]),      struct.pack("<f", boneMatrix.to_scale()[2])] )
            
            contents.write(boneData.boneID)
            contents.write(boneData.parentIndex)
            contents.write(boneData.localPosition)
            contents.write(boneData.localRotation)
            contents.write(boneData.localScale)
            contents.write(boneData.position)
            contents.write(boneData.rotation )
            contents.write(boneData.scale )
            contents.write(boneData.tPosition )
            
            contents.write( nullBytes(8) )
            
            count = count + 1
    
    #Index Translate Table
    if weapon:
        IndexTransTablePos = contents.tell()
        contents.seek(0x30)
        contents.write( struct.pack( "<I", IndexTransTablePos ) )
        contents.write( struct.pack( "<I", 0x60 ) )
        contents.seek(IndexTransTablePos)
        #We can nop this weapons dont use this as far as i know
        IndexTransTable = b"".join( [b"\00" for x in range(0x60) ])
        contents.write(IndexTransTable)
    else:
        #Pass for now i dont know what this does
        pass
    
    #Get Vertex Group data
    #Vertex groups seem to be related to LoD's and Batches but since weapons dont use either
    #We only need one vertex group with a few specific changes
    if weapon:
        
        vertexGroupHeaderPos = contents.tell()
        contents.seek(0x0038)
        contents.write( struct.pack( "<I", vertexGroupHeaderPos ) )
        contents.write( struct.pack( "<I", 1 ) )
        contents.seek(vertexGroupHeaderPos)
    
        vGroup = wmbVertexGroup()
        vGroup.vertexOffset      = nullText #nullBytes(4) #Well change this later
        vGroup.vertexExOffset    = nullText #nullBytes(4) #Well change this later
        vGroup.unknownA          = nullBytes(4) #Dont need
        vGroup.unknownB          = nullBytes(4) #Dont need
        vGroup.vertexSize        = b"\x1C"+nullBytes(3) #Stays the same
        vGroup.vertexExSize      = b"\x0C"+nullBytes(3) #nullBytes(4) #Stays the same
        vGroup.unknownC          = nullBytes(4) #Dont need
        vGroup.unknownD          = nullBytes(4) #Dont need
        vGroup.numVertex         = struct.pack("<I", len(mesh.data.vertices) ) #mesh vertices
        vGroup.vertexExDataFlags = b"\x05"+nullBytes(3) #Well keep this 0x5

        vGroup.indexBuffOffset   = nullBytes(4) #Well change this later
        vGroup.numIndexes        = struct.pack("<I", len(mesh.data.loops) )#nullBytes(4) #Well change this later
                
        contents.write(vGroup.vertexOffset      )
        contents.write(vGroup.vertexExOffset    )
        contents.write(vGroup.unknownA          )
        contents.write(vGroup.unknownB          )
        contents.write(vGroup.vertexSize        )
        contents.write(vGroup.vertexExSize      )
        contents.write(vGroup.unknownC          )
        contents.write(vGroup.unknownD          )
        contents.write(vGroup.numVertex         )
        contents.write(vGroup.vertexExDataFlags )

        contents.write(vGroup.indexBuffOffset   )
        contents.write(vGroup.numIndexes        )
        
    else:
        #Cant do anything with this yet
        vertexGroups = mesh.vertex_groups
        for group in vertexGroups:
            pass
    
    #Vertex Data
    vertexPos = contents.tell()
    contents.seek(vertexGroupHeaderPos)
    contents.write( struct.pack( "<I", vertexPos ) )
    contents.seek(vertexPos)
    normalList     = []
    usedVertexList = []
    for poly in mesh.data.polygons:
    
        for vert, loopIndex in zip(mesh.data.vertices, poly.loop_indices):
            loopData      = mesh.data.loops[loopIndex]
            vertexIndex   = loopData.vertex_index

            _wmbVertexData   = wmbVertexData()
            wmbVertexExData = wmbVertexExDataType4()

            if vertexIndex not in usedVertexList:
                vertexCoords  = mesh.data.vertices[vertexIndex].co
                vertexTangent = loopData.tangent #(x, y)
                UVData        = mesh.data.uv_layers.active.data[loopIndex].uv
                vertex_normal = mesh.data.vertices[vertexIndex].normal
                UVIntX = np.float16(UVData.x).view("int16")
                UVIntY = np.float16(1-UVData.y).view("int16")
                vTX = vertexTangent.x*255
                vTX = vertexTangent.x/2
            
                vTY = vertexTangent.y*255
                vTY = vertexTangent.y/2
                
                vTZ = vertexTangent.z*255
                vTZ = vertexTangent.z/2
                
                
                '''vTX = vertexTangent.x/255
                vTX = vertexTangent.x*2
            
                vTY = vertexTangent.y/255
                vTY = vertexTangent.y*2
                
                vTZ = vertexTangent.z/255
                vTZ = vertexTangent.z*2'''
                
                vertexColors = ColorTemp()
                #Vertex normal data GOTTA FIX VERTEX EX DATA
                wmbVertexExData.nX = struct.pack("<h", np.float16(1-vertex_normal.x).view("int16") )
                wmbVertexExData.nY = struct.pack("<h", np.float16(1-vertex_normal.y).view("int16") )
                wmbVertexExData.nZ = struct.pack("<h", np.float16(1-vertex_normal.z).view("int16") )
                wmbVertexExData.nD = b"\x00\x00"
                
                wmbVertexExData.map3U = struct.pack("<h", UVIntX )
                wmbVertexExData.map3V = struct.pack("<h", UVIntY )
                normalList.append(wmbVertexExData)
                
                _wmbVertexData.posX  = struct.pack("<f", vertexCoords.x)
                _wmbVertexData.posY  = struct.pack("<f", vertexCoords.y)
                _wmbVertexData.posZ  = struct.pack("<f", vertexCoords.z)
                
                _wmbVertexData.tanX  = struct.pack("<b", round(vTX) )
                _wmbVertexData.tanY  = struct.pack("<b", round(vTY) )
                _wmbVertexData.tanZ  = struct.pack("<b", round(vTZ) )
                _wmbVertexData.tanZ  = b"\xff"
                
                #This is gonna be messed up#
                _wmbVertexData.mapU  = struct.pack("<h", UVIntX )
                _wmbVertexData.mapV  = struct.pack("<h", UVIntY )
                _wmbVertexData.map2U = struct.pack("<h", UVIntX )
                _wmbVertexData.map2V = struct.pack("<h", UVIntY )
                
                _wmbVertexData.colX  = struct.pack("<B", round(vertexColors.x) )
                _wmbVertexData.colY  = struct.pack("<B", round(vertexColors.y) )
                _wmbVertexData.colZ  = struct.pack("<B", round(vertexColors.z) )
                _wmbVertexData.colD  = b"\xff"

                contents.write(_wmbVertexData.posX)
                contents.write(_wmbVertexData.posY)
                contents.write(_wmbVertexData.posZ)
                contents.write(_wmbVertexData.tanX)
                contents.write(_wmbVertexData.tanY)
                contents.write(_wmbVertexData.tanZ)
                contents.write(_wmbVertexData.tanZ)
                contents.write(_wmbVertexData.mapU)
                contents.write(_wmbVertexData.mapV)
                contents.write(_wmbVertexData.map2U)
                contents.write(_wmbVertexData.map2V)
                contents.write(_wmbVertexData.colX)
                contents.write(_wmbVertexData.colY)
                contents.write(_wmbVertexData.colZ)
                contents.write(_wmbVertexData.colD)
                
                usedVertexList.append(vertexIndex)
            
    contents.write(nullBytes(12))
                
    #Vertex Ex Data
    vertexExPos = contents.tell()
    contents.seek(vertexGroupHeaderPos+4)
    contents.write( struct.pack( "<I", vertexExPos ) )
    contents.seek(vertexExPos)
    
    for data in normalList:
        contents.write(wmbVertexExData.nX )
        contents.write(wmbVertexExData.nY )
        contents.write(wmbVertexExData.nZ )
        contents.write(wmbVertexExData.nD )
        contents.write(wmbVertexExData.map3U )
        contents.write(wmbVertexExData.map3V )
    contents.write(nullBytes(12))
    #Index Buffer Data
    #in blender index buffers are MeshLoops
    if weapon:
        indexBuffPos = contents.tell()
        contents.seek(vertexGroupHeaderPos+40)
        contents.write( struct.pack( "<I", indexBuffPos ) )
        contents.seek(indexBuffPos)
        """Gonna need to do some more work on this not what i thought im just gonna null it for the time being"""
        indexBuffer = b""
        for poly in mesh.data.polygons:
            for li in poly.loop_indices:
                vertex_index = mesh.data.loops[li].vertex_index
                indexBuffer = indexBuffer+struct.pack("<I", vertex_index)
        contents.write(indexBuffer)
    else:
        pass
                            
    #Batch Data
    #Pretty straight for word
    if weapon:
        batchPos = contents.tell()
        contents.seek(0x0040)
        contents.write( struct.pack( "<I", batchPos ) )
        contents.write( struct.pack( "<I", 1 ) )
        contents.seek(batchPos)
        
        hexVertices = struct.pack("<I", len(mesh.data.vertices))
        hexPolys    = struct.pack("<I", len(mesh.data.polygons))
        hexIndexes  = struct.pack("<I", round(len(indexBuffer)/4))
        batchData = b"\x00\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00"+hexVertices+hexIndexes+hexPolys

        contents.write(batchData)
    else:
        pass
    
    #LOD DATA
    if weapon:
        lodPos = contents.tell()
        contents.seek(0x0048)
        contents.write( struct.pack( "<I", lodPos ) )
        contents.write( struct.pack( "<I", 1 ) )
        contents.seek(lodPos)
        
        lodData = wmbLoDHeader()
        lodData.nameOffset      = nullBytes(4) #change later
        lodData.lodLevel        = nullBytes(4)
        lodData.batchStart      = nullBytes(4)
        lodData.batchInfoOffset = nullBytes(4) #change later
        lodData.numBatchInfo    = b"\x01\x00\x00\x00"
        
        contents.write(lodData.nameOffset)
        contents.write(lodData.lodLevel)
        contents.write(lodData.batchStart)
        contents.write(lodData.batchInfoOffset)
        contents.write(lodData.numBatchInfo)
        
        #Batch info stuff gotta FIX this later but its ok for now
        batchInfoPos = contents.tell()
        contents.seek(lodPos+12)
        contents.write( struct.pack( "<I", batchInfoPos ) )
        contents.write( struct.pack( "<I", 1 ) )
        contents.seek(batchInfoPos)
        
        contents.write(nullBytes(12)+b"\xFF\xFF\xFF\xFF"+nullBytes(4)+b"\xFF\xFF\xFF\xFF")
        
        currPos = contents.tell()
        contents.seek(lodPos)
        contents.write( struct.pack( "<I", currPos ) )
        contents.seek(currPos)
        contents.write( "LOD0".encode()+nullBytes(1) )
        
        currPos = contents.tell()
        if currPos % 4 == 0:
            pass
        else:
            contents.write( nullBytes( roundup(currPos, 8)-currPos ) )
        
    else:
        pass
        
    #Mesh Material Pair
    meshMaterialPos = contents.tell()
    contents.seek(0x0078)
    contents.write( struct.pack( "<I", meshMaterialPos ) )
    contents.write( struct.pack( "<I", 1 ) )
    contents.seek(meshMaterialPos)
    
    contents.write( nullBytes(8) )
    
    contents.write( nullBytes(8) )
    
    #Bone map
    currPos = contents.tell()
    contents.seek(0x0058)
    contents.write( struct.pack( "<I", currPos ) )
    contents.write( struct.pack( "<I", 1 ) )
    contents.seek(currPos)
        
    contents.write( nullBytes(4) )
    
    #Bone Sets
    if weapon:
        pass    
    
    #Mesh
    meshPos = contents.tell()
    contents.seek(0x0070)
    contents.write( struct.pack( "<I", meshPos ) )
    contents.write( struct.pack( "<I", 1 ) )
    contents.seek(meshPos)
    meshData = wmbMeshHeader()
    meshData.numBones = struct.pack( "<I", 1 )
    
    contents.write(meshData.nameOffset      )
    contents.write(meshData.floatX          )
    contents.write(meshData.floatY          )
    contents.write(meshData.floatZ          )
    contents.write(meshData.floatU          )
    contents.write(meshData.floatV          )
    contents.write(meshData.floatW          )
    contents.write(meshData.materialsOffset )#= nullBytes(4)
    contents.write(meshData.numfMaterial    )#= nullBytes(4)
    contents.write(meshData.bonesOffset     )#= nullBytes(4)
    contents.write(meshData.numBones        )
    
    meshNamePos = contents.tell()
    contents.seek(meshPos)
    contents.write( struct.pack( "<I", meshNamePos ) )
    contents.seek(meshNamePos)
    
    bytesMeshName = mesh.name.encode()
    contents.write( mesh.name.encode()+nullBytes(1) )
    
    MeshMaterialsPos = contents.tell()
    contents.seek(meshPos+28)
    contents.write( struct.pack( "<I", MeshMaterialsPos ) )
    contents.write( struct.pack( "<I", 1 ) )
    contents.seek(MeshMaterialsPos)
    
    contents.write( nullBytes(2) )
    
    MeshBonesPos = contents.tell()
    contents.seek(meshPos+36)
    contents.write( struct.pack( "<I", MeshBonesPos ) )
    contents.seek(MeshBonesPos)
    
    contents.write( nullBytes(2) )
    
    currPos = contents.tell()
    if currPos % 4 == 0:
        pass
    else:
        contents.write( nullBytes( roundup(currPos, 8)-currPos ) )
    
    
    #Material
    MaterialPos = contents.tell()
    contents.seek(0x0068)
    contents.write( struct.pack( "<I", MaterialPos ) )
    contents.write( struct.pack( "<I", 1 ) )
    contents.seek(MaterialPos)
    
    materialHeaderData = wmbMaterialHeader()
    materialHeaderData.numTextures = struct.pack("<I", 7 )
    
    contents.write(materialHeaderData.unknownA)
    contents.write(materialHeaderData.unknownB)
    contents.write(materialHeaderData.nameOffset)
    contents.write(materialHeaderData.shaderNameOffset)
    contents.write(materialHeaderData.techNameOffset)
    contents.write(materialHeaderData.unknownE)
    contents.write(materialHeaderData.textureOffset)
    contents.write(materialHeaderData.numTextures)
    contents.write(materialHeaderData.paramGroupOffset)
    contents.write(materialHeaderData.numParamGroup)
    contents.write(materialHeaderData.varOffset)
    contents.write(materialHeaderData.numVariables)
    
    materialNamePos = contents.tell()
    contents.seek(MaterialPos+8)
    contents.write( struct.pack( "<I", materialNamePos ) )
    contents.seek(materialNamePos)
    
    contents.write( mesh.material_slots[0].name.split(".")[0].encode()+nullBytes(1) )
    
    materialShaderPos = contents.tell()
    contents.seek(MaterialPos+12)
    contents.write( struct.pack( "<I", materialShaderPos ) )
    contents.seek(materialShaderPos)
    
    contents.write( "PBS00_XXXXX".encode()+nullBytes(1)  )
    
    materialTechPos = contents.tell()
    contents.seek(MaterialPos+16)
    contents.write( struct.pack( "<I", materialTechPos ) )
    contents.seek(materialTechPos)
    
    contents.write( "Default".encode()+nullBytes(1) )
    
    #Texture Data
    texturePos = contents.tell()
    contents.seek(MaterialPos+24)
    contents.write( struct.pack( "<I", texturePos ) )
    contents.seek(texturePos)
    
    textureData = wmbTexture()
    textureList = ["g_AlbedoMap", "g_LightMap", "g_MaskMap", "g_NormalMap","g_DetailNormalMap", "g_EnvMap", "g_IrradianceMap"]
    textureDataList = [b"\x2A\xCB\x7C\x68", b"\xF4\x16\x9C\x4E", b"\x3C\xCC\x0D\x19", b"\x51\x7E\x05\x73", b"\x9A\x92\xD4\x7F", b"\x84\x09\xBC\x1F", b"\x84\x09\xBC\x1F"]
    
    for index, value in enumerate(textureDataList):
        contents.write(textureData.nameOffset)
        contents.write(value)
    
    for index, val in enumerate(textureList):
        textureNamePos = contents.tell()
        contents.seek( texturePos+(index*8) )
        contents.write( struct.pack("<I", textureNamePos) )
        contents.seek(textureNamePos)
        contents.write(val.encode()+nullBytes(1))
       
    currPos = contents.tell()
    if currPos % 4 == 0:
        pass
    else:
        contents.write( nullBytes( roundup(currPos, 8)-currPos )+nullBytes(8) )
        
    paramGroupHeaderPos = contents.tell()
    contents.seek(MaterialPos+32)
    contents.write( struct.pack( "<I", paramGroupHeaderPos ) )
    contents.write( struct.pack( "<I", 2 ) )
    contents.seek(paramGroupHeaderPos)
    
    paramGroupHeader = wmbParamGroupsHeader()
    
    for i in range(2):
        if i == 0:
            paramGroupHeader.index = struct.pack( "<I", 0 )
            paramGroupHeader.numParam = struct.pack( "<I", 36 )
        if i == 1:
            paramGroupHeader.index = b"\xff\xff\xff\xff"
            paramGroupHeader.numParam = struct.pack( "<I", 4 )
        
        contents.write(paramGroupHeader.index)
        contents.write(paramGroupHeader.paramOffset)
        contents.write(paramGroupHeader.numParam)
        
    contents.write( nullBytes(8) )
    
    paramPos = contents.tell()
    contents.seek(paramGroupHeaderPos+4)
    contents.write( struct.pack( "<I", paramPos ) )
    contents.seek(paramPos)
    
    for i in range(2):
        paramPos = contents.tell()
        contents.seek( paramGroupHeaderPos+(i*12)+4 )
        contents.write( struct.pack( "<I", paramPos ) )
        contents.seek(paramPos)
        
        if i == 0:
            params  = b"\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x00"
            paramsUnknown  = b"\x00\x00\x80\x3F" #This calue changes
            params2 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            paramsUnknown2 = b"\xAE\x47\x21\x3F\x9A\x99\x59\x3F"
            params3 = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            finalParam = params+paramsUnknown+params2+paramsUnknown2+params3
        if i == 1:
            finalParam = nullBytes(4*4)
                
        contents.write(finalParam)
        
    #Variable Data
    variablePos = contents.tell()
    contents.seek(MaterialPos+40)
    contents.write( struct.pack( "<I", variablePos ) )
    contents.write( struct.pack( "<I", 50 ) )
    contents.seek(variablePos)
    
    varNameList = ["Binormal0", "Color0", "Normal", "Position", "Tangent0", "TexCoord0", "TexCoord1", "g_1BitMask", "g_AlbedoColor_X", "g_AlbedoColor_Y", "g_AlbedoColor_Z", "g_AmbientLightIntensity", "g_Anisotropic", "g_Decal", "g_DetailNormalTile_X", "g_DetailNormalTile_Y", "g_Glossiness", "g_IsSwatchRender", "g_LighIntensity0", "g_LighIntensity1", "g_LighIntensity2", "g_LightColor0_X", "g_LightColor0_Y", "g_LightColor0_Z", "g_LightColor1_X", "g_LightColor1_Y", "g_LightColor1_Z", "g_LightColor2_X", "g_LightColor2_Y", "g_LightColor2_Z", "g_LightIntensity", "g_Metallic", "g_NormalReverse", "g_ObjWetStrength", "g_OffShadowCast", "g_ReflectionIntensity", "g_Tile_X", "g_Tile_Y", "g_UV2Use", "g_UseDetailNormalMap", "g_UseEnvWet", "g_UseLightMap", "g_UseNormalMap", "g_UseObjWet", "g_UseOcclusionMap", "g_WetConvergenceGlossiness", "g_WetMagAlbedo", "g_bAlbedoOverWrite", "g_bGlossinessOverWrite", "g_bMetalicOverWrite", ]
    varDataList = [b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x3F", b"\x00\x00\x00\x3F", b"\x00\x00\x00\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\xCD\xCC\x4C\x3E", b"\x00\x00\x00\x00", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x80\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x80\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x9A\x99\x59\x3F", b"\xAE\x47\x21\x3F", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"]
    
    for index, val in enumerate(varDataList):
        variableData = wmbVariable()
        variableData.value = val
        contents.write(variableData.nameOffset)
        contents.write(variableData.value)
        
    for index, val in enumerate(varNameList):
        varNamePos = contents.tell()
        contents.seek(variablePos+(index*8))
        contents.write( struct.pack( "<I", varNamePos ) )
        contents.seek(varNamePos)
        
        contents.write( val.encode()+nullBytes(1) )

contents.close()
print("Saved FIle")