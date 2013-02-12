import random
import string
import subprocess
import json
import base64
import hashlib
import sys
import os

# Magic Image String delimiters
image_start = 'BEGIN_IMAGE_f9825uweof8jw9fj4r8'
image_end   = 'END_IMAGE_0238jfw08fjsiufhw8frs'

# Magic timing iedntifiers
timingStringIdentifier = 'e57__TIMING__f82'
meanStringIdentifier   = 'e57__MEAN__f82'

# Random name generated for student's output image file
student_file = ''.join(random.choice(string.ascii_lowercase) for x in range(10)) + '.png'

# number of times to execute the student code. We are executing the student's code
# more once because the student's code may non-deterministcally take a really long
# time to execute. Possibly caused by the virtualization layer in EC2 or resource
# contention between different student submissions. 
num_executions = 3

# an array to store the student's execution code, we are going to run the 
# student's code 3 times and take the median of the all the execution time
execution_times = []

# hack to include the CUDA lib path
os.environ["LD_LIBRARY_PATH"] = "$LD_LIBRARY_PATH:/usr/local/cuda-5.0/lib64"

#strip all timing strings from the output
def _stripPrints(inputString, identifier):
    pos = inputString.find(identifier)
    if pos == -1:
        return inputString, ''
    else:
        val = ''
        newOutputString = ''
        for line in inputString.split('\n'):
            if line.startswith(identifier):
                val = line.split()[1]
            elif not line == '':
                newOutputString += line + '\n'
        if identifier in newOutputString:
            #more than one!! bad news...probably cheating attempt
            return 'There is no reason to output the string ' + identifier + ' in your code\nCheating Suspected - Automatic Fail', ''
        else:
            return newOutputString, val

def make():
    try:
        subprocess.check_output(['make', '-s'], stderr = subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        sys.stderr.write(e.output + '\n')
        return False
    return True

def executeBinary():
    try:
        progOutput = ''
        for i in range(0, num_executions):
            progOutput = subprocess.check_output(['./hw', 'cinque_terre_small.jpg', student_file], stderr = subprocess.STDOUT)
            progOutput, time = _stripPrints(progOutput, timingStringIdentifier)
            if time != '':
                execution_times.append(float(time))
            else:
                execution_times.append(float(100))
        progOutput = progOutput.strip()
        if progOutput != '':
            progOutput = _strip_libd1394_error(progOutput)
            sys.stdout.write("Your code printed the following output: \n")
            sys.stdout.write(progOutput);
    except subprocess.CalledProcessError, e:
        #program failed, dump possible Make warnings, program output and quit
        progOutput, time = _stripPrints(e.output, timingStringIdentifier)
        sys.stderr.write(progOutput + '\n')
        sys.stdout.write('error output: ' + e.output + '\n')
        return False
    return True

def compareImages():
    try:
        subprocess.check_output(['./compare', 'cinque_terre.gold', student_file, '5.0', '5.0'], stderr = subprocess.STDOUT)        
    except subprocess.CalledProcessError, e:
        sys.stderr.write(e.output + '\n')
        return False
    return True

def dumpDiffImage():
    try:
        diffImage = open('differenceImage.png', 'rb').read()
        data = {}
        data['name'] = 'DifferenceImage'
        data['format'] = 'png'
        data['bytes'] = base64.encodestring(diffImage)
        sys.stdout.write(image_start + json.dumps(data) + image_end)
    except IOError:
        sys.stderr.write('Oops! We are unable to return the difference image. Please leave a message in the forum for the assistant instructor and let him know that something went wrong!\n')

def dumpStudentImage():
    try:
        studentImage = open(student_file, 'rb').read()
        data = {}
        data['name'] = 'studentImage'
        data['format'] = 'png'
        data['bytes'] = base64.encodestring(studentImage)
        sys.stdout.write(image_start + json.dumps(data) + image_end)
    except IOError:
        sys.stderr.write('Oops! We are unable to return the image generated by your program. Please leave a message in the forum for the assistant instructor and let him know that something went wrong! \n')

def dumpReferenceImage():
    try:
        referenceImage = open('cinque_terre.gold', 'rb').read()
        data = {}
        data['name'] = 'ReferenceImage'
        data['format'] = 'png'
        data['bytes'] = base64.encodestring(referenceImage)
        sys.stdout.write(image_start + json.dumps(data) + image_end)
    except IOError:
        sys.stderr.write('Oops! We are unable to return the reference image. Please leave a message in the forum for the assistant instructor and let him know that something went wrong! \n') 

def _strip_libd1394_error(msg):
    msg = msg.replace("libdc1394 error: Failed to initialize libdc1394", "")
    msg = msg.replace("libdc1394 error:", "")
    msg = msg.replace("Failed to initialize libdc1394", "")

    return msg

if make():
    sys.stdout.write('Your code compiled! \n')
    if executeBinary():
        execution_times.sort()
        median_time = execution_times[num_executions / 2]
        sys.stdout.write('Your code executed in ' + str(median_time) + ' ms \n')
        if compareImages():
            dumpStudentImage()
            sys.stdout.write('Good job!. Your image matched perfectly to the reference image \n')
        else:
            sys.stdout.write('Your image did not match the reference image. Use the following images as a reference and feel free to try again \n \n')
            sys.stdout.write('1st image is the reference image \n')
            sys.stdout.write('2nd image is the image generated by your program: \n')
            sys.stdout.write('3rd image is the difference between the reference image and your image: \n')

            dumpReferenceImage()
            dumpStudentImage()
            dumpDiffImage()  
    else:
        sys.stderr.write('We are unable to execute your code. Did you set the grid and/or block size correctly?\n')
else:
    sys.stdout.write('Your code did not compile. Please check your code for typos or syntax errors \n')