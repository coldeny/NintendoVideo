# This structure DOES NOT store box number of the video.
# ns_data_id of BOSS container does that. So, if ns_data_id
# is 2, that video will be at box #2. Anything else, here.

import construct as c
import hashlib # Pretty much optional, I only used it for testing and comparing files.

DateTime = \
c.Struct(
"year" / c.Int16ul,
"month" / c.Int8ul,
"day" / c.Int8ul,
"hour" / c.Int8ul,
"minute" / c.Int8ul,
"second" / c.Int8ul,

c.Padding(1),
    )

Color = \
c.Struct(
"red" / c.Byte,
"green" / c.Byte,
"blue" / c.Byte,
"alpha" / c.Byte
    )



# Rebuild barely works. F...

nvsp = c.Struct(
    "hdr" / c.Struct(
            "pos_hdr_start" / c.Tell,
            "hdr_start_addr" / c.Const(0x0, c.Int32ul),
            "hdr_end_addr" / c.Rebuild(c.Int32ul, lambda this: 4*7 + 4*len(this._.banners)),
            
            
            "mv_start_addr" / c.Rebuild(c.Int32ul, lambda this: this.hdr_end_addr),
            "mv_end_addr" / c.Int32ul, # won't work when building: c.Rebuild(c.Int32ul, lambda this: this._.mv.pos_mv_end),
            
            "thumbnail_len" / c.Int32ul, # won't work when building: c.Rebuild(c.Int32ul, c.len_(c.this._.mv.thumbnail_data)),
            
            c.Padding(4), # why do you exist?

            #"num_banners" / c.Rebuild(c.Int32ul, c.len_(c.this._.banners)),
            "num_banners" / c.Int32ul,
            
            #"banner_start_addrs" / c.Rebuild(c.Int32ul[c.this.num_banners], lambda this: [banner.pos_banner_start for banner in this._.banners]),
            "banner_start_addrs" / c.Int32ul[c.this.num_banners],
            
            "pos_hdr_end" / c.Tell,
    ),
            
    "mv" / c.Struct(
            "pos_mv_start" / c.Tell,

            "mv_len" / c.Const(0x248, c.Int32ul),
            
            "video_id" / c.PaddedString(0x20, "utf8"),
            
            "release" / DateTime,
            "expiration" / DateTime,
            
            "title" / c.PaddedString(0x78, "utf_16_le"),

            # This part was previously the beginning of "unknown2_idk"
            # Also, this actually DOESN'T HAVE TO BE equal to num banners. It just always was equal so far.
            # There is a weird thing going on, if you:
            # A - Set it to something between 0 and num_banners_again-1, it will play UNTIL THE END where it
            # will then report "corrupted" blah blah. Also I'm pretty sure banner order changes somehow.
            # B - Set it to something bigger than num_banners_again, then the entire video will NOT PLAY.
            "selected_banner_for_something" / c.Default(c.Byte, lambda this: this._.hdr.num_banners),
           
            # This part was always FF, but that doesn't mean IT HAS TO BE. Play with it. It most likely
	    # does something to banners but idk
            "_always_FF_thing" / c.Default(c.Byte, 0xFF),
            
            # 0 -> No restriction. Max I've seen was 18 (0x12) but that's not a hard limit (I tried lol).
            "age_restriction" / c.Default(c.Byte, 0),

            c.Padding(5), # why 5 bytes and not 1?
	    
	    #c.Rebuild(c.Int32ul, c.len_(c.this.video_data)),
            "video_len" / c.Int32ul, 
	    
            "description" / c.PaddedString(0x190, "utf_16_le"),

            
            # why cant we just do it like that?
            # "TypeError: unsupported operand type(s) for -: 'Tell' and 'int'"
            # c.Check(c.Tell - c.this.pos_mv_start == c.this.mv_len),
            "_pos_metadata_video_supposedly_end" / c.Tell,
            c.Check(c.this._pos_metadata_video_supposedly_end - c.this.pos_mv_start == c.this.mv_len),

            # "banner_ids" / c.Rebuild(c.PaddedString(0x20, "utf8")[c.this._.hdr.num_banners], lambda this: [banner.banner_id for banner in this._.banners]),
            "banner_ids" / c.PaddedString(0x20, "utf8")[c.this._.hdr.num_banners],
            
            "video_data" / c.Bytes(c.this.video_len),
            "video_data_SHA256" / c.Computed(lambda this: hashlib.sha256(this.video_data).digest()), # use lambda, not c.this, or weird error.
            
            c.Check(lambda this: this.video_data.startswith(
                (b'L2\xaa\xab', # The pretty common one (has 4 more bytes of \x00 afterwards, at least?)
                 b'L2\xbc\xb9', # The EWP_MD one (has 4 more bytes of \x00 afterwards, at least?)
                 b'L\x00\x00\x00\x00\x00\x00\x00',)) # The "ESP_MD3.2013-04-27.94.1.boss" one (This video did not even play with ffplay...)
                ),

            # https://construct.readthedocs.io/en/latest/misc.html#aligned
            # but i wont add c.Aligned(4, rest of video data thing) because
            # then it would add that to video data, right? i dont want that.
            "_pos_4kpad" / c.Tell,
            c.If(c.this._pos_4kpad % 4 != 0,
                 c.Padding(4 - c.this._pos_4kpad % 4)
                 ),

            "pos_mv_end" / c.Tell, # The actual ending of mv, same as start of thumbnail data itself.

            "thumbnail_data" / c.Bytes(c.this._.hdr.thumbnail_len),
            # FF D8 is jpeg magic, check this link:
            # https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format
            c.Check(lambda this: this.thumbnail_data.startswith(b"\xFF\xD8")),
            "thumbnail_data_SHA256" / c.Computed(lambda this: hashlib.sha256(this.thumbnail_data).digest()),
            

            "_pos_tnail_end" / c.Tell,
            c.If(c.this._pos_tnail_end % 4 != 0,
                c.Padding(4 - c.this._pos_tnail_end % 4)
                ), 
            
            ), 

    # previously "ilinks"
    # okay look ilink ids start with "I" but maybe that's just "I" of "Image".
    # Let's call this "banner" because of lines such as:
    # banner number   :%d
    # movie banner
    # BANNER
    # so now, every "ilink" is renamed to "banner".
    "banners" / c.Aligned(4, c.Struct(
            "pos_banner_start" / c.Tell,

            "metadata_len" / c.Const(0x16c, c.Int32ul),
            
            "banner_id" / c.PaddedString(0x20, "utf8"),

            c.Padding(0x10),
            
            # Renaming this after strings.exe on code.bin which had this line:
            # timePriority     :%08X
	    # i mean... what else could be timePriority? I'd say this guy over here?
            # "unknown3_idk" / c.Bytes(0x8),
            "time_priority" / c.Bytes(8),
            
            "url" / c.PaddedString(0x100, "utf8"),
            "color" / Color,
            "text" / c.PaddedString(0x28, "utf_16_le"),

            # "image_len" / c.Rebuild(c.Int32ul, c.len_(c.this.image_data)),
            "image_len" / c.Int32ul,
            
            "_pos_banner_metadata_end" / c.Tell,
            c.Check(c.this._pos_banner_metadata_end - c.this.pos_banner_start == c.this.metadata_len),
            "image_data" / c.Bytes(c.this.image_len),
            # FF D8 is jpeg magic, check this link:
            # https://en.wikipedia.org/wiki/JPEG_File_Interchange_Format
            c.Check(lambda this: this.image_data.startswith(b"\xFF\xD8")),
            "image_data_SHA256" / c.Computed(lambda this: hashlib.sha256(this.image_data).digest()),
            

    ))[c.this.hdr.num_banners],

)

