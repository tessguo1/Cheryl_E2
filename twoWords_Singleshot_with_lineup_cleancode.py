#Alex Holcombe alex.holcombe@sydney.edu.au
#See the github repository for more information: https://github.com/alexholcombe/twoWords
from __future__ import print_function
from psychopy import monitors, visual, event, data, logging, core, sound, gui
import psychopy.info
import scipy
import numpy as np
from math import atan, log, ceil
import copy
import time, sys, os #, pylab
try:
    from noiseStaircaseHelpers import printStaircase, toStaircase, outOfStaircase, createNoise, plotDataAndPsychometricCurve
except ImportError:
    print('Could not import from noiseStaircaseHelpers.py (you need that file to be in the same directory)')
try:
    import stringResponse
except ImportError:
    print('Could not import stringResponse.py (you need that file to be in the same directory)')
try:
    import letterLineupResponse
except ImportError:
    print('Could not import letterLineupResponse.py (you need that file to be in the same directory)')

wordEccentricity=  0.9 #4
tasks=['T1']; task = tasks[0]
#THINGS THAT COULD PREVENT SUCCESS ON A STRANGE MACHINE
#same screen or external screen? Set scrn=0 if one screen. scrn=1 means display stimulus on second screen.
#widthPix, heightPix
quitFinder = False #if checkRefreshEtc, quitFinder becomes True
autopilot=False
demo=False #False
exportImages= False #quits after one trial
subject='Hubert' #user is prompted to enter true subject name
if autopilot: subject='auto'
if os.path.isdir('.'+os.sep+'dataRaw'):
    dataDir='dataRaw'
else:
    print('"dataRaw" directory does not exist, so saving data in present working directory')
    dataDir='.'
timeAndDateStr = time.strftime("%d%b%Y_%H-%M", time.localtime())

showRefreshMisses=True #flicker fixation at refresh rate, to visualize if frames missed
feedback=True 
autoLogging=False
if demo:
    refreshRate = 60.;  #100

numWordsInStream = 1

# reads word in from external source
wordList1 = open("wordLists/Davis&BowersWL.txt")
wordList2 = open("wordLists/Davis&BowersWL2.txt")

wordList1 = [x.rstrip() for x in wordList1.readlines()]
wordList2 = [x.rstrip() for x in wordList2.readlines()]


lettersUnparsed = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z".upper()


for i in range(len(wordList1)):
    wordList1[i] = wordList1[i].replace(" ", "") #delete spaces

for i in range(len(wordList2)):
    wordList2[i] = wordList2[i].replace(" ", "") #delete spaces

bgColor = [-.7,-.7,-.7] # [-1,-1,-1]
cueColor = [-.7,-.7,-.7] #originally [1.,1.,1.]
letterColor = [1.,1.,1.]
cueRadius = 7 #6 deg in Goodbourn & Holcombe
widthPix= 1600 #monitor width in pixels of Agosta  [1280]
heightPix= 900 #800 #monitor height in pixels [800]
monitorwidth = 60 #38.7 #monitor width in cm [was 38.7]
scrn=1 #0 to use main screen, 1 to use external screen connected to computer
fullscr=True #True to use fullscreen, False to not. Timing probably won't be quite right if fullscreen = False
allowGUI = False
if demo: monitorwidth = 23#18.0
if exportImages:
    widthPix = 600; heightPix = 600
    monitorwidth = 13.0
    fullscr=False; scrn=1
    framesSaved=0
if demo:    
    scrn=1; fullscr=False
    widthPix = 800; heightPix = 600
    monitorname='testMonitor'
    allowGUI = True
viewdist = 57 #50. #cm
pixelperdegree = widthPix/ (atan(monitorwidth/viewdist) /np.pi*180)
print('pixelperdegree=',pixelperdegree)
    
# create a dialog from dictionary 
infoFirst = { 'Do staircase (only)': False, 'Check refresh etc':False, 'Fullscreen (timing errors if not)': False, 'Screen refresh rate': 60 }
OK = gui.DlgFromDict(dictionary=infoFirst, 
    title='AB experiment OR staircase to find thresh noise level for T1 performance criterion', 
    order=['Do staircase (only)', 'Check refresh etc', 'Fullscreen (timing errors if not)'], 
    tip={'Check refresh etc': 'To confirm refresh rate and that can keep up, at least when drawing a grating'},
    #fixed=['Check refresh etc'])#this attribute can't be changed by the user
    )
if not OK.OK:
    print('User cancelled from dialog box'); core.quit()
doStaircase = infoFirst['Do staircase (only)']
checkRefreshEtc = infoFirst['Check refresh etc']
fullscr = infoFirst['Fullscreen (timing errors if not)']
refreshRate = infoFirst['Screen refresh rate']
if checkRefreshEtc:
    quitFinder = True 
if quitFinder:
    import os
    applescript="\'tell application \"Finder\" to quit\'"
    shellCmd = 'osascript -e '+applescript
    os.system(shellCmd)

#set location of stimuli
#letter size 2.5 deg
SOAms = 150 #Battelli, Agosta, Goodbourn, Holcombe mostly using 133   #KR: was 233
#Minimum SOAms should be 84  because any shorter, I can't always notice the second ring when lag1.   71 in Martini E2 and E1b (actually he used 66.6 but that's because he had a crazy refresh rate of 90 Hz)
letterDurMs =   140
#Was 17. 23.6  in Martini E2 and E1b (actually he used 22.2 but that's because he had a crazy refresh rate of 90 Hz = 0
ISIms = SOAms - letterDurMs
letterDurFrames = int( np.floor(letterDurMs / (1000./refreshRate)) )
cueDurFrames = letterDurFrames
ISIframes = int( np.floor(ISIms / (1000./refreshRate)) )
#have set ISIframes and letterDurFrames to integer that corresponds as close as possible to originally intended ms
rateInfo = 'total SOA=' + str(round(  (ISIframes + letterDurFrames)*1000./refreshRate, 2)) + ' or ' + str(ISIframes + letterDurFrames) + ' frames, comprising\n'
rateInfo+=  'ISIframes ='+str(ISIframes)+' or '+str(ISIframes*(1000./refreshRate))+' ms and letterDurFrames ='+str(letterDurFrames)+' or '+str(round( letterDurFrames*(1000./refreshRate), 2))+'ms'
logging.info(rateInfo); print(rateInfo)

trialDurFrames = int( numWordsInStream*(ISIframes+letterDurFrames) ) #trial duration in frames

monitorname = 'testmonitor'
waitBlank = False
mon = monitors.Monitor(monitorname,width=monitorwidth, distance=viewdist)#relying on  monitorwidth cm (39 for Mitsubishi to do deg calculations) and gamma info in calibratn
mon.setSizePix( (widthPix,heightPix) )
units='deg' #'cm'

def openMyStimWindow(): #make it a function because have to do it several times, want to be sure is identical each time
    myWin = visual.Window(monitor=mon,size=(widthPix,heightPix),allowGUI=allowGUI,units=units,color=bgColor,colorSpace='rgb',fullscr=fullscr,screen=scrn,waitBlanking=waitBlank) #Holcombe lab monitor
    return myWin
myWin = openMyStimWindow()
refreshMsg2 = ''
if not checkRefreshEtc:
    refreshMsg1 = 'REFRESH RATE WAS NOT CHECKED'
    refreshRateWrong = False
