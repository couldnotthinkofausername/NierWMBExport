'''
Tool used to extract bone, maps, sets and 
translation indexes from Nier Automata 3D model files
'''
import sys
WMB_FILE = sys.argv[1]
try:
    OUT_FILE = sys.argv[2]
except:
    OUT_FILE = "test.hash"

WMB_BONE_OFFSET_POINTER = 0x28
WMB_BITT_OFFSET_POINTER = 0x30
WMB_BONE_MAP_POINTER = 0x58
WMB_BONE_SET_POINTER = 0x60

wmb_data = open(WMB_FILE, "rb")
out_data = open(OUT_FILE, "w")

#Bones
def extract_BONES(wmb):
    bone_list = []
    
    wmb.seek(WMB_BONE_OFFSET_POINTER)

    bone_offset = int.from_bytes(wmb.read(4), "little")
    bone_length = 0x58*int.from_bytes(wmb.read(4), "little")
    print("Bone Offset", hex(bone_offset) )

    wmb.seek(bone_offset)

    d = wmb.tell()

    while wmb.tell() < d+bone_length:
        boneDataList = []
        index = 0
        c = wmb.tell()
        
        while wmb.tell() < c+0x58:
            if index in (0, 1):
                boneDataList.append( int.from_bytes(wmb.read(2), "little") )
            else:
                boneDataList.append( int.from_bytes(wmb.read(4), "little") )
            
            index = index+1
        
        bone_list.append( boneDataList )
    
    id = "0:"
    for data in bone_list:
        line = " ".join([str(i) for i in data])
        out_data.write(id+line+"\n" )
        print(line)
    out_data.write("\n")

#Bone Index Translation Table
def extract_BITT(wmb):
    bitt_list = []
    wmb.seek(WMB_BITT_OFFSET_POINTER)
    
    bitt_offset = int.from_bytes(wmb.read(4), "little")
    bitt_length = int.from_bytes(wmb.read(4), "little")

    wmb.seek(bitt_offset)
    d = wmb.tell()
    
    while wmb.tell() < d+bitt_length:
        #print("{}/{}".format(wmb.tell(), d+bitt_length) )
        bitt_list.append( int.from_bytes(wmb.read(2), "little") )
        
    id = "1:"
    for index in bitt_list:
        out_data.write(id+str(index)+"\n" )
    out_data.write("\n")


#Bone Map
def extract_BM(wmb):
    bm_list = []
    wmb.seek(WMB_BONE_MAP_POINTER)
    bm_offset = int.from_bytes(wmb.read(4), "little")
    bm_length = 4*int.from_bytes(wmb.read(4), "little")

    wmb.seek(bm_offset)
    d = wmb.tell()

    while wmb.tell() < d+bm_length:
        bm_list.append( int.from_bytes(wmb.read(4), "little") )

    id = "2:"
    for index in bm_list:
        out_data.write( id+str(index)+"\n" )
    out_data.write("\n")

#Bone Sets
def extract_BS(wmb):
    bs_list  = [] #bone set list 
    bsh_list = [] #bone set header list
    wmb.seek(WMB_BONE_SET_POINTER)
    bsh_offset = int.from_bytes(wmb.read(4), "little")
    bsh_length = 8*int.from_bytes(wmb.read(4), "little")

    wmb.seek(bsh_offset)
    d = wmb.tell()

    while wmb.tell() < d+bsh_length:
        bsh_list.append( [int.from_bytes(wmb.read(4), "little"), int.from_bytes(wmb.read(4), "little")]
        )

    id = "3:"
    for bsh_data in bsh_list:
        line = " ".join( [ str(i) for i in bsh_data ] )
        out_data.write( id+line+"\n" )

        bs_offset = bsh_data[0] #bone set offset
        bs_length = bsh_data[1] #num of bone indexes
        
        wmb.seek(bs_offset)
        
        for i in range(bs_length):
            i = i
            bs_list.append( int.from_bytes( wmb.read(2), "little" ) )

    out_data.write("\n")

    id = "4:"
    for index in bs_list:
        out_data.write(id+str(index)+"\n" )
    out_data.write("\n")


extract_BONES(wmb_data)
extract_BITT(wmb_data)
extract_BM(wmb_data)
extract_BS(wmb_data)

wmb_data.close()
out_data.close()
input()