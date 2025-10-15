from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.web import bp
from app.models.user import User
from app import db


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Account is disabled', 'error')
            return render_template('auth/login.html')
        
        login_user(user, remember=True)
        flash('Login successful', 'success')
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        return redirect(url_for('web.dashboard'))
    
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('web.login'))


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Password recovery page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not email or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/reset_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/reset_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found', 'error')
            return render_template('auth/reset_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        
        flash('Password reset successful. You can now login with your new password.', 'success')
        return redirect(url_for('web.login'))
    
    return render_template('auth/reset_password.html')