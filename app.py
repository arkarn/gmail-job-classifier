from flask import Flask, request, json, redirect, url_for
from flask import render_template
from imap_tools import MailBox
from job_descriptions import jds
import difflib

app = Flask(__name__)
app.debug = True


buckets = [jd['jobid']+" "+jd['position']+" "+jd['keywords'] for jd in jds]
print(buckets)



@app.route("/")
def home():
    return render_template('index.html')

@app.route("/signin", methods=['POST'])
def signin():
    username = request.form['username']
    password = request.form['password']
    if username and password:
        #return redirect(url_for('inbox')) #json.dumps({'validation' : validateUser(username, password)})
        emails = []
        with MailBox('imap.gmail.com').login(username, password, 'INBOX') as mailbox:
            print("success")
            for i, msg in enumerate(mailbox.fetch(bulk=True, limit=4, reverse=True)):
                email = {'attachments':[], 'from':msg.from_, 'sub':msg.subject, 'job':""}
                email['id'] = i+1
                emails.append(email)
                for att in msg.attachments:
                    email['attachments'].append(att.filename)
                email['job'] = classify(msg.subject, msg.text)
        return render_template('basic_table.html', title='Gmail Jobs classifier',
                           emails=emails)


    return json.dumps({'validation' : False})


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


