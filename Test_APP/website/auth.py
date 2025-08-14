from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User, Names
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)
# GENERATE USER NAME FUNCTION
def generate_username(first_name, last_name):
    first_part = (first_name[:4].lower()).ljust(4, '_')
    last_part = (last_name[:4].lower()).ljust(4, '_')
    base = f"{first_part}.{last_part}"
    count = 1
    username = f"{base}{count}"
    while User.query.filter_by(username=username).first():
        count+=1
        username = f"{base}{count}"
    return username

# LOG IN PAGE
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        
        if user:
            if check_password_hash(user.password, password):
                flash("Sesión iniciada exitosamente.", category = 'success')
                login_user(user,remember=True)
                session['userName'] = user.username
                user_name = user.username
                #print("User logged in:", session.get('userName'))
                return redirect(url_for('views.home'))
            else:
                flash("Contraseña incorrecta. Intente de nuevo.", category='error')
        else: 
            flash("Usuario no existe.", category = 'error')
    return render_template("login.html", user = current_user)

#LOG OUT
@auth.route('logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#SIGN UP PAGE
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user: 
            flash("Ya existe una cuenta con ese correo electronico. Intente de nuevo.", category = 'error')
        elif len(email) < 4:
            flash('Entre un correo electronico válido.', category = 'error')
        elif len(first_name) < 2 or len(last_name) < 2:
            flash('Entre nombre y apellido válido.', category = 'error')
        elif password1 != password2:
            flash('Contraseñas deben de ser iguales.', category = 'error')
        elif len(password1) < 7:
            flash('Contraseña necesita al menos 7 caracteres', category = 'error')
        else:
            username = generate_username(first_name, last_name)
            group = 'admin' if first_name.strip().lower() == 'admin' else 'standard'

            new_user = User(email = email, 
                            first_name = first_name, 
                            last_name = last_name, 
                            username=username, password = generate_password_hash(password1, method = 'pbkdf2:sha256'),
                            group=group)
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Cuenta ha sido creada. Su nombre de usuario es: {username}. Guardelo para sus records.', category = 'success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))
    return render_template("sign_up.html", user = current_user)

#EDITING USER GROUPS
'''@auth.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user_group(user_id):
    if current_user.group not in['admin']:
        flash("Unauthorized access", category='error')
        return redirect(url_for('views.home'))

    user_list = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_group = request.form.get('group')
        user_list.group = new_group
        db.session.commit()
        flash("User group updated", category='success')
        return redirect(url_for('auth.admin_dashboard'))

    return render_template('admin.html', user=current_user, user_list=user_list)'''

# ADMIN DASHBOARD
@auth.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.group not in['admin', 'manager']:
        flash("Acceso denegado", category='error')
        return redirect(url_for('views.home'))
    
    # Handle form to add a new name
    if request.method == 'POST':
        # Determine which form was submitted using a hidden field
        if request.form.get('form_name') == 'edit_user':
            user_id = request.form.get('user_id')
            new_group = request.form.get('group')
            user = User.query.get(user_id)
            if user and new_group:
                user.group = new_group
                db.session.commit()
                flash("Grupo de usuario fue actualizado", category='success')
                return redirect(url_for('auth.admin_dashboard'))    

    users = User.query.all()
    names_all = Names.query.all()
    return render_template('admin.html', user=current_user, users=users, names_all = names_all)

# ADMIN DASHBOARD
@auth.route('/names', methods=['GET', 'POST'])
@login_required
def add_names():
    if current_user.group not in['admin', 'manager']:
        flash("Acceso denegado", category='error')
        return redirect(url_for('views.home'))
    
    # Handle form to add a new name
    if request.method == 'POST':
        # Determine which form was submitted using a hidden field
        if request.form.get('form_name') == 'add_name':
            name = request.form.get('Name')
            if name:
                name_upper = name.title()
                new_name = Names(name=name_upper)
                db.session.add(new_name)
                db.session.commit()
                flash("Nombre añadido", category='success')
                return redirect(url_for('auth.add_names'))

    users = User.query.all()
    names_all = Names.query.all()
    return render_template('nombres.html', user=current_user, users=users, names_all = names_all)