import cv2
import numpy as np
import pytesseract
import imutils
import re

##### From the given a word and a number find the dose information
# because of the OCR nature we have two list one number (is just the tessaract OCR system looking only for numbers)
# word (is tessaract OCR looking for numbers and letters)
def order_output(word,number):

    ### create a list from all words and numbers
    words=word.upper().split("\n")
    numbers=number.split("\n")
    #print(words)
    #print(numbers)


    output="error" # final output of the data
    agent="" # agent name used
    regex = r'[0-9]' # sort for numbers
    numberlist=[] #list of numbers
    wordlist=[] #list of words
    nprev="" #placeholder previous nuber found
    nextnu=False # next string is a number? 

    #### Go through the numbers for dose amount
    for n in numbers:
        if (re.match("_", n)!=None):#Blank found
            nprev=None
            continue
        if (re.match(regex, n)==None) or (len(n)<1):#no numbers found
            continue
        if nextnu==True:# string is a number
            numberlist.append(n+" " + nprev)#append it to the number list
            nextnu=False
        if ":" in n:# is it two number seprated by a :
            if n.rfind(":")<4:
                if nprev!=None:
                    numberlist.append(nprev+" " + n)
                else:
                    nextnu=True
        nprev=n
    
    numb2=[]
    pastele='' 

    ###### go through the list of words   
    for ele in words:
        if len(ele)<1:#is the word a blank ie. <1
            pastele=ele
            continue
        elif ele in pastele == True: # OCR will some times treat non-letter as letters they often are repeated
            pastele=ele
            continue 
        pastele=ele

        if re.findall("[0-9]",ele)!=[]:# does the element have a number 
            if re.findall("[a-zA-Z]",ele)!=[]: #does it have a letter
                non=1
            else: # the element maybe a number just not found
                numb2.append(ele)

        # dose thee element slightly match the desired values
        if "FENT" in ele or "TENT" in ele or "NTAN" in ele: # does the element match one of these then we assume 
            if agent != "fentaNYL 1000: ": # is the past agent being repeated
                agent="fentaNYL 1000: "
                wordlist.append(agent)#add to the agent list
                numb2.append("dose_here")#add the dose here
        elif "SODI" in ele or "SODJ" in ele or "SADI" in ele:
            if agent != "Sodium Cl 3%: ":
                agent="Sodium Cl 3%: "
                wordlist.append(agent)
                numb2.append("dose_here")

    #print(words)
    #print(wordlist)
    #print(numb2)
    #print(numberlist)  

    ### compare the list of words and number to create the dosing information
    if len(numberlist)==len(wordlist):# if they are the same then we have only one dose amount and agent
        output=""
        for i in range(len(numberlist)):
            output+=(wordlist[i]+" "+numberlist[i]+" ")
        return output
    elif numb2.count("dose_here")==len(wordlist):#if we have a miss match replace dose here with actual amount
        stto=0
        output=""
        for i in range(len(wordlist)):
            stto= numb2.index("dose_here",stto)+1
            if numb2[stto-3] != "dose_here":# is volume recored or not
                output+=(wordlist[i]+" "+numb2[stto-3]+" ")
            else:
                output+=(wordlist[i]+" "+numb2[stto-2]+" ")

        return output
    else:# there is a missmatch between dose agent and amount
        output= ["Error miss match"]
        return output


#### resize the image
def resize_img(img, percent):
    width = int(img.shape[1] * percent / 100)
    height = int(img.shape[0] * percent / 100)
    dim = (width, height)
    # resize image
    imgout = cv2.resize(img, dim, interpolation = cv2.INTER_CUBIC)
    return imgout

