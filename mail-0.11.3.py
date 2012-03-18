#! /usr/bin/python
"""

Mail2Backup (C) Raja Jamwal <linux1@zoho.com>

Changes:
	Support for mangaling archive content	 3/2/12
	Support for upload progress		 1/2/12
	Support for last modified date/time	 30/1/12
	Support for tree type directory listing  30/1/12
	Email contain content in HTML
	Email contain list of files in archive
"""
import os
import tarfile
from optparse import OptionParser
#import smtplib
from smtplib import SMTP, quotedata, CRLF, SMTPDataError
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

import re
import time
import sys

smtp_server = "smtp.mail.yahoo.co.in" # smtp.gmail.com for google "TTL" check is auto
# gmail - smtp_server = "smtp.gmail.com"
smtp_port = "587" # port may be 465 or 587, check with mail provider
# gmail - smtp_login = ["example@gmail.com","password"] # example@example.com, password
smtp_login = ["example@ymail.com","example"] # example@example.com, password

# gmail - mail_meta =  ["example@gmail.com", "example@zoho.com", ""] # from, to, subject
mail_meta =  ["example@ymail.com", "example@zoho.com", ""] # from, to, subject
mail_text = "<html><body><b><h2>Backup2Mail</h2> &copy; Raja Jamwal. version 0.11</b><br/>Attachment contains following files:<hr/>" # some text

demangle_file = None
mangle_file = False
bcc = None

prev_pct = 0
def callback( progress, total ):
	global prev_pct
	sys.stdout.write('\x08' * (len(str(prev_pct))+1))
	pct = (float(progress*100))/total
	sys.stdout.write(str(round(pct,2))+"%")
	prev_pct = round(pct,2)
	sys.stdout.flush()	

class ExtendedSMTP(SMTP): 	
    def data(self,msg):
        """
			This is a modified copy of smtplib.SMTP.data()
			
			Sending data in chunks and calling self.callback
			to keep track of progress,
		"""
        self.putcmd("data")
        (code,repl)=self.getreply()
        if self.debuglevel >0 : print>>stderr, "data:", (code,repl)
        if code != 354:
            raise SMTPDataError(code,repl)
        else:
            q = quotedata(msg)
            if q[-2:] != CRLF:
                q = q + CRLF
            q = q + "." + CRLF
            
            # begin modified send code
            chunk_size = 2048
            bytes_sent = 0
            
            while bytes_sent != len(q):
                chunk = q[bytes_sent:bytes_sent+chunk_size]
                self.send(chunk)
                bytes_sent += len(chunk)
                if hasattr(self, "callback"):
                    self.callback(bytes_sent, len(q))
            # end modified send code
            
            (code,msg)=self.getreply()
            if self.debuglevel >0 : print>>stderr, "data:", (code,msg)
            return (code,msg)

def prep_send(filec):
  try:
	print "Sending through \""+smtp_server+"\"..."
	msg = MIMEMultipart()
	print "Details... "
	
	print "   Server   ("+str(smtp_server)+","+smtp_port+")"
	print "   Login    ("+smtp_login[0]+","+smtp_login[1]+")"
	print "   From	    ("+str(mail_meta[0])+")"
	print "   To	    ("+str(mail_meta[1])+")"
	print "   Directory("+filec+")"
	
	msg['From'] = mail_meta[0]
  	#msg['To'] = (mail_meta[1])

	to_recv = []
	to_recv.append(mail_meta[1])
	for i in bcc:
		if str(i) != "None":
			to_recv.append(i)

	msg['To'] = COMMASPACE.join(to_recv)

  	msg['Date'] = formatdate(localtime=True)
  	msg['Subject'] = "Backup2mail "+str(mail_meta[2])+" "+str(os.path.basename(filec))+" "+str(formatdate(localtime=True))
	msg.attach(MIMEText(mail_text, "html"))
	
	#add the file TODO: multiple files with multi directory option
	print "Encoding binary data for email..."
    	part = MIMEBase('application', "octet-stream")
    	part.set_payload( open(filec,"rb").read() )
    	Encoders.encode_base64(part)
    	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filec))
    	msg.attach(part)

	sys.stdout.write("Authenticating and sending..... ")
	#server = smtplib.SMTP(smtp_server,smtp_port) #port 465 or 587
	server = ExtendedSMTP(smtp_server,smtp_port)
	server.callback = callback
	server.ehlo()

	if server.has_extn('STARTTLS'):
		server.starttls()
		server.ehlo()

	server.login(smtp_login[0],smtp_login[1])

	#server.set_debuglevel(1)
	server.sendmail(mail_meta[0], to_recv, msg.as_string())
	server.close()	

	print ""
	print "Done..."
  except:
	print ""
   	print "Error: Unable to send email due to an error"

