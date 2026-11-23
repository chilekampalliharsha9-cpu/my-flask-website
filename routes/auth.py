from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.models import User, EmergencyContact, Volunteer

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        is_volunteer = bool(request.form.get('is_volunteer'))

        if not username or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already registered. Please choose a different one.', 'warning')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please log in.', 'warning')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            phone=phone,
            address=address,
            is_volunteer=is_volunteer,
            volunteer_status='Available' if is_volunteer else 'Offline'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # If registered as volunteer, create volunteer record
        if is_volunteer:
            skills = request.form.get('skills', 'General Emergency Relief, Evacuation Assistance')
            volunteer = Volunteer(
                user_id=user.id,
                skills=skills,
                location=address or 'City Center',
                available=True,
                status='Available',
                contact_number=phone or 'N/A'
            )
            db.session.add(volunteer)
            db.session.commit()

        flash('Account registered successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            if session.get('mobile_app'):
                return redirect(url_for('main.index'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.address = request.form.get('address', '').strip()
        
        # Volunteer toggle
        is_vol = bool(request.form.get('is_volunteer'))
        current_user.is_volunteer = is_vol
        
        vol_status = request.form.get('volunteer_status', 'Available')
        current_user.volunteer_status = vol_status

        # Update volunteer profile if exists or create
        if is_vol:
            skills = request.form.get('skills', 'First Aid, Evacuation')
            vol = Volunteer.query.filter_by(user_id=current_user.id).first()
            if not vol:
                vol = Volunteer(
                    user_id=current_user.id,
                    skills=skills,
                    location=current_user.address or 'City Center',
                    available=True,
                    status=vol_status,
                    contact_number=current_user.phone or 'N/A'
                )
                db.session.add(vol)
            else:
                vol.skills = skills
                vol.location = current_user.address or vol.location
                vol.status = vol_status
                vol.contact_number = current_user.phone or vol.contact_number

        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    vol_profile = Volunteer.query.filter_by(user_id=current_user.id).first()
    return render_template('profile.html', contacts=contacts, volunteer_profile=vol_profile)


@auth_bp.route('/contacts/add', methods=['POST'])
@login_required
def add_contact():
    name = request.form.get('contact_name', '').strip()
    phone = request.form.get('contact_phone', '').strip()
    relationship = request.form.get('contact_relation', 'Family').strip()

    if name and phone:
        contact = EmergencyContact(
            user_id=current_user.id,
            name=name,
            phone=phone,
            relationship=relationship
        )
        db.session.add(contact)
        db.session.commit()
        flash(f'Emergency contact {name} added successfully.', 'success')
    else:
        flash('Please provide both contact name and valid phone number.', 'danger')

    return redirect(url_for('auth.profile'))


@auth_bp.route('/contacts/delete/<int:contact_id>', methods=['POST', 'GET'])
@login_required
def delete_contact(contact_id):
    contact = EmergencyContact.query.get_or_404(contact_id)
    if contact.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.profile'))

    db.session.delete(contact)
    db.session.commit()
    flash('Emergency contact removed.', 'info')
    return redirect(url_for('auth.profile'))
