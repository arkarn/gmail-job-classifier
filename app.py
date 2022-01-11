from flask import Flask, request, json, redirect, url_for
from flask import render_template
from imap_tools import MailBox

app = Flask(__name__)
app.debug = True



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
            for i, msg in enumerate(mailbox.fetch(bulk=True, limit=20, reverse=True)):
                email = {'attachments':[], 'from':msg.from_, 'sub':msg.subject}
                email['id'] = i+1
                emails.append(email)
                for att in msg.attachments:
                    email['attachments'].append(att.filename)
        return render_template('basic_table.html', title='Gmail Jobs classifier',
                           emails=emails)


    return json.dumps({'validation' : False})

    
            
    
if __name__ == '__main__':
   app.run()


