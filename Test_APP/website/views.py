from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, current_app, make_response, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from .models import  Equip, Dispatch, Return, DailyLog, Projects, Images, Training, TrainingLog, Traindocs, Names, EquipSeguridad, EquipSeguridadDisp, Incidentes, Incidentesdocs, PettyCash, PettyCashItems, PettyCashItemsDocs, Materials, MaterialsDisp
from. import db, mail
import json, os, uuid
from sqlalchemy import desc, text
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from datetime import datetime
from weasyprint import HTML

views = Blueprint('views', __name__)

def notify_on_submission(petty_cash):
    first_item = petty_cash.pettycashitems[0] if petty_cash.pettycashitems else None
    project = first_item.project if first_item else None
    # Define recipients
    engineer_email = project.email if project else None
    accounting_emails = ['accounting@pctmconstruction.com']
    submitter_email = petty_cash.user.email if petty_cash.user else None

    # Engineer notification
    if engineer_email:
        msg = Message(
            subject=f"Petty Cash fue sometido para: {project.project if project else 'Unknown Project'}",
            recipients=[engineer_email]
        )
        msg.body = f"Petty Cash ID {petty_cash.id} fue sometido por: {petty_cash.user.first_name} {petty_cash.user.last_name} para el proyecto: {project.project if project else 'Unknown Project'}."
        mail.send(msg)

    # Accounting notification
    if accounting_emails:
        msg = Message(
            subject=f"Petty Cash fue sometido para: {project.project if project else 'Unknown Project'}",
            recipients=accounting_emails
        )
        msg.body = f"Petty Cash ID {petty_cash.id} fue sometido por: {petty_cash.user.first_name} {petty_cash.user.last_name} para el proyecto: {project.project if project else 'Unknown Project'}."
        mail.send(msg)

    # Submitter confirmation
    if submitter_email:
        msg = Message(
            subject="Su forma de Petty fue sometida exitosamente!",
            recipients=[submitter_email]
        )
        msg.body = f"Su forma de Petty Cash: {petty_cash.id} fue sometida exitosamente! Pronto se le estara revisando la forma para ser procesada. Favor de no descartar ningun recibo relacionado a esa forma de petty antes de que la forma se procese adecuadamente."
        mail.send(msg)

def notify_on_processed(petty_cash):
    first_item = petty_cash.pettycashitems[0] if petty_cash.pettycashitems else None
    project = first_item.project if first_item else None
    accounting_emails = ['accounting@pctmconstruction.com']
    submitter_email = petty_cash.user.email if petty_cash.user else None
    processor_email = petty_cash.processed_by.email if petty_cash.processed_by else None

    # Accounting notification
    if accounting_emails:
        msg = Message(
            subject=f"Petty Cash fue procesado ID {petty_cash.id}",
            recipients=accounting_emails
        )
        msg.body = f"Petty Cash ID {petty_cash.id} fue procesado por: {petty_cash.processed_by.first_name} para: {project.project if project else 'Unknown Project'}."
        mail.send(msg)

    # Submitter notification
    if submitter_email:
        msg = Message(
            subject=f"Su forma de Petty Cash fue procesada: {petty_cash.id}",
            recipients=[submitter_email]
        )
        msg.body = f"Su forma de Petty Cash: {petty_cash.id} fue procesada exitosamente por: {petty_cash.processed_by.first_name} para: {project.project if project else 'Unknown Project'}."
        mail.send(msg)

    # Processor confirmation
    if processor_email:
        msg = Message(
            subject=f"Usted acaba de procesar Petty Cash ID {petty_cash.id}",
            recipients=[processor_email]
        )
        msg.body = f"Ha procesado exitosamente al Petty Cash ID {petty_cash.id} que fue sometido por: {petty_cash.user.first_name} {petty_cash.user.last_name} para: {project.project if project else 'Unknown Project'}."
        mail.send(msg)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    
    return render_template("home.html", user = current_user)


@views.route('/equipment', methods=['GET', 'POST'])
@login_required
def equipment():
    if request.method == 'POST':
        equip_key = request.form.get('EquipKey')
        equips = request.form.get('EquipName')
        descrip = request.form.get('EquipDesc')


        if len(equips) < 1 or len(equip_key) < 8:
            flash('Escriba informacíon válida y completa.', category='error')
        else: 
            new_equip = Equip(name=equips, desc = descrip, equipKey=equip_key)
            db.session.add(new_equip)
            db.session.commit()
            flash("Equipo creato existosamente.", category='success')
    
    all_projects=Projects.query.all()
    search_query = request.args.get('equip', '')
    if search_query:
        equipments = Equip.query.filter(Equip.name.ilike(f"%{search_query}%")).all()
    else:
        equipments = Equip.query.all()
    return render_template("equipment.html", user = current_user, equipments=equipments, all_projects=all_projects)

