# NintendoVideo

To *try to* create your file, you need an options dict. The dict will look similar to the dict you get when you do parse() on an official file such as ESE_MD4 and convert it to a dict.
So yeah, this nvsp thing can be converted to a dict. 

so um i used this to rebuild a file and it worked fine. i changed the thumbnail and it worked fine. but when i touched the video, it didnt work. so there is this "unknown2_idk" thing. hope someone finds what it really does. i feel like last 4 bytes of it is just padding... maybe it contains which box the file must go + something else or maybe its a 4 byte address. who knows? dani knows.

i only took whats in https://www.3dbrew.org/wiki/Nintendo_Video
