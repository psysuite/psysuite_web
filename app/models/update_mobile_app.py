from datetime import datetime
from app import db


class PsysuiteApplication(db.Model):
    __tablename__ = "mobile_applications"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False, unique=True)
    sver = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=True)
    apk_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<PsysuiteApplication v{self.version} ({self.sver})>'

    def stableupdate(self, host_url):
        """Generate XML update response for Android app"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<update>
    <version>{self.version}</version>
    <sver>{self.sver}</sver>
    <description><![CDATA[{self.description or ''}]]></description>
    <name>PsySuite</name>
    <url>{host_url}api/psysuite.apk</url>
</update>'''

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'version': self.version,
            'sver': self.sver,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

    @staticmethod
    def get_latest():
        """Get the latest version"""
        return PsysuiteApplication.query.order_by(PsysuiteApplication.version.desc()).first()