@views.route('/dispatch', methods=['GET', 'POST'])
@login_required
def equip_dispatch():
    if request.method == 'POST':
        #print('Form data:', request.form)
        first_name = request.form.get('firstNameDispatch')
        last_name = request.form.get('lastNameDispatch')
        equipment_id = request.form.get('EquipUID')
        #print("selected eqipment id: ", equipment_id)
        project_id = request.form.get("project_id")
        
        if len(first_name) < 1 or len(last_name) < 1 or not project_id:
            flash('Escriba informacíon válida y completa.', category='error')
        else:
            equipment_id=int(equipment_id)
            new_disp = Dispatch(
                firstname=first_name,
                lastname=last_name,
                project_id=project_id,
                equipID=equipment_id
            )
            db.session.add(new_disp)
            #print("Saving dispatch with equipment ID:", equipment_id)
            #print("Dispatch object:", new_disp.__dict__)
            db.session.commit()
            flash("Despacho de equipo grabado exitosamente.", category='success')
            return redirect(url_for('views.equip_dispatch'))
    equipments = Equip.query.all()
    available_equipment = []
    for equip in equipments:
        last_dispatch=Dispatch.query.filter_by(equipID=equip.id).order_by(desc(Dispatch.date)).first()
        if not last_dispatch:
            available_equipment.append(equip)
            continue
        last_return = Return.query.filter_by(dispID=last_dispatch.id).order_by(desc(Return.date)).first()
        if last_return and last_return.date > last_dispatch.date:
            available_equipment.append(equip)
    all_dispatches = Dispatch.query.order_by(desc(Dispatch.date)).all()
    active_dispatches = []
    for disp in all_dispatches:
        has_return = Return.query.filter_by(dispID=disp.id).first()
        if not has_return:
            active_dispatches.append(disp)
    dispatches_active = active_dispatches
    dispatch_list = Dispatch.query.all()
    equip_avail = available_equipment
    all_projects=Projects.query.all()
    return render_template("dispatch.html", user = current_user, dispatch_list=dispatch_list, 
                           equipments=equipments, equip_avail=equip_avail, dispatches_active=dispatches_active, all_projects=all_projects)


@views.route('/return', methods=['GET', 'POST'])
@login_required
def equip_return():
    if request.method == 'POST':
        #print('Form data:', request.form)
        first_name = request.form.get('firstNameReturn')
        last_name = request.form.get('lastNameReturn')
        dispatch_id = request.form.get('DispID')
        #print("selected eqipment id: ", equipment_id)
        

        if len(first_name) < 1 or len(last_name) < 1 :
            flash('Escriba informacíon válida y completa.', category='error')
        else:
            dispatch_id = int(dispatch_id) 
            new_return = Return(
                firstname=first_name,
                lastname=last_name,
                dispID=dispatch_id
            )
            db.session.add(new_return)
            #print("Saving dispatch with equipment ID:", equipment_id)
            #print("Dispatch object:", new_disp.__dict__)
            db.session.commit()
            flash("Devolución de equipo fue grabado exitosamente", category='success')
            return redirect(url_for('views.equip_return'))
    dispatched = (db.session.query(Dispatch).outerjoin(Return).filter(Return.id.is_(None)).all())
    all_returns = Return.query.order_by(Return.date.desc()).all()
    all_projects=Projects.query.all()
    return_list = Return.query.all()
    return render_template("return.html", user = current_user, return_list=return_list, dispatched_items = dispatched, all_returns = all_returns, all_projects=all_projects)

@views.route('/status', methods=['GET'])
@login_required
def equipment_status():
    status_list = []
    all_equipment=Equip.query.all()
    for equip in all_equipment:
        all_dispatches=Dispatch.query.filter_by(equipID=equip.id).order_by(desc(Dispatch.date)).all()
        last_dispatch=all_dispatches[0] if all_dispatches else None
        if all_dispatches:
            dispatch_ids=[d.id for d in all_dispatches]
            last_return = Return.query.filter(Return.dispID.in_(dispatch_ids)).order_by(desc(Return.date)).first()
        else:
            last_return = None

        if not last_dispatch:
            status="Disponible"
            last_dispatch_date = None
            last_return_date= None
            project_id = None
        elif not last_return:
            status = "En el Field"
            last_dispatch_date = last_dispatch.date
            last_return_date = None
            project_id = last_dispatch.project
        elif last_return.date> last_dispatch.date:
            status = "Disponible"
            last_dispatch_date = last_dispatch.date
            last_return_date = last_return.date
            project_id = None
        else:
            status = "En el Field"
            last_dispatch_date = last_dispatch.date
            last_return_date= last_return.date
            project_id = last_dispatch.project


        status_list.append({
            'name': equip.name,
            'equipKey': equip.equipKey,
            'desc' : equip.desc,
            'status': status,
            'last_dispatch': last_dispatch_date,
            'last_return': last_return_date,
            'project': project_id
        })
    all_projects=Projects.query.all()
    return render_template('status.html', user=current_user, status_list=status_list, all_projects=all_projects)
    
