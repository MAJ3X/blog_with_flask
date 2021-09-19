from MySQLdb import cursors
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL 
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from functools import wraps
import hashlib

#userregistrationform

class RegForm(Form):
    name = StringField('isim soyisim',validators = [validators.Length(min = 4,max = 25)])
    username = StringField('Kullanici Adi',validators = [validators.Length(min = 5,max = 35)])
    e_mail = StringField('E-Mail',validators = [validators.Email(message='Lutfen gecerli bir e-mail adresi giriniz...')])
    upass = PasswordField('Parola',validators=[
        validators.DataRequired(message='Parolasiz nah girersin...'),
        validators.EqualTo(fieldname='confirm',message='duzgun yaz')
    ])
    confirm = PasswordField('Parola Dogrulama')

class LoginForm(Form):
    username = StringField('Kullanici adi')
    upass = PasswordField('Parola')

app = Flask(__name__)
app.secret_key = ('mblog')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'm&b'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def index():
    articles = [
        
        {'id':1,'title':'deneme','content':'deneme icrerigi'},
        {'id':2,'title':'deneme1','content':'deneme icrerigi1'}

    ]

    return render_template('index.html',answer = 'evet',islem = 4,articles = articles)

# deneme
@app.route('/hoop', methods=['POST', 'GET'])
def getPage():
    if request.method == 'POST':
        strTextBoxVal= request.form['telno']
        print(strTextBoxVal)
    return render_template('regs.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:

            return f(*args, **kwargs)
        else:
            flash('Bu sayfayi goruntulemek icin giris yapiniz','danger')
            return redirect(url_for('login'))
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    query = 'SELECT * From articles WHERE author = %s'

    result = cursor.execute(query,(session['username'],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template('dashboard.html',articles = articles)
    else:
        return render_template('dashboard.html')

    return render_template('dashboard.html')

#register
@app.route('/register', methods = ['GET','POST'])
def register():
    form = RegForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        e_mail = form.e_mail.data
        upass = hashlib.sha256(form.upass.data.encode()).hexdigest()

        cursor = mysql.connection.cursor()

        sorgu = 'INSERT into users(name,username,email,password) VALUES (%s,%s,%s,%s)' 

        cursor.execute(sorgu,(name,username,e_mail,upass))

        mysql.connection.commit()

        cursor.close()
        
        flash('Kayıt Başarılı...Lütfen Giriş Yapınız','success')
        
        return redirect(url_for('login'))

    else:

        return render_template('register.html',form = form)

@app.route('/login', methods = ['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        username = form.username.data
        password_entered = form.upass.data

        cursor = mysql.connection.cursor()

        query = 'Select *From users where username = %s'
        result = cursor.execute(query,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
            if hashlib.sha256(password_entered.encode()).hexdigest() == real_password:
                flash('Giris basarili','success')
                
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                flash('Parolanizi yanlis girdiniz','danger')
                return redirect(url_for('login'))
        else:
            flash('Boyle bir kullanici bulunmuyor...','danger')
            return redirect(url_for('login'))
    
    return render_template('login.html',form = form)


@app.route('/article/<string:id>')
def detail(id):
    cursor = mysql.connection.cursor()

    query = 'SELECT * From articles WHERE id = %s'

    result = cursor.execute(query,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template('article.html',article = article)
    else:
        return render_template('article.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/addarticle',methods = ['GET','POST'])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        query = 'INSERT into articles(title,author,content) VALUES (%s,%s,%s)'

        cursor.execute(query,(title,session['username'],content))

        mysql.connection.commit()

        cursor.close()

        flash('Makale Basariyla Eklendi','success')

        return redirect(url_for('dashboard'))

    return render_template('addarticle.html',form = form)

class ArticleForm(Form):
    title = StringField('Makale Basligi',validators=[validators.length(min = 5,max =100)])
    content = TextAreaField('Makale icerigi',validators=[validators.length(min = 10)])

@app.route('/delete/<string:id>')
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    query = 'SELECT * From articles WHERE author = %s and id = %s'

    result = cursor.execute(query,(session['username'],id))

    if result > 0:
        query2 = 'DELETE From articles WHERE id = %s'

        cursor.execute(query2,(id,))

        mysql.connection.commit()

        return redirect(url_for('dashboard'))

    else:
        flash('Böyle bir makale yok veya bu isleme yetkiniz yok!!!','danger')
        return redirect(url_for('index'))

@app.route('/edit/<string:id>',methods = ['GET','POST'])
@login_required
def update(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()

        query = 'SELECT * From articles WHERE author = %s and id = %s'
        result = cursor.execute(query,(session['username'],id))

        if result == 0:
            flash('Böyle bir makale yok veya bu isleme yetkiniz yok!!!','danger')
            return redirect(url_for('index'))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            
            form.title.data = article['title']
            form.content.data = article['content']
            return render_template('update.html',form = form)
       
    else:
        #postreq
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data

        query2 = 'UPDATE articles SET title = %s,content =%s WHERE id=%s'
        
        cursor = mysql.connection.cursor()
        cursor.execute(query2,(newtitle,newcontent,id))

        mysql.connection.commit()

        flash('Makale başarıyla güncellendi','success')

        return redirect(url_for('dashboard'))

@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()

    query = 'SELECT * From articles'

    result = cursor.execute(query)

    if result > 0:
        articles = cursor.fetchall()

        return render_template('articles.html',articles = articles)
    else:
        return render_template('articles.html')

@app.route('/search',methods = ['GET','POST'])
def search():
    if request.method == 'GET':
        return redirect(url_for('index'))
    else:
        keyword = request.form.get('keyword') #burası boş geliyor, get olarak alınıyor, ve yarrak kafalı, get değilse diorsun ve get parametresinden veri alyıyon

        cursor = mysql.connection.cursor()

        query = "SELECT * From articles WHERE title like '" + keyword + "%'"#böyle dene

        result = cursor.execute(query)


        if result == 0:
            flash('Aranan kelimeye uygun makale bulunamadi','warning')

            return redirect(url_for('articles'))
        else:
            articles = cursor.fetchall()

            return render_template('articles.html',articles = articles)
            
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__': 
    app.run(debug=True, use_debugger=True)