else: #checkRefreshEtc
    runInfo = psychopy.info.RunTimeInfo(
            # if you specify author and version here, it overrides the automatic detection of __author__ and __version__ in your script
            #author='<your name goes here, plus whatever you like, e.g., your lab or contact info>',
            #version="<your experiment version info>",
            win=myWin,    ## a psychopy.visual.Window() instance; None = default temp window used; False = no win, no win.flips()
            refreshTest='grating', ## None, True, or 'grating' (eye-candy to avoid a blank screen)
            verbose=True, ## True means report on everything 
            userProcsDetailed=True  ## if verbose and userProcsDetailed, return (command, process-ID) of the user's processes
            )
    #print(runInfo)
    logging.info(runInfo)
    print('Finished runInfo- which assesses the refresh and processes of this computer') 
    #check screen refresh is what assuming it is ##############################################
    Hzs=list()
    myWin.flip(); myWin.flip();myWin.flip();myWin.flip();
    myWin.setRecordFrameIntervals(True) #otherwise myWin.fps won't work
    print('About to measure frame flips') 
    for i in range(50):
        myWin.flip()
        Hzs.append( myWin.fps() )  #varies wildly on successive runs!
    myWin.setRecordFrameIntervals(False)
    # end testing of screen refresh########################################################
    Hzs = np.array( Hzs );     Hz= np.median(Hzs)
    msPerFrame= 1000./Hz
    refreshMsg1= 'Frames per second ~='+ str( np.round(Hz,1) )
    refreshRateTolerancePct = 3
    pctOff = abs( (np.median(Hzs)-refreshRate) / refreshRate)
    refreshRateWrong =  pctOff > (refreshRateTolerancePct/100.)
    if refreshRateWrong:
        refreshMsg1 += ' BUT'
        refreshMsg1 += ' program assumes ' + str(refreshRate)
        refreshMsg2 =  'which is off by more than' + str(round(refreshRateTolerancePct,0)) + '%!!'
    else:
        refreshMsg1 += ', which is close enough to desired val of ' + str( round(refreshRate,1) )
    myWinRes = myWin.size
    myWin.allowGUI =True

### 

myWin.close() #have to close window to show dialog box

defaultNoiseLevel = 0 #to use if no staircase, can be set by user
trialsPerCondition = 20 #default value
dlgLabelsOrdered = list()
if doStaircase:
    myDlg = gui.Dlg(title="Staircase to find appropriate noisePercent", pos=(200,400))
else: 
    myDlg = gui.Dlg(title="RSVP experiment", pos=(200,400))
if not autopilot:
    myDlg.addField('Subject name (default="Hubert"):', 'Hubert', tip='or subject code')
    dlgLabelsOrdered.append('subject')
if doStaircase:
    prefaceStaircaseTrialsN = 5
    easyTrialsCondText = 'Num preassigned noise trials to preface staircase with (default=' + str(prefaceStaircaseTrialsN) + '):'
    myDlg.addField(easyTrialsCondText, tip=str(prefaceStaircaseTrialsN))
    dlgLabelsOrdered.append('easyTrials')
    myDlg.addField('Staircase trials (default=' + str(staircaseTrials) + '):', tip="Staircase will run until this number is reached or it thinks it has precise estimate of threshold")
    dlgLabelsOrdered.append('staircaseTrials')
    pctCompletedBreak = 101
else:
    myDlg.addField('\tPercent noise dots=',  defaultNoiseLevel, tip=str(defaultNoiseLevel))
    dlgLabelsOrdered.append('defaultNoiseLevel')
    myDlg.addField('Trials per condition (default=' + str(trialsPerCondition) + '):', trialsPerCondition, tip=str(trialsPerCondition))
    dlgLabelsOrdered.append('trialsPerCondition')
    pctCompletedBreak = 50
    
myDlg.addText(refreshMsg1, color='Black')
if refreshRateWrong:
    myDlg.addText(refreshMsg2, color='Red')
if refreshRateWrong:
    logging.error(refreshMsg1+refreshMsg2)
else: logging.info(refreshMsg1+refreshMsg2)

if checkRefreshEtc and (not demo) and (myWinRes != [widthPix,heightPix]).any():
    msgWrongResolution = 'Screen apparently NOT the desired resolution of '+ str(widthPix)+'x'+str(heightPix)+ ' pixels!!'
    myDlg.addText(msgWrongResolution, color='Red')
    logging.error(msgWrongResolution)
    print(msgWrongResolution)
myDlg.addText('Note: to abort press ESC at a trials response screen', color='DimGrey') #color names stopped working along the way, for unknown reason
myDlg.show()

if myDlg.OK: #unpack information from dialogue box
   thisInfo = myDlg.data #this will be a list of data returned from each field added in order
   if not autopilot:
       name=thisInfo[dlgLabelsOrdered.index('subject')]
       if len(name) > 0: #if entered something
         subject = name #change subject default name to what user entered
   if doStaircase:
       if len(thisInfo[dlgLabelsOrdered.index('staircaseTrials')]) >0:
           staircaseTrials = int( thisInfo[ dlgLabelsOrdered.index('staircaseTrials') ] ) #convert string to integer
           print('staircaseTrials entered by user=',staircaseTrials)
           logging.info('staircaseTrials entered by user=',staircaseTrials)
       if len(thisInfo[dlgLabelsOrdered.index('easyTrials')]) >0:
           prefaceStaircaseTrialsN = int( thisInfo[ dlgLabelsOrdered.index('easyTrials') ] ) #convert string to integer
           print('prefaceStaircaseTrialsN entered by user=',thisInfo[dlgLabelsOrdered.index('easyTrials')])
           logging.info('prefaceStaircaseTrialsN entered by user=',prefaceStaircaseTrialsN)
   else: #not doing staircase
       trialsPerCondition = int( thisInfo[ dlgLabelsOrdered.index('trialsPerCondition') ] ) #convert string to integer
       print('trialsPerCondition=',trialsPerCondition)
       logging.info('trialsPerCondition =',trialsPerCondition)
       defaultNoiseLevel = int (thisInfo[ dlgLabelsOrdered.index('defaultNoiseLevel') ])
else: 
   print('User cancelled from dialog box.')
   logging.flush()
   core.quit()
if not demo: 
    allowGUI = False

myWin = openMyStimWindow()
#set up output data file, log file,  copy of program code, and logging
infix = ''
if doStaircase:
    infix = 'staircase_'
fileName = os.path.join(dataDir, subject + '_' + infix+ timeAndDateStr)
if not demo and not exportImages:
    dataFile = open(fileName+'.txt', 'w')
    saveCodeCmd = 'cp \'' + sys.argv[0] + '\' '+ fileName + '.py'
    os.system(saveCodeCmd)  #save a copy of the code as it was when that subject was run
    logFname = fileName+'.log'
    ppLogF = logging.LogFile(logFname, 
        filemode='w',#if you set this to 'a' it will append instead of overwriting
        level=logging.INFO)#errors, data and warnings will be sent to this logfile
if demo or exportImages: 
  dataFile = sys.stdout; logF = sys.stdout
  logging.console.setLevel(logging.ERROR)  #only show this level  messages and higher
logging.console.setLevel(logging.ERROR) #DEBUG means set  console to receive nearly all messges, INFO next level, EXP, DATA, WARNING and ERROR 