@views.route('/daily_log', methods=['GET', 'POST'])
@login_required
def daily_log():
    if request.method == 'POST':
        files = request.files.getlist('images')
        project_id = request.form.get('project_id')
        notes = request.form.get('notes')

        if not files or not project_id:
            flash("Imagenes y proyecto son requeridos. Si el proyecto que busca no aparece en el listado, haga click en Crear proyecto.", category='error')
            return redirect(url_for('views.daily_log'))
        
        new_log = DailyLog(
            project_id = project_id,
            notes = notes,
            user_id = current_user.id
        )
        db.session.add(new_log)
        db.session.flush()

        UPLOAD_FOLDER = os.path.join(current_app.root_path, '..', 'static', 'logs')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename=f'{uuid.uuid4().hex}_{filename}'
                save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                #print("Current direc: ", os.getcwd())
                #print("Saving file to: ", save_path)
                file.save(save_path)
        
                new_image=Images(
                    filename=unique_filename,
                    filepath=save_path,
                    log_id=new_log.id)
                db.session.add(new_image)
    
        db.session.commit()
        flash("Log Diario ha sido grabado exitosamente.", category='success')
        return redirect(url_for('views.daily_log'))
    all_logs = DailyLog.query.all()
    sorted_logs = DailyLog.query.order_by(DailyLog.uploaded_at.desc()).all()
    all_projects = Projects.query.all()
    return render_template("daily_log.html", user=current_user, 
                           all_logs = all_logs, all_projects=all_projects,
                           sorted_logs=sorted_logs)

@views.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    if request.method == 'POST':
        project_name = request.form.get('Project')
        job_num = request.form.get('JobNumber')
        engineer_name = request.form.get('engineer')
        email= request.form.get('email')

        project = project_name.upper()
        engineer = engineer_name.upper()

        existing_job = Projects.query.filter_by(jobnumber=job_num).first()

        if not project_name or not job_num or not engineer_name or not email:
            flash("Entre información válida y completa.", category='error')
        elif existing_job: 
            flash("Proyecto ya existe.", category = 'error')
        else:
            try:
                new_proj = Projects(project=project, jobnumber=job_num, engineer=engineer, email=email)
                db.session.add(new_proj)
                db.session.commit()
                flash("Proyecto fue creado exitosamente.", category='success')
                return redirect(url_for('views.projects'))
            except Exception as e:
                flash("Hubo un error creando el proyecto deseado. Intente de nuevo.", category='error')
                
    projects_all = Projects.query.all()
    return render_template("projects.html", user=current_user, projects_all=projects_all)

@views.route('/check-log-file')
def check_log_file():
    filepath = os.path.join(current_app.root_path, '..', 'static', 'logs', 'IMG_0041.PNG')
    filepath = os.path.abspath(filepath)
    exists = os.path.isfile(filepath)
    return f"Checking: {filepath} — Exists: {exists}"

@views.route('/logs/<int:log_id>', methods=['GET'])
def log_detail(log_id):
    log = DailyLog.query.get(log_id)
    if not log:
        flash("Log diario no fue encontrado.", category='error')
        return redirect(url_for('views.daily_log')) 
    return render_template("dailylog_detail.html", user=current_user, log=log)

@views.route('/profile', methods=['GET'])
def profile():
    return render_template("profile.html", user=current_user)

@views.route('/delete-log', methods=['POST'])
def delete_log():
    data = request.get_json()
    log_id = data.get('LogId')

    if log_id:
        log = DailyLog.query.get(log_id)
        if log:
            db.session.delete(log)
            db.session.commit()
            flash("Log diario fue borrado exitosamente.", category='success')
            return jsonify({'success': True}), 200
        else:
            flash("Hubo un error borrando el log diario. Intente de nuevo", category='error')
            return jsonify({'error': 'Log not found'}), 404
    return jsonify({'error': 'Invalid request'}), 400

@views.route('/trainings', methods=['GET', 'POST'])
@login_required
def training():
    if request.method == 'POST':
        training = request.form.get('Training')
        
        training_name = training.upper()

        existing_training = Training.query.filter_by(name=training_name).first()

        if not training_name:
            flash("Entra informacion valida.", category='error')
        elif existing_training: 
            flash("Adiestramiento ya existe.", category = 'error')
        else:
            try:
                new_training = Training(name = training_name)
                db.session.add(new_training)
                db.session.commit()
                flash("Adiestramiento creado!", category='success')
                
            except Exception as e:
                db.session.rollback()
                flash("Adiestramiento no fue creado", category='error')
            else: 
                return redirect(url_for('views.training'))
                
    trainings_all = Training.query.all()
    return render_template("trainings.html", user=current_user, trainings_all = trainings_all)

