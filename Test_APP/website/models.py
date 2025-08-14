from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique = True)
    username = db.Column(db.String(10), unique = True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    group = db.Column(db.String(50), default='standard')
    

class Equip(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    equipKey = db.Column(db.String(8))
    name = db.Column(db.String(50))
    desc = db.Column(db.String(150))
    disp = db.relationship("Dispatch", backref='Equip', lazy=True)
    
    
    
class Dispatch(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='dispatch')
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    equipID = db.Column(db.Integer, db.ForeignKey('equip.id'), nullable=False)


class Return(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    dispID = db.Column(db.Integer, db.ForeignKey('dispatch.id'), nullable=False)
    dispatch = db.relationship("Dispatch", backref='returns')

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=func.now())
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='daily_log')
    notes = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref = 'daily_log')
    images = db.relationship('Images', backref = 'daily_log')

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    log_id = db.Column(db.Integer, db.ForeignKey('daily_log.id'))

class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project= db.Column(db.String(100), nullable = False)
    jobnumber = db.Column(db.String(10))
    engineer = db.Column(db.String(150))
    email=db.Column(db.String(150))

class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(100), nullable = False)

class TrainingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_id = db.Column(db.Integer, db.ForeignKey('names.id'), nullable=False)
    name = db.relationship('Names', backref = 'names')
    training_id = db.Column(db.Integer, db.ForeignKey('training.id'), nullable=False)
    training_name = db.relationship('Training', backref='training_log')
    date = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref = 'training_log')
    docs_summary = db.Column(db.String(100), nullable=False)
    traindocs = db.relationship('Traindocs', backref='training_log', lazy=True)

class Traindocs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    train_log_id = db.Column(db.Integer, db.ForeignKey('training_log.id'))

class Names(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(100), nullable = False)

class EquipSeguridad(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    qty = db.Column(db.Integer)
    unit = db.Column(db.String(0))
    
class EquipSeguridadDisp(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    qty = db.Column(db.Integer)
    equip_id = db.Column(db.Integer, db.ForeignKey('equip_seguridad.id'), nullable=False)
    equipseguridad_name = db.relationship('EquipSeguridad', backref='equip_seguridad_disp')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='equip_seguridad_disp')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref = 'equip_seguridad_disp')
    date = db.Column(db.DateTime(timezone=True), default=func.now())

class Incidentes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_id = db.Column(db.Integer, db.ForeignKey('names.id'), nullable=False)
    name = db.relationship('Names', backref = 'incidentes')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='incidentes')
    date = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref = 'incidentes')
    indidentesdocs = db.relationship('Incidentesdocs', backref='incidentesdocs', lazy=True)

class Incidentesdocs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    incidentes_id = db.Column(db.Integer, db.ForeignKey('incidentes.id'))

class PettyCash(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    petty_num = db.Column(db.String(10), nullable=False, unique=True)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='petty_cash')
    total_amount = db.Column(db.Float, default=0.0)   # ✅ ADD THIS HERE
    status = db.Column(db.String(20), default='No Completado')  # ✅ Optional status field

    processed_date = db.Column(db.DateTime(timezone=True), nullable=True)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])
    review_notes = db.Column(db.Text, nullable=True)

    pettycashitems = db.relationship('PettyCashItems', backref='petty_cash', cascade="all, delete-orphan")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.petty_num = self.generate_petty_num()
    
    def update_total(self):
        self.total_amount = sum(item.quantity or 0 for item in self.pettycashitems)

    @staticmethod
    def generate_petty_num():
        # Count existing entries (can be filtered by year/month if desired)
        count = db.session.query(PettyCash).count() + 1
        return f"PC-{count:03d}"  # PC-001, PC-002, ...

class PettyCashItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(timezone=True))
    paid_to = db.Column(db.String(50), nullable=False)
    material = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='petty_cash_items')
    pettycash_id = db.Column(db.Integer, db.ForeignKey('petty_cash.id'), nullable=False)
    

class PettyCashItemsDocs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    pettycashitem_id = db.Column(db.Integer, db.ForeignKey('petty_cash_items.id'), nullable=False)
    item = db.relationship("PettyCashItems", backref="docs")

class Materials(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    material_name = db.Column(db.String(50))
    dimensions = db.Column(db.String(50))
    qty = db.Column(db.Integer)
    unit = db.Column(db.String(10))
    loc = db.Column(db.String(30))
    replenished_date = db.Column(db.DateTime(timezone=True), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='materials')

class MaterialsDisp(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Projects', backref='materialdispatch')
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    materialID = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    material = db.relationship('Materials', backref='materialdispatch')
    disp_qty = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='materialdispatch')
    

