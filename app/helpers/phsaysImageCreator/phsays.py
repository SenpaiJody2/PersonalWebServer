import base64, math, textwrap, re, requests, sys
from emoji import get_emoji_unicode_dict

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def PILtoBase64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
def Base64toPIL(base64_str):
    return Image.open(BytesIO(base64.decodebytes(bytes(base64_str, "utf-8"))))


class _emoji:
    def __init__(self, src, index):
        self.index = index
        self.type : int = 0 if len(src) == 1 else 1
        self.bytes : BytesIO = self.getBytesIO(src)
        
    def getBytesIO(self,src):
        if (self.type == 0): #utf-32 emoji
            res : requests.Response = requests.get(f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{ord(src):x}.png")
            return BytesIO(res.content)
        else: #discord emoji
            src = src[src.rfind(":") + 1 : len(src) - 1]
            res : requests.Response = requests.get(f"https://cdn.discordapp.com/emojis/{src}.png")
            return BytesIO(res.content)



def getImage(basetext, fontpath = "ARIAL_MONO.ttf", path_prefix=""):
    #basetext = "ham sandwich <:otswoah:698942793619472496>"
    #indexes 0 and 14
    
    #print(re.split("<:[a-zA-Z]*:[0-9]*>", basetext))

    UNICODE_EMOJI_REGEX = '|'.join(map(re.escape, sorted(get_emoji_unicode_dict("en").values(), key=len, reverse=True)))
    ALL_EMOJI_REGEX = re.compile(f"({'<a?:[a-zA-Z0-9_~-]{2,32}:[0-9]{17,22}>'}|{UNICODE_EMOJI_REGEX})")
 

    _emojiList = []
    while search := ALL_EMOJI_REGEX.search(basetext):
        span = search.span()
        _emojiList.append(_emoji(search.group(), span[0] + len(_emojiList)))
        basetext = basetext[0:span[0]]+ "\0\0" +basetext[span[1]::]

    if not re.search("[^\0]",basetext): # if only emojis, add a space so that font checking works
        basetext = " " + basetext
    #basetext = UNICODE_EMOJI_REGEX.sub("W", basetext )
    #basetext = DISCORD_REGEX.sub("W", basetext )



    #imgbbkey = "8e3f141757491e9ca42e8012783b4199"
    #basetext = "eat it dipshit"

    textImage:Image
    baseImage:Image



    baseImage = Image.open(f"{path_prefix}/base.png")

    fontpath = path_prefix + "/" + fontpath

    width = 600 
    height = 260

    textImage = Image.new("RGBA",size=(width,height),color=(255,255,255,0))


    #font = ImageFont.truetype('CONSOLA.ttf', 24)
   

    font = ImageFont.truetype(fontpath, size=1)
    fontsize = 1
    tarr = [basetext]

    if len(basetext.split(" ")) == 1 and len(basetext) < 20:    #do not wrap single words that are too short    
        while font.getsize(basetext)[0] < width:
            fontsize += 1       
            font = ImageFont.truetype(fontpath, fontsize)
        fontsize -= 1
        font = ImageFont.truetype(fontpath, fontsize)
    else: 
        while (font.getsize("q")[1] * len(tarr)) < height:
            fontsize += 1       
            font = ImageFont.truetype(fontpath, fontsize)
            tarr = textwrap.wrap(basetext, math.floor(width/font.getsize("a")[0]))
        fontsize -= 1
        font = ImageFont.truetype(fontpath, fontsize)
        tarr = textwrap.wrap(basetext, math.floor(width/font.getsize("a")[0]))
  
    if (fontsize) > 332:
        fontsize = 332
        font = ImageFont.truetype(fontpath, fontsize)
        tarr = textwrap.wrap(basetext, math.floor(width/font.getsize("a")[0]))

    textheight = font.getsize("Bq")[1] * len(tarr)
    textlength = max(font.getsize(s)[0] for s in tarr)
    
    charWidth = font.getsize("s")[0]

    emoji_index = 0
    y = math.ceil((height-textheight)/2)
    for line in tarr:
        i = 0
        while i < len(line):
            if line[i] == '\0':
                img : Image.Image = Image.open(_emojiList[emoji_index].bytes).convert("RGBA")
                img = img.resize((math.floor(charWidth*1.5), math.floor(charWidth*1.5)))
                x_disp = math.floor((i - len(line)/2) * charWidth)
                textImage.paste(img,(int(width/2) + x_disp,y+int(fontsize/3)),img)
                i+=1
                emoji_index+=1
            i+=1
        y += font.size

    
    draw = ImageDraw.Draw(textImage)
    draw.text((math.floor((width-textlength)/2),(math.ceil((height-textheight)/2))),"\n".join(tarr), font=font, fill=(0,0,0),align="center")
    #textImage.show()
    
    textImage = textImage.rotate(10, expand=True)

    textImage = textImage.resize((350,200))

    baseImage.paste(textImage,(50,120), textImage)
    
    #output = 'data:image/jpeg;base64,' + PILtoBase64(baseImage)
    #print(PILtoBase64(baseImage),end="")
    return PILtoBase64(baseImage)


