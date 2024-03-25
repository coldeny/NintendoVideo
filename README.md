# NintendoVideo

I only took whats in https://www.3dbrew.org/wiki/Nintendo_Video and then did a few experiments to find out a few more things.

Here are some files for you to parse: https://archive.org/details/nvspf
But you can't just parse them as is, so please check the description first.

You can then parse and change the video data or whatever you want to change. Then you can build that back to decrypted payload. When you are ready, encrypt it back to a BOSS file and while doing so, change "ns data id" to your desired box number. Change "program id" or "title id" if you want the file to work on a different region of nintendo video. Check that archive.org link again for title ids of different nintendo video regions.

If I got something wrong, let me know.
