import zipfile
from flask import Flask, request, json, redirect, url_for, send_file, session
from flask import render_template
from imap_tools import MailBox
from job_descriptions import jds
from io import BytesIO    
import os
import difflib

from flask_session import Session
  
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.secret_key = os.urandom(12).hex()
app.debug = True


buckets = [jd['jobid']+" "+jd['position']+" "+jd['keywords'] for jd in jds]


@app.route("/")
def home():
    return render_template('index.html')

@app.route("/signin", methods=['POST'])
def signin():
    session['attachment_files'] = []
    username = request.form['username']
    password = request.form['password']
    if username and password:
        #return redirect(url_for('inbox')) #json.dumps({'validation' : validateUser(username, password)})
        emails = []
        with MailBox('imap.gmail.com').login(username, password, 'INBOX') as mailbox:
            print("success")
            for i, msg in enumerate(mailbox.fetch(bulk=True, limit=50, reverse=True)):
                if len(msg.attachments)>0:
                    email = {'attachments':[], 'from':msg.from_, 'sub':msg.subject, 'job':""}
                    email['id'] = i+1
                    emails.append(email)
                    for att in msg.attachments:
                        email['attachments'].append(att.filename)
                        if (att.filename is not None) and (att.size < 1e7):
                            #print('content_id:', i+1, att.content_id)
                            session['attachment_files'].append((i+1, att.filename, att.payload))
                    email['job'] = classify(msg.subject, msg.text)
        return render_template('basic_table.html', title='Gmail Jobs classifier',
                           emails=emails)


    return json.dumps({'validation' : False})

@app.route("/download", methods=['POST'])
def download():
    ids = request.form.getlist('download_checkbox')
    email_index_to_download = [int(id[3:]) for id in ids]
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for emailIndex, filename, content in session['attachment_files']:
            if emailIndex in email_index_to_download:
                zf.writestr(filename, content)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='export.zip', as_attachment=True)
        



def classify(subject, text):
    if ('job' in subject) | ('job' in text):
        mailtext = subject.lower() +" "+ text.lower()
        ll = scorer(mailtext)
        #print(f"a={mailtext}\nll={ll}")
        ind = ll.index(max(ll))
        #print(f"index: {ind}")
        return jds[ind]['jobid']+" ("+jds[ind]['position']+")"
    else: return ""


def scorer(content):
    scores=[]
    for bucket in buckets:
        score=0
        for word in bucket.split():
            if word.lower() in content.lower():
                score+=1
        scores.append(score)
    return scores
            
    
if __name__ == '__main__':
   app.run(host='0.0.0.0', port=80, debug=True)