if fullscr and not demo and not exportImages:
    runInfo = psychopy.info.RunTimeInfo(
        # if you specify author and version here, it overrides the automatic detection of __author__ and __version__ in your script
        #author='<your name goes here, plus whatever you like, e.g., your lab or contact info>',
        #version="<your experiment version info>",
        win=myWin,    ## a psychopy.visual.Window() instance; None = default temp window used; False = no win, no win.flips()
        refreshTest='grating', ## None, True, or 'grating' (eye-candy to avoid a blank screen)
        verbose=False, ## True means report on everything 
        userProcsDetailed=True,  ## if verbose and userProcsDetailed, return (command, process-ID) of the user's processes
        #randomSeed='set:42', ## a way to record, and optionally set, a random seed of type str for making reproducible random sequences
            ## None -> default 
            ## 'time' will use experimentRuntime.epoch as the value for the seed, different value each time the script is run
            ##'set:time' --> seed value is set to experimentRuntime.epoch, and initialized: random.seed(info['randomSeed'])
            ##'set:42' --> set & initialize to str('42'), and will give the same sequence of random.random() for all runs of the script
        )
    logging.info(runInfo)
logging.flush()

textStimuliStream1 = list()
textStimuliStream2 = list() #used for second, simultaneous RSVP stream
def calcAndPredrawStimuli(wordList1,wordList2):
    global textStimuliStream1, textStimuliStream2
    del textStimuliStream1[:]
    del textStimuliStream2[:]
    if len(wordList1) < numWordsInStream:
        print('Error! Your word list must have at least ',numWordsInStream,'strings')
    for i in range(0,len(wordList1)): #draw the words that will be used on this trial, the first numWordsInStream of the shuffled list
       word1 = wordList1[ i ]#     #[ idxsIntoWordList[i] ]
       word2 = wordList2[ i ]
       textStimulusStream1 = visual.TextStim(myWin,text=word1,height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging)
       textStimulusStream2 = visual.TextStim(myWin,text=word2,height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging)
       textStimulusStream1.setPos([-wordEccentricity,0]) #left
       textStimuliStream1.append(textStimulusStream1)
       textStimulusStream2.setPos([wordEccentricity,0]) #right
       textStimuliStream2.append(textStimulusStream2)
        
#create click sound for keyboard
try:
    click=sound.Sound('406__tictacshutup__click-1-d.wav')
except: #in case file missing, create inferiro click manually
    logging.warn('Could not load the desired click sound file, instead using manually created inferior click')
    click=sound.Sound('D',octave=4, sampleRate=22050, secs=0.015, bits=8)

if showRefreshMisses:
    fixSizePix = 32 #2.6  #make fixation bigger so flicker more conspicuous
else: fixSizePix = 32
fixColor = [1,1,1]
if exportImages: fixColor= [0,0,0]
fixatnNoiseTexture = np.round( np.random.rand(fixSizePix/4,fixSizePix/4) ,0 )   *2.0-1 #Can counterphase flicker  noise texture to create salient flicker if you break fixation

fixation= visual.PatchStim(myWin, tex=fixatnNoiseTexture, size=(fixSizePix,fixSizePix), units='pix', mask='circle', interpolate=False, autoLog=False)
fixationBlank= visual.PatchStim(myWin, tex= -1*fixatnNoiseTexture, size=(fixSizePix,fixSizePix), units='pix', mask='circle', interpolate=False, autoLog=False) #reverse contrast
fixationPoint= visual.PatchStim(myWin,tex='none',colorSpace='rgb',color=(1,1,1),size=10,units='pix',autoLog=autoLogging)

respPromptStim = visual.TextStim(myWin,pos=(0, -.9),colorSpace='rgb',color=(1,1,1),alignHoriz='center', alignVert='center',height=.05,units='norm',autoLog=autoLogging)
acceptTextStim = visual.TextStim(myWin,pos=(0, -.8),colorSpace='rgb',color=(1,1,1),alignHoriz='center', alignVert='center',height=.05,units='norm',autoLog=autoLogging)
acceptTextStim.setText('Hit ENTER to accept. Backspace to edit')
respStim = visual.TextStim(myWin,pos=(0,0),colorSpace='rgb',color=(1,1,0),alignHoriz='center', alignVert='center',height=1,units='deg',autoLog=autoLogging)
clickSound, badKeySound = stringResponse.setupSoundsForResponse()
requireAcceptance = False
nextText = visual.TextStim(myWin,pos=(0, .1),colorSpace='rgb',color = (1,1,1),alignHoriz='center', alignVert='center',height=.1,units='norm',autoLog=autoLogging)
NextRemindCountText = visual.TextStim(myWin,pos=(0,.2),colorSpace='rgb',color= (1,1,1),alignHoriz='center', alignVert='center',height=.1,units='norm',autoLog=autoLogging)
screenshot= False; screenshotDone = False
stimList = []
#SETTING THE CONDITIONS
cuePositions =  np.array([0]) # [4,10,16,22] used in Martini E2, group 2
#Implement the fully factorial part of the design by creating every combination of the following conditions
for cuePos in cuePositions:
   for rightResponseFirst in [False,True]:
      for bothWordsFlipped in [False]:
        for probe in ['both']:
            for indication in [True]:
                stimList.append( {'cuePos':cuePos, 'rightResponseFirst':rightResponseFirst, 'leftStreamFlip':bothWordsFlipped, 'rightStreamFlip':bothWordsFlipped, 'probe':probe, 'indication':indication} )

trials = data.TrialHandler(stimList,trialsPerCondition) #constant stimuli method
trialsForPossibleStaircase = data.TrialHandler(stimList,trialsPerCondition) #independent randomization, just to create random trials for staircase phase
numRightWrongEachCuepos = np.zeros([ len(cuePositions), 1 ]); #summary results to print out at end

logging.info( 'numtrials=' + str(trials.nTotal) + ' and each trialDurFrames='+str(trialDurFrames)+' or '+str(trialDurFrames*(1000./refreshRate))+ \
               ' ms' + '  task=' + task)

def numberToLetter(number): #0 = A, 25 = Z
    #if it's not really a letter, return @
    if number < 0 or number > 25:
        return ('@')
    else: #it's probably a letter
        try:
            return chr( ord('A')+number )
        except:
            return('@')

def letterToNumber(letter): #A = 0, Z = 25
    #if it's not really a letter, return -999
    #HOW CAN I GENERICALLY TEST FOR LENGTH. EVEN IN CASE OF A NUMBER THAT' SNOT PART OF AN ARRAY?
    try:
        #if len(letter) > 1:
        #    return (-999)
        if letter < 'A' or letter > 'Z':
            return (-999)
        else: #it's a letter
            return ord(letter)-ord('A')
    except:
        return (-999)

def wordToIdx(word,wordList):
    #if it's not in the list of stimuli, return -999
    try:
        #http://stackoverflow.com/questions/7102050/how-can-i-get-a-python-generator-to-return-none-rather-than-stopiteration
        firstMatchIdx = next((i for i, val in enumerate(wordList) if val.upper()==word), None) #return i (index) unless no matches, in which case return None
        #print('Looked for ',word,' in ',wordList,'\nfirstMatchIdx =',firstMatchIdx)
        return firstMatchIdx
    except:
        print('Unexpected error in wordToIdx with word=',word)
        return (None)
        