def mangle_file_data(path, demangle=False):

	file_content = bytearray(open(path, "rb").read())

	if demangle == False:
		sys.stdout.write("Mangling archive content..... ")
	else:
		sys.stdout.write("Demangling archive content..... ")

	prog = 0
	total = len(file_content)
	for i in range(len(file_content)):
	        file_content[i] ^=0x71
		if (i%1024) == 0:
			sys.stdout.write('\x08' * (len(str(prog))+1))
			now = (float(i*100))/total
			sys.stdout.write(str(round(now,2))+"%")
			prog = round(now,2)
			sys.stdout.flush()	

	open(path, "wb").write(file_content)
	print ""


def main(args=None):
	global mail_text

	if(os.path.exists(args+str("README"))):
		mail_text += "<pre><span style=\"font-size: 15px\">"+open(args+str("README")).read()+"</span></pre>"	

	mail_text += "<table border=\"0\"><tr><th>File</th><th>Size</th><th>Modified time</th></tr>"

	tar_file = args.replace('/', '').lower()+".tar.bz2"
	tar = tarfile.open(tar_file, 'w:bz2')
	level = ""
	rexp = re.compile(r"/")
	for dirpath, dirnames, filenames in os.walk(args):
	 mail_text += "<tr VALIGN=\"TOP\"><td>"+str(level)+"<b>"+str(dirpath)+"</b></td><td>DIR</td></tr>"
	 for file in filenames:
		print "   "+str(dirpath)+str(file)
		match = rexp.findall(str(dirpath))
		times = len(match)
		level = ""
		for i in range(1, times):
			level += str("&nbsp;")
		tar.add(os.path.join(dirpath, file))
		mail_text += "<tr VALIGN=\"TOP\"><td>"+str(level)+str(file)+"</td><td>"+str(os.path.getsize(os.path.join(dirpath, file))/1024)+" KB"+"</td>"+str(time.ctime(os.path.getmtime(str(dirpath))))+"</tr>"
	 #level += str(".")
	mail_text += "</table></body></html>"	
	tar.close()

	if mangle_file == True:
		mangle_file_data(tar_file)
		
	prep_send(tar_file)
    
if __name__ == "__main__":

    #print "\nBackup2Mail (C) Raja Jamwal <linux1@zoho.com>"
    parser = OptionParser(usage="%prog [--dir] [dir] [smtp options]")
    parser.add_option("-d", "--dir", dest="directory", help ="directory to backup")
    parser.add_option("-f", "--from", dest="from_id", help="email addr. to send from", default=mail_meta[0])
    parser.add_option("-t", "--to", dest="to_id", help="email addr. to send to", default=mail_meta[1])

    parser.add_option("-s", "--server", dest="server", help="SMTP server addr.", default=smtp_server)
    parser.add_option("-p", "--port", dest="port", help="SMTP port number", default=smtp_port)
    parser.add_option("-u", "--username", dest="username", help="SMTP login username", default=smtp_login[0])
    parser.add_option("-l", "--password", dest="password", help="SMTP login password", default=smtp_login[1]) 

    parser.add_option("-m", "--mangle", dest="mangle", action="store_true", help="Mangle file content to avoid file scanning from email provider", default=mangle_file)
    parser.add_option("-x", "--demangle", dest="dmangle", help="Demangle previously mangled file", default=demangle_file)
    parser.add_option("-c", "--cc", dest="bcc", help="Send carbon copies to", default=bcc)
    
    options, args = parser.parse_args()

    if str(options.from_id) != None:
	mail_meta[0] = str(options.from_id)

    if str(options.to_id) != None:
	mail_meta[1] = str(options.to_id)

    if str(options.server) != None:
	smtp_server = str(options.server)

    if str(options.port) != None:
	smtp_port = str(options.port)

    if str(options.username) != None:
	smtp_login[0] = str(options.username)

    if str(options.password) != None:
	smtp_login[1] = str(options.password)

    if str(options.dmangle) != None:
	demangle_file = str(options.dmangle)

    if str(options.bcc) != None:
	bcc = str(options.bcc).split(",")

    if options.mangle != False:
	mangle_file = True

    if os.path.isdir(str(options.directory))!=True and str(demangle_file) == "None":
	print "Error: "+str(options.directory)+ " is not a directory or doesn't exist"
	exit()

    if str(demangle_file) != "None":
	mangle_file_data(demangle_file, True)
    else:
	print "Compressing and sending : "+str(options.directory)
	main(options.directory)


