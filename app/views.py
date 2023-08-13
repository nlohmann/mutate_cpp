# coding=utf-8

from flask import render_template, abort, redirect, url_for, flash, request
from app import app, db
from app.forms import CreateProjectForm, CreateFileForm, SetConfirmationForm
from app.models import Project, File, Patch, Run
from app.utils.SourceFile import SourceFile
from app.utils.Mutation import get_mutators
from app.utils.Statistics import Statistics
import os
from app.utils.Executor import Executor

executor = None


@app.before_first_request
def init_executor():
    global executor
    executor = Executor(app)


##############################################################################
# Jinja
##############################################################################

@app.template_filter()
def basename(text):
    return os.path.basename(text)


@app.template_filter()
def striptext(text):
    if type(text) != str:
        return text
    return text.strip()


@app.template_filter()
def command_icon(command):
    if command == 'build_command':
        return '<i class="text-muted fa fa-cog">'
    elif command == 'quickcheck_command':
        return '<i class="text-muted fa fa-search">'
    elif command == 'test_command':
        return '<i class="text-muted fa fa-search-plus">'
    else:
        return command


@app.context_processor
def inject_values():
    return {
        'mutators': get_mutators(),
        'executor': executor,
        'stats': Statistics()
    }


##############################################################################
# Routes
##############################################################################

@app.route('/')
def route_v2_root():
    return render_template('v2_index.html')


@app.route('/projects')
def route_v2_projects():
    projects = Project.query.all()
    return render_template('v2_projects.html', projects=projects)


@app.route('/queue')
def route_v2_queue():
    # retrieve parameters
    page = int(request.args.get('page', 1))

    # initial patch query
    patches = Patch.query.filter(Patch.state == 'incomplete')

    # add pagination
    patches = patches.paginate(page, app.config['ITEMS_PER_PAGE'], False)

    return render_template('v2_queue.html', patches=patches)


@app.route('/queue/start')
def route_v2_queue_start():
    executor.start()
    return redirect(url_for('route_v2_queue'))


@app.route('/queue/stop')
def route_v2_queue_stop():
    executor.stop()
    return redirect(url_for('route_v2_queue'))


@app.route('/projects/create', methods=['GET', 'POST'])
def route_v2_projects_create():
    form = CreateProjectForm()

    if form.validate_on_submit():
        project = Project(name=form.name.data,
                          workdir=form.workdir.data,
                          build_command=form.build_command.data,
                          quickcheck_command=form.quickcheck_command.data,
                          quickcheck_timeout=form.quickcheck_timeout.data,
                          test_command=form.test_command.data,
                          test_timeout=form.test_timeout.data,
                          clean_command=form.clean_command.data)
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('route_v2_project_project_id', project_id=project.id))

    for field, error_msg in form.errors.items():
        flash('Error in field "{field}": {error_msg}'.format(
            field=field,
            error_msg=' '.join(error_msg)
        ), category='error')

    return render_template('v2_create_project.html', form=form)


@app.route('/projects/<int:project_id>')
def route_v2_project_project_id(project_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)
    else:
        return render_template('v2_project.html', project=project)


@app.route('/projects/<int:project_id>/delete')
def route_v2_project_project_id_delete(project_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)
    else:
        db.session.delete(project)
        db.session.commit()

        flash('Project {name} successfully delete.'.format(name=project.name),
              category='message')

        return redirect(url_for('route_v2_projects'))


