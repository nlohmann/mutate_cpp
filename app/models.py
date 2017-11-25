# coding=utf-8

from app import db
from sqlalchemy.sql import func


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    workdir = db.Column(db.Text)
    build_command = db.Column(db.Text)
    quickcheck_command = db.Column(db.Text, nullable=True)
    quickcheck_timeout = db.Column(db.Float, nullable=True)
    test_command = db.Column(db.Text)
    test_timeout = db.Column(db.Float, nullable=True)
    clean_command = db.Column(db.Text, nullable=True)
    files = db.relationship('File', backref='project', lazy='dynamic', cascade='delete')
    patches = db.relationship('Patch', backref='project', lazy='dynamic', cascade='delete')

    def __repr__(self):
        return '<Project %r>' % self.name

    @property
    def findings(self):
        return self.patches.filter(Patch.state == 'survived').count()

    @property
    def last_finding(self):
        return self.patches.filter(Patch.state == 'survived').order_by(Patch.id.desc()).first().runs[-1].timestamp_end


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    content = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), index=True)
    patches = db.relationship('Patch', backref='file', lazy='dynamic', cascade='delete')

    def __repr__(self):
        return '<File %r>' % self.filename


class Patch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Text)
    line = db.Column(db.Integer)
    column_start = db.Column(db.Integer)
    column_end = db.Column(db.Integer)
    code_original = db.Column(db.Integer)
    code_replacement = db.Column(db.Integer)
    patch = db.Column(db.Text)
    state = db.Column(db.Text)
    confirmation = db.Column(db.Text)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), index=True)
    runs = db.relationship('Run', backref='patch', lazy='dynamic', cascade='delete')

    def __repr__(self):
        return '<Patch %r>' % self.id

    @property
    def killed_stage(self):
        """return the first unsuccessful run's command"""
        # noinspection PyPep8
        return self.runs.filter(Run.success == False).first().command

    @property
    def runtime(self):
        return self.runs.with_entities(func.sum(Run.duration)).scalar()


class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp_start = db.Column(db.DateTime)
    timestamp_end = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    command = db.Column(db.Text)
    success = db.Column(db.Boolean)
    log = db.Column(db.Text)
    output = db.Column(db.Text)
    patch_id = db.Column(db.Integer, db.ForeignKey('patch.id'), index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), index=True)

    def __repr__(self):
        return '<Run %r>' % self.id