def fill_options(mandatory_options):
    # Derive options and add them to mandatory options.
    
    all_options = mandatory_options.copy()
    
    all_options.update({
        "hdr":{
            "mv_end_addr": 0x0, # will be fixed during build_bytes
            "banner_start_addrs": [], # will be filled here
              },
        })

    # mv section
    all_options["mv"]["video_len"] = len(mandatory_options["mv"]["video_data"])

    all_options["hdr"]["thumbnail_len"] = len(mandatory_options["mv"]["thumbnail_data"])
    
    banner_ids = [banner["banner_id"] for banner in mandatory_options["banners"]]
    all_options["hdr"]["num_banners"] = len(banner_ids)
    all_options["mv"]["banner_ids"] = banner_ids

    all_options["hdr"]["banner_start_addrs"] = [0x0 for _ in range(len(banner_ids))] # will be fixed during build_bytes
    
    for idx, banner in enumerate(mandatory_options["banners"]):
        all_options["banners"][idx]["image_len"] = len(banner["image_data"])
        
    return all_options

def remove_io_keys(dictionary:dict):
        if isinstance(dictionary, dict):
            return {
                key: remove_io_keys(value)
                for key, value in dictionary.items()
                if key != "_io"
            }
        elif isinstance(dictionary, list):
            return [remove_io_keys(item) for item in dictionary]
        else:
            return dictionary

def parse(data, return_as_dict=False):
    if isinstance(data, str):
        with open(data, "rb") as f:
            data = f.read()
    elif isinstance(data, bytes):
        pass
    else:
        raise TypeError("'data' must be bytes (contents of decrypted BOSS file's payload) or string (file path).")

    parsed = nvsp.parse(data) # parsed is now a c.Container
    if return_as_dict:
        parsed = remove_io_keys(dict(parsed))
        
    return parsed

def build(options, derive_options=True) -> bytes:
    if isinstance(options, c.Container):
        # shouldnt actually happen...
        options = dict(options)
    elif isinstance(options, dict):
        pass
    else:
        raise TypeError("'options' must be a dict or construct.Container.")

    if derive_options:
        # When would it be False? Whenever you
        # build(parse(fn)) TO SAVE TIME (optional)
        # When would it be True? Whenever you
        # build(parse(your_own_options_dict)) (mandatory)
        options = fill_options(options)

    options = nvsp.parse(nvsp.build(options))
    
    # Fixing addresses...
    options["hdr"]["mv_end_addr"] = con.mv.pos_mv_end
    for i, banner in enumerate(con.banners):
        options["hdr"]["banner_start_addrs"][i] = banner.pos_banner_start

    return nvsp.build(options)