@app.route('/projects/<int:project_id>/files/add', methods=['GET', 'POST'])
def route_v2_project_project_id_files_add(project_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    form = CreateFileForm()
    if form.validate_on_submit():
        try:
            filename = form.filename.data

            file_content = open(filename, encoding='utf-8').read()

            file = File(filename=filename,
                        content=file_content,
                        project_id=project.id)
            db.session.add(file)
            db.session.commit()

            flash('File <samp>{filename}</samp> successfully added to project.'.format(filename=file.filename),
                  category='message')

            return redirect(url_for('route_v2_project_project_id', project_id=project.id))

        except FileNotFoundError:
            flash('File <samp>{filename}</samp> not found.'.format(filename=form.filename.data), category='error')

    for field, error_msg in form.errors.items():
        flash('Error in field "{field}": {error_msg}'.format(
            field=field,
            error_msg=' '.join(error_msg)
        ), category='error')

    return render_template('v2_add_file_to_project.html', form=form, project=project)


@app.route('/projects/<int:project_id>/files/<int:file_id>')
def route_v2_project_project_id_files_file_id(project_id, file_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    file = File.query.get(file_id)
    if file is None:
        abort(404)

    return render_template('v2_file.html', project=project, file=file)


@app.route('/projects/<int:project_id>/files/<int:file_id>/delete')
def route_v2_project_project_id_files_file_id_delete(project_id, file_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    file = File.query.get(file_id)
    if file is None:
        abort(404)

    db.session.delete(file)
    db.session.commit()

    flash('File <samp>{filename}</samp> successfully removed from project.'.format(filename=file.filename),
          category='message')

    return redirect(url_for('route_v2_project_project_id', project_id=project.id))


@app.route('/projects/<int:project_id>/patches')
def route_v2_project_project_id_patches(project_id):
    # retrieve project
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    # retrieve parameters
    page = int(request.args.get('page', 1))
    patch_state = request.args.get('patch_state')
    confirmation_state = request.args.get('confirmation_state')
    run_state = request.args.get('run_state')

    # initial patch query
    patches = Patch.query.filter(Patch.project_id == project_id)

    # filter patch state and confirmation state
    if patch_state:
        patches = patches.filter(Patch.state == patch_state)
    if confirmation_state:
        patches = patches.filter(Patch.confirmation == confirmation_state)
    if run_state:
        patches = patches.join(Run).filter(Run.log == run_state)

    # add pagination
    patches = patches.paginate(page, app.config['ITEMS_PER_PAGE'], False)

    return render_template('v2_patches.html', project=project, patches=patches, filter_patch_state=patch_state,
                           filter_confirmation_state=confirmation_state, filter_run_state=run_state)


@app.route('/projects/<int:project_id>/patches/<int:patch_id>', methods=['GET', 'POST'])
def route_v2_project_project_id_patches_patch_id(project_id, patch_id):
    # retrieve project
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    # retrieve patch
    patch = Patch.query.get(patch_id)
    if patch is None:
        abort(404)

    # retrieve parameters
    filter_patch_state = request.args.get('filter_patch_state')
    filter_confirmation_state = request.args.get('filter_confirmation_state')
    filter_run_state = request.args.get('filter_run_state')

    form = SetConfirmationForm()

    if request.method == 'GET':
        form.confirmation.data = patch.confirmation
    else:
        patch.confirmation = form.confirmation.data
        db.session.commit()

    # retrieve previous and next patch id
    filtered_patches = Patch.query
    if filter_patch_state:
        filtered_patches = filtered_patches.where(Patch.state == filter_patch_state)
    if filter_confirmation_state:
        filtered_patches = filtered_patches.where(Patch.confirmation == filter_confirmation_state)
    if filter_run_state:
        filtered_patches = filtered_patches.join(Run).filter(Run.log == filter_run_state)

    previous_patch = filtered_patches.where(Patch.id < patch.id).order_by(Patch.id.desc()).first()

    next_patch = filtered_patches.where(Patch.id > patch.id).order_by(Patch.id).first()

    return render_template('v2_patch.html', project=project, patch=patch, form=form,
                           filter_patch_state=filter_patch_state, filter_confirmation_state=filter_confirmation_state,
                           filter_run_state=filter_run_state, previous_patch=previous_patch, next_patch=next_patch)


@app.route('/projects/<int:project_id>/files/<int:file_id>/generate', methods=['GET', 'POST'])
def route_v2_project_project_id_files_file_id_generate(project_id, file_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    file = File.query.get(file_id)
    if file is None:
        abort(404)

    if request.method == 'POST':
        try:
            first_line = int(request.form.get('first_line'))
        except ValueError:
            first_line = 1

        try:
            last_line = int(request.form.get('last_line'))
        except ValueError:
            last_line = -1

        s = SourceFile(file, first_line, last_line)
        s.generate_patches()
        flash('Successfully created patches.', category='message')
        return redirect(url_for('route_v2_project_project_id', project_id=project.id))

    else:
        return render_template('v2_generate_patches.html', project=project, file=file)


@app.route('/projects/<int:project_id>/patches/<int:patch_id>/runs/<int:run_id>')
def route_v2_project_project_id_patches_patch_id_runs_run_id(project_id, patch_id, run_id):
    project = Project.query.get(project_id)
    if project is None:
        abort(404)

    patch = Patch.query.get(patch_id)
    if patch is None:
        abort(404)

    run = Run.query.get(run_id)
    if run is None:
        abort(404)

    return render_template('v2_run.html', project=project, patch=patch, run=run)


@app.route('/mutators')
def route_v2_mutators():
    return render_template('v2_mutators.html')


@app.route('/mutators/<mutator_id>')
def route_v2_mutators_mutator_id(mutator_id):
    mutator = get_mutators().get(mutator_id)

    # retrieve parameters
    page = int(request.args.get('page', 1))

    # initial query
    patches = Patch.query.filter(Patch.kind == mutator_id)

    # add pagination
    patches = patches.paginate(page, app.config['ITEMS_PER_PAGE'], False)

    if mutator is None:
        abort(404)

    return render_template('v2_mutator.html', mutator=mutator, patches=patches)