maxNumRespsWanted = 2

#print header for data file
print('experimentPhase\ttrialnum\tsubject\ttask\t',file=dataFile,end='')
print('noisePercent\tleftStreamFlip\trightStreamFlip\trightResponseFirst\tprobe\t',end='',file=dataFile)

for i in range(maxNumRespsWanted):
#   dataFile.write('cuePos'+str(i)+'\t')   #have to use write to avoid ' ' between successive text, at least until Python 3
   dataFile.write('answer'+str(i)+'\t')
   dataFile.write('response'+str(i)+'\t')
   dataFile.write('correct'+str(i)+'\t')
   

#   dataFile.write('responsePosRelative'+str(i)+'\t')
print('timingBlips',file=dataFile)
#end of header
    
def  oneFrameOfStim( n,cue,seq1,seq2,cueDurFrames,letterDurFrames,ISIframes,thisTrial,textStimuliStream1,textStimuliStream2,
                                       noise,proportnNoise,allFieldCoords,numNoiseDots): 
#defining a function to draw each frame of stim.
#seq1 is an array of indices corresponding to the appropriate pre-drawn stimulus, contained in textStimuli

  
  SOAframes = letterDurFrames+ISIframes
  cueFrames = thisTrial['cuePos']*SOAframes  #cuesPos is global variable
  stimN = int( np.floor(n/SOAframes) )
  frameOfThisLetter = n % SOAframes #earvery SOAframes, new letter
  showLetter = frameOfThisLetter < letterDurFrames #if true, it's not time for the blank ISI.  it's still time to draw the letter
  
  #print 'n=',n,' SOAframes=',SOAframes, ' letterDurFrames=', letterDurFrames, ' (n % SOAframes) =', (n % SOAframes)  #DEBUGOFF
  thisStimIdx = seq1[stimN] #which letter, from A to Z (1 to 26), should be shown?
  if seq2 is not None:
    thisStim2Idx = seq2[stimN]
  #so that any timing problems occur just as often for every frame, always draw the letter and the cue, but simply draw it in the bgColor when it's not meant to be on
  cue.setLineColor( bgColor )
  if type(cueFrames) not in [tuple,list,np.ndarray]: #scalar. But need collection to do loop based on it
    cueFrames = list([cueFrames])
  for cueFrame in cueFrames: #cheTck whether it's time for any cue
      if n>=cueFrame and n<cueFrame+cueDurFrames:
         cue.setLineColor( cueColor )

  if showLetter:
    textStimuliStream1[thisStimIdx].setColor( letterColor )
    textStimuliStream2[thisStim2Idx].setColor( letterColor )
  else: 
    textStimuliStream1[thisStimIdx].setColor( bgColor )
    textStimuliStream2[thisStim2Idx].setColor( bgColor )
  textStimuliStream1[thisStimIdx].flipHoriz = thisTrial['leftStreamFlip']
  textStimuliStream2[thisStim2Idx].flipHoriz = thisTrial['rightStreamFlip']
  textStimuliStream1[thisStimIdx].draw()
  textStimuliStream2[thisStim2Idx].draw()
  cue.draw()
  refreshNoise = False #Not recommended because takes longer than a frame, even to shuffle apparently. Or may be setXYs step
  if proportnNoise>0 and refreshNoise: 
    if frameOfThisLetter ==0: 
        np.random.shuffle(allFieldCoords) 
        dotCoords = allFieldCoords[0:numNoiseDots]
        noise.setXYs(dotCoords)
  if proportnNoise>0:
    noise.draw()
  return True 
  


# #######End of function definition that displays the stimuli!!!! #####################################
#############################################################################################################################
  thisProbe = thisTrial['probe']
  #if thisProbe=='both':
  #  numRespsWanted = 1
  #else: numRespsWanted = 0
  
cue = visual.Circle(myWin, 
                 radius=cueRadius,#Martini used circles with diameter of 12 deg
                 lineColorSpace = 'rgb',
                 lineColor=bgColor,
                 lineWidth=4.0, #in pixels. Was thinner (2 pixels) in letter AB experiments
                 units = 'deg',
                 fillColorSpace = 'rgb',
                 fillColor=None, #beware, with convex shapes fill colors don't work
                 pos= [0,0], #the anchor (rotation and vertices are position with respect to this)
                 interpolate=True,
                 autoLog=False)#this stim changes too much for autologging to be useful
                 
ltrHeight =  0.7 #2.5 #Martini letters were 2.5deg high
#All noise dot coordinates ultimately in pixels, so can specify each dot is one pixel 
noiseFieldWidthDeg=ltrHeight *1.0
noiseFieldWidthPix = int( round( noiseFieldWidthDeg*pixelperdegree ) )

def timingCheckAndLog(ts,trialN):
    #check for timing problems and log them
    #ts is a list of the times of the clock after each frame
    interframeIntervs = np.diff(ts)*1000
    #print '   interframe intervs were ',around(interframeIntervs,1) #DEBUGOFF
    frameTimeTolerance=.3 #proportion longer than refreshRate that will not count as a miss
    longFrameLimit = np.round(1000/refreshRate*(1.0+frameTimeTolerance),2)
    idxsInterframeLong = np.where( interframeIntervs > longFrameLimit ) [0] #frames that exceeded 150% of expected duration
    numCasesInterframeLong = len( idxsInterframeLong )
    if numCasesInterframeLong >0 and (not demo):
       longFramesStr =  'ERROR,'+str(numCasesInterframeLong)+' frames were longer than '+str(longFrameLimit)+' ms'
       if demo: 
         longFramesStr += 'not printing them all because in demo mode'
       else:
           longFramesStr += ' apparently screen refreshes skipped, interframe durs were:'+\
                    str( np.around(  interframeIntervs[idxsInterframeLong] ,1  ) )+ ' and was these frames: '+ str(idxsInterframeLong)
       if longFramesStr != None:
                logging.error( 'trialnum='+str(trialN)+' '+longFramesStr )
                if not demo:
                    flankingAlso=list()
                    for idx in idxsInterframeLong: #also print timing of one before and one after long frame
                        if idx-1>=0:
                            flankingAlso.append(idx-1)
                        else: flankingAlso.append(np.NaN)
                        flankingAlso.append(idx)
                        if idx+1<len(interframeIntervs):  flankingAlso.append(idx+1)
                        else: flankingAlso.append(np.NaN)
                    flankingAlso = np.array(flankingAlso)
                    flankingAlso = flankingAlso[np.negative(np.isnan(flankingAlso))]  #remove nan values
                    flankingAlso = flankingAlso.astype(np.integer) #cast as integers, so can use as subscripts
                    logging.info( 'flankers also='+str( np.around( interframeIntervs[flankingAlso], 1) )  ) #because this is not an essential error message, as previous one already indicates error
                      #As INFO, at least it won't fill up the console when console set to WARNING or higher
    return numCasesInterframeLong
    #end timing check
    
trialClock = core.Clock()
numTrialsCorrect = 0; 
numTrialsApproxCorrect = 0;
numTrialsEachCorrect= np.zeros( maxNumRespsWanted )
numTrialsEachApproxCorrect= np.zeros( maxNumRespsWanted )
debugClock = core.Clock()

