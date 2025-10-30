import os
import logging
from flask import request, flash, redirect, url_for, render_template, Response, abort, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app.api import bp
from app.models.update_mobile_app import PsysuiteApplication
from app.api.forms import MobileApplicationForm
from app.utils.decorators import admin_required
from app import db


@bp.route('/psysuite/versions', methods=['GET'])
@login_required
@admin_required
def psysuite_versions():
    """List all PsySuite versions"""
    try:
        versions = PsysuiteApplication.query.order_by(PsysuiteApplication.version.desc()).all()
        latest = PsysuiteApplication.get_latest()
        
        return render_template('admin/psysuite_versions.html', 
                             versions=versions, 
                             latest=latest)
    except Exception as e:
        logging.error(f"Error loading PsySuite versions: {e}")
        flash('Error loading versions', 'error')
        return redirect(url_for('web.dashboard'))


@bp.route('/psysuite/new', methods=['GET', 'POST'])
@login_required
@admin_required
def psysuite_application_new():
    """Create new PsySuite version"""
    form = MobileApplicationForm()
    
    # Pre-populate form with next version number
    latest = PsysuiteApplication.get_latest()
    if latest and request.method == 'GET':
        form.version.data = latest.version + 1
        # Suggest next version string (increment patch version)
        if latest.sver:
            try:
                parts = latest.sver.split('.')
                if len(parts) >= 3:
                    parts[2] = str(int(parts[2]) + 1)
                    form.sver.data = '.'.join(parts)
                else:
                    form.sver.data = latest.sver
            except:
                form.sver.data = latest.sver
    
    if form.validate_on_submit():
        try:
            # Check if version already exists
            existing = PsysuiteApplication.query.filter_by(version=form.version.data).first()
            if existing:
                flash(f'Version {form.version.data} already exists', 'error')
                return render_template('admin/psysuite_application_new.html', form=form, latest=latest)
            
            # Create APK directory if it doesn't exist
            apk_dir = os.path.join(current_app.instance_path, 'apk')
            os.makedirs(apk_dir, exist_ok=True)
            
            # Save APK file
            filename = f'psysuite_v{form.version.data}.apk'
            filepath = os.path.join(apk_dir, filename)
            form.apk.data.save(filepath)
            
            # Create database record
            mobile_application = PsysuiteApplication(
                version=form.version.data,
                sver=form.sver.data,
                description=form.description.data,
                apk_path=filepath,
                created_by=current_user.email
            )
            
            db.session.add(mobile_application)
            db.session.commit()
            
            flash(f'PsySuite version {form.sver.data} (v{form.version.data}) uploaded successfully', 'success')
            return redirect(url_for('api.psysuite_versions'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Version number already exists', 'error')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating PsySuite version: {e}")
            flash('Error uploading new version', 'error')
    
    return render_template('admin/psysuite_application_new.html', form=form, latest=latest)


@bp.route('/psysuite/latest', methods=['GET'])
@login_required
@admin_required
def psysuite_application_latest():
    """View latest PsySuite version details"""
    latest = PsysuiteApplication.get_latest()
    return render_template('admin/psysuite_application_detail.html', mobile_application=latest)


# Public API endpoints for Android app
@bp.route('/psysuitestableupdate.xml')
def psysuitestableupdate():
    """XML endpoint for Android app to check for updates"""
    try:
        logging.info("PsySuite update check requested")
        mobile_application = PsysuiteApplication.get_latest()
        
        if not mobile_application:
            logging.warning("No PsySuite versions available")
            abort(404)
        
        xml_response = mobile_application.stableupdate(request.host_url)
        logging.info(f"Serving update info for version {mobile_application.version}")
        
        return Response(response=xml_response, status=200, mimetype="application/xml")
        
    except Exception as e:
        logging.error(f"Error serving update XML: {e}")
        abort(500)


@bp.route('/psysuitestableupdate_plain.xml')
def get_update_plain():
    """Plain HTTP version of update XML for Android compatibility"""
    try:
        logging.info("PsySuite plain HTTP update check requested")
        mobile_application = PsysuiteApplication.get_latest()
        
        if not mobile_application:
            logging.warning("No PsySuite versions available")
            return Response('<?xml version="1.0"?><error>No versions available</error>',
                          mimetype='application/xml'), 404
        
        xml_response = mobile_application.stableupdate(request.host_url)
        logging.info(f"Serving plain HTTP update info for version {mobile_application.version}")
        
        return Response(response=xml_response, status=200, mimetype="application/xml")
        
    except Exception as e:
        logging.error(f"Error serving plain HTTP update XML: {e}")
        return Response(f'<?xml version="1.0"?><error>{str(e)}</error>',
                       mimetype='application/xml'), 500


@bp.route('/psysuite.apk')
def psysuite_apk():
    """Download endpoint for latest PsySuite APK"""
    try:
        mobile_application = PsysuiteApplication.get_latest()
        
        if not mobile_application:
            logging.warning("No PsySuite APK available")
            abort(404)
        
        if not os.path.exists(mobile_application.apk_path):
            logging.error(f"APK file not found: {mobile_application.apk_path}")
            abort(404)
        
        logging.info(f"Serving APK download for version {mobile_application.version}")
        
        return send_file(
            mobile_application.apk_path, 
            mimetype='application/vnd.android.package-archive',
            as_attachment=True,
            download_name=f'psysuite_v{mobile_application.version}.apk'
        )
        
    except Exception as e:
        logging.error(f"Error serving APK: {e}")
        abort(500)