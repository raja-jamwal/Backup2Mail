#! /usr/bin/python
"""

Mail2Backup (C) Raja Jamwal <linux1@zoho.com>

Changes:
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

smtp_server = "smtp.gmail.com"
smtp_port = "587" # port may be 465 or 587, check with mail provider
smtp_login = ["example@gmail.com","password"] # example@example.com, password
mail_meta =  ["from@gmail.com", "to@gmail.com", "Backup"] # from, to, subject
mail_text = "<html><body><b><h2>Backup2Mail</h2> &copy; Raja Jamwal. version 0.1</b><br/>Attachment contains following files:<hr/>" # some text

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
  #try:
	print "Sending through \""+smtp_server+"\"..."
	msg = MIMEMultipart()
	print "Details... "
	
	print "   Server   ("+str(smtp_server)+","+smtp_port+")"
	print "   Login    ("+smtp_login[0]+","+smtp_login[1]+")"
	print "   From	    ("+str(mail_meta[0])+")"
	print "   To	    ("+str(mail_meta[1])+")"
	print "   Directory("+filec+")"
	
	msg['From'] = mail_meta[0]
  	msg['To'] = COMMASPACE.join(mail_meta[1])
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
	server.starttls()
	server.ehlo()
	server.login(smtp_login[0],smtp_login[1])
	server.sendmail(mail_meta[0],mail_meta[1],msg.as_string())
	server.close()	
	print "Done..."
  #except socket.gaierror:
   	#print "Error: unable to send email"

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
	prep_send(tar_file)
    
if __name__ == "__main__":

    #print "\nBackup2Mail (C) Raja Jamwal <linux1@zoho.com>"
    parser = OptionParser(usage="%prog [--dir] [dir] [smtp options]")
    parser.add_option("-d", "--dir", dest="directory", help ="directory to backup")
    parser.add_option("-f", "--from", dest="from_id", help="email addr. to send from", default=mail_meta[0])
    parser.add_option("-t", "--to", dest="to_id", help="email addr. to send to", default=mail_meta[1])

    parser.add_option("-s", "--server", dest="server", help="smtp server addr.", default=smtp_server)
    parser.add_option("-p", "--port", dest="port", help="smtp port number", default=smtp_port)
    parser.add_option("-u", "--username", dest="username", help="smtp login username", default=smtp_login[0])
    parser.add_option("-l", "--password", dest="password", help="smtp login password", default=smtp_login[1]) 
    
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

    if os.path.isdir(str(options.directory))!=True:
	print "Error: "+str(options.directory)+ " is not a directory or doesn't exist"
	exit()
    print "Compressing and sending : "+str(options.directory)

    main(options.directory)


