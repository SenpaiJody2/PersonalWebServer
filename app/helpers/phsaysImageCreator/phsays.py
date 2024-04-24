import base64, math, re, requests, sys
from emoji import get_emoji_unicode_dict

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from pilmoji import Pilmoji

def getErrorPicture(path_prefix):
    #Image.open(f"{path_prefix}/error.png").show()
    return PILtoBase64(Image.open(f"{path_prefix}/error.png"))


def PILtoBase64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
def Base64toPIL(base64_str):
    return Image.open(BytesIO(base64.decodebytes(bytes(base64_str, "utf-8"))))




class _emoji:
    def __init__(self, src, index):
        self.index = index
        self.isCustom : int = 0 if len(src) == 1 else 1
        self.bytes : BytesIO = self.getBytesIO(src)
        
    def getBytesIO(self,src):
        if (self.isCustom == 0): #utf-32 emoji
            res : requests.Response = requests.get(f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{ord(src):x}.png")
            return BytesIO(res.content)
        else: #discord emoji
            src = src[src.rfind(":") + 1 : len(src) - 1]
            res : requests.Response = requests.get(f"https://cdn.discordapp.com/emojis/{src}.png")
            return BytesIO(res.content)
    def __str__(self):
        return f"Emoji Object [index:{self.index}, isCustom:{self.isCustom}, bytes:{self.bytes}]"
    def __repr__(self):
            return f"Emoji Object [index:{self.index}, isCustom:{self.isCustom}, bytes:{self.bytes}]"


def getSize(words : list[str], fontInfo : ImageFont.FreeTypeFont) -> tuple[float,float]:
    text = " ".join(words)
    (_,_,length,_) = fontInfo.getbbox(text) # returns (x,y, width, height)
    metrics = fontInfo.getmetrics()
    height = (metrics[0]+metrics[1])

    return (length, height)


def getRatio(lines : list[list[str]], fontInfo : ImageFont.FreeTypeFont) -> float:
    width = 0
    height = 0
    for line in lines:
        size = getSize(line, fontInfo)
        width = size[0] if size[0] > width else width
        height += size[1]
    return float(width)/float(height)

def divideWords(words : list[str], partitions : int, fontInfo : ImageFont.FreeTypeFont) -> list[list[str]]:
    averageLength = getSize(words, fontInfo)[0]/partitions
    
    output = [[]]
    currentLine = 0
    currentLineLength = 0


    for word in words:
        futureLineLength = getSize(output[currentLine] + [word], fontInfo)[0]
        if (futureLineLength < averageLength or currentLineLength + ((futureLineLength-currentLineLength)/2) < averageLength):
            currentLineLength = futureLineLength
            output[currentLine].append(word)
        else:
            if (currentLine == partitions):
                break
            currentLineLength = 0
            currentLine += 1
            output.append([word])
    return output

def getImage(inputtext, fontpath = "ARIAL_MONO.ttf", path_prefix=""):

    try:
        cleanedText =inputtext
        baseText = inputtext

        UNICODE_EMOJI_REGEX = '|'.join(map(re.escape, sorted(get_emoji_unicode_dict("en").values(), key=len, reverse=True)))
        ALL_EMOJI_REGEX = re.compile(f"({'<a?:[a-zA-Z0-9_~-]{2,32}:[0-9]{17,22}>'}|{UNICODE_EMOJI_REGEX})")
    

        _emojiList = []
        while search := ALL_EMOJI_REGEX.search(cleanedText):
            span = search.span()
            _emojiList.append(_emoji(search.group(), span[0] + len(_emojiList)))
            cleanedText = cleanedText[0:span[0]]+ "\0" +cleanedText[span[1]::]

        textImage:Image
        baseImage:Image


        baseImage = Image.open(f"{path_prefix}/base.png")
        fontpath = path_prefix + "/" + fontpath

        width = 350
        height = 200

        textImage = Image.new("RGBA",size=(width,height),color=(255,255,255,0))


        font = ImageFont.truetype(fontpath, size=32)

        cleanedText_split = cleanedText.split(" ")
        tarr = [cleanedText_split]
        
        targetRatio = width / (height/1.25)

        oldRatio = 10000
        currentRatio = 9999
        
        partitions = 1
        
        safetylimit = 0

        #print("Target: ",targetRatio)
        if (len(cleanedText_split) > 1):
            while True: 
                tarr = divideWords(cleanedText_split, partitions, font)
                if (currentRatio != 9999):
                    oldRatio = currentRatio
                currentRatio = getRatio(tarr, font)
                
                #print(f"{oldRatio}, {currentRatio}")
                #print(f"{math.fabs(targetRatio-oldRatio)} < {math.fabs(targetRatio - currentRatio)}")
                #print("-----")
                if math.fabs(targetRatio-oldRatio) <= math.fabs(targetRatio - currentRatio):
                    currentRatio = oldRatio
                    partitions-=1
                    tarr = divideWords(cleanedText_split, partitions, font)
                    break
                safetylimit +=1
                if (safetylimit > 1000):
                    raise RuntimeError("Looped Too Many Times during Ratio Process")
                partitions +=1



        ##COPYING PARTITION PATTERN
        tarr_with_emote = []
        baseText = baseText.split(" ")

        j = 0 
        for line in tarr:
            tarr_with_emote.append(baseText[j:j+len(line)])
            j += len(line)

        #print(f"Partitions: {partitions}")
        #print(f"Ratio: {currentRatio}")
        #print(f"tarr: {tarr}")
        
        longestIndex = 0
        longestLength = 0
        for i in range(0, len(tarr)):
            length = getSize(tarr[i],font)[0]
            if length > longestLength:
                longestIndex = i
                longestLength = length
        

        fontSize = 200

        
        while (True):     
            fontSize -=5
            font = ImageFont.truetype(fontpath, size=fontSize)
            longestSize = getSize(tarr[longestIndex],font)
            if (longestSize[0] < width and longestSize[1]*len(tarr) < height):
                fontSize +=5

                while (True):     
                    fontSize -= 1
                    font = ImageFont.truetype(fontpath, size=fontSize)
                    longestSize = getSize(tarr[longestIndex],font)
                    if (longestSize[0] < width and longestSize[1]*partitions < height):
                        font = ImageFont.truetype(fontpath, size=fontSize)
                        break
                break
        
        measuring_lines = [" ".join(line) for line in tarr] 
        writing_lines = [" ".join(line) for line in tarr_with_emote] 
        draw = ImageDraw.Draw(textImage)

        #draw.text((math.floor((width-longestSize[0])/2),math.floor((height/2)-(longestSize[1]*partitions/2))),"\n".join(measuring_lines), font=font, fill=(0,0,0),align="center", spacing=longestSize[1]*0.0)

        with (Pilmoji(textImage, draw=draw) as pmj):
            printingHeight = math.floor((height-(longestSize[1]*len(measuring_lines)))/2)
            for i,line in enumerate(measuring_lines):
                x_offset = getSize([line], font)[0]
                pmj.text((math.floor((width-x_offset)/2), math.floor(printingHeight)),writing_lines[i], font=font, fill=(0,0,0), align="center", spacing=longestSize[1]*0.0, emoji_scale_factor=1)
                printingHeight += (longestSize[1])

        textImage = textImage.rotate(10, expand=True)
        textImage = textImage.resize((350,200))
        baseImage.paste(textImage,(50,120), textImage)
        
        #baseImage.show()
        #output = 'data:image/jpeg;base64,' + PILtoBase64(baseImage)
        return PILtoBase64(baseImage)
    except:
        return getErrorPicture(path_prefix)


    
    
# if __name__ == "__main__":

    #main()
    # try:
    #     main()
    # except:
    #     PrintError()


