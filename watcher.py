import sys
import ConfigParser
import os.path
import re
import shutil
import errno

# Configuration read
config = ConfigParser.RawConfigParser()
config.read('/share/HDA_DATA/CastgetStuff/watcher/watcher.cfg')

# Globals definition
filename = None
individualMode = False
testMode = False
destinationDirectory = config.get("Watcher", "DestinationDirectory")
filenameRegularExpression = config.get("Watcher", "FilenameRegularExpression")

# Print the usage instructions
def PrintHelp( p_ProgramFilename = "watcher.py" ):
    print "Usage: " + p_ProgramFilename + " Arguments Filename"
    print ""
    print "Where arguments can be selected from"
    print "  -h  --help        Shows this help screen"
    print "  -i  --individual  Allows you to mark only an individual episode as watched"
    print "  -t  --test        Allows you to just test what episodes will be moved"
    print ""
    print "Filename is the file to mark as watched. By default this marks all episodes before that one as watched as well"

# Handle the passed arguments
def HandleArgs( p_Arguments ):
    global filename, individualMode, testMode
    for argument in p_Arguments[1:]:
        if ( argument == "-h" or argument == "--help" ) :
            PrintHelp( p_Arguments[0] )
            exit()
        elif ( argument == "-i" or argument == "--individual" ) :
            individualMode = True
        elif ( argument == "-t" or argument == "--test" ) :
            testMode = True
        else :
            if ( filename is None ) :
                filename = os.path.abspath( argument )
            else :
                print "Error! Multiple filenames entered!"
                PrintHelp( p_Arguments[0] )
                exit()


# Get the episode number from a complete filename
def GetEpisodeNumber( p_Filename ) :
    global filenameRegularExpression
    expressionCheck = re.match(filenameRegularExpression,p_Filename)
    if ( expressionCheck is None ) :
        print "Could not interpret show filename. Please fix the regular expression used!"
        print "Filename used: " + p_Filename
        exit()
    return int(expressionCheck.group("episode_number"))
    
# Get the season number from a complete filename
def GetSeasonNumber( p_Filename ) :
    global filenameRegularExpression
    expressionCheck = re.match(filenameRegularExpression,p_Filename)
    if ( expressionCheck is None ) :
        print "Could not interpret show filename. Please fix the regular expression used!"
        print "Filename used: " + p_Filename
        exit()
    return int(expressionCheck.group("season_number"))

# Make sure the path exists
def MakeDirectory(path):
    try:
        os.makedirs(path)
    except:
        # We dont care if the directory already exists
        pass

# Moves the episode to the destination directory
def MoveEpisode( p_Filename ):
    filenameExpression = re.match(r".*/([^/]*/[^/]*/[^/]*$)",p_Filename)
    if( filenameExpression is None ):
        print "Unable to move episode: " + p_Filename +". Regular expression failed."
        exit()
    SourceFile = p_Filename
    DestinationFile = os.path.join(destinationDirectory,filenameExpression.group(1))
    print "Moving Episode: " + SourceFile + " to " + DestinationFile
    if not testMode :
        MakeDirectory(os.path.dirname(DestinationFile))
        shutil.move(SourceFile, DestinationFile)
    
# Moves the entire season to the destination directory
def MoveSeason( p_Filename ):
    filenameExpression = re.match(r".*/[^/]*/([^/]*/Season [^/]*$)",p_Filename)
    if( filenameExpression is None ):
        print "Unable to move season: " + p_Filename +". Regular expression failed."
        exit()
    SourceFile = p_Filename
    DestinationFile = os.path.join(destinationDirectory,filenameExpression.group(1))
    print "Moving Season: " + SourceFile + " to " + DestinationFile
    if not testMode :
        MakeDirectory(os.path.dirname(DestinationFile))
        shutil.move(SourceFile, DestinationFile)
    
# Remove the season directory if it is empty. Returns true if a directory was removed.
def RemoveEmptySeason( SeasonDirectory ) :
    if len(os.listdir(SeasonDirectory)) == 0:
        print "Removing empty Season directory: " + SeasonDirectory
        os.rmdir(SeasonDirectory)
        return True
    else :
        return False
        
# Remove the show directory if it is empty. Returns true if a directory was removed.
def RemoveEmptyShow( ShowDirectory ) :
    if len(os.listdir(ShowDirectory)) == 0:
        print "Removing empty Show directory: " + ShowDirectory
        os.rmdir(ShowDirectory)
        return True
    else :
        return False

# Logic starting point, firstly we check our arguments
HandleArgs( sys.argv )
if ( not os.path.exists(filename) ) :
    print "Error! Filename specified does not exist."
    exit()

# Move the selected episode and delete the season directory if it is empty
MoveEpisode(filename)
seasonDirectory = os.path.dirname(filename)

# If we are only moving one file, we are done
if ( individualMode ) :
    RemoveEmptySeason(seasonDirectory)
    print "Done!"
    exit()

# Get the stats about the selected episode
SelectedEpisodeNumber = GetEpisodeNumber(filename)
SelectedSeasonNumber = GetSeasonNumber(filename)

# Scan through the season moving older episodes if we didnt delete it
for scannedFilename in os.listdir(seasonDirectory):
    newEpisodeFilename = os.path.join(seasonDirectory,scannedFilename)
    newEpisodeNumber = GetEpisodeNumber(newEpisodeFilename)
    if ( newEpisodeNumber < SelectedEpisodeNumber ) :
        MoveEpisode(newEpisodeFilename)

# Scan through the show moving older seasons
showDirectory = os.path.dirname(seasonDirectory)
for scannedFilename in os.listdir(showDirectory):
    expression = re.match(r"Season (\d+)",scannedFilename)
    if ( expression is not None ) :
        if ( int(expression.group(1)) < SelectedSeasonNumber ) :
            MoveSeason( os.path.join(showDirectory,scannedFilename) )
            
RemoveEmptySeason(seasonDirectory)
RemoveEmptyShow(showDirectory)