@views.route('/trainings_log', methods=['GET', 'POST'])
@login_required
def training_log():
    if request.method == 'POST':
        update_id = request.form.get('update_id')

        #  Handle UPDATE of training log date
        if update_id:
            train_log = TrainingLog.query.get_or_404(update_id)
            if current_user.group not in ['admin','manager']:  # Optional permissions
                flash("No tienes permiso para actualizar.", category='error')
                return redirect(url_for('views.training_log'))

            new_date = request.form.get('date')
            try:
                train_log.date = datetime.strptime(new_date, '%Y-%m-%d').date()
                db.session.commit()
                flash("Fecha actualizada exitosamente.", category='success')
            except Exception as e:
                print(e)
                flash("Error al actualizar la fecha.", category='error')
            return redirect(url_for('views.training_log'))

        # Handle NEW training log creation
        docs = request.files.getlist('docs')
        name = request.form.get('Name')
        training_id = request.form.get('training_id')
        date = request.form.get('Date')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash("Fecha inválida.", category='error')
            return redirect(url_for('views.training_log'))

        if not name or not training_id or not date:
            flash("La información completa es requerida.", category='error')
            return redirect(url_for('views.training_log'))

        docs_status = "N/A"
        new_train_log = TrainingLog(
            training_id=training_id,
            name_id=name,
            date=date_obj,
            user_id=current_user.id,
            docs_summary=docs_status
        )
        db.session.add(new_train_log)
        db.session.flush()

        uploaded_any = False
        if docs:
            UPLOAD_FOLDER = os.path.join(current_app.root_path, '..', 'static', 'train')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            for file in docs:
                if file and file.filename:
                    uploaded_any = True
                    filename = secure_filename(file.filename)
                    unique_filename = f'{uuid.uuid4().hex}_{filename}'
                    save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(save_path)

                    new_docs = Traindocs(
                        filename=unique_filename,
                        filepath=save_path,
                        train_log_id=new_train_log.id)
                    db.session.add(new_docs)

        if uploaded_any:
            new_train_log.docs_summary = "Documents uploaded"
        db.session.commit()
        flash("Documentos han sido sometidos!", category='success')
        return redirect(url_for('views.training_log'))
    all_train_logs = TrainingLog.query.all()
    trainings_all = Training.query.all()
    
    names_list = Names.query.all()
    return render_template("training_log.html", user=current_user, names_list=names_list,
                           all_train_logs = all_train_logs, trainings_all = trainings_all)

@views.route('/trainings_logs/<int:train_log_id>', methods=['GET'])
def train_log_detail(train_log_id):
    train_log = TrainingLog.query.get(train_log_id)
    if not train_log:
        flash("Log not found.", category='error')
        return redirect(url_for('views.training_log')) 
    return render_template("trainlog_detail.html", user=current_user, train_log=train_log)

@views.route('/equip_seguridad', methods=['GET', 'POST'])
@login_required
def equip_seguridad():
    if request.method == 'POST':
        update_id = request.form.get('update_id')

        #  Handle UPDATE of QTY
        if update_id:
            equip_seg= EquipSeguridad.query.get_or_404(update_id)
            if current_user.group not in ['admin','manager']:  # Optional permissions
                flash("No tienes permiso para actualizar.", category='error')
                return redirect(url_for('views.equip_seguridad'))

            new_qty = request.form.get('qty')
            try:
                equip_seg.qty += int(new_qty)
                db.session.commit()
                flash("Cantidad actualizada exitosamente.", category='success')
            except Exception as e:
                print(e)
                flash("Error al actualizar la cantidad.", category='error')
            return redirect(url_for('views.equip_seguridad'))

        # Handle NEW equip creation
        name = request.form.get('EquipSegName')
        qty = request.form.get('QTY')
        unit = request.form.get('UNIT')
        name_upper = name.upper()
        if not name or not qty or not unit:
            flash("La información completa es requerida.", category='error')
            return redirect(url_for('views.equip_seguridad'))

       
        new_equip_seg = EquipSeguridad(name=name_upper, qty=qty, unit=unit)
        db.session.add(new_equip_seg)
        db.session.commit()
        flash("Equipo de Seguridad añadido!", category='success')
        return redirect(url_for('views.equip_seguridad'))
    all_equip_seg = EquipSeguridad.query.all()
    return render_template("equip_seguridad.html", user = current_user, all_equip_seg=all_equip_seg)

@views.route('/equip_seguridad_disp', methods=['GET', 'POST'])
@login_required
def equip_seguridad_disp():
    if request.method == 'POST':
        qty_disp = request.form.get('qty')
        equipment_id = request.form.get('EquipSegID')
        project_id = request.form.get('ProjectID')
        equipment_id_int=int(equipment_id)
        project_id_int=int(project_id)
        
        try: 
            qty_disp = int(qty_disp)
            if qty_disp <= 0:
                flash("Cantidad despachada debe ser mayor que cero.", category='error')
                return redirect(url_for('views.equip_seguridad_disp'))
            all_equip_seg = EquipSeguridad.query.get_or_404(equipment_id_int)
            if all_equip_seg.qty < qty_disp:
                flash("No hay suficiente cantidad para despachar.", category='error')
                return redirect(url_for('views.equip_seguridad_disp'))
            all_equip_seg.qty -= qty_disp
            
            new_equip_seg_disp = EquipSeguridadDisp( qty = qty_disp, equip_id = equipment_id_int, project_id = project_id_int, user_id=current_user.id)
            db.session.add(new_equip_seg_disp)
           
            db.session.commit()
            flash("Despacho de Equipo de Seguridad gracado!", category='success')
            return redirect(url_for('views.equip_seguridad_disp'))
        except Exception as e:
            print(e)
            flash("Ocurrió un error al despachar el equipo.", category='error')
    all_equip_seg = EquipSeguridad.query.all()
    all_equip_seg_disp = EquipSeguridadDisp.query.all()
    all_projects = Projects.query.all()
    sorted_dispatches = EquipSeguridadDisp.query.order_by(EquipSeguridadDisp.date.desc()).all()
    return render_template("equip_seg_disp.html", user = current_user, all_equip_seg = all_equip_seg, all_equip_seg_disp = all_equip_seg_disp, all_projects = all_projects, sorted_dispatches = sorted_dispatches)