def do_RSVP_stim(thisTrial, seq1, seq2, proportnNoise,trialN,thisProbe):
    #relies on global variables:
    #   textStimuli, logging, bgColor
    #  thisTrial should have 'cuePos'
    global framesSaved #because change this variable. Can only change a global variable if you declare it
    global debugClock
    cuesPos = [] #will contain the positions in the stream of all the cues (targets)

    cuesPos.append(thisTrial['cuePos'])
    cuesPos = np.array(cuesPos)
    noise = None; allFieldCoords=None; numNoiseDots=0
    if proportnNoise > 0: #gtenerating noise is time-consuming, so only do it once per trial. Then shuffle noise coordinates for each letter
        (noise,allFieldCoords,numNoiseDots) = createNoise(proportnNoise,myWin,noiseFieldWidthPix, bgColor)

    preDrawStimToGreasePipeline = list() #I don't know why this works, but without drawing it I have consistent timing blip first time that draw ringInnerR for phantom contours
    cue.setLineColor(bgColor)
    preDrawStimToGreasePipeline.extend([cue])
    for stim in preDrawStimToGreasePipeline:
        stim.draw()
    myWin.flip(); myWin.flip()
    #end preparation of stimuli
    
    core.wait(.1)
    trialClock.reset()
    indicatorPeriodMin = 0.3 #was 0.3
    indicatorPeriodFrames = int(indicatorPeriodMin*refreshRate)
    fixatnPeriodMin = 0.1
    fixatnPeriodFrames = int(   (np.random.rand(1)/2.+fixatnPeriodMin)   *refreshRate)  #random interval between 800ms and 1.3s
    ts = list(); #to store time of each drawing, to check whether skipped frames


    for i in range(fixatnPeriodFrames+20):  #prestim fixation interval
        #if i%4>=2 or demo or exportImages: #flicker fixation on and off at framerate to see when skip frame
        #      fixation.draw()
        #else: fixationBlank.draw()
        fixationPoint.draw()
        myWin.flip()  #end fixation interval
    #myWin.setRecordFrameIntervals(True);  #can't get it to stop detecting superlong frames
    t0 = trialClock.getTime()

    midDelay = 0.5 #0.5
    
    midDelayFrames = int(midDelay *refreshRate)
    #insert a pause to allow the window and python all to finish initialising (avoid initial frame drops)
    for i in range(midDelayFrames):
         myWin.flip()
    
    
    
    if thisTrial['indication']:
        #if thisProbe=='both':
            for i in range(indicatorPeriodFrames+20):
                indicator1 = visual.TextStim(myWin, text = u"####",pos=(wordEccentricity, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging )
                indicator2 = visual.TextStim(myWin, text = u"####",pos=(-wordEccentricity, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging)


    #indicator = visual.TextStim(myWin, text = thisProbe, pos=(0, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging )
                indicator1.draw()
                indicator2.draw()


                myWin.flip()

    else:
          for i in range(indicatorPeriodFrames+20):
                indicator3 = visual.TextStim(myWin, text = u"       ",pos=(0, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging )
                indicator3.draw()
                myWin.flip()

    midDelay2 = 0.0 #0.5
    
    midDelay2Frames = int(midDelay2 *refreshRate)
    #insert a pause to allow the window and python all to finish initialising (avoid initial frame drops)
    for i in range(midDelay2Frames):
         myWin.flip()
    
    for n in range(trialDurFrames): #this is the loop for this trial's stimulus!
            worked = oneFrameOfStim( n,cue,seq1,seq2,cueDurFrames,letterDurFrames,ISIframes,thisTrial,textStimuliStream1,textStimuliStream2,
                                                         noise,proportnNoise,allFieldCoords,numNoiseDots ) #draw letter and possibly cue and noise on top
            fixationPoint.draw()
            if exportImages:
                myWin.getMovieFrame(buffer='back') #for later saving
                framesSaved +=1
            myWin.flip()
            
            t=trialClock.getTime()-t0;  ts.append(t);
            
        # adding a noise mask
    thisProbe = thisTrial['probe']
    
    if thisProbe == 'long':
        noiseMaskMin = 0.2 #0.20
    else: noiseMaskMin = 0.2# .20
        
    noiseMaskFrames = int(noiseMaskMin *refreshRate)

    noiseTexture = scipy.random.rand(128,128)*2.0-1

    myPatch1 = visual.GratingStim(myWin, tex=noiseTexture, pos=(1, 0),        
             size=(1.5,1), units='deg',
             interpolate=False,
             autoLog=False)#this stim changes too much for autologging to be useful
    
    myPatch2 = visual.GratingStim(myWin, tex=noiseTexture, pos=(-1, 0),        
             size=(1.5,1), units='deg',
             interpolate=False,
             autoLog=False)
    myPatch1.phase += (1 / 128.0, 0.5 / 128.0)  # increment by (1, 0.5) pixels per frame
    myPatch2.phase += (1 / 128.0, 0.5 / 128.0)  # increment by (1, 0.5) pixels per frame
    
    #noiseMaskFrames = int(noiseMaskMin *refreshRate)
    #myPatch1 = visual.TextStim(myWin, text = u"####",pos=(wordEccentricity, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging )
    #myPatch2 = visual.TextStim(myWin, text = u"####",pos=(-wordEccentricity, 0),height=ltrHeight,colorSpace='rgb',color=letterColor,alignHoriz='center',alignVert='center',units='deg',autoLog=autoLogging)
    for i in range(noiseMaskFrames):
         myPatch1.draw()
         myPatch2.draw()
         myWin.flip()
    #myWin.flip() #Need this
    debugClock.reset()
    if thisProbe == 'long':
        probeDelay = 1.5
    else: probeDelay = 0.0
    
    probeDelayFrames = int(probeDelay *refreshRate)
    #insert a pause to allow the window and python all to finish initialising (avoid initial frame drops)
    for i in range(probeDelayFrames):
         myWin.flip()
           
    #end of big stimulus loop
    myWin.setRecordFrameIntervals(False);
    
    if task=='T1':
        respPromptStim.setText('What was the underlined word?',log=False)   
    else: respPromptStim.setText('Error: unexpected task',log=False)
    
    postCueNumBlobsAway=-999 #doesn't apply to non-tracking and click tracking task
    
    correctAnswerIdxsStream1 = np.array( seq1[cuesPos] )
    correctAnswerIdxsStream2 = np.array( seq2[cuesPos] )
    #print('correctAnswerIdxsStream1=',correctAnswerIdxsStream1, 'wordList[correctAnswerIdxsStream1[0]]=',wordList[correctAnswerIdxsStream1[0]])
    return cuesPos,correctAnswerIdxsStream1,correctAnswerIdxsStream2,ts

def handleAndScoreResponse(passThisTrial,response,responseAutopilot,task,cuePos,correctAnswerIdx,wordList):
    #Handle response, calculate whether correct, ########################################
    #responses are actual characters
    #correctAnswer is index into stimSequence
    #autopilot is global variable
    if autopilot or passThisTrial:
        response = responseAutopilot
    correct = 0
    #approxCorrect = 0
    #posOfResponse = -999
    #responsePosRelative = -999
    idx = correctAnswerIdx
    print("thisidxs=",idx)
    print("thiswordlist=",wordList)
    correctAnswer = wordList.upper()
    responseString= ''.join(['%s' % char for char in response])
    responseString= responseString.upper()
    print('correctAnswer=',correctAnswer ,' responseString=',responseString)
    if correctAnswer == responseString:
        correct = 1
    print('correct=',correct)
    
    #responseWordIdx = wordToIdx(responseString,wordList)
    
    #if responseWordIdx is None: #response is not in the wordList
     #   posOfResponse = -999
      #  logging.warn('Response was not present in the stimulus stream')
    #else:
     #   posOfResponse= np.where( responseWordIdx==stimSequence )
      #  posOfResponse= posOfResponse[0] #list with two entries, want first which will be array of places where the response was found in the sequence
       # if len(posOfResponse) > 1:
        #    logging.error('Expected response to have occurred in only one position in stream')
       # posOfResponse = posOfResponse[0] #first element of list (should be only one element long 
       # responsePosRelative = posOfResponse - cuePos
       # approxCorrect = abs(responsePosRelative)<= 3 #Vul efficacy measure of getting it right to within plus/minus
    #print('wordToIdx(',responseString,',',wordList,')=',responseWordIdx,' stimSequence=',stimSequence,'\nposOfResponse = ',posOfResponse) #debugON
    #print response stuff to dataFile
    #header was answerPos0, answer0, response0, correct0, responsePosRelative0
#    print(cuePos,'\t', end='', file=dataFile)
    print(correctAnswer, '\t', end='', file=dataFile) #answer0
    print(responseString, '\t', end='', file=dataFile) #response0
    print(correct, '\t', end='',file=dataFile) 
    #print(probe, '\t', end='',file=dataFile)#correct0
   # print(responsePosRelative, '\t', end='',file=dataFile) #responsePosRelative0

    return correct
    #end handleAndScoreResponses
    staircase1.addResponse(correct)
def play_high_tone_correct_low_incorrect(correct, passThisTrial=False):
    highA = sound.Sound('G',octave=5, sampleRate=6000, secs=.3, bits=8)
    low = sound.Sound('F',octave=3, sampleRate=6000, secs=.3, bits=8)
    highA.setVolume(0.9)
    low.setVolume(1.0)
    if correct:
        highA.play()
    elif passThisTrial:
        high= sound.Sound('G',octave=4, sampleRate=2000, secs=.08, bits=8)
        for i in range(2): 
            high.play();  low.play(); 
    else: #incorrect
        low.play()

expStop=False
nDoneMain = -1 #change to zero once start main part of experiment
if doStaircase:
    #create the staircase handler
    useQuest = True
    if  useQuest:
        staircase = data.QuestHandler(startVal = 95, 
                              startValSd = 80,
                              stopInterval= 1, #sd of posterior has to be this small or smaller for staircase to stop, unless nTrials reached
                              nTrials = staircaseTrials,
                              #extraInfo = thisInfo,
                              pThreshold = threshCriterion, #0.25,    
                              gamma = 1./26,
                              delta=0.02, #lapse rate, I suppose for Weibull function fit
                              method = 'quantile', #uses the median of the posterior as the final answer
                              stepType = 'log',  #will home in on the 80% threshold. But stepType = 'log' doesn't usually work
                              minVal=1, maxVal = 100
                              )
        print('created QUEST staircase')
    else:
        stepSizesLinear = [.2,.2,.1,.1,.05,.05]
        stepSizesLog = [log(1.4,10),log(1.4,10),log(1.3,10),log(1.3,10),log(1.2,10)]
        staircase = data.StairHandler(startVal = 0.1,
                                  stepType = 'log', #if log, what do I want to multiply it by
                                  stepSizes = stepSizesLog,    #step size to use after each reversal
                                  minVal=0, maxVal=1,
                                  nUp=1, nDown=3,  #will home in on the 80% threshold
                                  nReversals = 2, #The staircase terminates when nTrials have been exceeded, or when both nReversals and nTrials have been exceeded
                                  nTrials=1)
        print('created conventional staircase')
        
    if prefaceStaircaseTrialsN > len(prefaceStaircaseNoise): #repeat array to accommodate desired number of easyStarterTrials
        prefaceStaircaseNoise = np.tile( prefaceStaircaseNoise, ceil( prefaceStaircaseTrialsN/len(prefaceStaircaseNoise) ) )
    prefaceStaircaseNoise = prefaceStaircaseNoise[0:prefaceStaircaseTrialsN]
    
    phasesMsg = ('Doing '+str(prefaceStaircaseTrialsN)+'trials with noisePercent= '+str(prefaceStaircaseNoise)+' then doing a max '+str(staircaseTrials)+'-trial staircase')
    print(phasesMsg); logging.info(phasesMsg)

    #staircaseStarterNoise PHASE OF EXPERIMENT
    corrEachTrial = list() #only needed for easyStaircaseStarterNoise
    staircaseTrialN = -1; mainStaircaseGoing = False
    while (not staircase.finished) and expStop==False: #staircase.thisTrialN < staircase.nTrials
        if staircaseTrialN+1 < len(prefaceStaircaseNoise): #still doing easyStaircaseStarterNoise
            staircaseTrialN += 1
            thisIncrement = prefaceStaircaseNoise[staircaseTrialN]
            noisePercent = 0
        else:
            if staircaseTrialN+1 == len(prefaceStaircaseNoise): #add these non-staircase trials so QUEST knows about them
                mainStaircaseGoing = True
                print('Importing ',corrEachTrial,' and intensities ',prefaceStaircaseNoise)
                staircase.importData(100-prefaceStaircaseNoise, np.array(corrEachTrial))
                printStaircase(staircase, descendingPsycho, briefTrialUpdate=False, printInternalVal=True, alsoLog=False)
            try: #advance the staircase
                printStaircase(staircase, descendingPsycho, briefTrialUpdate=True, printInternalVal=True, alsoLog=False)
                noisePercent = 0 - staircase.next()  #will step through the staircase, based on whether told it (addResponse) got it right or wrong
                thisIncrement = prefaceStaircaseNoise[staircaseTrialN]

                staircaseTrialN += 1
            except StopIteration: #Need this here, even though test for finished above. I can't understand why finished test doesn't accomplish this.
                print('stopping because staircase.next() returned a StopIteration, which it does when it is finished')
                break #break out of the trials loop
        #print('staircaseTrialN=',staircaseTrialN)
        idxsStream1, idxsStream2 = calcAndPredrawStimuli(wordList1,wordList2)
        cuesPos,correctAnswerIdxsStream1,correctAnswerIdxsStream2, ts  = \
                                        do_RSVP_stim(cuePos, idxsStream1, idxsStream2, noisePercent/100.,staircaseTrialN)
        speedupMessages = [   'time after mask until left do_RSVP_stim' +  str( debugClock.getTime() )   ]
        debugClock.reset()
        numCasesInterframeLong = timingCheckAndLog(ts,staircaseTrialN)
        speedupMessages.append([   'timingCheckAndLog:' +  str( debugClock.getTime() )   ])
        debugClock.reset()
        expStop,passThisTrial,responses,buttons,responsesAutopilot = \
              letterLineupResponse.doLineup(myWin,bgColor,myMouse,clickSound,badKeySound,possibleResps,showBothSides,sideFirstLeftRightCentral,autopilot) #CAN'T YET HANDLE MORE THAN 2 LINEUPS
        print('Now')
        print(responses)



#        expStop,passThisTrial,responses,responsesAutopilot = \
#                stringResponse.collectStringResponse(numRespsWanted,respPromptStim,respStim,acceptTextStim,myWin,clickSound,badKeySound,
#                                                                               requireAcceptance,autopilot,responseDebug=False)
        speedupMessages.append([   'collectStringResponse:' +  str( debugClock.getTime() )   ])
        debugClock.reset()

        if not expStop:
            if mainStaircaseGoing:
                print('staircase\t', end='', file=dataFile)
            else: 
                print('staircase_preface\t', end='', file=dataFile)
             #header start      'trialnum\tsubject\ttask\t'
            print(staircaseTrialN,'\t', end='', file=dataFile) #first thing printed on each line of dataFile
            print(subject,'\t',task,'\t', round(noisePercent,2),'\t', end='', file=dataFile)
            correct,approxCorrect,responsePosRelative= handleAndScoreResponse(
                                                passThisTrial,responses,responseAutopilot,task,sequenceLeft,cuesPos[0],correctAnswerIdx,wordList )
            speedupMessages.append([   'handleAndScoreResponse:' +  str( debugClock.getTime() )   ])
            debugClock.reset()
            print(numCasesInterframeLong, file=dataFile) #timingBlips, last thing recorded on each line of dataFile
            speedupMessages.append([   'printing of numCasesInterframeLong to file:' +  str( debugClock.getTime() )   ])
            debugClock.reset()
            core.wait(.06)
            if feedback: 
                play_high_tone_correct_low_incorrect(correct, passThisTrial=False)
            print('staircaseTrialN=', staircaseTrialN,' noisePercent=',round(noisePercent,3),' T1approxCorrect=',T1approxCorrect) #debugON
            corrEachTrial.append(T1approxCorrect)
            if mainStaircaseGoing: 
                staircase.addResponse(T1approxCorrect, intensity = 100-noisePercent) #Add a 1 or 0 to signify a correct/detected or incorrect/missed trial
                #print('Have added an intensity of','{:.3f}'.format(100-noisePercent), 'T1approxCorrect =', T1approxCorrect, ' to staircase') #debugON
    #ENDING STAIRCASE PHASE
    #print(speedupMessages)
    if staircaseTrialN+1 < len(prefaceStaircaseNoise) and (staircaseTrialN>=0): #exp stopped before got through staircase preface trials, so haven't imported yet
        print('Importing ',corrEachTrial,' and intensities ',prefaceStaircaseNoise[0:staircaseTrialN+1])
        staircase.importData(100-prefaceStaircaseNoise[0:staircaseTrialN], np.array(corrEachTrial)) 
    print('framesSaved after staircase=',framesSaved) #debugON

    timeAndDateStr = time.strftime("%H:%M on %d %b %Y", time.localtime())
    msg = ('prefaceStaircase phase' if expStop else '')
    msg += ('ABORTED' if expStop else 'Finished') + ' staircase part of experiment at ' + timeAndDateStr
    logging.info(msg); print(msg)
    printStaircase(staircase, descendingPsycho, briefTrialUpdate=True, printInternalVal=True, alsoLog=False)
    #print('staircase.quantile=',round(staircase.quantile(),2),' sd=',round(staircase.sd(),2))
    threshNoise = round(staircase.quantile(),3)
    if descendingPsycho:
        threshNoise = 100- threshNoise
    threshNoise = max( 0, threshNoise ) #e.g. ff get all trials wrong, posterior peaks at a very negative number
    msg= 'Staircase estimate of threshold = ' + str(threshNoise) + ' with sd=' + str(round(staircase.sd(),2))
    logging.info(msg); print(msg)
    myWin.close()
    #Fit and plot data
    fit = None
    try:
        intensityForCurveFitting = staircase.intensities
        if descendingPsycho: 
            intensityForCurveFitting = 100-staircase.intensities #because fitWeibull assumes curve is ascending
        fit = data.FitWeibull(intensityForCurveFitting, staircase.data, expectedMin=1/26., sems = 1.0/len(staircase.intensities))
    except:
        print("Fit failed.")
    plotDataAndPsychometricCurve(staircase,fit,descendingPsycho,threshCriterion)
    #save figure to file
    pylab.savefig(fileName+'.pdf')
    print('The plot has been saved, as '+fileName+'.pdf')
    pylab.show() #must call this to actually show plot
else: #not staircase
    noisePercent = defaultNoiseLevel
    phasesMsg = 'Experiment will have '+str(trials.nTotal)+' trials. Letters will be drawn with superposed noise of ' + "{:.2%}".format(defaultNoiseLevel)
    print(phasesMsg); logging.info(phasesMsg)
    nDoneMain =0
    calcAndPredrawStimuli(wordList1,wordList2)
    while nDoneMain < trials.nTotal and expStop==False: #MAIN EXPERIMENT LOOP
        if nDoneMain==0:
            msg='Starting main (non-staircase) part of experiment'
            logging.info(msg); print(msg)
        thisTrial = trials.next() #get a proper (non-staircase) trial
        thisProbe = thisTrial['probe']
        if thisProbe=='both':
          numRespsWanted = 2
        else: numRespsWanted = 1
        
        #Determine which words will be drawn
        idxsStream1 = np.arange( len(wordList1) ) #indexes for RSVP stream
        np.random.shuffle(idxsStream1)
        correspondingWordsAtLeftAndRight = True
        if correspondingWordsAtLeftAndRight:
            idxsStream2 = copy.deepcopy(idxsStream1)
        else:
            idxsIntoWordList2 = np.arange( len(wordList2) )
            np.random.shuffle(idxsStream2)
    
        cuesPos,correctAnswerIdxsStream1,correctAnswerIdxsStream2, ts  = \
                                                                    do_RSVP_stim(thisTrial, idxsStream1, idxsStream2, noisePercent/100.,nDoneMain,thisProbe)
        if nDoneMain>0:
                speedupMessages.append([   'from end of trial to beginning of next:' +  str( 1000*debugClock.getTime() )   ])
                debugClock.reset()
                #print(speedupMessages)
        speedupMessages = [   'time after mask until left do_RSVP_stim' +  str( 1000*debugClock.getTime() )   ]
        debugClock.reset()
        numCasesInterframeLong = timingCheckAndLog(ts,nDoneMain)
        speedupMessages.append([   'timingCheckAndLog:' +  str( 1000*debugClock.getTime() )   ])
        debugClock.reset()
        #call for each response
        myMouse = event.Mouse()
        #alphabet = list(string.ascii_lowercase)
        possibleResps = wordList1
        showBothSides = True
        sideFirstLeftRightCentral = 0
        #possibleResps.remove('C'); possibleResps.remove('V
        
        expStop = list(); passThisTrial = list(); responses=list(); responsesAutopilot=list()
        numCharsInResponse = len(wordList1[1])
        dL = [None]*numRespsWanted #dummy list for null values
        expStop = copy.deepcopy(dL); responses = copy.deepcopy(dL); responsesAutopilot = copy.deepcopy(dL); passThisTrial=copy.deepcopy(dL)
        if thisProbe == 'both':
            print("Doing bothsides")
            responseOrder = [0,1]

            if thisTrial['rightResponseFirst']: #change order of indices depending on rightResponseFirst. response0, answer0 etc refer to which one had to be reported first
                    responseOrder.reverse()
                #x = 2* wordEccentricity*(i*2-1) #put it 3 times farther out than stimulus, so participant is sure which is left and which right
            expStop,passThisTrial,responses,buttons,responsesAutopilot = \
                    letterLineupResponse.doLineup(myWin,bgColor,myMouse,clickSound,badKeySound,possibleResps,showBothSides,sideFirstLeftRightCentral,autopilot) #CAN'T YET HANDLE MORE THAN 2 LINEUPS

    


#                expStop[i],passThisTrial[i],responses[i],responsesAutopilot[i] = stringResponse.collectStringResponse(
#                                        numCharsInResponse,x,respPromptStim,respStim,acceptTextStim,fixationPoint,myWin,clickSound,badKeySound,
#                                                                                   requireAcceptance,autopilot,responseDebug=True) 
            speedupMessages.append([   'collectStringResponse:' +  str( 1000*debugClock.getTime() )   ])
            debugClock.reset()
            expStop = np.array(expStop).any(); passThisTrial = np.array(passThisTrial).any()
        
        if not expStop:
                print('main\t', end='', file=dataFile) #first thing printed on each line of dataFile to indicate main part of experiment, not staircase
                print(nDoneMain,'\t', end='', file=dataFile)
                print(subject,'\t',task,'\t', round(noisePercent,3),'\t', end='', file=dataFile)
                print(thisTrial['leftStreamFlip'],'\t', end='', file=dataFile)
                print(thisTrial['rightStreamFlip'],'\t', end='', file=dataFile)
                print(thisTrial['rightResponseFirst'],'\t', end='', file=dataFile)
                print(thisTrial['probe'],'\t', end='', file=dataFile)
                i = 0
                eachCorrect = np.ones(numRespsWanted)*-999

                print("numRespsWanted = ",numRespsWanted)
                for i in [0,1]:#range(numRespsWanted): #scored and printed to dataFile in left first, right second order even if collected in different order
                    if i==0:
                        print("i=",i)
                        sequenceStream = idxsStream1; correctAnswerIdxs = correctAnswerIdxsStream1; wordList = wordList1;
                    else: sequenceStream = idxsStream2; correctAnswerIdxs = correctAnswerIdxsStream2; wordList = wordList2;
                    print ("sequenceStream = ",sequenceStream)
                    print ("correctAnswerIdxs = ", correctAnswerIdxs)
                    print ("wordList = ", wordList)
                    print ("responses = ", responses)
                    correct = (
                            handleAndScoreResponse(passThisTrial,responses[i],responsesAutopilot,task,thisTrial['cuePos'],correctAnswerIdxs,wordList[correctAnswerIdxs] ) )
                    #eachCorrect[i] = correct
        

              #  if (thisProbe == 'both'):
              #      for i in [0,1]:#range(numRespsWanted):




#                    Resps = [0,1]
#                else:
#                    Resps = [0]
#                for i in Resps: #scored and printed to dataFile in left first, right second order even if collected in different order
#                    if (thisProbe=='both'):
#                        if i==0:
#                           sequenceStream = idxsStream1; correctAnswerIdxs = correctAnswerIdxsStream1; wordList = wordList1; 
#                        else: sequenceStream = idxsStream2; correctAnswerIdxs = correctAnswerIdxsStream2; wordList = wordList2;
#                        correct = handleAndScoreResponse(passThisTrial,responses[i],responsesAutopilot[i],task,sequenceStream,thisTrial['cuePos'],correctAnswerIdxs[i],wordList )
#                        eachCorrect[i] = correct
#
#                    else: 
#                       if (i==1 and thisTrial['rightResponseFirst']) or (i==0 and not thisTrial['rightResponseFirst']):
#                           sequenceStream = idxsStream1; correctAnswerIdxs = correctAnswerIdxsStream1; wordList = wordList1;
#                       else: sequenceStream = idxsStream2; correctAnswerIdxs = correctAnswerIdxsStream2; wordList = wordList2; 
#                       correct = handleAndScoreResponse(passThisTrial,responses[i],responsesAutopilot[i],task,sequenceStream,thisTrial['cuePos'],correctAnswerIdxs[i],wordList ) 
#                       eachCorrect[i] = correct
                print(numCasesInterframeLong, file=dataFile) #timingBlips, last thing recorded on each line of dataFile
                #print('correct=',correct,'eachCorrect=',eachCorrect)
                numTrialsCorrect += eachCorrect.all() #so count -1 as 0
                numTrialsEachCorrect += eachCorrect #list numRespsWanted long
                    
                if exportImages:  #catches one frame of response
                     myWin.getMovieFrame() #I cant explain why another getMovieFrame, and core.wait is needed
                     framesSaved +=1; core.wait(.1)
                     myWin.saveMovieFrames('images_sounds_movies/frames.png') #mov not currently supported 
                     expStop=True
                #core.wait(.1)
                if feedback: play_high_tone_correct_low_incorrect(correct, passThisTrial=False)
                nDoneMain+=1
                speedupMessages.append([   'end of trial:' +  str( 1000*debugClock.getTime() )   ])
                debugClock.reset()
                #dataFile.flush(); logging.flush()
                #print('nDoneMain=', nDoneMain,' trials.nTotal=',trials.nTotal) #' trials.thisN=',trials.thisN
                if (trials.nTotal > 6 and nDoneMain > 2 and nDoneMain %
                     ( trials.nTotal*pctCompletedBreak/100. ) ==1):  #dont modulus 0 because then will do it for last trial
                        nextText.setText('Press "SPACE" to continue!')
                        nextText.draw()
                        progressMsg = 'Completed ' + str(nDoneMain) + ' of ' + str(trials.nTotal) + ' trials'
                        NextRemindCountText.setText(progressMsg)
                        NextRemindCountText.draw()
                        myWin.flip() # myWin.flip(clearBuffer=True) 
                        waiting=True
                        while waiting:
                           if autopilot: break
                           elif expStop == True:break
                           for key in event.getKeys():      #check if pressed abort-type key
                                 if key in ['space','ESCAPE']: 
                                    waiting=False
                                 if key in ['ESCAPE']:
                                    expStop = True
                        myWin.clearBuffer()
                speedupMessages.append([   '*definitely* the end of  the trial:' +  str( 1000*debugClock.getTime() )   ])
                debugClock.reset()
                core.wait(.1);  time.sleep(.1)
            #end main trials loop
    timeAndDateStr = time.strftime("%H:%M on %d %b %Y", time.localtime())
    msg = 'Finishing at '+timeAndDateStr
    print(msg); logging.info(msg)
    if expStop:
        msg = 'user aborted experiment on keypress with trials done=' + str(nDoneMain) + ' of ' + str(trials.nTotal+1)
        print(msg); logging.error(msg)

    if not doStaircase and (nDoneMain >0):
        print('Of ',nDoneMain,' trials, on ',numTrialsCorrect*1.0/nDoneMain*100., '% of all trials all targets reported exactly correct',sep='')
        for i in range(numRespsWanted):
            print('stream',i,': ',round(numTrialsEachCorrect[i]*1.0/nDoneMain*100.,2), '% correct',sep='')
    dataFile.flush()
    logging.flush(); dataFile.close()
    myWin.close() #have to close window if want to show a plot
