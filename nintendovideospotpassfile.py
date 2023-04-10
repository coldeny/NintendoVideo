import construct as c

#Types i guess?
Timestampt = \
c.Debugger(c.Struct(
"year" / c.Int16ul,
"month" / c.Int8ul,
"day" / c.Int8ul,
"hours" / c.Int8ul,
"minutes" / c.Int8ul,
"seconds" / c.Int8ul,
"unknown3_padding" / c.Padding(1) #or c.Byte
    ))

Color = \
c.Debugger(c.Struct(
"red" / c.Byte,
"green" / c.Byte,
"blue" / c.Byte,
"alpha" / c.Byte))



nvsp = c.Struct(
"hdr" / c.Struct(
        "pos_hdr_start" / c.Tell,
        
	"hdr_start_addr" / c.Int32ul,
	c.Check(c.this.hdr_start_addr == 0x0),

	"hdr_end_addr" / c.Int32ul,
	"mv_start_addr" / c.Int32ul,
	c.Check(c.this.hdr_end_addr == c.this.mv_start_addr),
	"mv_end_addr" / c.Int32ul,

	"vid_tnail_len" / c.Int32ul,

	"unknown1_padding" / c.Bytes(4), #c.Byte[4],
	
	"num_ilinks" / c.Int32ul,
	"ilink_start_addrs" / c.Int32ul[c.this.num_ilinks],

        "pos_hdr_end" / c.Tell,
        
	#stop if addresses arent %4=0
	#stop if num ilinks is 0? or negative
        #but who cares?
        #c.Probe(),
),
	
"mv" / c.Struct(
        "pos_mv_start" / c.Tell,
        
	"mv_len" / c.Int32ul,
	c.Check(c.this.mv_len == 0x248),
	"video_id" / c.PaddedString(0x20, "utf8"),
	"release_date" / Timestampt,
	"expiration_date" / Timestampt,
	"video_title" / c.PaddedString(0x78, "utf_16_le"),
	"unknown2_idk" / c.Bytes(8), #c.Byte[0x8],

        #UNKNOWN2 IS THE THING I NEED

	"video_len" / c.Int32ul,
	"video_description" / c.PaddedString(0x190, "utf_16_le"),

        #None of these checks will work unless you add the
        #start poses accordingly, c.Tell is still absolute position.
        #""""_pos_0x248check" / c.Tell,
        #c.StopIf(c.this._pos_0x248check != 0x248),"""

	"ilink_ids" / c.PaddedString(0x20, "utf8")[c.this._.hdr.num_ilinks],

	"video_data" / c.Bytes(c.this.video_len),
        #check is broken: c.Check(c.this.video_data.startswith(b"L2\xAA\xAB")),
        	
	"_pos_4kpad" / c.Tell,
	c.If(c.this._pos_4kpad % 4 != 0,
             c.Padding(4 - c.this._pos_4kpad % 4)
             ),

        "pos_mv_end" / c.Tell, #The actual ending of mv, same as start of video thumbnail data itself.

        #Normally, I would "align" this "mv" thing, but vid tnail cannot access hdr
        #as such I have to put it back inside. So aligned? No more.
        "video_tnail_data" / c.Bytes(c.this._.hdr.vid_tnail_len), #Bytes() doesnt work.
        
        #FF D8 is jpeg magic, check this link:
        #https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format
        #Note: The check is still broken for some reason. Same with moflex's check.
        #Then why did i keep it? i forgot. if it causes issues, comment or fix it.
        c.Check(lambda this: this.video_tnail_data.startswith(b"\xFF\xD8")),

        "pos_vid_tnail_end" / c.Tell,
        c.If(c.this.pos_vid_tnail_end % 4 != 0,
            c.Padding(4 - c.this.pos_vid_tnail_end % 4)
            ), #This last line could be removed
        #and replaced with Aligned(4,... of mv struct but, really idc just work first
        #works: c.Check(False)
        
        ), #mv end


#ilinks
"ilinks" / c.Aligned(4, c.Struct(
        "pos_ilink_start" / c.Tell,
        
        "metadata_len" / c.Int32ul,
        c.Check(c.this.metadata_len == 0x16c),
        "ilink_id" / c.PaddedString(0x20, "utf8"),
        c.Padding(0x10), #probably?
        "unknown3_idk" / c.Bytes(0x8),

        "url" / c.PaddedString(0x100, "utf8"),
        "color" / Color,
        "text" / c.PaddedString(0x28, "utf_16_le"),

        #0x168 + 0x4 is 0x16c which checks out.
        #0x4 part comes from image_len below.
        #so dont worry. it isnt a typo.
        #"_pos_endofilinkmetadata" / c.Tell,
        #c.StopIf(c.this._pos_endofilinkmetadata != 0x168),

        "image_len" / c.Int32ul, 
        "image_data" / c.Bytes(c.this.image_len),

))[c.this.hdr.num_ilinks],

)

"You know what? Actually the whole nvsp could become an aligned struct (to 4) as well. but it works as is now. so i wont do that"

#So basically:
def build(options:dict):
    x = nvsp.build(data_dict)
    y = nvsp.parse(x)

    #Now we have to fix addresses.
    options["hdr"]["hdr_start_addr"] = y.hdr.pos_hdr_start
    options["hdr"]["hdr_end_addr"] = y.hdr.pos_hdr_end
    options["hdr"]["mv_start_addr"] = y.mv.pos_mv_start
    options["hdr"]["mv_end_addr"] = y.mv.pos_mv_end

    for i, ilink in enumerate(y.ilinks):
        data_dict["hdr"]["ilink_start_addrs"][i] = ilink.pos_ilink_start

    x = nvsp.build(data_dict) #final. fixed.
    return x

def parse(data):
    return nvsp.parse(data)
    
