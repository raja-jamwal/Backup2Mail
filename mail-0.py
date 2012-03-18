#! /usr/bin/python
"""

Mail2Backup (C) Raja Jamwal <linux1@zoho.com>

Changes:
	Email contain list of files in archive
"""
import os
import tarfile
from optparse import OptionParser
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

smtp_server = "smtp.gmail.com"
smtp_port = "587" # port may be 465 or 587, check with mail provider
smtp_login = ["example@gmail.com","password"] # example@example.com, password
mail_meta =  ["from@gmail.com", "to@gmail.com", "Backup"] # from, to, subject
mail_text = "<html><body><center><b>Mail2Backup</b><br/>Attachment contains following files:<hr/><table border=\"0\"><tr><th>File</th><th>Size</th></tr><br/>" # some text

def prep_send(filec):
  #try:
	print "Sending to "+smtp_server
	msg = MIMEMultipart()
	print "Composing email "
	print "-----------------------------------------------------------"
	print "+ SMTP"
	print "  Server		"+str(smtp_server)
	print "  Port   	"+smtp_port
	print "+ Login		"
	print "  username 	"+smtp_login[0]
	print "  password 	"+smtp_login[1]
	print "+ Mail"
	print "  From 		"+str(mail_meta[0])
	print "  To   		"+str(mail_meta[1])
	print "  Directory 	"+filec
	print "-----------------------------------------------------------"
	msg['From'] = mail_meta[0]
  	msg['To'] = COMMASPACE.join(mail_meta[1])
  	msg['Date'] = formatdate(localtime=True)
  	msg['Subject'] = "Backup2mail "+str(mail_meta[2])+" "+str(os.path.basename(filec))+" "+str(formatdate(localtime=True))
	msg.attach(MIMEText(mail_text, "html"))
	
	#add the file TODO: multiple files with multi directory option
	print "Encoding file data for email"
    	part = MIMEBase('application', "octet-stream")
    	part.set_payload( open(filec,"rb").read() )
    	Encoders.encode_base64(part)
    	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filec))
    	msg.attach(part)

	print "Authenticating & Sending..."
	server = smtplib.SMTP(smtp_server,smtp_port) #port 465 or 587
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
	tar_file = args.replace('/', '').lower()+".tar.bz2"
	tar = tarfile.open(tar_file, 'w:bz2')
	level = "."
	for dirpath, dirnames, filenames in os.walk(args):
	 mail_text += "<tr><td>"+str(level[1::])+str(dirpath)+"</td><td>DIR</td></tr>"
	 for file in filenames:
		print "Compressing "+str(dirpath)+str(file)
		tar.add(os.path.join(dirpath, file))
		mail_text += "<tr><td>"+str(level)+str(file)+"</td><td>"+str(os.path.getsize(os.path.join(dirpath, file))/1024)+" KB"+"</td></tr>"
	 #level += str(".")
	mail_text += "</table></center></body></html>"	
	tar.close()		
	prep_send(tar_file)
    
if __name__ == "__main__":

    print "\nBackup2Mail (C) Raja Jamwal <linux1@zoho.com>"
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
    print "Will compress and send : "+str(options.directory)

    main(options.directory)