@views.route('/equip_seguridad_estatus', methods=['GET'])
@login_required
def equip_seguridad_estatus():
    all_equip_seg = EquipSeguridad.query.all()
    return render_template('equip_seg_estatus.html', user=current_user, all_equip_seg = all_equip_seg)

@views.route('/incidentes', methods=['GET', 'POST'])
@login_required
def incidentes():
    if request.method == 'POST':
        docs = request.files.getlist('docs')
        name_id = request.form.get('Name')
        project_id = request.form.get('project_id')
        date = request.form.get('Date')
        project_id_int=int(project_id)
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash("Fecha inválida.", category='error')
            return redirect(url_for('views.training_log'))

        if not name_id or not project_id or not date:
            flash("La información completa es requerida.", category='error')
            return redirect(url_for('views.training_log'))

        
        new_incident = Incidentes(
            project_id=project_id_int,
            name_id=name_id,
            date=date_obj,
            user_id=current_user.id)
        
        db.session.add(new_incident)
        db.session.flush()

        
        if docs:
            UPLOAD_FOLDER = os.path.join(current_app.root_path, '..', 'static', 'incident')
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            for file in docs:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f'{uuid.uuid4().hex}_{filename}'
                    save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(save_path)

                    new_docs = Incidentesdocs(
                        filename=unique_filename,
                        filepath=save_path,
                        incidentes_id=new_incident.id)
                    db.session.add(new_docs)

        db.session.commit()
        flash("Incidente ha sido grabado!", category='success')
        return redirect(url_for('views.incidentes'))
    all_incidents = Incidentes.query.all()
    sorted_incidents = Incidentes.query.order_by(Incidentes.date.desc()).all()
    names_list = Names.query.all()
    all_projects=Projects.query.all()
    return render_template("incidentes.html", user=current_user, names_list=names_list, all_incidents = all_incidents, sorted_incidents = sorted_incidents, all_projects = all_projects)

@views.route('/pettycash', methods=['POST', 'GET'])
@login_required
def pettycash():
    all_pettys = PettyCash.query.all()
    my_requests = PettyCash.query.filter_by(user_id=current_user.id).order_by(PettyCash.id.desc()).all()
    return render_template('pettycash.html', user=current_user, 
                           all_pettys = all_pettys, my_requests=my_requests)

@views.route('/pettycash/new', methods=['POST', 'GET'])
@login_required
def create_pettycash():
    
    if request.method == 'POST':
        new_petty = PettyCash(user_id=current_user.id, status='No Completado')
        db.session.add(new_petty)
        db.session.commit()
        
        return redirect(url_for('views.edit_pettycash', petty_id=new_petty.id))
    all_pettys = PettyCash.query.all()
    all_projects=Projects.query.all()
    return render_template('pettycash.html', user=current_user, all_pettys = all_pettys, all_projects=all_projects)

@views.route('/pettycash/<int:petty_id>/edit', methods=['GET','POST'])
@login_required
def edit_pettycash(petty_id):
    petty = PettyCash.query.get_or_404(petty_id)
    items = PettyCashItems.query.filter_by(pettycash_id=petty.id).all()
    all_projects = Projects.query.all()
    return render_template('edit_pettycash.html', petty=petty, items=items, all_projects=all_projects, user=current_user)