### used to find borders of key image
def find_border_components(contours, ary):
    key_contours=[]

    img_h=ary.shape[0]
    img_w=ary.shape[1]
    for i, c in enumerate(contours):
        x,y,w,h = cv2.boundingRect(c)
        if (h*w)>(0.3*img_h*img_w):
            key_contours.append((x,y,w,h))
    if len(key_contours)==0:
        return
    
    key_contours.sort(key=lambda x:(x[2]*x[3]))
    #print(key_contours)
    borders=(key_contours[0][0],key_contours[0][1],key_contours[0][0]+key_contours[0][2]+key_contours[0][0],key_contours[0][1]+key_contours[0][3])
    return borders 

#### main function takes an image and converts it to dosing information
def main(imgin):#input is a RGB array image
    img =cv2.cvtColor(imgin,cv2.COLOR_RGB2GRAY)# convert to greyscale

    #img=cv2.imread(imgin,0)



    edges = cv2.Canny(img,100,200) # find all the edges
    kernel = np.ones((2,2), dtype=np.uint8) # define a kernel size used to find the edges
    edges=cv2.dilate(edges, kernel, iterations=3) # find the images edges 
    #cv2.imwrite("B.jpg",edges)


    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) #use edges to create contours
    borders = find_border_components(contours, edges) # Note the main disply must be atleast 50% of display window
    if borders!=None:
        img=img[borders[1]:borders[3],borders[0]:borders[2]]

    ### resize the image based on borders
    img = resize_img(img,400)
    #cv2.imwrite("C.jpg",img)
    

    ### black and white the image to get solid letters and numbers
    if np.median(img) < 200:
        img = 255-img
    img=cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY, 101, 23)
    #cv2.imwrite("D.jpg",img)

    ## Again find the edges and then reshape
    edges = cv2.Canny(img,100,200)
    kernel = np.ones((3,3), dtype=np.uint8)
    edges=cv2.dilate(edges, kernel, iterations=6)
    #cv2.imwrite("E.jpg",edges)

    #### check for image rotation
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    height, width = img.shape
    h_len=height
    rect=((width/2,height/2),(height,width),0)
    for i, c in enumerate(contours):
        ((x,y), (h,w),rotation) = cv2.minAreaRect(c)
        if w>width*0.5:
            if h<h_len:
                rect=cv2.minAreaRect(c)
                h_len=h
    ((x,y), (h,w),rotation)=rect
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    img2=cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
    img2=cv2.drawContours(img2,[box],0,(0,0,255),10)
    #print(rotation)

    ####  rotate image
    if rotation!=None and rotation<-45:
        img = imutils.rotate(img, angle=90+rotation)
    #### trim after rotation
    if borders!=None:
        if round(x-w/2)<60:
            img=img[round(height*0.05):round(height*0.9),60:round(x+w/2)]
        else:
            img=img[round(height*0.05):round(height*0.9),round(x-w/2):round(x+w/2)]
    #cv2.imwrite("F.jpg",img)

    ## use tesseract to assess the image
    d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    # from the tesseract image found object extract them and put them into a vertical image
    n_boxes = len(d['level'])
    maxw=np.max(d['width'])
    full=np.ones((1,round(maxw/2)+10))*255
    for i in range(n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
        #cv2.rectangle(img4, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if w<round(maxw/2):
            if h<200:
                bas=np.ones((h+20,round(maxw/2)+10))*255
                #print(h,w,maxw,x+w-x,w+10-10,round(maxw/2))
                crop_img = img[y:(y+h), x:(x+w)]
                bas[0:h, 10:(w+10)]=crop_img
                full=np.vstack((full,bas))


    img=full
    #cv2.imwrite("G.jpg",img)    


    #### use OCR tesseract to find all words and numbers
    custom_config = r'-c tessedit_char_whitelist=0123456789.:_ --psm 11'
    final_num= (pytesseract.image_to_string(img, config=custom_config)) 

    custom_config = r'-c tessedit_char_blacklist=\"--psm 11'
    final_text= (pytesseract.image_to_string(img, config=custom_config)) 

    
    ###### sort the words and numbers from OCR
    worder= order_output(final_text,final_num)

    #print(worder)

    return worder

