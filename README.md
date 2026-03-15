A quick converter. 

I needed a simple way to quickly bring a xopp to my remarkable for annotating and then bring it back without losing data. Basically, we scan the xopp, translate all the pen strokes to remarkable strokes, rasterize the rest of the document to a pdf, send it to the remarkable, which can then write on it and edit/erase the translated pen strokes, etc, and then we can bring it back to xopp, ideally, losing no data. I haven't tested this very much so there are likely quite a few bugs. Most of this was written by Gemini, so it certainly should not be trusted, but, it does work well for my very limited use case. 

It's a good start though for a more serious treatment of this. The trickiest bit for me was figuring out how the coordinates transform and how remarkable handles PDFs, since they don't really mention it on their website anywhere. 

You have to put your IP and SSH password in `libs/rm_io_tools/.env`. You call this through `python3 main.py push mynotebook.xopp` and then you bring it back (overwriting) with `python3 main.py pull`. It does make a backup. Alternatively you can also do `python3 main.py pull -o where/to/put/it.xopp`.

```
# libs/rm_io_tools/.env

RM_IP=10.11.99.1
RM_PASSWORD=password
```

Note: I vendored `ricklupton/rmscene` (MIT) for my own simplicity. Thanks.