@views.route('/pettycash/<int:petty_id>/items', methods=['GET','POST'])
@login_required
def update_pettycash_items(petty_id):
    petty = PettyCash.query.get_or_404(petty_id)
    # Extract form lists (same as before)
    item_ids = request.form.getlist('item_id[]')
    dates = request.form.getlist('date[]')
    paid_tos = request.form.getlist('paid_to[]')
    materials = request.form.getlist('material[]')
    descriptions = request.form.getlist('description[]')
    quantities = request.form.getlist('quantity[]')
    project_ids = request.form.getlist('project_id[]')
    new_indexes = request.form.getlist('new_index[]')

    try:
        for i in range(len(dates)):
            if not dates[i]:
                continue

            date_obj = datetime.strptime(dates[i], '%Y-%m-%d').date()
            qty = float(quantities[i]) if quantities[i] else 0.0
            project_id = int(project_ids[i]) if project_ids[i] else None

            existing_item_id = item_ids[i]
            if existing_item_id:
                # Update existing
                item = PettyCashItems.query.get(int(existing_item_id))
                if item and item.pettycash_id == petty.id:
                    item.date = date_obj
                    item.paid_to = paid_tos[i]
                    item.material = materials[i]
                    item.description = descriptions[i]
                    item.quantity = qty
                    item.project_id = project_id

                    # Handle file for existing item
                    file_field = f'docs_item_{item.id}'
                    file = request.files.get(file_field)
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(current_app.root_path, '..', 'static', 'pettycash', filename)
                        file.save(filepath)

                        doc = PettyCashItemsDocs(
                            filename=filename,
                            filepath=filepath,
                            pettycashitem_id=item.id
                        )
                        db.session.add(doc)

            else:
                # New item
                item = PettyCashItems(
                    date=date_obj,
                    paid_to=paid_tos[i],
                    material=materials[i],
                    description=descriptions[i],
                    quantity=qty,
                    project_id=project_id,
                    pettycash_id=petty.id
                )
                db.session.add(item)
                db.session.flush()

                 # Get correct new index to look for file
                if i < len(new_indexes):
                    new_index = new_indexes[i]
                    file_field = f'docs_new_{new_index}'
                    file = request.files.get(file_field)

                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(current_app.root_path, '..', 'static', 'pettycash', filename)
                        file.save(filepath)

                        doc = PettyCashItemsDocs(
                            filename=filename,
                            filepath=filepath,
                            pettycashitem_id=item.id
                        )
                        db.session.add(doc)

               
           
        petty.update_total()
        db.session.commit()
        # Determine which button was clicked
        action = request.form.get('action')

        # Only allow status change if it's still 'No Completado'
        if petty.status == "No Completado":
            if action == "submit":
                petty.status = "Sometido"
                db.session.commit()
                notify_on_submission(petty)
            else:
                petty.status = "No Completado"  
                db.session.commit()# Optional, just to be explicit
        flash("Petty Cash items updated successfully.", "success")        
        
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating items: {str(e)}", "danger")

    return redirect(url_for('views.pettycash', petty_id=petty.id, user=current_user))


