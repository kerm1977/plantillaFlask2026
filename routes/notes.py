from . import notes_admin
from routes import bp

bp.add_url_rule('/api/notes', view_func=notes_admin.list_notes, methods=['GET'])
bp.add_url_rule('/api/notes', view_func=notes_admin.create_note, methods=['POST'])
bp.add_url_rule('/api/notes/<int:note_id>', view_func=notes_admin.update_note, methods=['PUT'])
bp.add_url_rule('/api/notes/<int:note_id>', view_func=notes_admin.delete_note, methods=['DELETE'])
bp.add_url_rule('/api/notes/<int:note_id>/share', view_func=notes_admin.share_note, methods=['POST'])
bp.add_url_rule('/api/notes/<int:note_id>/unshare', view_func=notes_admin.unshare_note, methods=['POST'])