@views.route('/pettycash/<int:petty_id>/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_pettycash_item(petty_id, item_id):
    petty = PettyCash.query.get_or_404(petty_id)
    item = PettyCashItems.query.get_or_404(item_id)
    if item.pettycash_id != petty.id:
        flash("Item does not belong to this petty cash.", "danger")
        return redirect(url_for('views.edit_pettycash', petty_id=petty.id))

    try:
        # Delete docs and files related to this item first
        for doc in item.docs:
            try:
                os.remove(os.path.join(current_app.root_path, '..', 'static', 'pettycash', doc.filename))
            except FileNotFoundError:
                pass
            db.session.delete(doc)

        db.session.delete(item)
        petty.update_total()
        db.session.commit()
        flash("Item deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", "danger")

    return redirect(url_for('views.edit_pettycash', petty_id=petty.id, user=current_user))



@views.route('/pettycash/<int:petty_id>/items/<int:item_id>/docs/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_pettycash_item_doc(petty_id, item_id, doc_id):
    # Step 1: Fetch the petty cash and document
    petty = PettyCash.query.get_or_404(petty_id)
    item = PettyCashItems.query.get_or_404(item_id)
    doc = PettyCashItemsDocs.query.get_or_404(doc_id)

    # Step 2: Permission check — is everything related properly?
    if item.pettycash_id != petty.id or doc.pettycashitem_id != item.id:
        flash("Invalid document or item relationship.", "danger")
        return redirect(url_for('views.edit_pettycash', petty_id=petty_id))

    # Step 3: Delete the file from disk
    try:
        full_path = os.path.join(current_app.root_path, '..', 'static', 'pettycash', doc.filename)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", "warning")

    # Step 4: Delete from DB
    try:
        db.session.delete(doc)
        db.session.commit()
        flash("Document deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Database error while deleting doc: {str(e)}", "danger")

    return redirect(url_for('views.edit_pettycash', petty_id=petty_id, user=current_user))

@views.route('/pettycash/accounting')
@login_required
def pettycash_accounting():
    if current_user.group not in ['admin', 'manager']:
        flash("Acceso denegado", category='error')
        return redirect(url_for('views.home'))
    project_id = request.args.get("project_id", type=int)

    submitted_query = PettyCash.query.filter_by(status='Sometido').order_by(PettyCash.id.desc())
    processed_query=PettyCash.query.filter_by(status='Procesado').order_by(PettyCash.id.desc())
    if project_id:
        submitted_query = (
            submitted_query.join(PettyCash.pettycashitems)
                           .filter(PettyCashItems.project_id == project_id)
        )
        processed_query = (
            processed_query.join(PettyCash.pettycashitems)
                           .filter(PettyCashItems.project_id == project_id)
        )

    submitted_pettys = submitted_query.all()
    processed_pettys = processed_query.all()
    all_pettys = PettyCash.query.all()
    all_projects = Projects.query.all()
    return render_template('petty_all.html', submitted_pettys=submitted_pettys, user=current_user, all_pettys=all_pettys, all_projects = all_projects, processed_pettys=processed_pettys)

@views.route('/pettycash/<int:petty_id>/review', methods=['GET', 'POST'])
@login_required
def review_pettycash(petty_id):
    if current_user.group not in ['admin', 'manager']:
        flash("Acceso denegado", category='error')
        return redirect(url_for('views.home'))

    petty = PettyCash.query.get_or_404(petty_id)
    items = PettyCashItems.query.filter_by(pettycash_id=petty.id).all()

    if request.method == 'POST':
        #print("Form action:", request.form.get('action'))
        #print("Form keys:", request.form.keys())
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')

        for idx, item_id in enumerate(item_ids):
            item = PettyCashItems.query.get(int(item_id))
            if item and item.pettycash_id == petty.id:
                try:
                    item.quantity = float(quantities[idx])
                except ValueError:
                    item.quantity = 0.0  # Or handle invalid input as needed
        # Recalculate total after updating all items
        total = sum(item.quantity for item in petty.pettycashitems)
        petty.total_amount = total

        petty.review_notes = request.form.get('review_notes', '') 
        #print("Notas recibidas:", request.form.get('review_notes'))

        # Handle status update
        if request.form.get('action') == 'mark_processed':
            petty.status = 'Procesado'
            petty.processed_date = datetime.utcnow()
            petty.processed_by = current_user
            
            db.session.commit()
            petty_id=petty
            notify_on_processed(petty)
            flash("Solicitud marcada como procesada.", "success")
            return redirect(url_for('views.pettycash_accounting'))

        # Handle file deletion and replacements
        for item in items:
            # Deleting old files
            delete_doc_ids = request.form.getlist(f'delete_docs_{item.id}[]')
            for doc_id in delete_doc_ids:
                doc = PettyCashItemsDocs.query.get(int(doc_id))
                if doc:
                    try:
                        os.remove(os.path.join(current_app.root_path, '..', 'static', 'pettycash', doc.filename))
                    except FileNotFoundError:
                        pass
                    db.session.delete(doc)

            # Upload new file(s)
            files = request.files.getlist(f'docs_item_{item.id}')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(current_app.root_path, '..', 'static', 'pettycash', filename)
                    file.save(filepath)

                    new_doc = PettyCashItemsDocs(
                        filename=filename,
                        filepath=filepath,
                        pettycashitem_id=item.id
                    )
                    db.session.add(new_doc)

        db.session.commit()
        flash("Archivos actualizados correctamente.", "success")
        return redirect(url_for('views.pettycash_accounting', petty_id=petty.id))
    all_projects = Projects.query.all()
    return render_template('review_pettycash.html', petty=petty, items=items, user=current_user, all_projects=all_projects)

@views.route('/pettycash/<int:petty_id>/view', methods=['GET', 'POST'])
@login_required
def view_pettycash(petty_id):
    if current_user.group not in ['admin', 'manager']:
        flash("Acceso denegado", category='error')
        return redirect(url_for('views.home'))

    petty = PettyCash.query.get_or_404(petty_id)
    items = PettyCashItems.query.filter_by(pettycash_id=petty.id).all()
    all_projects = Projects.query.all()

    return render_template('view_pettycash.html', petty=petty, items=items, user=current_user, all_projects=all_projects)

@views.route('/pettycash/<int:petty_id>/pdf')
@login_required
def generate_petty_pdf(petty_id):
    petty = PettyCash.query.get_or_404(petty_id)
    items = petty.pettycashitems
    all_projects = Projects.query.all()

    html = render_template('print_pettycash.html', petty=petty, items=items, user=current_user, all_projects=all_projects)
    # Set base_url so that relative paths work (for images, CSS, etc.)
    pdf = HTML(string=html, base_url=current_app.root_path).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=PettyCash_{petty.petty_num}.pdf'
    return response

ENGINEER_MAP = {
    'carl.paez1': 'CARLOS PAEZ',
    'aman.marr1': 'AMANDA MARRERO',
    'mark.smith': 'Mark Smith'
}

@views.route('/pending_approvals')
@login_required
def pending_approvals():
    # Map the current logged-in user to an engineer name
    engineer_name = ENGINEER_MAP.get(current_user.username)

    if not engineer_name:
        flash("Usuario no es ENG.")
        return redirect(url_for('views.home'))

    # Find projects managed by this engineer
    engineer_projects = Projects.query.filter_by(engineer=engineer_name).all()
    project_ids = [p.id for p in engineer_projects]

    # Get all PettyCashItems linked to those projects
    items = PettyCashItems.query.options(joinedload(PettyCashItems.petty_cash))\
        .filter(PettyCashItems.project_id.in_(project_ids)).all()

    # Extract unique petty cash requests with status 'Submitted'
    pettycash_requests = {
        item.petty_cash for item in items
        if item.petty_cash and item.petty_cash.status == 'Sometido'
    }
    pettycash_approved = {
        item.petty_cash for item in items
        if item.petty_cash and item.petty_cash.status == 'Procesado'
    }
    all_projects = Projects.query.all()
    return render_template('eng_petty.html', petty_requests=sorted(pettycash_requests, key=lambda p: p.date, reverse=True), user=current_user, petty_processed=sorted(pettycash_approved, key=lambda p:p.date, reverse=True), all_projects = all_projects)

@views.route('/materials', methods=['GET'])
@login_required
def material_status():
    # NEW: Handle search
    search_term = request.args.get('q')
    if search_term:
        all_materials = Materials.query.filter(Materials.material_name.ilike(f'%{search_term}%')).all()
        
    else:
        all_materials = Materials.query.all()
    
    all_projects=Projects.query.all()
    return render_template("materiales_estatus.html", user = current_user, all_materials=all_materials, all_projects=all_projects)

@views.route('/materials/new', methods=['GET', 'POST'])
@login_required
def materials():
    if request.method == 'POST':

        update_id = request.form.get('update_id')

        #  Handle UPDATE of QTY
        if update_id:
            material= Materials.query.get_or_404(update_id)
            if current_user.group not in ['admin','manager']:  # Optional permissions
                flash("No tienes permiso para actualizar.", category='error')
                return redirect(url_for('views.materials_status'))

            new_qty = request.form.get('qty_new')
            location = request.form.get('loc_new')
            try:
                material.qty += int(new_qty)
                material.replenished_date = datetime.utcnow()
                material.user_id = current_user.id
                material.loc = location
                db.session.commit()
                flash("Informacion actualizada exitosamente.", category='success')
            except Exception as e:
                print(e)
                flash("Error al actualizar la cantidad.", category='error')
            return redirect(url_for('views.materials'))

        material = request.form.get('MaterialName')
        dimensions = request.form.get('Dimensions')
        qty_raw = request.form.get('quantity')
        
        unit = request.form.get('Unit')
        loc = request.form.get("Location")
        
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            qty = 0
        material_name=material.upper()

        exist_mat = Materials.query.filter(Materials.material_name == material_name).first()

        if exist_mat: 
            flash("Ya existe ese material en el listado.", category = 'error')
        elif len(material_name) < 1 or len(dimensions) < 1 or qty < 1:
            flash('Escriba informacíon válida y completa.', category='error')
        else: 
            new_mat = Materials(material_name=material_name, dimensions=dimensions, qty=qty, loc=loc, unit=unit,  user_id=current_user.id)
            db.session.add(new_mat)
            db.session.commit()
            flash("Material creato existosamente.", category='success')
    
    all_materials = Materials.query.all()
    all_projects=Projects.query.all()
    return render_template("materiales.html", user = current_user, all_materials=all_materials, all_projects=all_projects)

@views.route('/materials/disp', methods=['GET', 'POST'])
@login_required
def material_dispatch():
    if request.method == 'POST':
        #print('Form data:', request.form)
        first_name = request.form.get('FirstName')
        last_name = request.form.get('LastName')
        project_ID = request.form.get('ProjectID')
        material_ID = request.form.get("MaterialID")
        Quantity = request.form.get("DispQuantity")
        firstname=first_name.upper()
        lastname=last_name.upper()
        project_id=int(project_ID)
        material_id=int(material_ID)
        

        try:
            disp_qty=int(Quantity)
            if len(first_name) < 1 or len(last_name) < 1 or not project_ID or not material_ID:
                flash('Escriba informacíon válida y completa.', category='error')
                return redirect(url_for('views.material_dispatch'))
            if disp_qty <=0:
                flash('Cantidad despachada debe ser mayor que cero.', category='error')
                return redirect(url_for('views.material_dispatch'))
            material = Materials.query.get_or_404(material_id)
            if disp_qty > material.qty:
                flash('Esa cantidad es mas de la que hay disponible. Entre otra cantidad.', category='error')
            material.qty -= disp_qty
          
            mat_disp = MaterialsDisp(
                firstname=firstname,
                lastname=lastname,
                project_id=project_id,
                materialID=material_id,
                disp_qty=disp_qty,
                user_id=current_user.id
            )
            db.session.add(mat_disp)
            db.session.commit()
            flash("Despacho de material grabado exitosamente.", category='success')
            return redirect(url_for('views.material_status'))
        except Exception as e:
            print(e)
            flash("Ocurrió un error al despachar el equipo.", category='error')
        material = Materials.query.get_or_404(material_id)

    
        
    all_mat_disp = MaterialsDisp.query.order_by(MaterialsDisp.date.desc()).all()
    all_projects=Projects.query.all()
    all_materials = Materials.query.all()
    return render_template("material_dispatch.html", user = current_user, all_mat_disp=all_mat_disp, all_materials=all_materials, all_projects=all_projects)

@views.route('/materials/<int:mat_id>', methods=['GET'])
def material_detail(mat_id):
    mat = Materials.query.get_or_404(mat_id)  # ✅ Get the material, not a dispatch

    all_mat_disp = MaterialsDisp.query.filter_by(materialID=mat.id).order_by(MaterialsDisp.date.desc()).all()


    return render_template("material_detail.html", user=current_user, mat=mat, all_mat_disp=all_mat_disp)